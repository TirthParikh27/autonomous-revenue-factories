# Result: failed the local gate (17 November 2026)

Run 20261117T085052Z-optimise-f81ecb. Numbers are copied from `state/gate/crypto-lowrisk-tilt-1d.json` and `state/trials/crypto-1d.jsonl`.

## Sweep
- 41 trials on `crypto-1d`: 1 on the starting parameters (t000001), 40 from the sweep (t000002 to t000040), and the gate run (t000041).
- Every sweep trial had a positive raw Sharpe, ranging from 0.36 to 1.14 (gate quartiles 0.36 / 0.53 / 0.73 / 0.91 / 1.14). The strategy is always about 0.96 to 0.99 invested and long only, so a uniformly positive Sharpe points to market exposure, not selection skill.
- Shorter volatility windows (21 to 33 days) gave raw Sharpe of about 0.7 to 1.14 across rebalance values 10 to 30. Windows of 39 days or more gave 0.36 to 0.78. `bottom_k` 3 was usually best, with 2 and 4 close behind.
- Costs were small: 0.011 to 0.047 a year, on a turnover of 3.7 to 15.7 a year.

## Chosen parameters
`risk_lookback` 27, `bottom_k` 3, `rebalance` 25. This is the centre of the broad short-window region (window 21 to 33, rebalance about 21 to 30, k 3), rounded to plain values. It sits next to the top-ranked point (27/3/24). I picked it as the centre of that region, not because it ranked first.

## Gate (t000041): **fail**
- leak_test: pass.
- deflated_sharpe: **fail**, 0.22 against a minimum of 0.95. The average market-adjusted Sharpe of the 40 alike trials is -0.1. This variant's is 0.23. Market beta is 0.53. The Sharpe needed to beat luck is 0.25. Trials logged: 41. Distinct ideas: 2.
- positive_at_stressed_costs: pass, with a market-adjusted return of 0.0727 a year at 2x costs.
- beats_buy_and_hold: **fail**, Sharpe 0.9 against a benchmark of 1.03.
- Supporting evidence: sweep overfitting probability 0.59. Sub-period Sharpes 2.01, -1.38, 1.81, 1.33, 0.41. Max drawdown -0.8068. 151 orders, turnover 10.18 a year, costs 0.0305 a year.

## Verdict
Killed. The family is closed. This hits the card's kill condition "apparent alpha comes from low beta ... not from the mechanism". Once market exposure is removed, the variants average a slightly negative Sharpe. The raw result is a cheaper-volatility way of holding the market, and it does not beat holding the basket.

Not checked: the card's "mostly BTC" kill condition. The engine files do not report holdings by symbol, and I may not compute them myself. The fail does not depend on it.

Known biases: the universe was chosen with hindsight, the cost model is assumed rather than measured, and my training data may include the development period. The literature disagrees on the sign of this effect, so a fail does not prove a low-risk effect is absent in broader crypto universes. It means the evidence is not here.
