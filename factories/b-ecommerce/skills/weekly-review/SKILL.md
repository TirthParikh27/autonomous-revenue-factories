---
name: weekly-review
description: Review the week's run reports, ledger, metrics, check results and rejected escalations for Factory B and propose at most three evidence-backed changes as pull requests. Use for the weekly self-improvement run.
---

# Weekly review

Stage 8 of Factory B. Changes no item state. Produces a review file, lesson entries and pull requests. Read `CLAUDE.md` and `FACTORY_SPEC.md` section 7 first.

## Inputs

- `journal/<date>/` for the last 7 days, `journal/LESSONS.md`, the previous review in `journal/reviews/`.
- `ledger/spend.jsonl`, `ledger/revenue.jsonl`.
- `state/metrics/`, `state/checks/`, `state/items/`, `state/campaigns/write_log.jsonl`.
- `escalations/rejected/` and `escalations/approved/` for the week.
- Open pull requests from earlier reviews and their stated review dates.

## Steps

1. Run the start-of-run checks in `CLAUDE.md`.
2. Run `tools/week_summary` (to be built). It computes from files, not from run-report prose: spend by category and stage, verified revenue, contribution margin after ads, result after tokens and tooling, items by stage and kill reason, check pass rate, hours any payment path was failing before detection, runs where the report claimed success but a check failed, late or missing scheduled runs.
3. Examine, in this order:
   - Honesty: every run where the report and a deterministic check disagreed. This comes first.
   - Plumbing: purchase-check failures, credential problems, late runs.
   - Funnel: which discovery signal kinds preceded kills and which preceded verified orders. With few items, say that no pattern can be claimed.
   - Economics: assumed versus observed fees, refund rate and COGS.
   - Cost: tokens per stage against `budget.yaml`.
   - Operator decisions: reasons on rejected packets.
   - Earlier proposals whose review date has arrived: did the named metric move?
4. Choose at most three changes, at most one per skill. Each must be writable as: observation (with file references), hypothesis, the single change, the metric that will judge it, review date. No evidence from this factory's own files means no proposal.
5. Open one pull request per change on a `claude/review-<week>-<n>` branch. Allowed targets: skills other than their "Never" sections, `agents/` prompts other than tool lists, `state/seeds.md`, `state/exclusions.md` (additions only), `templates/` drafts (which still need `F-COMP-1` before use), discovery scoring weights, new assertions for `tools/` with tests.
6. Anything touching `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, hooks, settings, the wrapper, `tools/purchase_check/`, lint block lists (removals), agent tool lists or any "Never" section is not a pull request. Raise `GEN-2`.
7. Append at most 3 dated, evidence-linked entries to `journal/LESSONS.md`. Keep the file at or under 60 lines by merging or removing the weakest old entries, and say which were removed.
8. Write `journal/reviews/<week>.md`: the `week_summary` output, the proposals, earlier proposals judged, and a plain statement of the factory's position: total spent, total verified revenue, contribution margin after ads, result after tokens, days and dollars left in the validation budget.
9. If the validation budget or window is exhausted without verified revenue and no `BUD-2` is open, raise it.
10. End with the shared `run-report` skill.

## Tools

Repo files, `tools/week_summary`, GitHub for pull requests. No web access, no processor, store or ad-account access. Numbers come from files the telemetry run wrote.

## Deterministic check

- `tools/week_summary` exit 0 and its output pasted unedited into the review.
- CI on each pull request: one skill touched at most, no protected path touched, proposal template fields present.
- At most three pull requests opened this week by this stage.

## Outputs

- `journal/reviews/<week>.md`, updated `journal/LESSONS.md`, 0 to 3 pull requests, possibly `GEN-2` or `BUD-2`

## Stop conditions

- `week_summary` fails or inputs are missing: write the review with what exists, list what is missing, propose nothing.
- Fewer than 5 runs in the week: write the summary, propose nothing.

## Never

- Never merge your own pull request or push to `main`.
- Never propose loosening a kill threshold, a risk threshold, a write limit or a compliance rule through a pull request.
- Never propose more spend as the remedy for no demand without a `GEN-2` or `F-ADS-1` packet carrying the unit economics.
- Never describe the week more favourably than `week_summary` does. Zero revenue is reported as zero.
- Never infer a pattern from fewer than 10 orders or fewer than 5 items.
