# Code review: crypto-volmanaged-basket-1d

Run 20261117T084519Z-build-f98666. Task `code`. Read: `card.md`, `strategy.py`, `params.yaml`, and for execution semantics `engine/backtest.py` and `engine/config.yaml`. I ran nothing.

## 1. Does the code do exactly what the card says, with nothing added and nothing missing?

**No.** The text of `strategy.py` follows the card. The positions the engine actually trades do not, because the engine filters the strategy's `band` through its own filter.

- `engine/config.yaml` line 31 sets `execution.rebalance_band: 0.02`. `engine/backtest.py` lines 31-41 (`_band`) apply it **per symbol**: a symbol's position changes only when its new target weight differs from the held weight by more than 0.02, or the new target is 0.
- `strategy.py` line 33 gives each coin weight `exposure / 10` (ten symbols in `engine/config.yaml` line 19). So a change in per-coin weight of 0.02 equals a change in total exposure of **0.20**.
- The card's `band` range is 0.10 to 0.30 (card, Parameters table). For `band` = 0.10 and 0.15, the strategy issues exposure changes that the engine ignores until the accumulated change passes 0.20. The traded no-trade band is then roughly max(`band`, 0.20). It is neither the declared band nor a clean replacement for it. The two filters run on different reference points (the strategy's `current` and the engine's `held`), so the resulting path depends on both.
- Effect on honesty: the card says `band` "controls turnover", but in the lower part of the declared range it barely does. A sweep over `band` will show results that are flat in 0.10 to 0.20 because of the engine, not because the idea is stable. That would look like the "broad region" evidence the result review relies on, and every one of those near-duplicate trials still counts against the bar.
- The same filter also stops the strategy from ever entering from cash at total exposure of 0.20 or below (per coin 0.02 or below). That is a further departure, but it matters less.

Smaller points, not decisive on their own:
- Line 35 zeroes a coin's weight on any bar where its close is missing. The engine treats a zero target as an exit (`backtest.py` line 38), so a one-bar data gap makes the strategy sell that coin and buy it back. That trade comes from the data gap, not from the band rule the card states. I did not check whether `data/dev` crypto-1d has gaps.
- Line 13: `close.pct_change()` uses pandas' default fill behaviour, so returns across a gap are smoothed into the next bar. This uses only past data and does not leak.

The builder's stated choices are reasonable readings of a silent card: an absolute band, starting in cash until the first estimate, and the basket return as the mean of coin returns.

## 2. Is every number that changes behaviour a declared parameter, with the card's ranges?

**Yes.** `vol_lookback` 20 to 90, `vol_target` 0.3 to 1.0 and `band` 0.10 to 0.30 match the card (`params.yaml` lines 3-5). `BARS_PER_YEAR = 365` (`strategy.py` line 8) equals `bars_per_year` for crypto-1d in `engine/config.yaml` line 14, and the card states `vol_target` in annualised terms. I accept it as a unit conversion. The step sizes were not in the card. They only set how many trials a sweep costs. `chosen` is the midpoint of all three ranges, which does not point to any selection.

## 3. Could any path use the future in a way the leak test might miss?

**No**, not in the code. `rolling(lookback).std()` on `pct_change()` and the forward loop in `banded_exposure` use only bars up to t. Two declared, non-code biases remain. First, the ten-coin universe is today's survivors (`engine/config.yaml` lines 17-18, and the card). Second, the `vol_target` range is described relative to how volatile the basket is known to be ("from heavy de-risking to rarely de-risking"). That knowledge can only come from prior knowledge of crypto volatility, which may include the dev period. The card admits training-data contamination. Neither bias is a code leak.

## 4. Does any helper keep state between calls, or reach beyond `bars` and `params`?

**No.** `banded_exposure` keeps `current` only inside a single call. Nothing is global or mutable. It imports only `math`, `numpy` and `pandas`.

## 5. Does the card name who pays and why, and what would kill the idea?

**Yes.** It names holders who stay fully exposed through forced-deleveraging episodes, and it cites Moreira and Muir (2017) for why risk taken in high-volatility periods is poorly paid. It says plainly that the crypto evidence is indirect and that the equity replications are contested. The kill conditions are specific: no alpha after the market adjustment, correlation with the killed trend family, a narrow corner of the ranges, or a result that comes from one year. The counterparty argument is weak, and the card says so.

## Decision

**Reject**, on item 1. As executed, the declared `band` parameter does not do what the card says over the lower part of its declared range, because the engine's per-symbol `rebalance_band` (0.02 × 10 coins = 0.20 of total exposure) overrides it. Any sweep would partly measure the engine's band rather than the card's, and would make the result look more stable than it is. I make no suggestion on how to change the parameters or ranges. Under hard rule 5 the card cannot be edited after the first trial, and the engine is not the builder's to change. If the per-symbol band is judged to be an engine issue affecting weight-scaled strategies in general, that is `F-ENG-1`.
