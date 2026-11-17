---
name: paid-test
description: Stage 7 of Factory A. Use when an item is at `live` to prepare paused campaigns optimised for trial start (installs for an iOS app, site visits for a web product), raise the spend approval, and move the app through paid tranche 1 and tranche 2. Kill and winner decisions belong to telemetry-winner-detection.
---

# Paid test

The demand test showed that people click and commit. This stage finds out whether they start trials and pay, and what each payer costs. Read `CLAUDE.md` and `budget.yaml` first.

## Inputs

- One item at `live`, with a free slot under `pipeline.max_concurrent_paid_tests`.
- The winning creative and audience from `demand/<id>/`, the app's store URL, `apps/<id>/store/claims.yaml`.
- The `ads.paid_t1`, `ads.paid_t2` and `paid_test` sections of `budget.yaml`.

## Steps

1. Confirm the trial-started and first-purchase events reach the ad platform as conversion events: from RevenueCat for an iOS app, from Stripe through the site for a web product. If the read-back shows no test event received, stop and report. A campaign that cannot see trials cannot be judged.
2. Write three creatives to `ads/<id>/paid/`. Use real screenshots and screen recordings from the shipped build. Remove the "in development" wording. Run `checks/copy_lint`.
3. Write `ads/<id>/paid/plan.json`: one campaign optimised for trial start, lifetime budget and duration for tranche 1, the tranche 2 budget that follows if tranche 1 passes, and the reference points telemetry will weigh, from `budget.yaml`.
4. Raise `A-AD-2` for the item. It covers both tranches, up to $600 in total. Move the item to `awaiting_human`.
5. When the packet is in `approved/`, run `python3 publish.py ads ads/<id>/paid/plan.json --packet A-AD-2`. It creates the tranche 1 campaign paused and reads it back. Until ad credentials exist it runs dry and writes `readback.json` without contacting Meta.
6. The operator activates and writes `paid_test.activated` into the item file. Move the item to `paid_t1`.
7. When telemetry moves the item to `paid_t2`, create the tranche 2 campaign the same way. The operator activates.
8. When telemetry judges the item a winner, it moves to `winner` and telemetry raises `A-WIN-1`. When it calls a kill, `A-SUN-1` is raised. In both cases the running campaign ends at its lifetime budget. Ask the operator in the packet to pause it sooner if the kill was on zero trials.

## Hard checks

- `checks/ads_paused` and `checks/copy_lint`, as in the demand test.

## Outputs

- `ads/<id>/paid/` creatives and plan, packet `A-AD-2`.
- Item at `awaiting_human`, `paid_t1`, `paid_t2`.

## Never

- Never activate a campaign, raise a budget, or create a third tranche. Scale spend exists only through `A-WIN-1`.
- Never change the app's price, trial length or paywall during a test.
- Never count a trial as a payer, or ad-platform-reported purchases as revenue. Payers come from RevenueCat and revenue from the store for iOS. For web both come from Stripe.
- Never use a testimonial, a rating or an invented user in an ad.

## Finish

End by calling the shared `run-report` skill. Include the conversion-event read-back and the `checks/ads_paused` output.
