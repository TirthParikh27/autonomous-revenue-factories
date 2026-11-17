# Approve the first demand-test batch: 3 ideas, tranche 1 at $30 each
Factory: a-consumer-apps   Item: batch 2026-11-17-b1 (3 items)   Trigger: A-AD-1   Raised: 2026-11-17   Expires: 2026-11-24

## What I want to do
Deploy three concept landing pages and create three PAUSED Meta campaigns (US, broad, 18+, 3 days, $30 lifetime each) from `demand/batches/2026-11-17-b1/plan.json`. You activate them. This packet also covers tranche 2 ($170, 7 days) and one $100 top-up per idea that telemetry advances.

| Idea | Job | Price shown | Files |
|---|---|---|---|
| 2026-11-17-lecture-recording-never-lost | Lecture recorder that saves audio as you record and recovers interrupted recordings | $4.99 a month | `demand/<id>/site/`, `ads/` (3 concept cards + copy), `claims.yaml` |
| 2026-11-17-private-journal-that-never-loses-entries | Local-only journal, no AI, backup you can test restoring | $3.99 a month | same layout |
| 2026-11-17-source-faithful-ai-study-material | Study cards built only from your own notes, each with its source (never called AI) | $5.99 a month | same layout |

Each page says "in development", shows the price on the button, states nothing is charged today, and links a privacy page. Events: `page_view`, `price_click`, `committed_signup`. Prices are the specs' intentions; competitor prices were not checked (see run report).

## Why now (evidence)
Three items sit at `specced`. Only real traffic can pass them. `checks/copy_lint --pre-build --has-price`: OK, 6 files clean for each idea (this run). `checks/ads_paused` on the plan: FAIL only because `monthly_caps_usd.ads` is 0 (batch total $90 against a cap of $0), which is the BUD-1 condition.

## Cost and worst case
- Tranche 1: $90 (3 x $30). Tranche 2 plus top-up if all three advance: up to $810 (3 x $270). Most this packet can spend: $900.
- Worst case: the full batch budget spent with no idea passing. Also a possible Meta ad-account restriction (new account, subject-matter is subscription apps).
- Kill calls will weigh, not gate on: top third of the batch by cost per landing-page view, 1.0% link click-through, then 300+ visitors with at least 1% price-click-then-email (2% to pass), at most $30 per signup (`budget.yaml` `demand_test`).

## How to undo it
Campaigns are created paused and never activated by me. Do not activate, or pause in Ads Manager. Remove the pages by reverting the merge.

## If you say no
Items stay at `specced` and are parked after 30 days.

## What I am doing meanwhile
Nothing is deployed and no campaign exists. Items move to `awaiting_human`.

## Your steps
1. Raise `monthly_caps_usd.ads` (to at least $900 for the full packet, or $90 for tranche 1 only) and `total` in `budget.yaml`; set the Meta account spending limit.
2. Approve `PII-1` and `ACC-1` (Meta ad account, Cloudflare Pages, Supabase early-access table). Replace the DRAFT `privacy.html` in each site with the approved notice, and fill `CONFIG` (pixel id, signup endpoint, publishable key) at the top of each page's script.
3. Merge the batch pull request (not yet opened: this run could not run git or open a PR), then confirm each public URL.
4. Run `publish.py ads demand/batches/2026-11-17-b1/plan.json --packet A-AD-1`, activate in Ads Manager, and write `demand_test.activated` into the batch file.
5. Export the nine SVG cards to PNG for upload.
