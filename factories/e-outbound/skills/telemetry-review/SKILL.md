---
name: telemetry-review
description: Pull Factory E funnel and revenue numbers from sources of truth, enforce kill criteria and page expiry (daily mode), or review the week and propose at most three changes as pull requests (weekly mode). Use for the daily telemetry run and the weekly self-improvement run.
---

# Telemetry and review

Stage 9 of `FACTORY_SPEC.md`. The run prompt names the mode: `daily` or `weekly`.

## Inputs

- `ledger/`, `journal/`, `state/funnel/`, `state/items/`, `state/replies/`, `escalations/rejected/`.
- Gmail (label `factory-e`), Google Calendar, HubSpot deals, PostHog demo page events, Stripe (read-only).
- `budget.yaml`: `validation`, `volume`, `funnel_bands`.

## Daily mode

1. Run the start-of-run checks in `CLAUDE.md`.
2. Count from sources of truth, not from item files: sent leads (labelled sent mail with a demo slug), replies, calendar-proven conversations, open drafts, HubSpot deals by stage, live demo pages, page views per slug from PostHog.
3. Write `state/metrics/<date>.json` with each number, where it was read and when.
4. Run `checks/funnel_invariants` across the whole funnel. Any mismatch between sources and item files raises `E-FUNNEL-1`.
5. Read Stripe for new payments and refunds. Record with the shared `ledger` skill. A paid proposal moves its lead from `awaiting_human` to `won` only if `E-CLIENT-1` is also approved.
6. Expire demo pages older than `demo_page_ttl_days` for leads in a terminal stage by removing their data files. Confirm on the next run that they return 404.
7. Move `delivering` leads with an operator hand-off note in HubSpot to `delivered`.
8. Evaluate validation rules: spend against budget, weeks against window, the 50-sent checkpoint, the 100-sent decision, operator minutes. If any fires, raise `E-KILL-1` or `BUD-1` and pause as the spec says.
9. Post nothing to Slack beyond the wrapper's one line unless a trigger fired.

## Weekly mode

1. Read the week's run reports, funnel files, metrics, reply classes and rejected packets.
2. Compute and write to `journal/reviews/<week>.md`:
   - funnel table by stage with every kill reason's share
   - conversations booked per 100 sent, cumulative, beside the benchmark (about 3.43% any reply, 0.5 to 2.5% meetings, both vendor figures) with the sample size stated
   - token cost per `demo_verified` lead and per sent lead
   - operator minutes per sent lead
   - replies and bookings by signal type
   - for each sent lead, the word-level difference between the Gmail draft and the sent message, summarised as repeated edit patterns
   - demo views against replies, labelled as correlation only
3. Propose at most three changes, one per skill, each with observation, hypothesis, single change, judging metric and review date. Open each as a pull request. Allowed subjects are listed in spec section 9.
4. Anything outside that list (volume, channels, Mode 2, vendors, offers, off-limits files, check logic) is written as an escalation proposal instead, or dropped.
5. Promote at most three evidence-linked lessons to `journal/LESSONS.md`. Keep the file under 60 lines by merging older entries.
6. Judge last week's merged changes against their stated metric. Say plainly if the sample is too small to judge. With fewer than 20 sent leads behind a change, it usually is.

## Tools

Gmail `search_threads`, Calendar `list_events`, HubSpot read tools, PostHog `exec`, Stripe read tools, GitHub for pull requests, Read, Write, Bash.

## Deterministic check

- Every metric in the metrics file has a source and a read time.
- Revenue lines carry a Stripe reference read in this run.
- `checks/funnel_invariants` passes or an `E-FUNNEL-1` packet exists.
- Weekly: no more than three PRs, none touching off-limits paths (CI path check).

## Outputs

Metrics file, ledger lines, review file, pull requests, escalation packets when triggered.

## Stop conditions

- A source of truth is unreachable: report the metric as unknown. Do not substitute the item-file count.
- Stripe connector not yet connected: revenue is reported as "not measurable", never as zero revenue confirmed.

## Never

- Never report a reply rate without its denominator and source.
- Never describe a result as lift from the demo page. There is no control group.
- Never merge your own pull request or edit a skill directly.
- Never propose more sending volume as an improvement.

End by calling the shared `run-report` skill.
