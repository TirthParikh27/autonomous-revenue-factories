---
name: creative
description: Produce a small set of compliant ad creatives (product demo, screen recording or clearly scripted explainer) and a manifest for a live product. Use when a live product has a passing purchase check and the operator has indicated in budget.yaml or an approved packet that a paid test may be proposed.
---

# Creative

Stage 5 of Factory B. Moves an item from `live` (or `iterating`) to `creative_ready`. Produces files only. Nothing is uploaded or published. Read `CLAUDE.md` and `budget.yaml` first.

Context: the research prices AI video at a few dollars per variant, so volume is cheap and gives no edge. The exposure is compliance. Make few assets and make them defensible.

## Inputs

- Item file in `live` with a passing purchase check under 26 hours old.
- `state/offers/<id>.yaml` (`claims_allowed`, price) and the live page.
- Formats already approved through `F-COMP-1` (listed in `templates/creative_formats.md`).
- For `iterating`: the previous manifest and the metrics that motivated the change.

## Steps

1. Run the start-of-run checks in `CLAUDE.md`. Take one item.
2. If `ads.enabled` is false in `budget.yaml` and no packet asks for creatives, write a run report saying the stage is not enabled and exit.
3. Start the `store-builder` sub-agent to produce 3 to 5 assets in `products/<id>/creatives/`:
   - Formats: product demo, screen recording of the digital product, static image with product and price, or a scripted explainer. A spokesperson format must be visibly a presenter, never a customer.
   - Every script line and caption is drawn from `claims_allowed`. The price shown equals the live price.
   - One primary text, one headline and one description per asset, within the platform's length limits (confirm limits at build time).
4. Write `products/<id>/creatives/manifest.json`. One entry per asset: file path, format, script text, caption text, destination URL, `ai_generated` (true if it contains any synthetic person, voice or photorealistic generated scene), tool used, and cost.
5. Run the checks below, then start the `checkout-verifier` sub-agent on the manifest.
6. If any asset uses a format not yet in `templates/creative_formats.md`, raise `F-COMP-1` for that format and leave the asset out of the manifest until approved.
7. All checks pass with at least 3 assets: set `stage: creative_ready` and raise `F-ADS-1` with the shared `escalate` skill, using the packet contents in `ESCALATION.md`. The packet proposes caps no higher than the ceilings in `budget.yaml`. If the ceilings are 0, say so in the packet and propose the `suggested_first_test` values for the operator to consider.
8. Record tool spend with the shared `ledger` skill. End with the shared `run-report` skill.

## Tools

- ffmpeg, and HyperFrames for HTML-composed motion (HyperFrames skills and HeyGen CLI are on the operator's Mac, verified 2026-11-16; run with `npx hyperframes`). This is why the stage runs as a Desktop task.
- Screen capture of the product by scripted browser.
- No image, video or avatar generation service is selected. Their API access and pricing were not verified. Using one is `F-ACCT-1`, and avatar output is always `ai_generated: true`.

## Deterministic check

All must exit 0, output pasted in the run report:

- `tools/claims_lint` on every script and caption in the manifest. It blocks health, safety, income and guarantee claims, urgency and scarcity phrases, review and testimonial patterns ("I bought", "I tried", "changed my life", star ratings, "customers say"), and comparative price claims.
- `tools/check_manifest`: schema valid, every file exists, format and size within the platform spec recorded in `templates/`, `ai_generated` present on every entry, destination URL equals the live page URL, price text equals the live price.
- The destination URL returns 200.

## Outputs

- `products/<id>/creatives/` and `manifest.json` on a `claude/` branch with a pull request
- `F-ADS-1` packet

## Stop conditions

- Purchase check stale or failing: stop, this is `F-PAY-1` territory.
- A risk freeze (`F-RISK-1`) is open: do not produce creatives.
- Fewer than 3 assets pass: leave the item in `live` and report.
- Per-run budget reached.

## Never

- Never produce a testimonial, review, "customer story", reaction video, before-and-after, or any first-person statement of using or benefiting from the product.
- Never depict a real person, brand, logo or copyrighted character.
- Never omit or set `ai_generated` to false to avoid a platform label.
- Never upload, post, schedule or send a creative anywhere. Not to an ad account, a social scheduler or HubSpot.
- Never generate more than 5 assets per product per run.
