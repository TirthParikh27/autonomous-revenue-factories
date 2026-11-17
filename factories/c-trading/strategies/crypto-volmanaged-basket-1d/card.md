# crypto-volmanaged-basket-1d

Written 17 November 2026, before any test. Run 20261117T084053Z-ideate-b169cc. Dataset: `crypto-1d`.

## Idea

Hold an equal-weight basket of the ten coins and scale total exposure down when the basket's recent volatility is high. Excess goes to cash. Exposure never exceeds 1.

## Why someone would pay for this

Volatility clusters and can be forecast, but expected returns do not rise one for one with it, so risk taken in high-volatility periods is poorly paid (Moreira and Muir, Journal of Finance 2017). The counterparty is weakly argued: in crypto the likely payers are holders who stay fully exposed through forced-deleveraging episodes. No crypto paper found establishes this. Equity replications are contested (Cederburg et al. 2020). Crypto support is indirect: Grobys et al. 2025 (vol-scaled crypto momentum) and a practitioner note (Man Group, claimed figures not used as evidence). Scout file: `state/scout/2026-11-17-crypto-daily-nontrend.json`. Scout read abstracts and summaries only, not full texts.

## Rules

- Each day close, compute the realised volatility of the equal-weight basket's daily returns over a trailing window.
- Target exposure = min(1, target volatility / realised volatility). Split equally across the ten coins; the rest is cash.
- Change holdings only when target exposure moves outside a band around current exposure.
- Long only, no leverage. Decided at the daily close, traded at the next open.

## Parameters and ranges

| Parameter | Range | Meaning |
|---|---|---|
| `vol_lookback` | 20 to 90 days | window for basket volatility |
| `vol_target` | annualised, from 0.3 to 1.0 | volatility the basket is scaled to (spans the range from heavy de-risking to rarely de-risking) |
| `band` | 0.10 to 0.30 | no-trade band on exposure, controls turnover |

## What would kill it

- It fails any of the four coded checks.
- After market adjustment it has no alpha: it is only the basket with a lower average exposure.
- Its returns move with the killed trend family (volatility rises in sell-offs), so it counts as the same idea.
- It works only at a narrow corner of the ranges, or its result is one year.

## Expected behaviour if real

Similar upside to the basket in calm markets, smaller drawdowns in crashes, exposure well below 1 in 2022. A few to a few dozen exposure changes a year. Likely whipsaw: selling after the drop and re-entering late. The plain expectation is that it fails the gate as market exposure; I am curious whether the volatility timing adds anything.

Known biases: universe chosen with hindsight, slippage assumed, and the model's training data may include the test period.
