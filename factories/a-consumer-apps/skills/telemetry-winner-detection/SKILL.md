---
name: telemetry-winner-detection
description: Stage 9 of Factory A. Use on the daily telemetry run to pull ad, landing-page, store and RevenueCat metrics, record verified revenue in the ledger, and make kill, advance and winner calls for items at `demand_t1`, `demand_t2`, `submitted`, `live`, `paid_t1`, `paid_t2` or `winner`.
---

# Telemetry and winner detection

Read-only against every external system. You fetch, record, decide transitions with evidence, and report. Read `CLAUDE.md` and `budget.yaml` first.

## Inputs

- Items at `demand_t1`, `demand_t2`, `submitted`, `live`, `paid_t1`, `paid_t2`, `winner`.
- `ads`, `demand_test`, `paid_test`, `winner` and `validation` sections of `budget.yaml`.
- `state/metrics/inbox/`: App Store Connect exports and post reach figures dropped in by the operator.
- `state/submissions.jsonl`.
- `ledger/spend.jsonl`, `ledger/revenue.jsonl`.

## Steps

0. **Ad spend.** For every active test, read spend, impressions, link clicks and landing-page views per campaign from the ad platform with the read-only reporting token. Record spend in the ledger with category `ads` and the campaign id as the source, once per day per campaign. If any campaign's spend exceeds its planned lifetime budget, or a campaign exists that is not in a plan file, raise `GEN-1` with priority `now`.
1. **Demand tests.** For each item at `demand_t1` or `demand_t2`, read from PostHog the unique visitors, `price_click` and `committed_signup` events since the batch's `demand_test.activated` date. Read the early-access row count from Supabase as a cross-check. Count only, never the rows. If the two counts differ by more than 10%, record both and flag it.
2. **Listing check.** For each item at `submitted`, fetch the public store URL recorded by the operator. If it returns the listing, move the item to `live` and set `live_at`.
3. **Subscriptions.** For each app at `live`, `paid_t1`, `paid_t2` or `winner`, read from the official RevenueCat MCP: trials started, trial to paid, active subscriptions, MRR, refunds, churn.
4. **Store data.** Read first-time downloads and proceeds from the newest file in `state/metrics/inbox/`, or from a reports-only credential if the operator has set one up. Record the file name and its date. If the newest data is more than 7 days old, say so and do not run day-based checkpoints on stale numbers.
5. Write everything to `state/metrics/<date>.json`, each number with its source and read time.
6. **Revenue.** Use the shared `ledger` skill. Record store proceeds per app net of commission, with the report reference. If only RevenueCat is available, record gross with `net_of_fees: false`. Record refunds as negative lines. Never record the same period twice. Check the last reference first.
7. **Decide.** For each test that has ended, weigh the numbers against the reference points in `budget.yaml`, the niche, the price point and the sample size. If inputs are missing, stale or trials have not matured, make no call and say so. Write each call in the run report with the numbers you used and why. The calls are:
   - `demand_t1` to `demand_t2` or `killed` when tranche 1 ends, ranked within its batch.
   - `demand_t2` to `demand_validated` or `killed`, or one top-up, when tranche 2 ends.
   - `paid_t1` to `paid_t2`, or `A-SUN-1`.
   - `paid_t2` to `winner` with `A-WIN-1`, or `A-SUN-1`.
   - Winner hold rule failed: `A-SUN-1`.
   - `demand_validated` to `killed` when stale.
   - After each batch's tranche 1 ends, append the rank correlation between the synthetic screen and real cost per landing-page view to `state/screen/accuracy.jsonl`.
8. **Factory budget.** Sum all spend. If the validation budget or window is exhausted and no item has reached `winner`, raise `BUD-2`.
9. Write one outbox line with priority `digest`: items moved, revenue recorded today, ad spend and total spend month to date.

## Tools

Ad platform reporting with a read-only token (no create or edit scope), RevenueCat official MCP with the narrowest available key, PostHog connector, Supabase connector (count queries only), WebFetch for public listing URLs, Read, Write.

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
- Never extend a checkpoint or skip a kill because the trend "looks good". A call either way needs numbers.
- Never write to the ad platform, RevenueCat, PostHog, Supabase or the store. Never pause, edit or create a campaign from this stage. If a campaign should stop early, say so in the packet for the operator. Never change a price, offering or paywall.
- Never read or export early-access emails or customer identifiers into the repo.
- Never remove an app from sale or mark a live app `killed` without an approved `A-SUN-1`.

## Finish

End by calling the shared `run-report` skill. Include every call with its numbers and reasoning, each revenue line's source reference, and every metric that was missing or stale.
