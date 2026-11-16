---
name: content-qa
description: Gate a built directory site on near-duplicate text, template-fallback detection and fact accuracy before any deploy. Use when an item is at built, and again on every later page-tier build.
---

# Content QA

You are running stage 5 of Factory D. Assume no prior context. Read `CLAUDE.md` and `budget.yaml` (sections `content_qa`, `per_run.content_qa`) first.

This gate exists because of two documented failures: a site where about 89% of 8,000 pages were near-duplicates and none were indexed, and a site where a generation step fell back to templates so every page carried the same text without the operator noticing. The scripts decide. Your reading of the pages cannot overrule them.

## Inputs

- An item at `built`, with `sites/<id>/` on a `claude/` branch, `build_manifest.json` and `content_manifest.json`.
- `data/<id>/verified.jsonl`.

## Steps

1. Build the site to static output with the repo's build command. Do not modify any file.
2. Run the three gate scripts against the built output. They also run in CI on the pull request; you run them here to produce the report.
   - `tools/check_duplicates`: extracts each page's main content with template chrome removed (header, footer, navigation, fixed labels). Hashes it. Computes 5-word shingle sets and pairwise Jaccard similarity within each page type.
   - `tools/check_fallback`: reads `content_manifest.json` and scans rendered pages for any sentence of 8 or more words, outside the declared template label list, that appears on more than the allowed fraction of pages.
   - `tools/check_facts`: for a random sample of `fact_check_sample_pages` pages, compares every rendered fact field with the record in `verified.jsonl`.
3. Write the combined results to `sites/<id>/qa_report.json` with the real numbers, the thresholds they were compared against, and for any failure the ten worst page pairs or sentences.
4. If all three pass, ask the `content-verifier` agent to review 15 randomly chosen pages (seeded, with the seed recorded) against the acceptance list below. It reports only gaps that affect correctness or compliance.
5. If the verifier reports a gap, treat it as a failure. If the verifier reports none, that does not upgrade a script failure.
6. On pass, move the item to `qa_passed`. On failure, leave it at `built`, increment `scores.qa_failures`, and state the cause as one of: bug, template fallback, thin data. A third failure with cause "thin data" moves the item to `killed`.
7. End with the `run-report` skill. Paste each script's summary line.

## Acceptance list for the verifier sample

- Every statement on the page is supported by a field in the record.
- No personal data: no individual's name, personal phone, personal email or home address.
- No copied prose, no review text, no images from third parties.
- No superlatives, ratings or claims of quality.
- The last-verified date is present and matches the record.
- The page would be useful to someone choosing between these businesses, because it shows at least the minimum verified attributes.
- Sources page and removal page are linked from every page.

## Tools

- `tools/check_duplicates`, `tools/check_fallback`, `tools/check_facts` (scripts, also required CI checks).
- `content-verifier` agent.
- Shared skill: `run-report`.

## Deterministic check

All thresholds come from `budget.yaml` `content_qa`. The gate passes only if:

- Pages with an exact duplicate main-content hash: at most `max_exact_duplicate_main_content_pages` (0).
- Fraction of pages that have any neighbour at or above `near_duplicate_jaccard_threshold`: at most `max_near_duplicate_page_fraction`.
- No non-template sentence shared by more than `max_page_fraction_sharing_a_non_template_sentence` of pages.
- Records with `generation_source` of `template` or missing: `allowed_template_fallback_records` (0).
- Fact mismatches in the sample: `fact_check_max_mismatches` (0).
- Every listing page shows at least `min_verified_attributes_per_listing_page` verified fields.

These thresholds are the factory's own conservative numbers. The research found no sourced uniqueness threshold; the one figure seen (a 30% to 40% "uniqueness ratio") came from an unsourced agency post and is not relied on.

## Outputs

- `sites/<id>/qa_report.json`.
- Item at `qa_passed`, `built` or `killed`.

## Stop conditions

- A gate script crashes or is missing: the stage fails. Do not substitute your own estimate of similarity.
- The template label list would need to grow to make the check pass: stop. Changing that list is a change to `tools/` and is an escalation.

## Never

- Never edit site content, data or scripts in this stage. You only measure.
- Never pass a site because the duplicates are "only" boilerplate. Boilerplate is already stripped; what remains is content.
- Never lower a threshold, shrink the sample or change the seed after seeing a result.
- Never mark `qa_passed` without all three script outputs in the run report.
- Never suggest rewording to evade the duplicate check. The fixes are fewer pages or more verified data.
