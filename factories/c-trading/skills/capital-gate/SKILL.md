---
name: capital-gate
description: Assemble the evidence packet that asks the operator whether a paper-passed Factory C strategy should receive a first small live allocation. Use only when an item reaches `paper_passed`. This skill prepares a decision for a human; it never prepares, tests or enables live trading.
---

# Capital gate

Stage: `paper_passed` -> `awaiting_human` (trigger `F-CAP-1`). Batch: 1 item per run.

The default answer to this packet is no. Live allocation in `budget.yaml` is 0 and live keys do not exist. The packet's job is to let the operator say no quickly or yes with open eyes. Write it to inform, not to persuade.

## Inputs

- `budget.yaml` (`live`, `failure_policy.capital_packet_expiry_days`), `STOP` files, `escalations/`.
- The item, its card and the card's first commit hash.
- All registry lines for the item's family and cluster. `results/` for each. Read only.
- `paper/journal/` from `paper_start` to today.
- `ESCALATION.md`, section "`F-CAP-1` evidence packet".

## Steps

1. Check `escalations/` for an existing `F-CAP-1` packet on this item. If one was rejected, stop unless the evidence has materially changed, and say what changed. If one expired twice, move the item to `killed`.
2. Check that `F-LEGAL-1` and `F-LEGAL-2` have approved answers. If not, raise whichever is missing first and stop. A capital packet without them is incomplete.
3. Run `engine/registry_verify`. If it fails, raise `F-INT-1` and stop.
4. Build the packet at `escalations/open/<date>-live-<id>.md` with the ten sections listed in `ESCALATION.md`. Every figure is copied from a CI-written file and followed by its path.
5. In the trial log section, list every trial of the family and cluster, failed ones first. State the total registry count used for the deflated Sharpe ratio.
6. Delegate the "Known weaknesses" section to the `overfit-verifier` agent. Give it the packet draft and the file paths, not your summary. Include what it writes without softening it.
7. State the ask as the smallest step: one strategy, long only, no leverage, allocation at most `live.max_allocation_usd`. If that value is 0, say that the operator must raise it in `budget.yaml` by their own commit for approval to mean anything.
8. State what does not exist yet and must be built and reviewed by the operator before any live order: live runner, kill-switch flag file and watchdog, broker-side close on disconnect (availability unverified), credential storage out of agent reach.
9. Run `engine/packet_check <packet>`. Fix any mismatch by correcting the packet to the file, never the reverse.
10. Use the shared `escalate` skill to set `awaiting_human`, notify Slack and open the Linear issue. Expiry is `capital_packet_expiry_days`.

## Tools

Read, Write (the packet and the item file), the `overfit-verifier` agent, shared `escalate` skill, Slack and Linear connectors for the notification only.

## Deterministic check

- `engine/registry_verify` output, pasted.
- `engine/packet_check` output showing every number in the packet matches its source file, pasted in the packet and in the run report.

## Outputs

One packet, updated item, one Slack message, one Linear issue, run report.

## Stop conditions

- Any required figure is missing from CI-written files: do not estimate it. Record the gap and stop.
- `packet_check` fails twice: stop and report. Do not send a packet that fails.
- The strategy was killed by `paper-trade` between runs: stop.

## Never

- Never write, sketch or test live-trading code, and never look for live credentials.
- Never include a projected live return, an annualised paper figure, or a dollar estimate of future profit.
- Never omit a failed trial, a clock restart, a heartbeat gap or an `F-DIV-1` event.
- Never describe the packet as a recommendation to invest. Include the line: "This is not financial advice. Paper results are not revenue."
- Never raise `F-CAP-1` for more than one strategy at a time.
- Never treat anything except the operator's commit to `escalations/approved/` as approval.

End by calling the shared skill `factories/_shared/skills/run-report`.
