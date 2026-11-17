---
name: build
description: Stage 2 of Factory C. Use on the build run to turn a strategy card at stage `proposed` into code that passes the engine's lint and leak test and the reviewer, moving the item to `built`. Runs no trials.
---

# Build

Read `CLAUDE.md` and `budget.yaml` first. Take one item at `proposed`, the oldest.

## Steps

1. Read the card. If it cannot be coded as written (missing data, a rule that needs the future, a rule that is ambiguous), kill the item with that reason. Do not repair the idea here.
2. Write `strategies/<id>/params.yaml`: the `dataset`, the `ranges` exactly as the card declares them, and a `chosen` set from the middle of each range. `chosen` is a starting point for the checks, not a tuned result.
3. Write `strategies/<id>/strategy.py` with the single function `weights(bars, params)`. Follow the coding standards in `CLAUDE.md`. Use `lib.indicators`, and add an indicator there only when the card needs one it lacks.
4. Run `python3 -m engine check <id>`. It lints the code and runs the leak test: the weights computed on the full history must equal the weights computed with the future removed. Fix the code until it passes. A leak is fixed by removing it, never by changing the card.
5. Call the `reviewer` agent with the task `code`. It writes `strategies/<id>/review-code.md`. If it rejects, fix what it names and call it once more. A second rejection kills the item.
6. Move the item to `built` and record the check output and the review path in `evidence`.

## What good code looks like here

- The rules in the card and the rules in the code are the same rules. Nothing extra, nothing missing.
- No number that changes behaviour sits outside `params.yaml`.
- Every rolling or expanding calculation uses the past only. Common leaks: normalising by a full-sample mean or standard deviation, centred windows, ranking across time, back-filling gaps, choosing symbols by what happened later.
- Missing bars produce a zero weight, not an error and not a forward-filled signal that trades on stale prices.

## Never

- Never run `trial`, `sweep` or `gate` in this stage. The first counted trial belongs to `optimise`.
- Never edit the card. If the card is wrong, the item is killed and `ideate` may write a new one.
- Never work around the lint with an indirect import or a helper in `lib/` that reads files, the clock or the network.

## Finish

End with the shared `run-report` skill, with the `check` output pasted as evidence.
