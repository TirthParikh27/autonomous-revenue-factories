# Result: failed the local gate (17 November 2026)

Numbers are copied from `state/gate/crypto-trend-1h.json` and `state/trials/crypto-1h.jsonl`.

- 41 trials on `crypto-1h` (1 by hand, 40 by parameter search). All 41 behave alike and count as one idea.
- Chosen parameters: fast 78, slow 328, vol_window 336, from the middle of the best region.
- Raw result looks good: Sharpe 1.27, total return +844% over 2021 to 2025, against buy-and-hold Sharpe 1.05.
- After removing market exposure (beta 0.30) the idea's Sharpe is 0.65 across its variants. The deflated Sharpe ratio is 0.929 against a pass mark of 0.95. **Fail.**
- The other three checks passed: no look-ahead, positive at doubled costs, beats buy-and-hold.
- Evidence against it: yearly Sharpe was 3.31, -1.01, 1.87, 1.27, -0.81, so most of the result is 2021. Overfitting probability of the sweep is 0.74. Costs took 9.5% a year.

Verdict: killed. The family is closed. This is the outcome the research predicted for crypto trend following: mostly a cheaper way to hold the market.
