---
name: evolve
description: Propose parameter variants of an existing Factory C strategy under the fixed, logged trial budget. Use weekly when a family has a member at `validated`, `paper_trading` or `paper_passed` and trials remain in the family budget. Do not use it to rescue a killed family.
---

# Evolve

Creates new items at `hypothesized` with `parent` set. Batch: at most 2 variants per run, across all families.

Evolution here is deliberately weak. Every variant is a counted trial, and every counted trial raises the deflated Sharpe bar for the whole factory, including for the parent. The research notes warn that an agent told to find a passing strategy will tune until the gate passes. The budget is what stops that.

## Inputs

- `budget.yaml` (`research.trials_per_family`, `validation.max_trials`), `STOP` files, `escalations/`.
- `registry/trials.jsonl`, the family's `results/*/metrics.json` and `gate.json`. Read only.
- The parent's `hypothesis.md` with its declared parameter ranges.
- `paper/journal/` if the parent is on paper.

## Steps

1. List eligible families: at least one member at `validated` or later, and trials used below `trials_per_family`. Killed-only families are not eligible.
2. Check the window trial budget. If fewer than 10 trials remain in the window, do not evolve. New hypotheses have priority over tuning.
3. For one family, write `strategies/<parent id>/evolution/<date>.md` before creating anything:
   - What the family's existing trials show, with file paths.
   - The one question this variant answers (for example "is the result stable when the lookback moves one step").
   - The variant's parameter values. Each must lie inside the range on the parent card.
   - What result would make you stop evolving this family.
4. Prefer stability probes over improvement hunts: neighbouring values of one parameter. A strategy whose result collapses one step from its default is fragile. Record that as a finding and raise it in the next `F-CAP-1` packet for the family.
5. Create the variant: `strategies/<variant id>/hypothesis.md` copied from the parent with only parameter defaults changed and `parent` named, and `state/items/<variant id>.json` at `hypothesized` with `parent` and the family id.
6. Run `engine/card_schema` and `engine/variant_check` (parameters inside parent ranges, nothing else changed).
7. Commit to `claude/evolve-<family>-<date>`, open a PR. The `implement` skill picks the variant up on its next run and writes the trial request.

## Tools

Read, Write, `git`, `gh`. No market data. No trial requests are written by this skill.

## Deterministic check

- `engine/variant_check <variant>` output, pasted.
- A count from `registry/trials.jsonl`: family trials used and window trials used, with the command and output.
- The CI job enforces both budgets again when the trial is requested. Its count wins over yours.

## Outputs

Evolution note, variant cards and items, one PR, run report.

## Stop conditions

- Family budget reached: mark the family closed in the parent item's `history`. No further variants, ever.
- The last two variants of a family both failed a gate the parent passed: stop evolving it. The parent's pass is more likely luck than the variants' failures are.
- No eligible family: report and exit. This is the usual case.

## Never

- Never change rules, universe, add a parameter or widen a range. That is a new hypothesis and a new family.
- Never choose variant values after looking at which sub-period or symbol did best.
- Never replace a deployed parent with a variant. A variant goes through backtest, holdout rules and `F-PAPER-1` on its own.
- Never ask for a larger trial budget as part of this run. That is `F-ENG-1`.
- Never use paper results to pick variant values and then count the same paper period as that variant's evidence.

End by calling the shared skill `factories/_shared/skills/run-report`.
