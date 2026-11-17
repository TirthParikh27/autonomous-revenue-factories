---
name: optimise
description: Stage 3 of Factory C. Use on the optimise run to search a built strategy's declared parameter ranges on development data, choose a stable region, run the local gate, and move the item to `optimised`, `watch` or `killed`. Every evaluation is a counted trial.
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
5. Run `python3 -m engine gate <id>`. The engine writes `state/gate/<id>.json` with the coded checks and the supporting evidence.
6. If a coded check fails, read `only_luck_score_failed` in the gate file.
   - `false`: the item is killed and the family is closed. Write `result.md` with the numbers copied from the gate file.
   - `true`: the strategy passed everything except the deflated Sharpe ratio. It is a near miss, and you decide what it deserves. Go to **Near miss** below.
7. If every coded check passes, call the `reviewer` agent with the task `result`. It reads the gate file and the trial log and writes `strategies/<id>/review-result.md`. It can reject for reasons the coded checks do not see: an overfit sweep, one sub-period carrying the result, a near-copy of an existing strategy. A rejection kills the item.
8. If the reviewer does not reject, move the item to `optimised` and write `result.md`. The exam job on GitHub picks up `optimised` items by itself, runs the single look at unseen data, writes `exam/<id>.json` and moves the item to `paper` or `killed`. You do nothing more.

## Near miss

The gate cannot tell a modest real edge from luck on five years of data (`FACTORY_SPEC.md` section 9), so a strategy is not thrown away on that one number. You cannot pass it either. Only prices that did not exist when it was tuned can do that. Read the whole gate file and the card, then choose one, and write the reasoning in `result.md`:

- **Watch.** Move the item to `watch`. The daily job tracks it on new prices from tomorrow, at exactly these parameters. It never joins the combined book and is never escalated from `watch`. Choose this when the evidence beyond the score is good: a published, replicated mechanism, a broad stable region in the sweep, both halves of the universe working (`half_universe`), no single sub-period carrying the result, costs a small share of return.
- **Watch, and propose another market.** As above, and add a line to the item, `try_in: <market>`, for `ideate` to pick up. Only when the card's reason is general (it rests on how investors behave, such as trend or slow reaction to news) and so should hold elsewhere. Never for an idea that rests on one market's plumbing.
- **Kill.** The default when the evidence is thin: a low score with nothing else in its favour, a result carried by one symbol or one year, a mechanism with no support beyond this backtest.

Call the `reviewer` agent with the task `result` before moving an item to `watch`. A rejection kills it. There is no score band for this decision. Say what you weighed.

## Guidance

- One sweep is normally enough. A second sweep is justified when the first shows a promising region at the edge of what it sampled. It is not justified by a fail.
- The gate judges the average of all your variants that behave alike, so extra trials near a lucky point do not help. They only raise the bar for the next strategy on this dataset.
- A narrow fail is still a fail of the gate. It can earn a place on `watch`. It can never be turned into a pass by another trial.
- Say what you cannot explain. A good result with no visible reason is more likely an error than a discovery, so check the code and the data before believing it.

## Never

- Never change the declared ranges, the rules or the universe after the first trial.
- Never change `chosen` after the gate has run, and never re-run the gate to see whether a different choice passes.
- Never compute a metric yourself. Read it from the engine's files.

## Finish

End with the shared `run-report` skill. Paste the gate's pass or fail lines and the trial count as evidence.
