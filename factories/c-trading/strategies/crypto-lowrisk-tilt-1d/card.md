# crypto-lowrisk-tilt-1d

Written 17 November 2026, before any test. Run 20261117T084053Z-ideate-b169cc. Dataset: `crypto-1d`.

## Idea

Every few weeks, hold the few coins with the lowest recent volatility, equal weighted, and avoid the lottery-like ones. Always invested in the chosen coins.

## Why someone would pay for this

Lottery-seeking and leverage-constrained buyers overpay for volatile, high-upside coins, so those coins earn less per unit of risk (low-risk and MAX anomalies in equities: Ang et al. 2006, Bali, Cakici and Whitelaw). Crypto support: Grobys and Junttila 2021 (20 coins, 2016 to 2019), Leong et al. 2023 (4,000+ coins, mostly small). **The sign is disputed:** Ozdamar et al. 2021, Li et al. 2021, Zhang and Li 2020 and Bouri et al. 2024 find high-risk coins earn more. Evidence is for broad universes of small coins; it is untested here among ten large ones. Scout file: `state/scout/2026-11-17-crypto-daily-nontrend.json`, abstract-level reading only.

## Rules

- Every `rebalance` days, compute each coin's realised volatility of daily returns over the trailing window.
- Hold the `bottom_k` lowest-volatility coins equally weighted, fully invested. A coin already held is not traded.
- Long only, no leverage. Decided at the daily close, traded at the next open.

## Parameters and ranges

| Parameter | Range | Meaning |
|---|---|---|
| `risk_lookback` | 21 to 90 days | window for volatility |
| `bottom_k` | 2 to 5 coins | number of calm coins held |
| `rebalance` | 7 to 30 days | days between selections |

## What would kill it

- It fails any of the four coded checks.
- Selection collapses to mostly one coin (BTC), making it a single-asset bet.
- Apparent alpha comes from low beta in the 2021 to 2025 window, not from the mechanism.
- It needs one exact lookback, or the result is one year.

## Expected behaviour if real

Lower volatility and shallower drawdowns than the basket, slowly changing holdings, few trades (monthly at most), cost share small. Because the literature disagrees on the sign, a clean fail is quite likely and is an informative result.

Known biases: universe chosen with hindsight, slippage assumed, and the model's training data may include the test period.
