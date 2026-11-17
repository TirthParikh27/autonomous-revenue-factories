# Trading strategy factory: Define

Phase 2 of the double diamond. Date: 17 November 2026. Evidence for every claim is in [DISCOVERY_REPORT.md](DISCOVERY_REPORT.md). This document fixes the problem and the requirements. It does not choose a design.

## 1. The problem

Finding a strategy with a great backtest is easy and worthless: test enough variations and one looks excellent by luck. The real problem is to run a search that tests many strategies and still knows how much to trust its survivors, then to keep those survivors healthy as markets change.

**Problem statement.** Build a factory that continuously proposes, tests, optimises and maintains trading strategies on hourly to daily data, and tells the operator about a strategy only when it can state, with evidence, how likely that strategy is to be real.

The product is the process. Profit is not the goal, and no real money is involved.

## 2. What "winner" means

A strategy climbs a ladder. Each rung has a stated meaning, so a report never says more than the evidence supports.

| Rung | Meaning | Evidence |
|---|---|---|
| Candidate | Worth testing | A written idea with a reason it should work, and code that passes leak checks |
| Backtest-passed | Unlikely to be luck, given every trial the factory has run | Net-of-cost results that clear a bar which rises with the trial count, are stable across parameters and sub-periods, and pass a single look at held-back data |
| Paper-confirmed | Runs correctly and behaves as predicted | Paper results, re-priced with the factory's own costs, stay inside the range the backtest predicted |
| Winner (escalated) | The operator should look | Paper-confirmed, adds something to the book of existing strategies, with the full trial history attached |

Paper trading cannot prove a single strategy is profitable in a few months. The escalation therefore states its confidence plainly: how many trials were run, the adjusted odds that the result is luck, and what paper trading did and did not show.

## 3. Requirements

### The judge

- R1. A fixed engine decides every pass and fail. It owns the data, the cost model, the test windows, the metrics and the pass rules. Agents cannot edit it.
- R2. The engine changes only through a versioned change the operator approves. Earlier survivors are re-tested after a change.
- R3. Every test is logged before its result is shown, including failures. The bar for passing rises with the number of trials on the same data.
- R4. Costs are always on: fees, spread, slippage, and funding where it applies. Each strategy is re-run at higher costs.
- R5. Look-ahead is blocked by construction. A strategy only receives data up to the bar it is deciding on, and every candidate gets a mechanical test that changes future data and checks that past decisions do not move.
- R6. Some data is held back from the search and looked at once per strategy family. The search never sees it, not even as pass or fail on work in progress.
- R7. A reviewer model checks what code cannot: that the code matches the stated idea, and that the idea has a sensible reason. It can reject. It can never pass.
- R8. The judge is tested before it is trusted: it reproduces a known published result, finds an edge planted in synthetic data, and rejects pure noise.

### The search

- R9. Agents propose ideas and write strategy code. Ideas come with a reason someone would pay for the edge. Ideas with a reason get a lighter bar than brute-force search.
- R10. Near-duplicates are caught before they are counted as new ideas, by comparing both the rules and the returns.
- R11. Optimisation happens inside parameter ranges declared before the first test. Stable regions of parameters are preferred over the single best point.
- R12. The search covers several strategy families and several markets, so results do not depend on one idea or one dataset.

### Maintenance (the self-improving loop)

- R13. Every strategy on paper is tracked against a small set of health metrics, and against the range of outcomes its backtest predicted.
- R14. When a strategy leaves that range, the factory diagnoses the cause first: implementation fault, higher costs, regime change, or a fading edge.
- R15. The factory then acts: fix, re-tune, reduce weight, pause or retire. A paused strategy keeps running in shadow so evidence keeps accumulating.
- R16. A re-tune is a new counted trial. It passes the same gate and runs beside the old version on paper before replacing it. A strategy that needs repeated re-tuning is retired.
- R17. The factory also keeps a combined book of all paper-confirmed strategies and reports on it, because evidence builds faster across many strategies than on one.

### Operation

- R18. Paper only. No live keys exist in the factory. Order placement is done by plain scripts, never by a model.
- R19. The operator hears about winners, about anything that needs approval (engine changes, new markets, any spend), and gets a short periodic summary. Nothing else.
- R20. Every number in a report comes from a file the engine wrote.
- R21. It runs on free tools and free data to start. The kill switch and conventions shared by the other factories apply.

## 4. Scope

**In scope first**
- Holding periods from hours to a few weeks, on hourly and daily bars.
- US ETFs and crypto on an Alpaca paper account, FX on an OANDA demo account.
- Data: Alpaca (US bars since 2016), OANDA (FX since 2005), Binance public archive (crypto).
- Families: trend and momentum, mean reversion, carry, breakout, seasonality, cross-market signals, and combinations.

**Out of scope**
- Real money, leverage decisions, and anything needing a funded account.
- Speed-based strategies: arbitrage across venues, market making, anything faster than hourly bars. Bar data cannot test them honestly.
- Single-stock strategies, until survivorship-free data is paid for (about US$630 a year).
- Crypto derivatives, until a paper venue open to Australians is confirmed.
- Prediction markets.

## 5. How we will know the factory works

- It rejects noise and finds planted edges at the rates it claims (R8).
- Paper results of backtest-passed strategies land inside their predicted ranges about as often as predicted.
- The trial log is complete: every result in a report traces to a logged trial.
- Maintenance actions improve or correctly retire strategies more often than they churn them.
- A run that ends with "nothing passed" is a correct result, and is reported as one.

## 6. Tensions the design must resolve

1. **Trials only accumulate.** The more the factory tests on the same history, the higher the bar gets. The design needs a trial budget per dataset and a supply of fresh data: new markets, and time passing.
2. **Feedback versus leakage.** Agents improve faster with rich feedback, but every result they see becomes something they can fit to.
3. **Re-tuning versus overfitting.** The maintenance loop must fix real decay without chasing noise.
4. **Paper time.** Hourly strategies gather evidence faster than daily ones. The paper period should scale with how often a strategy trades, by judgement, with the reasoning shown.
5. **Strategy form.** Free-form Python is flexible. A restricted rule format makes leak prevention and duplicate checks much cheaper.
6. **Simplicity.** The existing blueprint puts every backtest in CI with a hash-chained registry. That is heavy. The design should find the lightest setup that still keeps the judge out of the agents' reach.
