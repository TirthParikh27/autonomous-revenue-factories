---
name: maintain
description: The self-improving loop of Factory C. Use on the maintenance run to read the health watch for every strategy on paper, diagnose any that left its predicted range, take one action (fix, re-tune, pause, retire), and confirm strategies that have run long enough. Does nothing to a strategy that is inside its range.
---

# Maintain

Read `CLAUDE.md` and `budget.yaml` first. Work through every item at `paper`, `confirmed` or `paused`.

The judge's daily job writes `paper/<id>.json` (the forward-test record) and `health/<id>.json` (the record against the range its backtest predicts). You read them. You never compute them.

## The one rule that matters

**A strategy inside its predicted range is left alone**, however bad the stretch looks. Losing runs are normal, and reacting to them is how a healthy strategy gets tuned into an overfit one. Say so in the run report and move on.

## Steps

1. For each item read `health/<id>.json`.
   - `too_early` or `in_range`: no action. Go to step 4.
   - `above_range`: no action, but note it. A record far better than predicted is more often a fault than a gift.
   - `below_range`: if `days_below_range_in_a_row` shows it is more than a blip, go to step 2. Otherwise note it and wait.
2. **Diagnose.** Read the paper record, the gate file, the card and `result.md`. Name one cause, with the evidence for it:
   - *Fault.* The code does something on new data it did not do in the backtest, for example a symbol with missing bars.
   - *Costs.* The strategy trades more than its backtest did.
   - *New conditions.* The market is in a state the development data never contained, and the card's mechanism depends on the old state.
   - *Fading edge.* Nothing is broken and conditions are ordinary, yet the result has drifted down. This is the default when nothing else fits.
   Write the diagnosis to `strategies/<id>/maintenance/<date>.md`.
3. **Act**, once, and record it in the item's history.
   - *Fix* a fault: write the corrected strategy as a new item `<id>-v2` at `proposed` with the same card, and move the old one to `killed`. The fix goes through build, optimise and the exam like any strategy.
   - *Re-tune*: allowed only when development data has moved forward to include the period that went wrong. Create `<id>-r<n>` at `built` with the same card, code and declared ranges, and leave it to `optimise`. Its trials are counted and it takes the exam. Move the old one to `paused` so both records keep running side by side. Whichever does better on paper stays, decided at a later run.
   - *Pause*: move to `paused`. The record keeps running, so evidence keeps building, and the strategy leaves the combined book.
   - *Retire*: move to `killed`. Also the outcome when a strategy has already been re-tuned and has left its range again.
   When development data has not moved forward yet, the choice is between pause and retire.
4. **Confirm.** Move a `paper` item to `confirmed` when its record is long enough to mean something and it has stayed in range. Judge the length from how often it trades and how wide its predicted range is, and write the reasoning in the item. As a guide, hourly strategies need weeks to a few months and daily ones several months. Before confirming, check in the gate file how close its nearest neighbour among confirmed strategies is. A near-copy adds nothing to the combined book and stays at `paper`.
5. Move a `paused` item back to `paper` when its record has returned inside its range and stayed there.

## Never

- Never change a deployed strategy's code or parameters in place. The daily job refuses any version that is not the one that passed the exam.
- Never re-tune on a hunch, on paper results alone, or to data the strategy has not been examined on.
- Never describe a paper result as profit, or a strategy as working because its recent result is good.
- Never escalate a failing strategy. Pause or retire it.

## Finish

End with the shared `run-report` skill. List every strategy with its status and what you did, including "nothing, in range".
