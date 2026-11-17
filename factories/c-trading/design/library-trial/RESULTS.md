# Library trial results

Date: 17 November 2026. Run in the cloud session on Python 3.13. The main tests use generated prices, because the data hosts were blocked at the time, and check mechanics, not strategy results. A real data check was added once the hosts were allowed. Scripts are in this folder.

Versions: vectorbt 1.2.1, TA-Lib 0.8.3, purgedcv 1.0.0, skfolio 1.12.17, Optuna 5.1.0, numpy 2.5.5, pandas 3.1.1.

## vectorbt (backtesting)

| Requirement | Result | Evidence |
|---|---|---|
| Decide on one bar, fill at the next bar's open | Pass | Matches a hand-written reference loop: final value 0.923127 vs 0.923121 (`t1.py`) |
| Fees and slippage, per market and varying over time | Pass | `t1.py` |
| Long and short, several markets sharing one cash pool | Pass | `t1.py` |
| Per-bar returns for every trial | Pass | 105,120 x 400 return matrix (`t2.py`) |
| 15-minute, hourly and daily bars | Pass | `t2.py` |
| Speed for sweeps | Pass | 400 backtests over 3 years of 15-minute bars in 18 seconds (`t2.py`) |
| Funding and carry costs | Not built in | Applied as an adjustment to per-bar returns in our wrapper (`t2.py`) |
| Limit orders, leverage | Not in the free version | From the research, not tested |

Notes: a plain `pip install vectorbt` first resolved to 1.0.0, so the version must be pinned. Target-percent sizing rebalances every bar, so the wrapper needs a rebalance threshold to avoid paying costs on drift.

## TA-Lib (indicators)

| Requirement | Result | Evidence |
|---|---|---|
| Correct values | Pass | SMA matches pandas to 5e-13 (`t3.py`) |
| Uses past bars only | Pass | SMA, EMA, RSI, Bollinger and MACD values before a cut date do not move when later prices are changed (`t3.py`) |
| Speed | Pass | 200 RSI variants on 105,120 bars in 0.12 seconds |

## purgedcv (overfitting statistics)

| Requirement | Result | Evidence |
|---|---|---|
| Deflated Sharpe ratio is correct | Pass | Identical to an independent implementation from the 2014 paper (`t5.py`) |
| Probability of backtest overfitting is correct | Pass | Identical to an independent CSCV implementation on 15 datasets (`t7.py`) |
| Rejects noise | Pass | Best of 100 random strategies passed a 0.95 deflated Sharpe bar in 0 of 300 experiments (`t5.py`) |
| Finds a planted edge | Pass | A planted Sharpe 1.5 edge over 10 years scored 0.99 and overfitting probability 0.00. A planted Sharpe 0.5 edge was not distinguishable from noise, as the research predicts (`t7.py`) |
| Speed | Slow | 89 seconds for 200 trials at 16 splits, against 1.2 seconds for the independent version |
| Effective number of trials by return correlation | Missing | Its method handles sequential optimisers, not the clustering method the spec calls for |

Input orientation is `(configs, observations)`. Passing the transpose gives a plausible but wrong answer with no error, so the wrapper must fix the orientation.

## Optuna (optimisation)

| Requirement | Result | Evidence |
|---|---|---|
| Searches inside declared parameter ranges | Pass | 60 trials of a two-parameter strategy on 3 years of hourly bars in 1.8 seconds, with the second range depending on the first (`t8.py`) |
| Every trial is recorded | Pass | All 60 trials and their return series captured, and a SQLite-backed study kept its trials across loads |
| Feeds the overfitting statistics | Pass | Deflated Sharpe ratio and overfitting probability computed from the 60 recorded trials |
| Stable regions can be checked | Pass | Sharpe at nine neighbouring parameter points ranged 1.99 to 2.67 against 2.67 at the best point |

The test price series had a planted trend, so the high scores show the plumbing works, not that a strategy was found.

## skfolio (cross-validation splits)

| Requirement | Result | Evidence |
|---|---|---|
| Combinatorial purged cross-validation | Pass | 10 folds with 2 test folds gave 45 splits and 9 test paths. Train and test never overlapped, and the purge and embargo gaps were respected in all 45 (`t9.py`) |
| Walk-forward | Pass | 5 splits, every test window after its training window |

## Data hosts, checked against provider docs

| Source | Host | Checked in |
|---|---|---|
| Binance public archive | `data.binance.vision` | [binance-public-data README](https://github.com/binance/binance-public-data) |
| Alpaca historical bars, stocks and crypto | `data.alpaca.markets` | [Alpaca stock bars reference](https://docs.alpaca.markets/us/reference/stockbars), [crypto bars reference](https://docs.alpaca.markets/us/reference/cryptobars-1) |
| Alpaca paper trading | `paper-api.alpaca.markets` | [Alpaca API reference](https://docs.alpaca.markets/us/v1.1/reference/getclock-1) |
| OANDA practice account, REST | `api-fxpractice.oanda.com` | [OANDA development guide](https://developer.oanda.com/rest-live-v20/development-guide/) |

Alpaca's crypto bars need no API key. Its stock bars and all OANDA requests need the account keys.

## Real data check

After the three data hosts were allowed in the cloud environment:

- Binance: three months of BTCUSDT 15-minute bars downloaded (8,832 bars, August to October 2026, no gaps). Timestamps are in microseconds.
- Alpaca crypto bars: reachable without a key (HTTP 200).
- OANDA practice API: reachable, and correctly refuses a request with no token (HTTP 401).
- vectorbt and TA-Lib ran end to end on the real Binance bars. A plain EMA 20/100 crossover returned -8.9% net of costs against +23.3% for buy and hold, which is the expected result for an untuned textbook rule and confirms costs are being charged.

## Not tested

Alpaca stock bars and OANDA candles need account keys, which do not exist yet.

## Recommendation

- Use vectorbt (pinned), TA-Lib, Optuna, purgedcv and skfolio.
- Write ourselves: the wrapper that locks vectorbt's settings and adds funding and a rebalance threshold, the effective-trial count by clustering, the leak test, the trial log and the pass rules.
- Keep the two independent statistics implementations as tests of purgedcv.
