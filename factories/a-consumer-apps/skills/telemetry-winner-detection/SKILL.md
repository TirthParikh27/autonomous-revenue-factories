---
name: telemetry-winner-detection
description: Stage 7 of Factory A. Use on the daily telemetry run to pull demand-test, store and RevenueCat metrics, record verified revenue in the ledger, and apply the numeric kill and winner rules to items at `demand_testing`, `submitted`, `live` or `winner`.
---

# Telemetry and winner detection

Read-only against every external system. A script decides transitions. You fetch, record and report. Read `CLAUDE.md` and `budget.yaml` first.

## Inputs

- Items at `demand_testing`, `submitted`, `live`, `winner`.
- `demand_test`, `live_checkpoints`, `winner` and `validation` sections of `budget.yaml`.
- `state/metrics/inbox/`: App Store Connect exports and post reach figures dropped in by the operator.
- `state/submissions.jsonl`.
- `ledger/spend.jsonl`, `ledger/revenue.jsonl`.

## Steps

1. **Demand tests.** For each item at `demand_testing`, read from PostHog the unique visitors and `waitlist_signup` events since `demand_test.first_published`. Read the waitlist row count from Supabase as a cross-check. Count only, never the rows. If the two counts differ by more than 10%, record both and flag it.
2. **Listing check.** For each item at `submitted`, fetch the public store URL recorded by the operator. If it returns the listing, move the item to `live` and set `live_at`.
3. **Subscriptions.** For each app at `live` or `winner`, read from the official RevenueCat MCP: trials started, trial to paid, active subscriptions, MRR, refunds, churn.
4. **Store data.** Read first-time downloads and proceeds from the newest file in `state/metrics/inbox/`, or from a reports-only credential if the operator has set one up. Record the file name and its date. If the newest data is more than 7 days old, say so and do not run day-based checkpoints on stale numbers.
5. Write everything to `state/metrics/<date>.json`, each number with its source and read time.
6. **Revenue.** Use the shared `ledger` skill. Record store proceeds per app net of commission, with the report reference. If only RevenueCat is available, record gross with `net_of_fees: false`. Record refunds as negative lines. Never record the same period twice. Check the last reference first.
7. **Decide.** Run `checks/decide state/metrics/<date>.json`. Apply exactly the transitions it emits:
   - `demand_testing` to `demand_validated` or `killed` at day 14.
   - `demand_validated` to `killed` when stale.
   - Live checkpoint failed at day 14, 35, 60 or 90: raise `A-SUN-1`.
   - Winner rule or early signal met: move to `winner` and raise `A-WIN-1`.
8. **Factory budget.** Sum all spend. If the validation budget or window is exhausted and `ledger/revenue.jsonl` has no verified line, raise `BUD-2`.
9. Post one Slack line: items moved, revenue recorded today, spend month to date.

## Tools

RevenueCat official MCP with the narrowest available key, PostHog connector, Supabase connector (count queries only), WebFetch for public listing URLs, Read, Write, the `checks/decide` script.

## Deterministic check

`checks/decide` reads the metrics file and `budget.yaml` and prints one line per item: the rule evaluated, the value, the threshold, the result. It refuses to evaluate a rule whose inputs are missing or stale and prints `insufficient data` instead. You may not move an item the script did not name. Paste its full output in the run report.

## Outputs

- `state/metrics/<date>.json`.
- Ledger revenue lines.
- Item transitions and any `A-SUN-1`, `A-WIN-1`, `BUD-2` packets.

## Stop conditions

- A source is unreachable: record the gap, do not estimate, continue with the others.
- RevenueCat and store proceeds disagree by more than 20% for the same period: record both, add no revenue line for that period, and raise `GEN-1`.
- You discover the key in use can write to RevenueCat or Supabase: report it as a finding in the run report.

## Never

- Never record revenue from your own estimate, a dashboard screenshot, a third-party estimator, or views.
- Never treat views, likes or follower counts as a winner signal.
- Never extend a checkpoint, round a value over a threshold, or skip a kill because the trend "looks good".
- Never write to RevenueCat, PostHog, Supabase or the store. Never change a price, offering or paywall.
- Never read or export waitlist emails or customer identifiers into the repo.
- Never remove an app from sale or mark a live app `killed` without an approved `A-SUN-1`.

## Finish

End by calling the shared `run-report` skill. Include the `checks/decide` output, each revenue line's source reference, and every metric that was missing or stale.
