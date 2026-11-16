---
name: paper-trade
description: Propose paper deployments for approved Factory C strategies and apply the paper-trading gates from the journal that CI writes. Use daily when any item is at `paper_trading`, or at `awaiting_human` with an approved `F-PAPER-1` packet. This skill never places an order and never talks to the broker.
---

# Paper trade

Stages: `awaiting_human` -> `paper_trading` -> `paper_passed` or `killed`. Batch: all items in those stages (at most `paper_gates.max_strategies_on_paper`).

Two scripts in GitHub Actions do the real work, with no model in them:
- **Runner**, every US trading day before the open: reads `paper/deployments.yaml` on `main`, checks `STOP`, loads each deployed strategy at its validated code hash, computes target weights from data up to the prior close, and submits orders to the Alpaca paper account within the runner's coded limits.
- **Journal**, every US trading day after the close: reads orders, fills and positions from the paper account and writes `paper/journal/<date>.json` (fills, assumed versus actual price, cost per side, divergence from market prints, heartbeat, equity, drawdown), then runs `engine/paper_gate`.

## Inputs

- `budget.yaml` (`paper_gates`), `STOP` files, `escalations/`.
- `paper/deployments.yaml`, `paper/journal/`, `results/<trial id>/gate.json`. Read only.
- Items at `awaiting_human` (trigger `F-PAPER-1`) and `paper_trading`.

## Steps

### A. Deploy (item has an approved `F-PAPER-1` packet)

1. Confirm the packet is in `escalations/approved/` on `main` and `paper_gates.enabled` is true. Otherwise stop for this item.
2. Delegate to the `paper-deployer` agent: open a PR that adds one entry to `paper/deployments.yaml` (strategy id, trial id, code hash, params hash, start date). Nothing else in the PR.
3. The operator merges it. Until the entry is on `main`, the item stays `awaiting_human`.
4. On a later run, when the entry is on `main` and the first journal file lists the strategy, move the item to `paper_trading` and set `paper_start`.

### B. Monitor (item at `paper_trading`)

1. Read the latest journal file and its `paper_gate` block for the strategy.
2. Copy to `state/metrics/<date>.json`: days, filled trades, mean absolute divergence in bps, measured cost per side, heartbeat status, drawdown, paper result. Each with the journal path.
3. Apply the verdict in the `paper_gate` block:
   - `kill` -> open a PR removing the deployment entry, move the item to `killed` with the gate name.
   - `clock_restart` -> increment `paper_clock_restarts`, reset `paper_start`. A second restart is a kill.
   - `pass` -> move to `paper_passed`. The `capital-gate` skill takes it from there.
   - `continue` -> no change.
4. If measured cost over at least 30 fills exceeds the assumed cost by more than 1.5x, raise `F-DIV-1`.
5. If the latest journal file is more than one trading day old, the journal or runner has failed. Report it and count it as a stage failure.

## Tools

Read, Write (item and metrics files), `gh`, the `paper-deployer` agent, shared `escalate` skill. No Alpaca tools, keys or MCP server.

## Deterministic check

- The journal file's own `paper_gate` verdict, pasted with its path.
- For a deployment: `gh pr view` output showing the PR touches only `paper/deployments.yaml`.
- For "first order appeared": the journal entry listing the order id, pasted. A merged PR is a request, not an outcome.

## Outputs

Deployment or removal PRs, item and metrics files, run report.

## Stop conditions

- `STOP` present: write nothing external, report.
- Journal shows positions or orders for a strategy not in `deployments.yaml`: raise `F-INT-1`.
- Journal shows any live-account identifier: raise `SEC-1` and write `Not done` for everything else.

## Never

- Never place, cancel or modify an order, and never ask for a broker key.
- Never call a paper result profit, return or revenue. Never write it to `ledger/revenue.jsonl`.
- Never propose a deployment whose code hash differs from the validated trial.
- Never restart, extend or shorten the paper clock yourself.
- Never deploy a variant in place of its parent. A variant needs its own trial, holdout rules and `F-PAPER-1`.

End by calling the shared skill `factories/_shared/skills/run-report`.
