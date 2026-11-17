# Factory C: Trading strategy factory

Status: architecture, revision 2 (17 November 2026). Nothing is built or run.
Nothing in this factory is financial advice. It is a research harness on paper accounts.

This revision replaces the 16 November blueprint. It is the output of a double diamond design process. The reasoning is in [`design/`](design/): [research](design/DISCOVERY_REPORT.md), [requirements](design/DEFINE.md) and [design options](design/DEVELOP.md). The other files in this folder (`CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, `skills/`, `agents/`) still describe the earlier blueprint and are rewritten in build step 1.

## 1. Purpose

The factory continuously proposes, tests, optimises and maintains trading strategies on 15-minute, hourly and daily data. It tells the operator about a strategy only when it can state, with evidence, how likely that strategy is to be real.

The product is the process. Profit is not the goal. No real money is involved.

Three findings from the research shape everything below:

- **Testing many strategies manufactures false winners.** With five years of daily data, about 45 variations are enough to produce a Sharpe of 1 by luck. So every trial is counted and the bar rises with the count.
- **Models are good builders and poor judges.** Independent audits rejected nearly everything LLM agents found, and agents game what they can touch. So a fixed engine judges, and models only propose, build and diagnose.
- **Paper trading cannot prove profit quickly.** A Sharpe-1 strategy needs about three years to confirm. So paper trading checks that a strategy runs correctly and behaves as predicted, and reports say exactly that.

"Nothing passed" is the most likely result of any run. It is a correct result and is reported as one.

## 2. Scope

- **Timeframe:** 15-minute, hourly and daily bars, holding periods from under an hour to a few weeks. All three data sources provide 15-minute history. The shorter the bar, the larger the share of return that costs take, so a 15-minute strategy has to clear the same cost tests with far less room.
- **Markets:** US ETFs and spot crypto (Alpaca paper account), FX (OANDA demo account).
- **Data:** Alpaca bars (US, from 2016), OANDA candles (FX, from 2005), Binance public archive (crypto). Pulled by scripts into fixed snapshots.
- **Strategy families:** any that bar data can test honestly. Trend, momentum, mean reversion, carry, breakout, seasonality, cross-market signals, and combinations.
- **Out of scope:** real money; anything faster than 15-minute bars or dependent on speed (arbitrage across venues, market making); single stocks until survivorship-free data is bought; crypto derivatives until a paper venue open to Australians is confirmed; prediction markets. Adding any of these is escalation `F-VENUE-1`.

## 3. The design in one picture

```
            agents (local, fast)                     |        fixed judge
                                                     |
  idea-scout -> card -> build -> optimise on dev data --> final exam (GitHub job)
                  ^        |           |             |        | pass
                  |     reviewer   every run is      |        v
                  |   (reject only) logged first     |   paper trading (scripts)
                  |                                  |        |
                  +---- maintain: diagnose, act <----+-- health watch (script)
                                                     |        |
                                                     |   winner packet -> operator
```

Left of the line, agents work in seconds on development data. Right of the line, nothing is written by a model: the exam, the paper runner and the health watch are scripts.

## 4. Components

### 4.1 Strategy and card

A strategy is one folder, `strategies/<id>/`:

- `card.md`: the idea, the reason someone pays for this edge, the markets, the parameter ranges, and what result would kill it. Written before the first test.
- `strategy.py`: one function. It receives price history up to the current bar and the parameters, and returns target positions. It has no file, network or clock access.
- `params.yaml`: the chosen parameters, inside the card's ranges.

The engine acts on a target at the next bar. A strategy cannot trade on a price it has just seen, which blocks the commonest look-ahead by construction.

### 4.2 Engine

`engine/` is a small Python package in the repo. Agents can run it and read it. They cannot edit it.

- **Backtester.** Positions lagged one bar, costs charged on every change in position, returns recorded per bar. A few hundred readable lines, cross-checked against vectorbt on a reference case.
- **Cost model.** Fees, half the spread, slippage that grows with order size, and funding where it applies. One table per market, sourced from venue fee pages. Every result is also produced at raised costs.
- **Leak test.** Changes data after a date and checks that decisions before that date do not move. Run on every candidate.
- **Statistics.** Deflated Sharpe ratio using the effective number of trials, probability of backtest overfitting across a parameter sweep, sub-period stability, parameter-neighbourhood stability, comparison with buy-and-hold. Implemented from the primary papers and cross-checked against skfolio and purgedcv.
- **Similarity check.** Compares a new strategy with every earlier one by rules and by return correlation, so a copy is not counted as a new idea.
- **Trial log.** `trials/<dataset>.jsonl`, append-only. The engine writes the line before it prints a result. The run wrapper commits it.

### 4.3 The gate

The engine decides pass or fail. Its rules sit in `engine/gate.yaml`, which only the operator changes.

A strategy passes when, on net-of-cost returns:

1. The deflated Sharpe ratio shows the result is unlikely to be the best of that many lucky trials. The trial count is every logged trial on the same dataset, grouped by how correlated their returns are.
2. It stays positive at raised costs.
3. It beats buy-and-hold of the same markets after costs.
4. The leak test passes.

These four are coded. The remaining evidence is reported for judgement, not coded as thresholds: overfitting probability of the sweep, stability across sub-periods and neighbouring parameters, and trade count. The reviewer weighs it and can reject, with reasons written to the item file.

### 4.4 Development data and the final exam

- Development data stops at a cutoff date. It is the only market data that exists where agents work.
- The held-back window, from the cutoff to today, exists only inside one GitHub Actions job.
- An agent requests an exam by opening a pull request with the strategy folder. The job takes the engine and its own workflow from `main` and only the strategy folder from the branch. It checks that the strategy's local trials are in the log, re-runs the gate on development data, then runs the strategy once on the held-back window.
- The job writes `exam/<id>.json`: pass or fail per check, nothing else. Agents never see held-back returns.
- A failed strategy's family is closed. It cannot be resubmitted with tweaks.
- The cutoff rolls forward on a schedule, releasing old exam data to development and adding new. Time supplies fresh exam data, and the paper period is the last unseen test.

### 4.5 Paper trading

Two scripts on a schedule matching each strategy's bar size. No model is involved. GitHub Actions schedules can start several minutes late, which is acceptable for hourly and daily bars. 15-minute strategies need a punctual scheduler, chosen in build step 6.

- **Runner.** Loads each deployed strategy at the exact code version that passed the exam, computes targets, nets them across strategies, and places paper orders. Paper endpoints are hard-coded.
- **Journal.** Pulls fills, re-prices each one with the engine's cost model, and attributes results to each strategy. Broker paper profit is treated as an upper bound and never reported as the result.

A strategy that passes the exam goes to paper automatically. Paper costs nothing, so no approval is needed.

### 4.6 Maintenance: the self-improving loop

Each paper strategy has a predicted range: the spread of outcomes its backtest implies for the time it has been running.

1. **Watch** (script, every day). Compares each strategy's re-priced paper results, costs and trade frequency with its predicted range. Writes `health/<id>.json`.
2. **Diagnose** (agent, when a strategy leaves its range). Reads the health file, fills and recent market data. Names one cause: implementation fault, higher costs, a regime the strategy was never tested in, or a fading edge. Proposes one action.
3. **Act.**
   - *Fix* an implementation fault and restart the paper clock.
   - *Re-tune* inside the card's declared ranges using recent data. The new version is a counted trial, takes the final exam, and runs in shadow beside the old version. The one that does better on paper stays.
   - *Reduce weight* or *pause*. A paused strategy keeps running in shadow so evidence keeps building.
   - *Retire.* Also the outcome for a strategy that keeps needing re-tunes.

A drop inside the predicted range triggers nothing. Bad stretches are normal, and reacting to them is how a healthy strategy gets tuned into an overfit one.

### 4.7 Combined book

All paper-confirmed strategies are combined at equal risk. The book's record is tracked like a strategy. Evidence builds faster across many weakly related strategies than on any one, so the book is the factory's main long-run measure.

## 5. Stages

One item per strategy, in the format of `factories/_shared/CONVENTIONS.md`.

| Stage | What happens | Done by | Moves to |
|---|---|---|---|
| `proposed` | Card written, similarity check passed | `idea-scout` agent, engine check | `built`, `killed` |
| `built` | Strategy code written, unit tests and leak test passed, reviewer confirms code matches card | `build` skill, `reviewer` agent | `optimised`, `killed` |
| `optimised` | Parameters searched inside declared ranges on development data, stable region chosen, gate passed locally | `optimise` skill, engine | `exam`, `killed` |
| `exam` | Final exam in CI | GitHub Actions | `paper`, `killed` |
| `paper` | Runs on paper, watched daily | scripts, `maintain` skill | `confirmed`, `paused`, `killed` |
| `confirmed` | Ran correctly and stayed in range for long enough, and adds to the combined book | `maintain` skill, engine check | `awaiting_human`, `paused`, `killed` |
| `awaiting_human` | Winner packet sent (`F-CAP-1`) | `winner-packet` skill | operator's decision |
| `paused` | Runs in shadow | scripts | `paper`, `killed` |

How long a strategy stays on paper is judged per strategy from how often it trades and how wide its predicted range is. The reasoning goes in the item file. As a guide, hourly strategies need weeks to a few months and daily ones several months.

## 6. What the operator sees

- **Winner packet (`F-CAP-1`).** The card, the trial count and adjusted odds, exam result, paper record re-priced with real costs, what paper did and did not show, contribution to the combined book, and every maintenance action taken. Live trading is not built. Funding an account is the operator's own step.
- **Approvals.** Creating the paper accounts and storing their keys (`F-ACC-1`), any paid data (`F-ACC-2`), any new market (`F-VENUE-1`), any engine or gate change (`F-ENG-1`).
- **A short weekly summary.** Funnel counts, trials used per dataset, strategies on paper, the combined book, spend.

Every number in a report is read from a file the engine or a script wrote.

## 7. Agents, skills and schedules

- **Sub-agents:** `idea-scout` (web access, no market data, one output file) and `reviewer` (reads card, code and engine output; can only reject).
- **Skills:** `ideate`, `build`, `optimise`, `maintain`, `winner-packet`, `weekly-review`.
- **Scripts:** data snapshots, engine, exam job, paper runner, journal, health watch.
- **Schedules:** scripts on GitHub Actions. Skills as Claude Code scheduled tasks, each run by hand three times before it is scheduled.

## 8. Hard guardrails

Only these are enforced in code. Everything else is guidance that a run weighs and explains.

| Guardrail | Enforced by |
|---|---|
| Paper only | No live keys exist. Paper endpoints are hard-coded in the runner |
| Agents cannot edit the engine, gate rules, trial log or exam results | Path deny rules, and the exam job uses `main`'s copy |
| Held-back data is never where agents work | It is fetched only inside the exam job |
| Every trial is counted | The engine logs before it prints, and the exam fails if trials are missing |
| No model in the order path | Runner and journal are scripts |
| Spend caps and kill switch | `budget.yaml`, run wrapper, `STOP` file |

Known gap: an agent with web access could look up recent prices itself. Deny rules cover the data vendors, and the paper period remains a test nothing can have seen.

## 9. Trusting the judge

Before any strategy is mined, the engine must:

1. Reproduce a known published result (time-series momentum across markets) to within reason.
2. Find an edge planted in synthetic data.
3. Reject pure noise, at the rate the gate claims, when fed hundreds of random strategies.

These are the factory's essential tests. They are re-run after every engine change, and earlier survivors are re-examined.

## 10. Standards the engine follows

Each part of the judge is taken from published research or established practice, not invented here. Sources and links are in [the research report](design/DISCOVERY_REPORT.md).

| Part | Standard | Source |
|---|---|---|
| Is the result luck, given the number of trials | Deflated Sharpe ratio | Bailey and López de Prado (2014) |
| Counting trials that are really the same idea | Effective number of trials by clustering return correlations | López de Prado (2019) |
| Is the optimisation overfit | Probability of backtest overfitting by combinatorial cross-validation | Bailey, Borwein, López de Prado and Zhu |
| How much testing a dataset can bear | Minimum backtest length | Bailey et al. |
| Evidence bar for a new idea | t-statistic above 3 as a reference point | Harvey, Liu and Zhu (2016) |
| Held-back data, looked at once | Single-use holdout | Masters; López de Prado's embargo stage |
| Costs | Fees, half spread, square-root impact, results at raised costs, costs no more than a third of gross return | Venue fee pages; Carver's speed limit; QuantConnect's volume cap |
| Optimisation | Few parameters, ranges fixed in advance, stable regions over single best points, fit across markets | Carver |
| Idea quality | A stated reason someone pays for the edge | Carver; AQR factor research |
| Novelty | Reject returns too correlated with existing strategies | WorldQuant BRAIN |
| Maintenance | Compare live results with the predicted distribution; refit on past data only; do not tune after bad out-of-sample results | Carver; López de Prado's lifecycle |
| Combining strategies | Equal risk weights across weakly related strategies | Carver; AQR |
| Separation of roles | The author of an idea never approves it; every trial logged | López de Prado; Man Group |

Metrics a strategy is tuned on: net-of-cost Sharpe ratio as the main measure, with drawdown, turnover and cost share reported beside it so that a high Sharpe from taking almost no risk is visible.

Where research gives no agreed number, such as a pass mark for overfitting probability, the spec does not invent one. The evidence is reported and judged.

## 11. Build order

1. Rewrite `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, skills and agents to match this spec.
2. Engine, cost model, statistics and the three judge tests.
3. Data snapshot scripts and the development cutoff.
4. One strategy taken by hand from card to local gate.
5. The exam job.
6. Paper runner and journal (needs `F-ACC-1`).
7. Health watch and the `maintain` skill.
8. Idea scout, then schedules.

## 12. Open items

- Whether the operator wants a longer paper period before a winner packet than the engine's own judgement.
- Cost tables need a fresh read of each venue's fee page at build time.
- Alpaca's free US data covers one exchange with about 4 to 5% of volume, so volume-based hourly signals on ETFs are unreliable until better data is bought.
- A paper venue for crypto funding carry that is open to Australians has not been confirmed.
