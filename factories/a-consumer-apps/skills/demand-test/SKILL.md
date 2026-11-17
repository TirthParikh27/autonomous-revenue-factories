---
name: demand-test
description: Stage 4 of Factory A. Use when items sit at `specced` to prepare a batch of landing pages with a visible price, demo video ads and paused ad campaigns, raise one approval packet for the batch, and move items through tranche 1 (ad click test) and tranche 2 (fake door with price). Measurement and kill decisions belong to telemetry-winner-detection.
---

# Demand test

No app is built until an idea passes both tranches with real paid traffic. You prepare assets and paused campaigns. The operator approves the batch and activates it. Read `CLAUDE.md` and `budget.yaml` first.

## Why real traffic

Strangers who see an ad owe the idea nothing. What they click and how far they go after seeing a price is behaviour. Nobody pays for an app they have not used, so the page takes no money. It asks for a series of small commitments instead, each costing the visitor a little more effort: tap the price, choose a plan, leave an email, answer one question. Someone who does all four wanted it. A synthetic panel, a survey or the `synthetic-screen` score is an opinion. Only behaviour passes an idea here.

## Inputs

- Items at `specced`, up to `ads.max_ideas_per_batch` and the free slots under `pipeline.max_concurrent_demand_tests`.
- `state/specs/<id>.md`, including the proposed price.
- `data/privacy_notice.md` if it exists (operator-approved text). If it does not, write a draft privacy page, mark it DRAFT, and ask for approval of the text in the `PII-1` packet. Pages are written per idea; there is no template.
- Competitor prices come from the scout file and the spec. Do not fetch competitor pages.
- The `ads` and `demand_test` sections of `budget.yaml`.

## Steps: preparing a batch

Work through the ideas one at a time and finish each completely (page, ads, checks, review) before starting the next. A run that ends with four finished ideas is better than one with fifteen half-made. A later run picks up the rest and adds them to the same batch before the packet is raised.

1. Preparing a batch costs tokens only, so prepare it even when the ads cap is 0 or accounts do not exist yet. Note what is missing: if `monthly_caps_usd.ads` does not cover the batch's tranche 1 budget, raise `BUD-1` with the amount needed. Do not stop.
2. If this is the factory's first early-access list and no `PII-1` packet is in `escalations/approved/`, raise it. Do not stop. No page is deployed and no email is collected until it is approved.
3. For each idea, create `demand/<id>/site/`: one static page, written for this idea, that states the job and the differentiation in the brand's voice with the idea's character, shows the product's screens as designed mock-ups marked "Concept", says "in development", and links to the privacy page. The funnel on the page:
   - A "Get early access at $X a month" button. Tapping it fires `price_click` and shows the plans.
   - Two plans (monthly at the spec's price and a yearly one at a discount). Choosing one fires `plan_selected` with the plan, and opens the form.
   - The form says the app is not available yet and nothing is charged today. One email field and a consent line. Submitting fires `committed_signup`.
   - After sign-up, one optional question about the visitor's situation (for example which competitor they use now). Answering fires `question_answered`.
   No payment or card detail is taken at any point. The page reads its settings from `window.LAUNCH`, loaded from `/config.js`, and works with every setting empty. Mark each element of the funnel `data-walk="1"`, `"2"` and so on in the order a visitor uses them, so the page check can walk it.
4. If `demand/config.js` does not exist, write it with empty values: `window.LAUNCH = { pixelId: "", signupEndpoint: "", signupKey: "", eventEndpoint: "" };`. It is the one place the operator fills in account details, once, for every page.
5. For each idea, make the ads in `demand/<id>/ads/` by following `skills/ad-creative/SKILL.md`: the character, three scripts, three demo videos, one still, and `ads.json`. Write `demand/<id>/claims.yaml`.
6. Check each page by using it. Run `node page_check.js demand/<id>/site`. It walks the funnel on a phone-sized screen with fake settings and prints the events that fired and the screenshots it saved in `demand/<id>/check/`. All five events must appear in order, with a sign-up posted, no script errors and no sideways scroll. Read the screenshots, then give them to the `creative-reviewer` agent with the ad frames. Fix what it reports, once.
7. Run `checks/copy_lint --pre-build --has-price` on the page, the scripts and `ads.json`. Drop ideas you cannot get right, and say why.
   Optional panel check: if tools whose names start with `mcp__pickfu__` are available, the operator has connected PickFu. For ideas you are unsure of, poll a small panel of the target audience on the three hooks, and record the cost with the shared `ledger` skill inside the `paid_api` cap. A panel is opinion: it can pick the hook to lead with and it can kill an idea people plainly do not care about, but it never passes one. If the tools are not there, skip this.
8. Write `demand/batches/<batch>/plan.json`: per idea, the page path, the ad files, the tranche 1 lifetime budget and duration from `budget.yaml`, the audience (broad, one country, the platform's own targeting), and the tracking parameters.
9. Write `demand/batches/<batch>/preview.html`: one page the operator opens to see the whole batch. Per idea: the job in a sentence, the price, the critic's verdict from `state/critic/<id>.md`, the three videos playing inline, the still, the page screenshots, and the reviewer's verdict. Use relative paths so it opens from disk.
10. Raise one `A-AD-1` packet for the whole batch. It links `preview.html` first, then lists the files. The operator commits them and opens the pull request. Move the items to `awaiting_human`.

## Steps: after approval

11. Go past this point only when the `A-AD-1` packet and `PII-1` are in `approved/`, and the ads cap covers the batch. Otherwise stop here and report what is waiting. When the pull request is merged, CI deploys the pages. Fetch each public URL and confirm it returns the page.
12. Run `python3 publish.py ads demand/batches/<batch>/plan.json --packet A-AD-1`. It creates one paused campaign per idea and reads each back. Until ad credentials exist it runs dry and writes `readback.json` without contacting Meta.
13. The operator activates the batch in Ads Manager and writes `demand_test.activated` into the batch file. When that date is present, move the items to `demand_t1`.
14. Tranche 2: when telemetry moves an item to `demand_t2`, create the tranche 2 campaign for it with `publish.py ads`, paused, using the best-performing creative. It is covered by the same `A-AD-1` packet, which states both tranche budgets. The operator activates. A top-up, where telemetry calls one, is created the same way.

## Hard checks

- `checks/copy_lint` fails any testimonial, rating, user count, "available now" wording or missing "in development" line.
- `checks/ads_paused` exits non-zero unless every campaign in the batch reads back as paused, with a lifetime budget equal to the plan and at or under the ceiling in `budget.yaml`, and the batch total is under the month's remaining ads cap. A create call returning success is not the evidence. The read-back is.

## Outputs

- `demand/<id>/site/`, `demand/<id>/ads/`, `demand/<id>/check/`, `demand/<id>/claims.yaml`, `demand/config.js`, `demand/batches/<batch>/plan.json` and `preview.html`.
- One `A-AD-1` packet per batch.
- Items at `awaiting_human`, then `demand_t1`, `demand_t2`.

## Stop conditions

- Ads cap or account spending limit not set: `BUD-1`. This stops the steps after approval, not the preparation.
- Meta, Cloudflare or any other account does not exist yet: `ACC-1`. Same: prepare the batch, stop before step 11.
- An ad is rejected by the platform: record the reason, do not resubmit a reworded copy more than once, and raise `GEN-1` if two ideas in one batch are rejected.
- The packet expires: the items are parked.

## Never

- Never set a campaign to active, raise a budget, or create a campaign outside `plan.json`.
- Never take a payment, a deposit or card details on a test page.
- Never say or imply that the app is available now, show download counts or ratings, or use a testimonial.
- Never read, export or email the early-access list. Telemetry reads counts only.
- Never extend a tranche or move an item between tranches yourself. Telemetry makes those calls.
- Never put an ad or page in a batch that you have not looked at as images.
- Never start app code for the item.

## Finish

End by calling the shared `run-report` skill. Include both check outputs, the page check output and the reviewer's verdict per idea, the batch total, and the read-back status of every campaign.
