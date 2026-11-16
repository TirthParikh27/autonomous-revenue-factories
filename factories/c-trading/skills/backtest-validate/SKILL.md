---
name: backtest-validate
description: Read the CI backtest and overfitting verdicts for Factory C items at `implemented`, then kill or advance them. Use daily when any item is waiting on a trial result. This skill reads verdicts; it never runs a backtest or computes a metric.
---

# Backtest and validate

Stage: `implemented` -> `validated` or `killed`. Batch: up to 5 items per run.

The backtest itself is a GitHub Actions job with no model in it. For each trial request it:
1. refuses the request if the family, window or holdout budget is used up;
2. appends a line to `registry/trials.jsonl` before running (trial id, strategy, family, code hash, params hash, data snapshot hash, previous line hash);
3. runs the engine on development data with costs and slippage, then walk-forward;
4. computes PBO and the deflated Sharpe ratio over all logged trials, and the return-correlation cluster;
5. runs `engine/gate_check`, writing `results/<trial id>/metrics.json` and `gate.json`;
6. only if every gate passes, runs the one holdout evaluation for the cluster and adds `holdout: pass|fail` to `gate.json`.

## Inputs

- `budget.yaml`, `STOP` files, `escalations/`.
- Items at `implemented`, their trial ids.
- `registry/trials.jsonl`, `results/<trial id>/gate.json`, `results/<trial id>/metrics.json`. Read only.

## Steps

For each item:

1. Find its registry line. If the request is older than 48 hours with no registry line, record it and raise `F-INT-1`. Do not re-request.
2. If the registry line exists but `gate.json` does not, the job is still running or failed. Check the workflow status with `gh`. Leave the item, note it under "Not done".
3. Read `gate.json`. Copy into the item's `scores`: each gate's value, threshold and pass or fail, with the file path as source. Copy the `cluster` id.
4. Decide by the file, with no judgement applied:
   - Any gate `fail`, or `holdout: fail` -> `killed`. The reason is the first failed gate's name and value.
   - `refused: budget` -> `killed` with reason "family trial budget used", or raise `F-VAL-1` if it was the window budget.
   - All gates pass and `holdout: pass` -> `validated`.
5. For a `validated` item: if a paper slot is free, raise `F-PAPER-1` with the `escalate` skill (packet contents in `ESCALATION.md`) and set `awaiting_human`. If no slot is free, leave it at `validated`.
6. Append the transition to `history`. Comment the verdict on the strategy PR in one line with the `gate.json` path.

## Tools

Read, Write (item files only), `gh` for workflow status and PR comments, shared `escalate` skill.

## Deterministic check

- `engine/registry_verify` output (hash chain intact, line count). Paste it.
- For each item, the `gate.json` path and its verdict line, pasted.
- The item's new stage must equal the stage implied by `gate.json`. The wrapper compares them.

## Outputs

Updated item files, PR comments, possibly one `F-PAPER-1` packet per validated item, run report with a table: item, first failed gate, value, threshold.

## Stop conditions

- `registry_verify` fails: stop everything, raise `F-INT-1`.
- A result file exists with no registry line, or the hashes disagree: `F-INT-1`.
- No items waiting: write the report and exit.

## Never

- Never compute, estimate or "sanity check" a metric yourself. If a number looks wrong, raise `F-ENG-1` with the file.
- Never describe a killed strategy as "close", "promising" or "worth another look".
- Never ask for the holdout numbers. Pass or fail is all there is.
- Never re-request a trial for a killed item.
- Never report metrics for a passing strategy without also reporting the registry trial count they were deflated against.

"All items killed" is the expected report. Write it plainly.

End by calling the shared skill `factories/_shared/skills/run-report`.
