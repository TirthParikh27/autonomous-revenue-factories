---
name: optimise
description: Stage 3 of Factory C. Use on the optimise run to search a built strategy's declared parameter ranges on development data, choose a stable region, run the local gate, and move the item to `optimised` or `killed`. Every evaluation is a counted trial.
---

# Optimise

Read `CLAUDE.md` and `budget.yaml` first. Take one item at `built`, the oldest.

This stage answers one question: is there a broad region of the declared ranges where the idea works after costs, and does the engine's gate accept it? It is not a hunt for the best number.

## Steps

1. Run `python3 -m engine trial <id>` once on the starting parameters. Read the result. If the idea plainly does nothing (flat, or costs take everything), kill it now. One trial is the cheapest way to fail.
2. Run `python3 -m engine sweep <id> -n <count>`. The search stays inside the card's ranges and logs every run. Choose the count from the number of parameters and what you need to learn, with `research.typical_sweep_trials` as a reference point, and never above `pipeline.max_trials_per_run` in total for this run.
3. Read the sweep from `state/trials/<dataset>.jsonl`. Look at how the result varies across each range, not at the top row:
   - Does a wide, connected region work, or only scattered points?
   - Is the result driven by one year, one symbol or a handful of trades?
   - What share of gross return do costs take, and how often does it trade?
4. Choose parameters from the middle of the broadest region that works, rounded to plain values. Write them to `chosen` in `params.yaml` and say why in `strategies/<id>/result.md`. If no such region exists, kill the item.
5. Run `python3 -m engine gate <id>`. The engine writes `state/gate/<id>.json` with the four coded checks and the supporting evidence.
6. If any coded check fails, the item is killed and the family is closed. Write `result.md` with the numbers copied from the gate file.
7. If all four pass, call the `reviewer` agent with the task `result`. It reads the gate file and the trial log and writes `strategies/<id>/review-result.md`. It can reject for reasons the coded checks do not see: an overfit sweep, one sub-period carrying the result, a near-copy of an existing strategy. A rejection kills the item.
8. If the reviewer does not reject, move the item to `optimised` and write `result.md`. The exam job on GitHub picks up `optimised` items by itself, runs the single look at unseen data, writes `exam/<id>.json` and moves the item to `paper` or `killed`. You do nothing more.

## Guidance

- One sweep is normally enough. A second sweep is justified when the first shows a promising region at the edge of what it sampled. It is not justified by a fail.
- The gate judges the average of all your variants that behave alike, so extra trials near a lucky point do not help. They only raise the bar for the next strategy on this dataset.
- A narrow fail is a fail. The first strategy through this factory failed at 0.929 against 0.95 and was killed.
- Say what you cannot explain. A good result with no visible reason is more likely an error than a discovery, so check the code and the data before believing it.

## Never

- Never change the declared ranges, the rules or the universe after the first trial.
- Never change `chosen` after the gate has run, and never re-run the gate to see whether a different choice passes.
- Never compute a metric yourself. Read it from the engine's files.

## Finish

End with the shared `run-report` skill. Paste the gate's pass or fail lines and the trial count as evidence.
