---
name: implement
description: Turn one hypothesis card into deterministic strategy code with unit tests and a trial request for Factory C. Use when an item is at `hypothesized`, or when `evolve` has created a variant item that needs its params file and trial request.
---

# Implement

Stage: `hypothesized` -> `implemented`. Batch: 1 item per run.

## Inputs

- `budget.yaml`, `STOP` files, `escalations/`.
- One item at `hypothesized` (oldest first) and its `strategies/<id>/hypothesis.md`.
- `engine/INTERFACE.md`, `engine/ALLOWED_IMPORTS`, `engine/fixtures/` (synthetic data only). Read only.

## Steps

1. Check the family and window trial budgets in `budget.yaml` against `registry/trials.jsonl`. If no trial is available, do not implement. Report and stop.
2. Delegate the build to the `strategy-builder` agent with the card path. It writes:
   - `strategies/<id>/strategy.py`: one pure function, history up to t-1 in, target weights for t out.
   - `strategies/<id>/params.yaml`: exactly the card's parameters at their defaults.
   - `strategies/<id>/tests/`: shape, weight limits, shift test for look-ahead, missing-bar behaviour.
3. Run the unit tests on the synthetic fixtures. At most 2 fix attempts. A third failure kills the item.
4. Delegate review to the `overfit-verifier` agent: does the code implement the card and nothing else, does any path use data at or after t, are there constants not on the card. It reports only gaps that affect correctness.
5. Fix real gaps once. If the verifier still reports a look-ahead path, kill the item.
6. Write `trials/requests/<trial id>.yaml`: strategy id, family, code path, params path, requested by run id. One request per item. Do not name a data window; CI chooses it.
7. Commit to `claude/strategy-<id>` and open a PR. CI picks up the request.
8. Move the item to `implemented`. Record the PR URL and trial id in `history`.

## Tools

Read, Write, Edit, Bash for `pytest` on fixtures only, `git`, `gh`. Agents: `strategy-builder`, `overfit-verifier`.

## Deterministic check

Local, pasted in the run report:
- `pytest strategies/<id>/tests` summary line.
- `engine/lint_imports strategies/<id>` output.
- `engine/lookahead_audit strategies/<id>` output.
- `engine/card_match strategies/<id>` output (params file equals card).

CI repeats all four on the PR. The CI result is the one that counts. A local pass with a CI fail is a failed run.

## Outputs

Strategy directory, trial request, PR, updated item, run report.

## Stop conditions

- Card is ambiguous enough that two readings give different code: kill the item with reason "card not implementable as written". Do not fix the card.
- Code needs an import outside the allowlist: kill, or raise `F-ENG-1` if the gap is general.
- Any tool call touching `engine/`, `registry/`, `results/` or `.github/` is denied: stop, report verbatim, raise `F-INT-1` if it was an edit attempt.

## Never

- Never run the strategy on real market data, and never fetch any.
- Never request more than one trial per item, or re-request a trial with changed code under the same id.
- Never add a parameter, filter or exit rule that is not on the card.
- Never print or return input data from strategy code.
- Never push to `main` or edit a workflow file.

End by calling the shared skill `factories/_shared/skills/run-report`.
