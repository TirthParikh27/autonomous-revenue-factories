---
name: weekly-review
description: Stage 7 of Factory G. Use on the weekly self-improvement run to read the week's journal, ledgers and metrics, test whether the willingness-to-pay gate predicted real payment, and propose at most three changes as pull requests. Never edits protected files.
---

# Weekly review

Goal: make next week's kills cheaper and next week's builds better aimed, with changes small enough that their effect can be attributed.

## Inputs

- `journal/<date>/` for the last 7 days, and `journal/LESSONS.md`.
- `ledger/spend.jsonl` and `ledger/revenue.jsonl`.
- `state/items/`, `state/specs/`, `state/metrics/`, `state/packets/*/verify.json`.
- `escalations/rejected/` and `escalations/approved/` from the last 30 days, including the operator's one-line reasons.
- Open pull requests from earlier reviews, with their review dates.
- `budget.yaml`.

## Steps

1. Preconditions. Stop with a run report if `STOP` exists or a cap is reached.
2. Build the funnel table from item files, not from run reports: count of items entering and leaving each stage this week and in total, kill reasons by stage, median token spend per item per stage.
3. Money check. Total spend by category, total verified revenue, net position, spend against `validation.budget_usd` and days used of `validation.window_days`. If the validation budget or window is exhausted with no revenue line, raise `G-BUD-2` with the `escalate` skill and make no proposals this week.
4. Calibration, the main question for this factory. For every item that has been live 30 days or more, set its `wtp_score` and evidence mix (A, B, C, D counts) beside its paid conversion and net MRR. State plainly whether higher scores went with more paying customers. With fewer than 3 live items, say the sample is too small to conclude anything and propose no change to scoring guidance.
5. Source yield. For each `gap_type`, count items discovered, specced, built, live and paying.
6. Friction. List verifier returns and `policy-check` failures by cause, store rejections by reason, wrapper failures by stage, and every day the synthetic money-path check failed with the delay before it was noticed.
7. Honesty audit. Pick 3 run reports at random. For each, re-run or re-read one claimed piece of evidence (a CI run, a file hash, a ledger line against its source reference). Record any mismatch as a finding. A mismatch is a higher priority than any optimisation.
8. Judge earlier proposals whose review date has passed: read the judging metric, state kept or reverted, and open a revert pull request if the metric got worse.
9. Choose at most three proposals, at most one per skill. Each is one change, written as:
   - Observation, with journal, ledger or metrics file references.
   - Hypothesis.
   - The single change.
   - The metric that will judge it and the review date (at least 2 weeks out).
10. Open one pull request per proposal on a `claude/review-<date>-<n>` branch. Allowed paths: `skills/`, `agents/`, `state/targets.yaml`, `journal/LESSONS.md`. Anything else (kill numbers, the WTP threshold, budgets, `CLAUDE.md`, `ESCALATION.md`, `policy/`, hooks, the wrapper) is written as a `G-SELF-1` packet instead, with the proposed diff as text.
11. Append at most 3 dated, evidence-linked entries to `journal/LESSONS.md` through a pull request. Keep the file under 100 lines by merging or removing entries that later evidence contradicted, and say which.
12. End with the `run-report` skill. Include the funnel table, the net position and the pull request URLs.

## Tools

Read, Grep, Glob. Bash for counting and for re-running one check in the honesty audit. git and the GitHub connector to open pull requests. No web tools. No Stripe access: revenue is read from the ledger, which telemetry already reconciled.

## Deterministic check

- CI path check on each pull request: only allowed paths changed, and at most one skill directory per pull request.
- A plain script confirms every proposal cites at least one existing file path, and that the funnel counts in the report equal a recount of `state/items/`.
- No more than three open review pull requests from this run.

## Outputs

Up to three pull requests, a `LESSONS.md` pull request, any `G-SELF-1` or `G-BUD-2` packets, a run report.

## Stop conditions

- Fewer than 5 runs in the week: write the funnel and money sections, propose nothing.
- An honesty-audit mismatch involving revenue: raise `G-MONEY-1`, propose nothing else.
- Per-run caps reached: publish what is complete and list what was skipped.

## Never

- Never merge a pull request or edit a skill directly on `main`.
- Never propose loosening a gate, a kill number or a permission rule through a skill edit that has the same effect by another wording.
- Never propose more throughput (more specs, more builds, more live tools) while no item has a paying customer.
- Never count installs, stars or review volume as success in the review.
- Never base a proposal on a single item unless it is a correctness or honesty fix.
- Never rewrite history in item files, ledgers or past run reports.
