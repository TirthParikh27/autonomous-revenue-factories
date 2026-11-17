# Trading strategy factory: Develop

Phase 3 of the double diamond. Date: 17 November 2026. Requirements (R1 to R21) and tensions are in [DEFINE.md](DEFINE.md). This document compares candidate designs and recommends one. The final architecture comes in the next phase.

## 1. The main choice: where the judge lives and what a strategy is

Four candidates. All four share the same stages (idea, code, backtest gate, paper, maintenance) and the same statistics. They differ in how they keep the judge honest and how fast the loop runs.

### A. Local lab

The engine is a Python package in the repo. Agents write each strategy as a Python function and run the engine from the command line. Engine files are protected by permission rules and a CI check. The trial log is a file the engine appends to.

- For: fastest loop (seconds per backtest), simplest to build, free-form strategies.
- Against: the held-back data sits on the same machine as the agent, so "never seen" depends on rules and not on structure. Free-form Python needs the leak tests to be good.

### B. Rule-spec factory

Strategies are not code. They are small spec files that combine building blocks from a fixed library (indicators, filters, entry and exit rules, sizing). The engine compiles and runs them.

- For: look-ahead is impossible by construction, duplicates are trivial to detect, thousands of sweeps run fast, and results are easy to compare.
- Against: agents can only express what the block library allows. New blocks need an engine change, which makes the operator a bottleneck. It suits brute-force search more than idea-led research.

### C. Sealed CI judge (the existing blueprint)

Agents never touch market data. Every backtest is a GitHub Actions job that logs the trial to a hash-chained registry before returning a result.

- For: strongest isolation. Nothing can be tested without being counted.
- Against: minutes per trial instead of seconds, which defeats the fast loop. Heavy to build and operate. Overkill for a paper-only factory.

### D. Hosted platform

Use QuantConnect or Freqtrade as engine and paper venue.

- For: mature cost models, less code to write.
- Against: QuantConnect needs paid nodes for agents and paper trading. Freqtrade is crypto only and its backtests assume no slippage. Neither exposes a trial log we control, and the pass rules would still have to be built outside.

### Comparison

| | A. Local lab | B. Rule-spec | C. Sealed CI | D. Hosted |
|---|---|---|---|---|
| Speed of the backtest loop | Fast | Fastest | Slow | Medium |
| Judge out of agents' reach (R1) | By rules | By rules | By structure | Partly |
| Held-back data truly unseen (R6) | Weak | Weak | Strong | Weak |
| Leak prevention (R5) | Tests | By construction | Tests | Tests |
| Room for idea-led strategies (R9) | High | Low | High | High |
| Build effort | Low | Medium | High | Medium |
| Running cost | Free | Free | Free | Paid |

### Recommended: A with the final exam from C

- **Fast loop locally.** Agents run the engine on development data, in seconds. Every run is logged by the engine before the result prints.
- **Final exam in CI.** The held-back data never exists where agents work. The development data stops at a cutoff date. One GitHub Actions job holds the later data, re-runs the full gate on a clean checkout of the engine, and runs the single holdout look. Only this job can mark a strategy backtest-passed.
- **Strategies are Python functions with a narrow contract.** A function receives history up to the current bar and returns target positions. The engine executes at the next bar, which blocks the commonest leak by construction. The mechanical future-change test covers the rest.
- **Parameters live in a card, not in code.** The card declares the idea, the reason, the parameter ranges and the expected behaviour before the first test. This gives duplicate checks and optimisation something structured to work on, which is the useful part of B without its limits.

This resolves tension 6 (simplicity) and most of tension 2 (leakage): the search is fast and free, and the part that must be tamper-proof is one small job.

## 2. Supporting choices

Each has a recommendation. None needs the operator's decision unless they disagree.

**Engine core.** A small in-house bar engine: positions lagged one bar, costs charged on every change in position, portfolio returns per bar. It is a few hundred lines, fully readable, and produces the per-bar return series the statistics need. It is cross-checked against vectorbt on a reference case. The alternative, building on vectorbt directly, is faster for huge sweeps but hides the execution assumptions that matter most.

**Statistics.** Deflated Sharpe with the effective number of trials (clustered by return correlation), probability of backtest overfitting across each parameter sweep, sub-period stability, parameter-neighbourhood stability, and results at raised costs. Implemented in the engine from the primary papers and cross-checked against skfolio and purgedcv. Bootstrap tests such as SPA are left out at first.

**Trial log.** One append-only file per dataset in the repo, committed by the run wrapper. CI refuses a final exam for a strategy whose local trials are missing from the log. No hash chain: git history is enough for a paper-only factory.

**Trial budget and fresh data (tension 1).** Each dataset (a market and a date range) has its own trial count, and the bar rises with it. The held-back window rolls forward on a schedule, so time itself supplies new exam data. The paper period is the last, never-seen test.

**Feedback to agents (tension 2).** On development data, agents see full results. From the final exam they see pass or fail per check and nothing else. A failed family is closed and cannot be resubmitted with tweaks.

**Paper trading.** A scheduled script computes target positions from frozen strategy code and places paper orders on Alpaca (ETFs, crypto) and OANDA (FX). A second script pulls fills and re-prices them with the factory's cost model. Hourly strategies run on an hourly schedule. Daily ones run once a day.

**Paper period (tension 4).** Judged per strategy from how often it trades and how wide its predicted range is, with the reasoning written in the item file. As a guide, hourly strategies need weeks to a few months and daily ones several months.

**Maintenance loop (tension 3).** Three scheduled steps.
1. *Watch.* A script compares each strategy's paper results with its predicted range and writes a health file. No model involved.
2. *Diagnose.* When a strategy leaves its range, an agent reads the health file, the fills and recent market data, and writes a diagnosis with one proposed action.
3. *Act.* Fix, re-tune, reduce weight, pause or retire. A re-tune re-fits inside the card's declared ranges on recent data, counts as a trial, takes the final exam again, and runs in shadow beside the old version. The better one on paper stays. Re-tunes per strategy are limited by judgement, and repeated re-tuning leads to retirement.

**Combined book.** Paper-confirmed strategies are combined with equal risk weights. Its record is reported every period and is part of every winner escalation.

**Agents.** Two sub-agents, matching the project's rule: a scout that proposes ideas (web access, no data, one output file) and a reviewer that can only reject. Coding and maintenance run as skills in the main session.

**Schedules.** Paper runner and health watch on GitHub Actions. Idea, build and maintenance runs as Claude Code scheduled tasks, each run by hand three times before it is scheduled.

## 3. What changes from the existing blueprint

- Backtests move from CI to local, with only the final exam in CI.
- Hash-chained registry replaced by an append-only log in git.
- Hard numeric gates in `budget.yaml` replaced by a bar that scales with trial count, plus judgement recorded in reports. Hard limits remain only for paper-only operation, spend and the kill switch.
- Scope widens from daily US ETFs to hourly and daily bars across ETFs, crypto and FX.
- A maintenance loop and a combined book are added.
- Four agents become two.
