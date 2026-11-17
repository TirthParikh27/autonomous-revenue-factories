---
name: ideate
description: Stage 1 of Factory C. Use on the idea run to turn researched trading ideas into strategy cards and create items at stage `proposed`. Runs no backtests and reads no market data.
---

# Ideate

You are a fresh session with no memory. Read `CLAUDE.md` and `budget.yaml` first.

## Inputs

- `state/items/`: every item, including killed ones. A killed family is closed.
- `strategies/*/card.md` and `strategies/*/result.md`: what was tried and what happened.
- `state/trials/<dataset>.jsonl`: how many trials each dataset has already absorbed.
- `engine/config.yaml`: the datasets, symbols and costs that exist today.
- `journal/LESSONS.md`.

## Steps

1. Count items at `proposed`. If the count is at or above `pipeline.max_items_awaiting_build`, write a run report saying so and exit.
2. Decide what the factory is short of. Look at which mechanisms, markets and timeframes the existing and killed items cover, and which datasets carry the fewest trials. A fresh dataset has the lowest bar, and a strategy unlike the others adds most to the combined book.
3. Delegate the reading to the `idea-scout` agent. Give it the gap you want filled, the list of existing and killed ideas in one line each, the datasets available, and an output path `state/scout/<date>-<slug>.json`. You do not read raw web pages yourself.
4. Judge each candidate the scout returns. Keep one when:
   - it names who pays and why, with a source that is more than a backtest;
   - it can be tested honestly on bar data that exists in `engine/config.yaml`, at the costs listed there. A card that shorts or borrows says so, and its expected edge must survive that market's margin fee and borrowing interest;
   - it is a different mechanism from every existing and killed card, not a variant of one;
   - its expected trading frequency leaves room for costs on its timeframe.
   - its rules do not re-implement what the engine already does. The engine fills at the next bar's open and charges fees and slippage. It also ignores weight changes smaller than a no-trade band per symbol, which a card may set to its own fixed value (`rebalance_band` in `params.yaml`, declared on the card, not swept).
5. For each one kept, up to `pipeline.max_new_cards_per_run`, write `strategies/<id>/card.md` in the shape of `strategies/crypto-trend-1h/card.md`: idea, why someone would pay, rules in words, parameters with ranges, what would kill it, and expected behaviour if real. Cite the scout's sources. Choose ranges from the mechanism (for example a trend horizon the literature supports), wide enough that a stable region can show itself, and before any test.
6. Create `state/items/<id>.json` at `proposed` in the shared format, with the card path and sources in `evidence`.
7. Record each candidate you dropped and why in `state/scout/rejected.jsonl`, so it is not proposed again.

## Outputs

- `state/scout/<date>-<slug>.json` from the scout.
- `strategies/<id>/card.md` and `state/items/<id>.json` per idea kept.

## Never

- Never run the engine in this stage. The card is fixed before any result exists.
- Never write a card for a market or instrument outside the spec's scope. Raise `F-VENUE-1` if the evidence for one is strong.
- Never take a performance figure from a web page as evidence the idea works. It is a reason to test, at most.
- Never reopen a killed family with a new name.

## Finish

End with the shared `run-report` skill. Include the keep or drop reason for every candidate.
