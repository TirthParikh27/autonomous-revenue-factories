---
name: demand-test
description: Stage 4 of Factory A. Use when items sit at `specced` to prepare a batch of landing pages with a visible price and paused ad campaigns, raise one approval packet for the batch, and move items through tranche 1 (ad click test) and tranche 2 (fake door with price). Measurement and kill decisions belong to telemetry-winner-detection.
---

# Demand test

No app is built until an idea passes both tranches with real paid traffic. You prepare assets and paused campaigns. The operator approves the batch and activates it. Read `CLAUDE.md` and `budget.yaml` first.

## Why real traffic

Strangers who see an ad owe the idea nothing. What they click and whether they leave an email after seeing a price is behaviour. A synthetic panel, a survey or the `synthetic-screen` score is an opinion. Only behaviour passes an idea here.

## Inputs

- Items at `specced`, up to `ads.max_ideas_per_batch` and the free slots under `pipeline.max_concurrent_demand_tests`.
- `state/specs/<id>.md`, including the proposed price.
- `data/landing_template/`, `data/privacy_notice.md` (operator-approved text).
- The `ads` and `demand_test` sections of `budget.yaml`.

## Steps: preparing a batch

1. Preparing a batch costs tokens only, so prepare it even when the ads cap is 0 or accounts do not exist yet. Note what is missing: if `monthly_caps_usd.ads` does not cover the batch's tranche 1 budget, raise `BUD-1` with the amount needed. Do not stop.
2. If this is the factory's first early-access list and no `PII-1` packet is in `escalations/approved/`, raise it. Do not stop. No page is deployed and no email is collected until it is approved.
3. For each idea, create `demand/<id>/site/`: one static page that states the job and the differentiation in the brand's voice, the words "in development", the proposed price on a "Get early access at $X a month" button, and a privacy link. Clicking the button fires `price_click` and opens a form that says the app is not available yet and nothing is charged today, with one email field and a consent line. Submitting fires `committed_signup`. No payment is taken at any point.
4. For each idea, write three ad creatives to `demand/<id>/ads/` (image or short motion from designed mock-ups labelled as concept, primary text, headline) and `demand/<id>/claims.yaml`.
5. Check each idea: the site builds, all three events fire, the price matches the spec, the "in development" and "nothing is charged today" lines and the privacy link are present, and no creative shows a mock-up as a shipping app. Run `checks/copy_lint --pre-build --has-price` on the page and ads. Drop ideas you cannot get right.
6. Write `demand/batches/<batch>/plan.json`: per idea, the page path, the three creatives, the tranche 1 lifetime budget and duration from `budget.yaml`, the audience (broad, one country, the platform's own targeting), and the tracking parameters.
7. Open one pull request with the batch's pages and raise one `A-AD-1` packet for the whole batch. Move the items to `awaiting_human`.

## Steps: after approval

8. Go past this point only when the `A-AD-1` packet and `PII-1` are in `approved/`, and the ads cap covers the batch. Otherwise stop here and report what is waiting. When the pull request is merged, CI deploys the pages. Fetch each public URL and confirm it returns the page.
9. Run `python3 publish.py ads demand/batches/<batch>/plan.json --packet A-AD-1`. It creates one paused campaign per idea and reads each back. Until ad credentials exist it runs dry and writes `readback.json` without contacting Meta.
10. The operator activates the batch in Ads Manager and writes `demand_test.activated` into the batch file. When that date is present, move the items to `demand_t1`.
11. Tranche 2: when telemetry moves an item to `demand_t2`, create the tranche 2 campaign for it with `publish.py ads`, paused, using the best-performing creative. It is covered by the same `A-AD-1` packet, which states both tranche budgets. The operator activates. A top-up, where telemetry calls one, is created the same way.

## Hard checks

- `checks/copy_lint` fails any testimonial, rating, user count, "available now" wording or missing "in development" line.
- `checks/ads_paused` exits non-zero unless every campaign in the batch reads back as paused, with a lifetime budget equal to the plan and at or under the ceiling in `budget.yaml`, and the batch total is under the month's remaining ads cap. A create call returning success is not the evidence. The read-back is.

## Outputs

- `demand/<id>/site/`, `demand/<id>/ads/`, `demand/<id>/claims.yaml`, `demand/batches/<batch>/plan.json`.
- One pull request and one `A-AD-1` packet per batch.
- Items at `awaiting_human`, then `demand_t1`, `demand_t2`.

## Stop conditions

- Ads cap or account spending limit not set: `BUD-1`. This stops the steps after approval, not the preparation.
- Meta, Cloudflare or any other account does not exist yet: `ACC-1`. Same: prepare the batch, stop before step 8.
- An ad is rejected by the platform: record the reason, do not resubmit a reworded copy more than once, and raise `GEN-1` if two ideas in one batch are rejected.
- The packet expires: the items are parked.

## Never

- Never set a campaign to active, raise a budget, or create a campaign outside `plan.json`.
- Never take a payment, a deposit or card details on a test page.
- Never say or imply that the app is available now, show download counts or ratings, or use a testimonial.
- Never read, export or email the early-access list. Telemetry reads counts only.
- Never extend a tranche or move an item between tranches yourself. Telemetry makes those calls.
- Never start app code for the item.

## Finish

End by calling the shared `run-report` skill. Include both check outputs, the batch total, and the read-back status of every campaign.
