---
name: weekly-review
description: Weekly self-improvement and portfolio review for the Apify actor factory. Use on the weekly review schedule. Scores last week's predictions against real numbers, proposes at most three changes as pull requests, batches retire and double-down proposals, and checks the validation budget.
---

# Weekly review

You are a fresh session. Read `CLAUDE.md`, `budget.yaml`, `FACTORY_SPEC.md` sections 6 to 8 and `journal/LESSONS.md` first. Complete steps 1 to 3 of the operating loop. This run changes no item stage except through escalations and the `parked` housekeeping in step 8, and edits no skill directly.

## Inputs

- `journal/<last 7 days>/`, `ledger/spend.jsonl`, `ledger/revenue.jsonl`, `state/metrics/`, `state/items/`, `state/retire_queue.json`, `state/payouts/`.
- `escalations/rejected/` and `approved/` from the last 30 days, including the operator's reasons.
- Open pull requests from earlier reviews and their review dates.

## Steps

1. Run `scripts/review_inputs`. It writes `state/review/<date>-numbers.json`: spend by category and by stage, spend on maintenance versus new builds, revenue from the ledger, per-actor users, estimated profit, canary green ratio, repairs, prepaid usage remaining, items killed by stage and reason, run failures by stage. Use these numbers. Do not total anything yourself.
2. Score predictions. For each published actor compare `predicted_users_30d` and predicted cost per result with actuals. For each killed item note the stage and what it cost. Write the table to the review file.
3. Judge earlier proposals whose review date has passed, using the metric each one named. State kept, reverted or inconclusive, with the numbers.
4. Find the single costliest problem of the week by dollars or by failed runs. Typical candidates for this factory:
   - scan signals that keep producing zero-user actors,
   - builds dying at live test for cost reasons that the spec could have predicted,
   - one actor consuming most repair tokens,
   - canary false alarms or missed breakages,
   - packets rejected for the same reason twice.
5. Write at most three proposals. Each has: observation with file references, hypothesis, the single change, the metric that will judge it, the review date. One change per skill per week. Allowed subjects: `state/scan_config.json` weights and themes, the spec template, fixture design rules, README and title wording rules, a skill's steps. Open one pull request per proposal.
6. Anything touching `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, `compliance/`, `scripts/`, workflows, hooks or settings is not a pull request. Raise `F-SELF-1` instead. An addition to the deny list is the one exception and goes as a pull request.
7. Portfolio decisions, each through the `escalate` skill:
   - Retire: one batched `F-RET-1` for everything in `state/retire_queue.json`, with the rule and numbers per actor.
   - Double down: if an actor meets the `winner` thresholds, add up to 2 adjacent candidates to the next `gap-scan` themes. No approval needed for a theme. The resulting actors still pass every gate.
   - Price: `F-PRICE-1` only with 30 days of usage data.
   - Cap: `F-CAP-1` only if green ratio has been at or above 0.90 for 30 days and maintenance tokens per live actor are falling.
   - Side bet: `F-SIDE-1` at most once per quarter, under its conditions.
8. Housekeeping. Move items `parked` for more than 30 days to `killed`. Check the day 45 checkpoint and the `validation` limits. Raise `F-VAL-1` if due.
9. Platform drift. If any run report this week noted a change in Apify's monetisation docs, commission, pricing models or payout rules, summarise it and raise `GEN-1`.
10. Lessons. Propose at most 2 new entries for `journal/LESSONS.md`, each dated, one or two lines, with a link to the evidence. Remove or merge entries so the file stays under 60 lines. This goes in a pull request.
11. Write `journal/<date>/weekly-review.md`: the numbers table, prediction scores, judged proposals, new proposals with pull request links, escalations raised, and one honest paragraph on whether the factory is on track against the validation budget. Under 120 lines.

## Tools

- Read, Grep, Glob. Bash for `scripts/review_inputs` and `scripts/validate_item`.
- GitHub connector for pull requests.
- Shared `escalate` skill. Model: Opus.

## Deterministic check

- `state/review/<date>-numbers.json` exists and every number in the review file matches it. `scripts/review_inputs --check journal/<date>/weekly-review.md` must exit 0.
- At most 3 proposal pull requests were opened, none touching a protected path (CI path check on each pull request).
- Each proposal contains all five fields.

## Outputs

- The weekly review file, up to 3 proposal pull requests, one `LESSONS.md` pull request, escalation packets.

## Stop conditions

- `STOP` or budget cap: write the numbers and the review file only. Open no pull requests.
- Fewer than 3 run reports in the week: say the data is too thin to judge and propose nothing.

## Never

- Never edit a skill, config or lesson file directly on a working branch that merges without the operator.
- Never propose loosening a compliance rule, the unit economics multiple, an approval gate or a cap as an ordinary pull request.
- Never credit a change with an improvement when fewer than 2 weeks or fewer than 5 items back it. Say inconclusive.
- Never describe estimated profit as revenue. Revenue is the revenue ledger, which comes from payout files.
- Never propose more builds as the answer to zero users. Propose a different niche, a kill, or a stop.
- Never recommend continuing past the validation budget without stating the total spent and the total verified revenue side by side.

End by calling the shared `run-report` skill.
