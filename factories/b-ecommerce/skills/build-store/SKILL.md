---
name: build-store
description: Build the product, product page, test-mode payment link, delivery path and policy pages for a specced item, with nothing live. Use when items are waiting in the specced stage. Digital variant builds a static page plus Stripe payment link; pod variant builds in Shopify through Shopify CLI.
---

# Build store

Stage 3 of Factory B. Moves items from `specced` to `built` or `killed`. Everything stays in test mode and on preview URLs. Going live is the operator's step after `F-LIVE-1`. Read `CLAUDE.md` and `budget.yaml` first.

## Inputs

- Item file in `specced`, `state/offers/<id>.yaml`, `state/offers/<id>.econ.json`.
- `templates/` for page and policy text the operator has approved (created at build time through `F-COMP-1`).
- `budget.yaml`: `per_item_caps_usd.build_tokens`, `variants`.

## Steps

1. Run the start-of-run checks in `CLAUDE.md`. Take one item.
2. Confirm the accounts the variant needs exist (approved `F-ACCT-1` packets). If not, raise `F-ACCT-1` and stop on this item.
3. Start the `store-builder` sub-agent with the offer spec path. It works on a `claude/build-<id>` branch and produces, under `products/<id>/`:
   - The product. `digital`: the deliverable files, original, with a SHA-256 hash recorded in `products/<id>/delivery.json`. `pod`: original design files and mockups.
   - The page: what it is, what the buyer receives and how, price from the offer spec, refund policy, contact, privacy notice. Only statements listed in `claims_allowed`.
   - The payment object in test mode. `digital`: a Stripe Payment Link created with the test-mode key, id saved in `products/<id>/payment.test.json`. `pod`: a product in the Shopify development store, applied through Shopify CLI.
   - The delivery path. `digital`: post-payment page that serves the download, plus the delivery email template. `pod`: the provider product mapping in draft, with no live order rights.
   - PostHog page and purchase events, with no personal data in event properties.
4. `pod` only: before applying any GraphQL or theme change, validate it with the Dev MCP tools `validate_graphql_codeblocks` and `validate_theme_codeblocks`. Apply through Shopify CLI. Keep the store password-protected.
5. Deploy to a preview URL (Cloudflare Pages preview for `digital`).
6. Run the build checks below. Then start the `checkout-verifier` sub-agent on the branch.
7. All checks pass and the verifier reports no correctness gap: open a pull request, set `stage: built`. Otherwise fix once and re-run. Third failed build on the item: kill it. Three consecutive failed runs of this stage is `FAIL-3`.
8. Record spend with the shared `ledger` skill. End with the shared `run-report` skill.

## Tools

- `digital`: Stripe test-mode key (connector `stripe_api_write` or Stripe CLI, whichever is confirmed at build time to create Payment Links. From December 2026 the Stripe MCP accepts only OAuth or an agent-tagged restricted key), Cloudflare Pages preview deploy.
- `pod`: Shopify CLI with headless auth (Theme Access password in `SHOPIFY_CLI_THEME_TOKEN` plus `SHOPIFY_FLAG_STORE`, verified 2026-11-16; the CLI is not on the operator's Mac), Shopify AI Toolkit / Dev MCP, POD provider REST API with a draft-only key.
- `tools/claims_lint`, link checker, `tools/check_ids`.

## Deterministic check

All must exit 0, output pasted in the run report:

- Page build script.
- Link checker on the preview URL: every link returns 200, including policy pages.
- `tools/claims_lint products/<id>/`.
- Price string on the rendered page equals `price` in the offer spec.
- `tools/check_ids`: the preview contains only test-mode identifiers.
- Deliverable hash matches `delivery.json`.
- `pod`: Dev MCP validators passed, and the design screen (blocked-terms list on all text in the design, plus a trademark lookup whose method must be confirmed at build time) is clean.

## Outputs

- `products/<id>/` on a `claude/` branch, a pull request, a preview URL
- Item file updated with preview URL and test payment id

## Stop conditions

- Token cap for the item's build reached: stop, report, kill if this is the third attempt.
- A live-mode key or identifier is visible to the run: do not use it, raise `SEC-1`.
- The delivery path needs an email sender or domain that does not exist: `F-ACCT-1`.
- Any doubt that a design or text is original: `F-COMP-1`.

## Never

- Never create a live-mode payment link, publish to a production URL or remove a store password.
- Never add reviews, ratings, testimonials, customer counts, countdown timers or invented discounts.
- Never write "no refunds" or alter approved policy text.
- Never use a brand, character, team, celebrity, lyric or an existing seller's design.
- Never install a community MCP server or an unpinned third-party package for store, POD or payment access.
- Never put secrets, or customer data, in the repo.
