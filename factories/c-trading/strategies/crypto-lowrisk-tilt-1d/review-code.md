# Code review: crypto-lowrisk-tilt-1d

Run 20261117T084844Z-build-43482e. Task `code`. Files read: `card.md`, `strategy.py`, `params.yaml`, `engine/backtest.py`, `engine/data.py`, `engine/config.yaml`, `lib/indicators.py` (`volatility`).

## 1. Does the code do exactly what the card says, with nothing added and nothing missing? Yes

- Volatility of daily returns over the trailing `risk_lookback` window: `indicators.volatility` is `close.pct_change().rolling(n).std()`. It uses bars up to and including t only. Leaving it unannualised does not change the ranking.
- Every `rebalance` days the code ranks ascending and holds the `bottom_k` lowest at 1/k, with nothing else held. Between selections the target is forward-filled.
- "A coin already held is not traded": a coin that stays selected keeps an identical 1/k target. `_band` in `engine/backtest.py` (line 38) then emits NaN, so no order is sent and the weight drifts with price. That is the literal reading of the card.
- Decided at the close, filled at the next open: the engine does `weights.shift(1)` and fills at `bars.open`.
- Long only, sum = k * (1/k) = 1.

Additions on points the card does not cover, none of which changes the idea:
- The strategy holds cash until every coin has a full estimate. That is about `risk_lookback` bars at the start.
- The schedule is anchored at the first valid bar.
- Ties break by column order.

A side effect of the no-trade rule: drifted incumbents are not trimmed, so a new entrant's 1/k target may be only partly fillable when the incumbents have grown. Holdings are therefore only roughly equal weight after the first selection. This follows from the card's own wording, so it is not a deviation, but results should not be read as a strict equal-weight portfolio.

## 2. Is every number that changes behaviour a declared parameter, with the card's ranges? Yes

- `risk_lookback` is 21 to 90 with step 3, which reaches 90 exactly. `bottom_k` is 2 to 5 and `rebalance` is 7 to 30. These match the card's table.
- The only literals in the code are 0.0 and 1.0, which are structural.
- The step sizes and `chosen` (54, 3, 18) were not in the card. All three chosen values sit inside the ranges and near the middle. They were fixed before any trial, so the card is not changed by them.

## 3. Could any path use the future in a way the leak test might miss? No

- Volatility and rank on each row use only past and current closes.
- The schedule phase depends only on the first valid bar, which truncating later bars cannot move.
- No constant is fitted from the full sample.
- The ranges come from the card, which was written before testing.
- The universe was chosen with hindsight on 17 Nov 2026 (`engine/config.yaml`). That is engine-level, shared by every strategy, and declared in the card's known biases. It is not something this code adds. It does matter more than usual here, because the cross-sectional ranking is done only among today's survivors.

## 4. Does any helper keep state between calls, or reach beyond `bars` and `params`? No

`selection_days` is pure: a new array on every call, no globals, no I/O.

## 5. Does the card name who pays and why, and what would kill the idea? Yes

- Who pays: lottery-seeking and leverage-constrained buyers overpay for volatile coins (low-risk and MAX anomaly, with citations). The card states plainly that the sign is disputed in crypto.
- Kill conditions: the four coded checks; selection collapsing to mostly BTC; alpha that is only low beta in 2021 to 2025; needing one exact lookback or one year.

## Remaining weaknesses (not grounds for rejection)

- The mechanism is unproven in a universe of ten large coins, and the card's own literature disagrees on the sign.
- Low-volatility selection among large coins will likely be a low-beta, BTC/ETH-heavy book. The gate's removal of market exposure is the real test. The card's kill condition on collapsing to BTC must be checked from the results.
- `engine/data.py` drops any bar where a symbol is missing. `pct_change` can then span a gap and treat it as a single return. This is minor on daily bars.

Code review verdict: not rejected.
