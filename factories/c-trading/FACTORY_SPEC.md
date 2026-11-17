# Factory C: Trading strategy factory

Status: architecture, revision 2 (17 November 2026). The engine, the final exam, the paper stage and the health watch are built and tested on crypto data, and the idea, build and optimise stages have each been run through the run wrapper (build steps 1 to 7). The judge's daily job is scheduled and does nothing until a strategy reaches `optimised` or `watch`. The agent stages are not scheduled yet.
Nothing in this factory is financial advice. It is a research harness on paper accounts.

This revision replaces the 16 November blueprint. It is the output of a double diamond design process. The reasoning is in [`design/`](design/): [research](design/DISCOVERY_REPORT.md), [requirements](design/DEFINE.md) and [design options](design/DEVELOP.md).

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
- **Markets:** crypto, US ETFs and FX. The engine has cost and margin terms for all three. Crypto data is in place. ETF and FX data need the operator's free Alpaca paper and OANDA demo keys.
- **Shorts and leverage:** allowed where the venue an Australian resident would use offers them, on that venue's terms: crypto up to 3x on Kraken spot margin, ETFs up to 2x on Alpaca, FX up to 20x on OANDA Australia. A strategy that uses either pays the margin venue's fee and borrowing interest throughout and is closed out if the account would have been liquidated.
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

Left of the line, agents work in seconds on development data. Right of the line, nothing is written by a model: the exam, the paper stage and the health watch are scripts.

## 4. Components

### 4.1 Strategy and card

A strategy is one folder, `strategies/<id>/`:

- `card.md`: the idea, the reason someone pays for this edge, the markets, the parameter ranges, and what result would kill it. Written before the first test.
- `strategy.py`: one function, `weights(bars, params)`. It returns the target weight of every symbol at every bar, decided with data up to and including that bar. It may import only numpy, pandas and the shared indicator library. A lint step refuses the imports, names and numpy or pandas calls that reach files, the network, the clock or randomness. A lint is not a sandbox, so the reviewer agent also reads the code, and the judge's job runs it with read-only access to the repository. A second job, which never runs strategy code, commits the result files.
- `params.yaml`: the dataset, the declared parameter ranges, the chosen parameters, and optionally the strategy's own no-trade band.

The engine trades a target at the next bar's open, so a strategy cannot trade on a price it has just seen. The function sees the whole history at once for speed, so the leak test (4.2) proves it only used the past.

### 4.2 Engine

`engine/` is a small Python package in the repo. Agents can run it and read it. They cannot edit it. It uses established libraries where they met the requirements in a trial ([results](design/library-trial/RESULTS.md)) and its own code where none did.

| Part | Built on | Notes |
|---|---|---|
| Backtester | Own (numba) | Next-bar fills, fees, slippage, borrowing interest, liquidation, and a rebalance band so drift does not pay costs. Open-source vectorbt has no leverage or borrowing cost, so it was replaced. In a one-off comparison on 17 November 2026 the two agreed to 0.06% over five years on an hourly strategy (not kept as a test, since vectorbt is no longer a dependency). Checked against a hand-written reference in tests |
| Indicators | TA-Lib | `lib/indicators.py`. Protected like the engine. A strategy that needs something else writes it inside its own file, where its code hash covers it |
| Parameter search | Optuna | Searches only inside the card's declared ranges. Every run is a counted trial |
| Cost model | Own | One table per market in `engine/config.yaml`, sourced from venue fee pages. Every result is also produced at raised costs |
| Leak test | Own | Removes the future and checks that past decisions do not change. Run on every candidate |
| Statistics | Own, from the primary papers | Deflated Sharpe ratio, overfitting probability, trial clustering. Checked against purgedcv in tests |
| Trial log | Own | `state/trials/<dataset>.jsonl` plus each trial's daily returns. Written before a result is returned. An identical re-run is not counted twice |

Commands: `python -m engine check|trial|sweep|gate <strategy>`, and `python -m engine.validate` for the judge's own tests.

### 4.3 The gate

The engine decides pass or fail. Its rules sit in `engine/gate.yaml`, which only the operator changes.

A strategy passes when all four hold:

1. **Leak test.** Past decisions do not change when later data is removed.
2. **Deflated Sharpe ratio.** The result is unlikely to be luck, given every trial logged on the same dataset. Two adjustments make this honest:
   - It is measured on returns after removing market exposure. A long-only strategy in a rising market earns a good Sharpe just by being invested, and that is not skill.
   - Trials whose returns move together count as one idea, and the idea is judged on the average of its variants. Picking the luckiest of forty near-identical parameter sets gains nothing.
3. **Costs.** The market-adjusted return stays positive with fees and slippage doubled.
4. **Benchmark.** Net Sharpe beats buy-and-hold of the same markets.

The remaining evidence is reported for judgement, not coded as thresholds: overfitting probability of the sweep, spread of results across the sweep, stability across sub-periods, drawdown, turnover and cost share. The reviewer weighs it and can reject, with reasons written to the item file.

A strategy that fails only the deflated Sharpe ratio is a near miss. It is not thrown away on that one number and it is not tweaked and re-tested, which is how false winners are made. The `optimise` run reads the whole result and decides whether to watch it on new prices, also try the idea in another market, or drop it. A watched strategy is promoted only by passing this same gate once more data has come in.

What the gate can and cannot see is measured in section 9. In short, on five years of data it finds strong edges and cannot tell a modest real edge from luck.

### 4.4 Development data and the final exam

- Development data stops at a cutoff date. It is the only market data that exists where agents work.
- The held-back window, from the cutoff to today, exists only inside one GitHub Actions job.
- The judge's job (`.github/workflows/c-trading-daily.yml`) runs daily and picks up every item at `optimised`. It takes the engine and its own workflow from `main`, and from the `factory-state` branch the strategy's `strategy.py` and `params.yaml` plus the run state it judges against: items, the trial log and gate files, all of which agents are denied from editing.
- It checks that the submitted code and parameters are the ones whose trials are in the log, re-runs the gate on development data, and only then runs the strategy once across the held-back window. Three things must hold there: the leak test passes, the market-adjusted return after costs is positive, and the result is not below the 5th percentile of what the development result predicts for a window that short.
- The job writes `exam/<id>.json`: pass or fail per check, nothing else, and moves the item to `paper` or `killed`. Agents never see held-back returns. A strategy takes the exam once.
- A failed strategy's family is closed. A later strategy whose development returns move with a failed one is refused before any look.
- The cutoff rolls forward on a schedule, releasing old exam data to development and adding new. Time supplies fresh exam data, and the paper period is the last unseen test.

### 4.5 Paper stage: a forward test

The operator chose a forward test by script over broker paper accounts (17 November 2026). Broker accounts can be added later for order plumbing, and are needed anyway for ETF and FX data.

- **What it is.** Each day the judge's GitHub job (`.github/workflows/c-trading-daily.yml`) downloads yesterday's bars and runs every strategy that passed the exam, at the exact code and parameters that passed (`engine/paper.py`). Only the days after its exam count. Those prices did not exist when the strategy was built, so nothing could have been fitted to them.
- **Fills and costs** are the engine's own, the same as in the backtest. The paper record and the backtest are therefore directly comparable, and no model is involved.
- **Output.** `paper/<id>.json`: the daily record of the strategy, the benchmark and the market-adjusted result.
- **What it does not test.** Real order handling and measured slippage. The cost model stays an assumption until a broker paper account is added.

A strategy that passes the exam starts its paper record automatically. It costs nothing, so no approval is needed.

### 4.6 Maintenance: the self-improving loop

Each paper strategy has a predicted range: the spread of outcomes its backtest implies for the time it has been running.

1. **Watch** (script, every day, in the same job). Compares each strategy's market-adjusted paper result with the range its development result predicts for a record that long. Writes `health/<id>.json` with `in_range`, `below_range`, `above_range` or `too_early` (under 30 days).
2. **Diagnose** (agent, when a strategy leaves its range). Reads the health file, fills and recent market data. Names one cause: implementation fault, higher costs, a regime the strategy was never tested in, or a fading edge. Proposes one action.
3. **Act.**
   - *Fix* an implementation fault. The corrected strategy is a new item that goes through build, optimise and the exam again.
   - *Re-tune* inside the card's declared ranges, once the development cutoff has moved forward to include the period that went wrong. The new version's trials are counted, it takes the final exam, and it runs beside the old version, which is paused. The one that does better on paper stays.
   - *Reduce weight* or *pause*. A paused strategy keeps running in shadow so evidence keeps building.
   - *Retire.* Also the outcome for a strategy that keeps needing re-tunes.

A drop inside the predicted range triggers nothing. Bad stretches are normal, and reacting to them is how a healthy strategy gets tuned into an overfit one.

### 4.7 Combined book

All paper-confirmed strategies are combined at equal risk. The book's record is tracked like a strategy. Evidence builds faster across many weakly related strategies than on any one, so the book is the factory's main long-run measure.

## 5. Stages

One item per strategy, in the format of `factories/_shared/CONVENTIONS.md`.

| Stage | What happens | Done by | Moves to |
|---|---|---|---|
| `proposed` | Card written, and it is a different mechanism from every existing and killed card | `ideate` skill, `idea-scout` agent | `built`, `killed` |
| `built` | Strategy code written, lint and leak test passed, reviewer confirms code matches card | `build` skill, `reviewer` agent | `optimised`, `watch`, `killed` |
| `optimised` | Parameters searched inside declared ranges on development data, stable region chosen, gate passed locally, reviewer did not reject. Waits here for the final exam | `optimise` skill, engine, `reviewer` agent, then the exam job | `paper`, `killed` |
| `watch` | A near miss: failed only the deflated Sharpe ratio, and the `optimise` run judged the rest of the evidence good. Tracked daily on new prices at fixed parameters. Never in the combined book, never escalated | scripts, `maintain` skill | `optimised` (by passing the gate once more data is in), `killed` |
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
- **Scripts:** data snapshots, engine, exam, paper stage, health watch.
- **Schedules:** scripts on GitHub Actions. Skills as Claude Code scheduled tasks, each run by hand three times before it is scheduled.

## 8. Hard guardrails

Only these are enforced in code. Everything else is guidance that a run weighs and explains.

| Guardrail | Enforced by |
|---|---|
| Paper only | No broker account or key of any kind exists. The paper stage is a calculation |
| Agents cannot edit the engine, gate rules, trial log or exam results | Path deny rules in `.claude/settings.json`, and the exam job uses `main`'s copy |
| Strategy code cannot reach files, the network, the clock or the repository | Lint on imports, names and numpy or pandas calls; the reviewer agent reads the code; the job that runs it has read-only access. This is defence in depth, not a sandbox |
| Agents evaluate strategies only through the engine | The allow list permits `python3 -m engine` and no other program |
| Prices after the cutoff are never where agents work | They are fetched only inside the judge's GitHub job |
| Every trial is counted | The engine logs before it prints, and the exam fails if trials are missing |
| No model judges a result | The exam, the paper stage and the health watch are scripts |
| Spend caps and kill switch | `budget.yaml`, run wrapper, `STOP` file |

Known gap: an agent with web access could look up recent prices itself. Deny rules cover the data vendors, and the paper period remains a test nothing can have seen.

## 9. Trusting the judge

The judge is tested before any strategy is mined, and again after every engine change. Results are in `engine/VALIDATION.json`.

| Test | Result (17 Nov 2026, engine version 3) |
|---|---|
| Matches an independent backtest | The engine's equity curve matches a hand-written loop to within 0.1% (`tests/test_judge.py`) |
| Catches look-ahead | A strategy using the next bar, and one normalising with the full-sample mean, both fail the leak test |
| Rejects noise | 200 random strategies on real crypto data. The best had a raw Sharpe of 1.33 from market exposure alone. None of the top 25 passed |
| Finds a planted edge | In a synthetic market, a planted edge with Sharpe 2 or 3 before costs passed. Sharpe 1 and 0.5 did not |

| The exam's look at unseen data | In 40 synthetic markets each, with ten unseen months: a strategy with no edge passed 22 times, Sharpe 2 passed 36 times, Sharpe 3 passed 34 times |

The fourth row is the gate's honest limit. Five years of data cannot separate a real Sharpe-1 edge from luck, which matches the research. Modest real edges will be rejected. That is the price of rejecting noise, and it eases only with more history, more markets, or time on paper.

The exam's limit is the last row. Ten months is too short to prove anything, so the unseen look removes about half of the false winners the gate lets through and wrongly fails about one real edge in eight. It is a consistency check, kept lenient on purpose: paper trading is free, so sending a false winner to paper costs little, and killing a real edge loses it for good. It gets stronger as the held-back window grows.

Not yet done: reproducing a published result (time-series momentum across asset classes). It needs daily data for ETFs or futures, which needs the Alpaca account.

## 10. Standards the engine follows

Each part of the judge is taken from published research or established practice, not invented here. Sources and links are in [the research report](design/DISCOVERY_REPORT.md).

| Part | Standard | Source |
|---|---|---|
| Is the result luck, given the number of trials | Deflated Sharpe ratio | Bailey and López de Prado (2014) |
| Counting trials that are really the same idea | Cluster trials by return correlation, judge each cluster on its average | López de Prado (2019), with hierarchical clustering in place of his ONC algorithm |
| Skill versus market exposure | Judge returns after removing the benchmark's contribution | The 2026 audit finding that apparent LLM-strategy skill was net long exposure |
| Is the optimisation overfit | Probability of backtest overfitting by combinatorial cross-validation | Bailey, Borwein, López de Prado and Zhu |
| How much testing a dataset can bear | Minimum backtest length | Bailey et al. |
| Evidence bar for a new idea | t-statistic above 3 as a reference point | Harvey, Liu and Zhu (2016) |
| Held-back data, looked at once | Single-use holdout | Masters; López de Prado's embargo stage |
| Costs | Fees and slippage on every trade from venue fee pages, results at doubled costs. Market impact is left out while positions are small | Venue fee pages; Carver's speed limit |
| Optimisation | Few parameters, ranges fixed in advance, stable regions over single best points, fit across markets | Carver |
| Idea quality | A stated reason someone pays for the edge | Carver; AQR factor research |
| Novelty | Reject returns too correlated with existing strategies | WorldQuant BRAIN |
| Robustness to the universe | Re-run on each half of the symbols, reported as evidence | WorldQuant BRAIN's sub-universe test |
| Near misses | Not discarded on one number and not tweaked. A model chooses which to watch; only new prices or another market can promote one | Harvey and Liu (2015) on marginal results; Moskowitz, Ooi and Pedersen (2012) on ideas that hold across markets; Carver on one set of parameters for all markets |
| Maintenance | Compare live results with the predicted distribution; refit on past data only; do not tune after bad out-of-sample results | Carver; López de Prado's lifecycle |
| Combining strategies | Equal risk weights across weakly related strategies | Carver; AQR |
| Separation of roles | The author of an idea never approves it; every trial logged | López de Prado; Man Group |

Metrics a strategy is tuned on: net-of-cost Sharpe ratio as the main measure, with drawdown, turnover and cost share reported beside it so that a high Sharpe from taking almost no risk is visible.

Where research gives no agreed number, such as a pass mark for overfitting probability, the spec does not invent one. The evidence is reported and judged.

## 11. Build order

1. Done: engine, cost model, statistics and the judge's tests.
2. Done for crypto: data snapshot script and the development cutoff. ETFs and FX need account keys.
3. Done: one strategy taken by hand from card to local gate (`strategies/crypto-trend-1h/`). It failed the gate narrowly, which is a valid result.
4. Done: `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, permissions, the `ideate`, `build`, `optimise` and `weekly-review` skills, and both agents.
5. Done: the exam (`engine/exam.py`) and its GitHub job. The job first runs for real once it is on `main` and a strategy reaches `optimised`.
6. Done: the paper stage as a forward test, with the health watch (`engine/paper.py`). Checked end to end on real data by treating the last months of development data as unseen.
7. Done: the `maintain` and `winner-packet` skills, and the combined book (`paper/book.json`). Neither skill has run yet, because nothing has reached paper.
8. Not yet built: moving the development cutoff forward, which re-tuning depends on.
9. Schedules, with run state on the `factory-state` branch.

## 12. Open items

- Whether the operator wants a longer paper period before a winner packet than the engine's own judgement.
- Fees follow the venues an Australian resident can use, read on 17 November 2026: Binance Australia spot (0.10%) for long-only crypto, Kraken Pro margin (0.38% plus 0.02% to open, about 44% a year on borrowed amounts) for crypto that shorts or borrows, Alpaca for ETFs, OANDA Australia for FX. Kraken's fee assumes $10K of monthly volume or $20K of assets. Below that it is 0.60 to 0.80%. Slippage is an assumption everywhere.
- FX financing charges OANDA's 1% admin fee but not the interest-rate difference between the two currencies, so carry ideas on FX cannot be tested until swap rates are part of the data.
- Liquidation is checked against each bar's high and low for the whole account. Real venues liquidate position by position and add a fee, so a near miss in the backtest is not safe.
- The trial log is committed on `main` under `state/` for now. It moves to the `factory-state` branch when the run wrapper is wired up.
- Alpaca's free US data covers one exchange with about 4 to 5% of volume, so volume-based hourly signals on ETFs are unreliable until better data is bought.
- A paper venue for crypto funding carry that is open to Australians has not been confirmed.
- Paper records are readable by agents and cover days that a later strategy's exam will also cover. An agent could learn a little about recent market direction from them.
