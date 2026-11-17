---
name: weekly-review
description: The self-improvement loop of Factory C. Use on the weekly review run to read the week's journal, trial log, item histories and operator decisions, write the weekly summary, and propose at most three evidence-backed changes to skills and agents. Never changes the engine, the gate or the budget.
---

# Weekly review

You propose. The operator merges or closes. Read `CLAUDE.md` and `budget.yaml` first.

## Inputs

- `journal/<date>/` run reports for the last 7 days, including every "Not done" and "Denied or blocked" section.
- `state/items/` histories, `strategies/*/result.md` and the reviewer's files.
- `state/trials/*.jsonl` and `state/gate/`.
- `exam/`, `paper/` and `health/` once they exist.
- `ledger/spend.jsonl`, `escalations/approved/` and `escalations/rejected/`.
- `journal/LESSONS.md` and last week's `journal/reviews/` file.

## Steps

1. Build the funnel from item histories, not from report prose: items entering and leaving each stage this week and to date, and kill reasons grouped by cause.
2. Per dataset, report the trial count, the number of distinct ideas those trials form (from the latest gate file on that dataset), and how many trials each kill cost.
3. Look for these problems:
   - Ideas killed late that could have been killed earlier. An optimise kill for costs that the card's own trading frequency predicted is an ideate defect.
   - The same mechanism proposed repeatedly under new names.
   - Sweeps larger than they needed to be, or second sweeps after a fail.
   - A run report that states a number without the file it came from.
   - Reviewer rejections that the coded checks should have caught, and the reverse. Either is evidence for an `F-ENG-1` packet, not a change you make.
   - Repeated permission denials or missing tools.
4. Judge earlier proposals whose review date has arrived, against the measure each one named.
5. Write at most 3 proposals, each with the observation and file references, the single change, the measure that will judge it, and a review date. Allowed paths: `skills/`, `agents/`. One change per skill per week.
6. Promote at most 3 lessons to `journal/LESSONS.md`: dated, one or two lines, each linking its evidence.
7. Write `journal/reviews/<iso-week>.md`: the funnel, trials per dataset, strategies on paper and the combined book once they exist, spend from the ledger, the verdicts from step 4 and the proposals.
8. Add one `digest` line to the outbox with the path to the review. Under 80 words.

## Never

- Never propose a looser gate, a cheaper cost model, uncounted trials or a wider scope as an ordinary change. Those are `F-ENG-1` or `F-VENUE-1`.
- Never describe paper results as profit, or the week as good or bad by paper result alone.
- Never rewrite `journal/LESSONS.md` history. Retire entries by proposing it.

## Finish

End with the shared `run-report` skill.
