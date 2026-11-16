---
name: weekly-review
description: Weekly prune-or-expand and self-improvement review for the directory factory. Produces prune and remediation pull requests from gate output, evidence-backed expansion notes, and at most three proposed process changes. Use for the scheduled weekly review run.
---

# Weekly review: prune, expand, improve

You are running stage 9 of Factory D. Assume no prior context. Read `CLAUDE.md`, `budget.yaml`, `FACTORY_SPEC.md` sections 5 to 8 and `journal/LESSONS.md` first.

## Inputs

- `journal/` run reports from the last 7 days.
- `ledger/spend.jsonl` and `ledger/revenue.jsonl`.
- `state/metrics/<id>/` for every live site, and `state/items/`.
- `escalations/rejected/` from the last 30 days, with the operator's reasons.
- `data/<id>/verify_report.json` and `sites/<id>/qa_report.json` for sites worked on this week.

## Part 1: honest scoreboard

1. From the ledger only, compute: spend this week and this month by category; total spend against `validation.budget_usd`; days elapsed in `validation.window_days`; verified revenue to date; revenue minus spend.
2. From metric files only, list per site: pages live, index ratio with counts, trailing 28-day clicks, trailing 30-day sessions, days since `canary_started`, next checkpoint and its date.
3. List failed runs, permission denials and any stage with two consecutive failures.
4. Write this to `journal/<date>/weekly.md`. No adjectives. If revenue is zero, the line reads "Verified revenue: USD 0".

## Part 2: prune

5. Run `tools/eval_gates --prune-list` for each live site. It lists pages to remove: submitted for more than 56 days and not indexed while the site's index ratio is under the pass mark; or indexed with zero impressions for 90 days. You do not add to or subtract from this list by judgment.
6. If a site is in a canary remediation cycle or has a `scale_fail` result, the script's list is the remediation or the rollback to the previous tier.
7. For each non-empty list, open one pull request that removes those pages from the build and the sitemap, so they return 404. State the list, the reason and the gate output. Removing pages is a reduction and needs only the operator's merge, not a packet. It never raises `page_cap`.
8. If the prune would leave a site with fewer than 20 pages, do not open it. The site is at its kill criterion; record that and let `index-telemetry` apply the kill or raise `D-KILL-1`.

## Part 3: expand

9. Expansion is considered only for a site at `index_confirmed` or later with the scale gate passed. Evidence allowed: Search Console queries with impressions for places or categories the site does not cover, and verified records already held that are outside the current tier.
10. Write expansion candidates to `state/expansion/<id>.md` with the evidence rows. New geography or new categories need new data, which means a new `D-NICHE-1` packet through `niche-discovery`. Add them to `state/seeds.md`; do not acquire anything.
11. Records older than `evidence_max_age_days` by more than 150 days need re-verification. List the count and estimated cost. Re-crawling uses the approved source and budget rules of `clean-verify`.

## Part 4: self-improvement

12. Look for patterns with evidence in at least two runs or two sites:
    - Which page types and attribute counts get indexed, and which do not.
    - Yield and cost per verified record by source and by drop reason.
    - QA failures by cause. Any template-fallback detection is always reported.
    - Niche score against canary outcome, once three sites have outcomes.
    - Reasons the operator gave for rejecting packets.
13. Propose at most three changes, at most one per skill. Each is a separate pull request whose description states: the observation with file references; the hypothesis; the single change; the metric that will judge it; the review date. Allowed targets: files under `skills/`, `agents/`, niche scoring weights, verifier extraction prompts, page templates, schemas.
14. A change that would loosen any gate, raise any cap, or touch `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, `tools/`, CI workflows, the wrapper, hooks or settings is not a pull request. Raise `GEN-1` with the evidence.
15. Review last month's merged proposals whose review date has passed. State for each whether the judging metric moved, with numbers. Propose reverting those that did not help.
16. Promote at most three lessons to `journal/LESSONS.md`: dated, one or two lines, each linking to the run reports or metric files that support it. If the file exceeds 60 lines, merge or remove the weakest entries in the same pull request.
17. End with the `run-report` skill.

## Tools

- Repo, git and the GitHub connector for pull requests.
- `tools/eval_gates`.
- Shared skills: `escalate`, `ledger`, `run-report`.

## Deterministic check

The wrapper requires `journal/<date>/weekly.md` to exist. A CI check on review pull requests requires: at most three open proposal pull requests from this review; no proposal touching a protected path; every prune pull request's page list identical to the `--prune-list` output committed alongside it; every number in `weekly.md` traceable to a ledger line id or a metrics file path given beside it.

## Outputs

- `journal/<date>/weekly.md`, prune or remediation pull requests, `state/expansion/<id>.md`, up to three proposal pull requests, a `LESSONS.md` update.

## Stop conditions

- Metrics for a site are older than 10 days: report it and skip prune and expansion for that site.
- The validation budget or window is reached: raise `D-KILL-1` if `index-telemetry` has not, and make no proposals other than the scoreboard.

## Never

- Never propose more pages as the answer to low indexing. The evidence points the other way.
- Never propose informational content, link building, outreach or indexing tricks.
- Never present a correlation from one site as a finding. Say "one site, not yet a pattern".
- Never edit a skill directly. Changes land only as pull requests the operator merges.
- Never describe the factory as working until the revenue ledger has lines in it.
