---
name: site-build
description: Generate the Astro static directory site for one item from its verified records only, within the item's page cap. Use when an item's D-DOM-1 packet is approved, or when content-qa has returned a built site for a fix.
---

# Site build

You are running stage 4 of Factory D. Assume no prior context. Read `CLAUDE.md` and `budget.yaml` (sections `content_qa`, `indexing`, `per_run.site_build`) first.

## Inputs

- An item in `awaiting_human` with an approved `D-DOM-1` packet (the packet or the operator's commit states the purchased domain), or an item at `built` with a failing `sites/<id>/qa_report.json`.
- `data/<id>/verified.jsonl` and `state/niches/<id>/brief.json`.
- `data/suppression.jsonl`.
- The item's `page_cap` (40 unless a `D-SCALE-1` approval raised it).

You do not read `data/<id>/extracts/` or any raw scraped page. Work from verified records only.

## Steps

1. Confirm the domain from the approved packet. If the operator has not recorded a purchased domain, exit and say so. Do not build against a placeholder domain.
2. Delegate the build to the `site-builder` agent with these requirements.
3. **Page types.** One listing page per verified record. Category pages and place pages only where at least `min_listings_per_category_page` verified listings exist. A home page. A sources page (where the data came from, how records are verified, last-checked date per record). A removal and correction request page. A disclosure page. No other page types.
4. **Listing page content.** Name, address, phone, website link, category, and every verified attribute for this niche, each shown as structured data. A last-verified date. A listing with fewer than `min_verified_attributes_per_listing_page` verified fields is not given its own page; it appears only as a row on category pages.
5. **Text.** Assemble sentences from fields. If any model-written sentence is used, the build step that writes it stores `generation_source: model` beside it in `sites/<id>/content_manifest.json`. If the generation call fails, the build fails. There is no template fallback path in the code.
6. **Selection under the cap.** If eligible pages exceed `page_cap`, rank listing pages by verified attribute count and keep the top ones. Excluded pages are not built at all, not built and hidden.
7. **Technical basics.** Canonical URL on the approved domain for every page. Structured data markup for a local business using only verified fields. A sitemap generated from the built page list. A robots file that allows crawling. No rating markup, since no ratings are held.
8. **Removal page.** It gives the operator's contact route as stated in the approved packet. It does not collect data through a form unless the operator has set one up.
9. Run `tools/check_build sites/<id>/`.
10. Commit to a `claude/` branch. Do not open the deploy pull request. That is `canary-deploy`.
11. On pass move the item to `built`. On failure leave the stage unchanged and report. A third consecutive failure raises `FAIL-3` through the wrapper.
12. End with the `run-report` skill.

## When fixing a QA failure

Read only `qa_report.json` and the files it names. Fix the cause, not the symptom. If near-duplicates are reported, the fix is to drop the thin pages or show more verified data, never to reword sentences so the check passes. If the cause is thin data, say so. After a third QA failure caused by thin data the item is killed.

## Tools

- Astro, Node, git, through the `site-builder` agent.
- `tools/check_build`.
- Shared skills: `ledger`, `run-report`.

## Deterministic check

`tools/check_build` exits 0 only if: the Astro build exits 0; built page count is at or under `page_cap`; every listing page key exists in `verified.jsonl`; every fact field rendered on a page equals the record's field; no suppressed key appears in the output; every category page has the minimum listings; sources, removal and disclosure pages exist; all internal links resolve; every canonical URL is on the approved domain; sitemap URL count equals built indexable page count; `content_manifest.json` has no entry with `generation_source` other than `model` or `fields`. Paste its output line.

## Outputs

- `sites/<id>/` source on a `claude/` branch.
- `sites/<id>/build_manifest.json` (page list with record keys and attribute counts) and `content_manifest.json`.
- Item at `built`.

## Stop conditions

- Run cap reached: commit work in progress to the branch and report what is left.
- The build needs a package or service not already in the lockfile that costs money or needs an account: raise `GEN-1`.

## Never

- Never add an informational page, a guide, a blog, a "cost of" page or an FAQ.
- Never invent a rating, a price, opening hours or a superlative.
- Never include images from a business website, from Google or from any third party.
- Never add an affiliate link, ad code or tracking beyond PostHog. Monetisation is a later, gated stage.
- Never build more pages than the cap and hide the extra ones with noindex.
- Never edit `tools/` or the CI workflows to make a check pass.
