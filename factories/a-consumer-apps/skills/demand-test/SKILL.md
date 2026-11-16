---
name: demand-test
description: Stage 3 of Factory A. Use when items sit at `specced` to prepare a waitlist landing page and concept posts as files and drafts, then raise the approval packet for the operator to deploy and publish. Measurement of a running test belongs to telemetry-winner-detection, not this skill.
---

# Demand test

No app is built until this test passes. You prepare assets. The operator makes them public. Read `CLAUDE.md` and `budget.yaml` first.

## Inputs

- Items at `specced`, up to the free slots under `pipeline.max_concurrent_demand_tests`.
- `state/specs/<id>.md`.
- `data/landing_template/` and `data/privacy_notice.md` (operator-approved text).
- The `demand_test` thresholds in `budget.yaml`.

## Steps

1. Count items at `demand_test_ready`, `demand_testing`, or `awaiting_human` on `A-DEM-1`. If the count is at the cap, exit with a run report.
2. If this is the factory's first waitlist, confirm that a `PII-1` packet is in `escalations/approved/`. If not, raise `PII-1` and stop work on waitlist storage.
3. Have the `app-builder` agent create `demand/<id>/site/`: one static page that states the job and the differentiation in the brand's voice, a single email field, a consent line, a link to the privacy notice, and the words "in development". Add the PostHog snippet with events `page_view` and `waitlist_signup`. The form writes email and consent timestamp to the item's waitlist table through a server-side insert only.
4. Write `demand/<id>/claims.yaml` with the claims the page and posts make. Before the app exists, claims describe what the app will do, phrased as intent.
5. Use the `content-drafts` skill in concept mode to render 6 posts from the spec's angles. Concept posts use designed mock-ups that are visibly labelled as concept. They are not presented as screenshots of a shipping app.
6. Run `checks/demand_assets demand/<id>/`.
7. On pass, raise `A-DEM-1` with the shared `escalate` skill. Move the item to `demand_test_ready`, then `awaiting_human`.
8. On a later run, if the packet is in `approved/`: have the `draft-publisher` agent place the 6 posts in Postiz as drafts and read each one back to confirm its state is draft. Do not deploy the page. The operator deploys, publishes the posts from the warmed account, and writes `demand_test.first_published` into the item file. When that date is present, move the item to `demand_testing`.

## Tools

Read, Write, Edit, Bash for the static build and the check script, PostHog connector (read project settings only), Supabase connector (create the waitlist table only after `PII-1`), Postiz through `draft-publisher`. Hosting is the operator's step.

## Deterministic check

`checks/demand_assets` exits non-zero unless: the site builds, the PostHog snippet and both events are present, the privacy link resolves to the approved notice, the form has a consent line, copy lint passes on the page and all captions (no testimonial patterns, no ratings, no unlisted claims, concept wording present), exactly 6 posts exist with `concept: true`, and each has at most `content.max_hashtags` hashtags. After scheduling, the Postiz read-back must show 6 drafts. A create call returning success is not the evidence. The read-back is.

## Outputs

- `demand/<id>/site/`, `demand/<id>/claims.yaml`, `demand/<id>/posts/manifest.json`.
- Packet `A-DEM-1`.
- Item at `demand_test_ready`, `awaiting_human`, then `demand_testing`.

## Stop conditions

- Per-item spend above `per_item_caps_usd.demand_test`: kill the item.
- Hosting, Postiz or any other account does not exist yet: raise `ACC-1`.
- The operator rejects `A-DEM-1`: move the item to `killed` or back to `specced` as the packet states.
- The packet expires: the item is parked.

## Never

- Never deploy the page, buy a domain, or publish a post.
- Never run ads or any paid traffic. `monthly_caps_usd.ads` is 0.
- Never show a mock-up as a real app, show fake download counts, or imply the app is available.
- Never read, export or email the waitlist. Telemetry reads counts only.
- Never extend a test window or lower a threshold. The numbers are in `budget.yaml`.
- Never start app code for the item.

## Finish

End by calling the shared `run-report` skill. Include the `checks/demand_assets` output and, if drafts were created, the Postiz read-back for each.
