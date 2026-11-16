---
name: live-test
description: Test a built or repaired actor against the live target with its fixed fixture set and apply the unit economics gate. Use when an item is in `built`, or when a repair pull request for a `degraded` actor has green CI. This is the factory's backtest and it is a hard gate before any publish packet.
---

# Live test

You are a fresh session. Read `CLAUDE.md`, `budget.yaml` (sections `unit_economics` and `per_item`) and `FACTORY_SPEC.md` section 5 first. Complete steps 1 to 3 of the operating loop. Work on at most 2 items.

You do not hold an Apify token and you do not run the actor yourself. A GitHub Actions workflow does the platform work. Your job is to start it, read its result files and apply the outcome it computed.

## Inputs

- Item in `built` (or `degraded` with a green repair pull request), its merged or approved branch, `fixtures/<id>/inputs.json`, `expected.schema.json`, `fixture_set_hash`.
- `budget.yaml`.

## Steps

1. Check attempts and money. If `per_item.max_live_test_attempts` is used up, kill (unpublished) or raise `F-REP-1` (published). Use the `ledger` skill to confirm the prepaid drawdown cap has room for `max_live_test_platform_usd`. If not, raise `BUD-1`.
2. Confirm `fixture_set_hash` matches the files. If the fixtures changed since the spec, the run report must say why. Do not test against a fixture set edited to suit the code.
3. Trigger the `fixture-run` workflow for the item and commit through the GitHub connector. The workflow (deterministic, no model):
   - reruns `scripts/deny_check`,
   - pushes a private build to Apify,
   - runs the full fixture set 3 times, spaced apart, at the spec's rate limits,
   - collects per-run results, platform cost, duration, HTTP status counts,
   - writes `state/metrics/runs/<id>-livetest-<date>.json`,
   - runs `scripts/unit_econ` and writes the `unit_econ` block.
4. Wait for the workflow. If it is still running when your run cap is near, write a run report saying "workflow pending" and exit. The next run picks it up.
5. Read the result file. Do not recompute its numbers. Copy into the item: fixture pass rate, schema validity, block rate, `cost_p90`, `price_per_result_usd`, multiple, `net_per_result`, zero-result run cost, pass or fail for each gate.
6. Apply the outcome:
   - All gates pass: new build moves `built -> tested`. A repair is marked ready for promotion (`F-REP-1` unless auto promotion is enabled in `budget.yaml`).
   - Fixture pass rate under `min_fixture_pass_rate`: first time, move `built -> specified` with a defect note naming the failing fixtures. Second time, kill.
   - Block rate over `max_block_rate`: kill an unpublished item. This is not a defect to fix.
   - Unit economics fail: check whether the gate would pass at a higher price that is still under `max_price_per_result_usd`. If yes, set that price, record it, and keep the result as a pass at the new price. If no, kill.
   - Live results differ from snapshots because the site changed: request fresh snapshots (`capture-fixtures`), move back to `specified` once.
7. Record the Apify cost of the test with the `ledger` skill (category `infra`, vendor `apify`, source the workflow's cost figure, marked prepaid when it came from Creator plan usage) and add it to the item's `spend_usd`.
8. Compare measured cost per result with the spec's prediction and write both numbers in the run report. The weekly review uses the gap.

## Tools

- GitHub connector: trigger `fixture-run`, read workflow status and the committed result file.
- Bash: `scripts/validate_item` only.
- Shared `ledger` and `escalate` skills.
- Haiku is enough unless a failure needs diagnosis, then Sonnet.

## Deterministic check

The result file written by the workflow is the check. Required to pass: 3 completed runs, fixture pass rate at or above `min_fixture_pass_rate`, 100% of returned items valid against the schema, block rate at or under `max_block_rate`, and every line of the `unit_econ` block true:

- `price >= price_multiple_of_cost x cost_p90`
- `price <= max_price_per_result_usd`
- `price x (1 - apify_commission) - cost_p90 > 0`
- zero-result run cost at or under `max_zero_result_run_usd`
- runtime and item bounds observed in every run

Paste the gate lines from the file in the run report with the file path and commit.

## Outputs

- `state/metrics/runs/<id>-livetest-<date>.json` (from the workflow).
- Item in `tested`, `specified` or `killed`, with `unit_econ` filled in.
- Ledger line for platform cost.

## Stop conditions

- `STOP` or budget cap.
- Workflow fails for a platform reason (build error, auth error, quota): report the log lines. Do not retry more than once in a run. A token or auth error is `F-ACCT-1`.
- Test platform cost exceeds `max_live_test_platform_usd`: the workflow aborts. Treat as a unit economics fail.

## Never

- Never run fewer than 3 fixture runs, drop a failing fixture, or exclude failed runs from the cost figure.
- Never compute or "correct" unit economics yourself. Only `scripts/unit_econ` output counts.
- Never lower `price_multiple_of_cost`, raise the price ceiling, or treat prepaid usage as free when computing cost.
- Never ask for, print or store the Apify token. Never edit the workflow.
- Never make the private build public.
- Never respond to blocks with retries beyond the spec, proxies or evasion.

End by calling the shared `run-report` skill.
