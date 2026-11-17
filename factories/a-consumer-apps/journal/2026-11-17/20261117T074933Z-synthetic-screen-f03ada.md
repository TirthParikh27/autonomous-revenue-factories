# Run 20261117T074933Z-synthetic-screen-f03ada
Stage: synthetic-screen   Items: 3 (batch 2026-11-17-b)   Model: sonnet (orchestrator), haiku (3 ranker subagents)   Cost: about $0.45 of $1.50 by the harness budget line, ledger entry left to the wrapper

## Did
- Checked for STOP (factory and repo root): none. Read `budget.yaml`. Open escalations: one, `SEC-1-20261117-gap-mining-b18d5b` (Business scout file). It does not touch these items, so I left it alone.
- Built three neutral cards (job, who, three sourced complaints, keyword figure, competitor count; no names, price or personas) from the finance and lifestyle scout files.
- Ran the ranking 3 times, each in a fresh subagent with the cards in a different order and letters. Files: `state/screen/2026-11-17-b/run-1.json` to `run-3.json`, exactly as returned. `result.json` written.
- Median ranks: journal 1 (ranks 1,1,2), spend tracking 2 (2,2,1), bill list 3 (3,3,3).
- Cut: the bill list, last in all three runs. Kept the other two, whose order swaps between runs.
- Moved journal and spend tracking `discovered` to `screened` with `screen_notes`. Moved the bill list `discovered` to `killed`.

## Evidence
- `Glob STOP` and `Glob ../../STOP` -> "No files found" for both.
- `Glob state/items/*.json` before the run -> 3 items at `discovered` (grep of "stage"): journal, bills, spend.
- Ranker outputs (verbatim in run files). Rank 3 went to the bill list in run 1 (id B), run 2 (id C) and run 3 (id A), by the id maps in `result.json`.
- Edits to the three item files each returned "updated successfully". I did not read them back.

## Not done
- Did not use `screen_runs`-style accuracy tracking: `state/screen/accuracy.jsonl` is written by telemetry later.
- Did not read items already at `specced` or `killed`. Not my stage.
- Did not write to the ledger. The wrapper records token cost.
- Did not reread the item files after editing, and did not run any `checks/`. This stage has no hard check.

## Denied or blocked
- none

## Findings
- The batch is only 3 ideas. The kill leaves a median-rank spread that is thin evidence either way.
- The bill list had the strongest scout evidence of the three (12 dated complaints, 4 apps, capability gaps) and lost on ad-tap appeal only. The ranker rewards emotional hooks over utilities. This kill is a weak signal and the item file says so. If the operator disagrees, it is a judgement call to revisit, not a rule.
- Rankers were haiku subagents, so the ranker model differs from the orchestrator. Previous batch `2026-11-17-a` did not record its ranker model.
- Scout files carry no keyword data, so the cards used "not available".

## Next
- journal-that-never-loses-entries: `screened`, then spec-differentiation.
- private-spend-tracking-without-bank-login: `screened`, then spec-differentiation. The spec must show manual entry or statement import is acceptable, since one reviewer wants bank linking.
- offline-bill-list-that-keeps-paid-status: `killed`, terminal.

## Proposed lesson
- none
