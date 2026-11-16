# Factory C: Trading strategy research factory

Status: blueprint. Nothing is built or run. Date: 16 November 2026.
Nothing in this factory is financial advice. It is an engineering and research harness for the operator's own account.

## 1. Purpose and honest evidence summary

The factory generates trading hypotheses, turns them into deterministic strategy code, tests them under strict overfitting controls, and forward-tests survivors on a paper account. The LLM is a researcher and code writer. It is never the trader, and no model call sits in the order path.

What the research found (`factory_c_algo_trading.md`, 16 Nov 2026):

- No verifiable live track record of a solo developer running a "generate, backtest, iterate" LLM loop to sustained net profit was found.
- The best academic test read (arXiv 2505.07078, 2004 to 2024, survivorship-corrected) found buy-and-hold significantly outperformed the LLM agents tested, with no significant alpha. Published results shrink or reverse as the test window lengthens.
- The only real-money public evidence (Alpha Arena) has the LLM as the trader. Four of six models lost 42% to 59% in about 17 days (sources conflict on the exact loss figures). In Season 1.5 (Nov to Dec 2025) 6 of 32 accounts ended in profit and the combined pool fell about 26% in two weeks (secondary sources). Season 2 had not run as of November 2026. That is why this factory keeps the model out of the order path.
- One practitioner found 14 of 20 LLM-generated strategies were the same mean-reversion idea.
- Retail base rates are poor (97% of persistent day traders lost money in the best long-run dataset read).

The most likely honest output of this factory is "no strategy passed". That is a valid, reported result, not a failure of the run. Paper profit is never revenue.

## 2. Scope

- In scope: US-listed equities and ETFs, long only, no leverage, daily bars, orders placed once per trading day, on an Alpaca paper account.
- Default universe: a fixed list of large, liquid, broad ETFs chosen by the operator. Reason: the notes could not confirm that any data source available here includes delisted single stocks, and survivorship-free constituents are required for honest single-stock tests. A fixed ETF list chosen today still carries a mild selection bias, which every report must state.
- Out of scope: prediction markets. Verified 2026-11-16: Polymarket is on ACMA's blocked gambling list, Kalshi's Member Agreement names Australia as a Restricted Jurisdiction, and ASIC's statement of 30 Oct 2026 says prediction market contracts "have all the features of a bet". Never proposed.
- Later, separately approved extensions only (trigger `F-VENUE-1`): crypto perps, single stocks, shorting, margin, options, intraday strategies.
- Live trading: not built. Live keys do not exist in the factory's environment. See `F-CAP-1`.

## 3. Trust boundaries (the design in one table)

| Component | Who writes it | Agent access |
|---|---|---|
| `strategies/<id>/` (hypothesis card, strategy module, params, unit tests) | Builder agent, on `claude/` branches | Read and write |
| `engine/` (backtest engine, cost model, walk-forward, PBO, deflated Sharpe, gate checker, similarity check, paper runner, journal script) | Operator, reviewed by hand | Read only. Edits denied |
| Market data, development window | Data job in CI | None. The agent never sees real price data |
| Market data, holdout window | Data job in CI, separate storage | None, and CI returns pass or fail only |
| `registry/trials.jsonl` (append-only, hash-chained) | CI only | Read only |
| `results/<trial id>/metrics.json`, `gate.json` | CI only | Read only |
| `paper/deployments.yaml` on `main` | Operator merge | Proposes by pull request |
| `paper/journal/<date>.json` | Journal script in CI | Read only |
| Alpaca paper API keys | CI secrets, usable only by workflows on `main` | None |

Consequence: the agent cannot run a backtest that is not counted. Every look at real data is a CI job that appends a trial to the registry before it returns anything.

The backtest engine itself is a build-time decision for the operator. The notes did not verify the maintenance status of any open-source Python backtester, and QuantConnect's remote MCP needs a paid agent node and the free A-MICRO node cannot connect (verified 2026-11-16; prices from a secondary source only). The blueprint only fixes the contract: the engine takes a strategy module, a params file and a data snapshot id, and writes `metrics.json` and a registry line. Formulas for PBO and the deflated Sharpe ratio must be implemented from the primary papers (Bailey and Lopez de Prado), which the research did not read. Do not implement them from this document.

## 4. State machine

Item = one strategy (`state/items/<id>.json`, format in `factories/_shared/CONVENTIONS.md`). Extra fields: `mechanism`, `cluster`, `parent` (for evolved variants), `trials_used`, `paper_start`, `paper_clock_restarts`.

| Stage (item moves to) | Input | Process | Tools | Deterministic check (outside the model) | Output artifact | Run by | Scheduler and cadence |
|---|---|---|---|---|---|---|---|
| **Input:** `hypothesized` | Mechanism taxonomy, registry, `journal/LESSONS.md`, killed items | Write up to 3 hypothesis cards, each answering "who pays you and why", with rules, parameter ranges and the kill result fixed before any test | Web search for the scout only (Claude Code built-in search, or the Parallel Search or Exa connector, one click), Read, Write | `engine/similarity_check` on the card: mechanism quota and text similarity against every card in the registry. `engine/card_schema` validation | `strategies/<id>/hypothesis.md`, item file | skill `hypothesize`, agent `hypothesis-scout` | Cloud scheduled task, weekly |
| **Process:** `implemented` | One `hypothesized` card | Write a pure strategy function against the engine interface, plus unit tests on synthetic fixture data. Open a PR with a trial request | Read, Write, Edit, Bash (pytest on fixtures), `gh` | CI: unit tests, import allowlist lint (no file, network or clock access in strategy code), look-ahead audit script, card-to-code parameter match | PR on `claude/strategy-<id>`, `trials/requests/<trial id>.yaml` | skill `implement`, agent `strategy-builder`, then `overfit-verifier` | Cloud scheduled task, daily, only if the queue is non-empty |
| **QA / Backtest:** `validated` or `killed` | Trial request on a branch | CI runs the engine on development data with costs and slippage, walk-forward, then PBO and deflated Sharpe over all logged trials, then the return-correlation cluster check. If every gate passes, CI runs the single holdout evaluation | GitHub Actions only. No model | `engine/gate_check` writes `gate.json` with pass or fail per gate. Thresholds in `budget.yaml` | Registry line, `results/<trial id>/metrics.json`, `gate.json` | GitHub Actions (backtest), then skill `backtest-validate` reads the verdict and moves state | Actions on trial request. Skill: cloud task, daily |
| **Output:** `paper_trading` | `validated` item, approved `F-PAPER-1` | Open a PR adding the strategy to `paper/deployments.yaml`. After the operator merges, the deterministic runner trades it on Alpaca paper | `gh`, Read, Write. Runner: Python script in Actions with paper keys | Runner refuses any deployment whose code hash differs from the validated trial. Runner checks `STOP` before every order | Deployment PR, paper orders (placed by the runner, never by a model) | skill `paper-trade`, agent `paper-deployer`. Runner: GitHub Actions | Runner: every US trading day, before the open. Skill: cloud task, daily |
| **Telemetry:** stays `paper_trading`, or `paper_passed`, or `killed` | Alpaca paper account: orders, fills, positions | Journal script pulls fills, compares each fill to the backtest's assumed price and cost, records heartbeat. Skill reads the journal and applies paper gates | Journal: Python script in Actions. Skill: Read, Write | `engine/paper_gate`: days, trade count, fill divergence, heartbeat, drawdown | `paper/journal/<date>.json`, `state/metrics/<date>.json` | GitHub Actions (journal), skill `paper-trade` | Journal: every US trading day after the close. Skill: daily |
| **Self-improvement (strategy):** new variant item at `hypothesized` | A `validated` or `paper_trading` parent with trial budget left | Propose parameter variants inside the ranges declared on the card. Each variant is a new item and a counted trial | Read, Write, `gh` | Per-family and global trial budgets enforced by CI. Deflated Sharpe is recomputed with the larger trial count | Variant items, trial requests | skill `evolve`, agent `strategy-builder` | Cloud scheduled task, weekly |
| **Capital gate:** `awaiting_human` | `paper_passed` item | Assemble the evidence packet for `F-CAP-1`. Nothing else | Read, Write, shared `escalate` skill | `engine/packet_check`: every number in the packet matches a file CI wrote | `escalations/open/<date>-live-<id>.md` | skill `capital-gate`, agent `overfit-verifier` for the packet audit | On demand, when an item reaches `paper_passed` |
| **Self-improvement (factory):** no item move | Week of journals, registry, ledger, metrics, rejected packets | At most 3 proposals as PRs to skills or agents. Verify registry integrity. Report funnel counts | Read, Write, `gh`, Slack and Linear connectors | `engine/registry_verify` (hash chain, every request has a trial line). Wrapper checks | Weekly report, PRs, `journal/LESSONS.md` entries | skill `weekly-review` | Cloud scheduled task, weekly, Opus |

Model routing follows ARCHITECTURE.md section 4.4. Sub-hourly work does not exist in this factory. The runner and journal are plain scripts.

## 5. Allowed transitions

```
(new)            -> hypothesized
hypothesized     -> implemented | killed
implemented      -> validated | killed | awaiting_human
validated        -> awaiting_human            (F-PAPER-1, paper deployment)
awaiting_human   -> paper_trading             (F-PAPER-1 approved and deployment PR merged)
awaiting_human   -> live_small                (F-CAP-1 approved; live path is not built in this blueprint)
awaiting_human   -> <stage named in the packet's "If you say no"> | killed
paper_trading    -> paper_passed | killed | awaiting_human
paper_passed     -> awaiting_human            (F-CAP-1)
paper_passed     -> killed                    (operator rejects, or packet expires twice)
live_small       -> awaiting_human            (any auto-pause trigger; resume is manual, F-LIVE-1)
live_small       -> killed
any stage        -> awaiting_human            (SEC-1, F-INT-1, F-LEGAL-*, GEN-1)
any stage        -> killed
killed           -> (terminal)
```

A variant created by `evolve` is a new item with `parent` set. It enters at `hypothesized` and goes through every later stage on its own. There is no transition from `killed` to anything, and no transition that skips `validated` or `paper_passed`.

## 6. Gates and kill criteria

Thresholds marked [playbook] come from one practitioner playbook read in the research (AI Fin Hub, "backtest to paper to live"). It is one source's rules of thumb, not an industry standard. Thresholds marked [proposed] are this blueprint's own conservative defaults with no external source. All numbers live in `budget.yaml`.

| Stage | Kill when (any one) |
|---|---|
| `hypothesized` | No concrete answer to "who pays you and why". Mechanism quota exceeded (more than 1 card per mechanism category per batch, or the category already holds 30% of all cards) [proposed]. Text similarity to an existing card above the limit. More than 4 free parameters [proposed]. Expected trades per year too few to reach the paper trade minimum in 120 days [proposed] |
| `implemented` | Unit tests fail after 2 fix attempts. Look-ahead audit fails. Strategy code needs an import outside the allowlist. Code and card disagree on parameters |
| Backtest | Fewer than 100 trades in the development window [proposed]. Net Sharpe after costs not above buy-and-hold SPY over the same window [proposed, from the academic finding]. Out-of-sample Sharpe below 80% of in-sample Sharpe in walk-forward [playbook]. PBO 0.5 or above [playbook]. PBO 0.3 to 0.5 without walk-forward confirmation [playbook]. Deflated Sharpe ratio 0.5 or below, computed with every trial in the registry [playbook threshold]. Net result negative at 2x assumed costs [proposed]. Daily-return correlation above 0.7 with a strategy that already failed (same cluster, not a new idea) [proposed] |
| Holdout | Holdout fails (CI reports pass or fail only). One holdout evaluation per cluster, ever. A failed cluster is closed |
| `paper_trading` | Mean absolute fill divergence 10 bps or more [playbook]. Paper drawdown above the limit in `budget.yaml`. 120 days without reaching 30 trades [proposed]. Second heartbeat failure after a clock restart [proposed] |
| Family | Trial budget for the family used up with no `validated` member |

Paper gate to reach `paper_passed`: at least 30 calendar days [playbook] and at least 30 filled trades [proposed; the playbook gives no trade minimum and the research calls 30 days statistically thin], divergence under 10 bps, no heartbeat gap since the last clock restart (a gap restarts the 30 days [playbook]), paper Sharpe not below 50% of walk-forward out-of-sample Sharpe [proposed].

Cost assumptions: the research found no venue-specific slippage or fee figures. Default is 10 bps per side [proposed; the same figure one academic paper used], replaced by measured paper costs once a journal exists. Changing the cost model is an engine change (`F-ENG-1`).

**Factory-level validation budget:** USD 200 of token and API spend, 150 counted trials, 6 holdout evaluations, within 120 days of the first scheduled run. When any of the three is used up, or at day 120, the factory pauses and raises `F-VAL-1` for a keep-or-kill decision. Verified revenue will almost certainly be zero at that point because live capital defaults to zero. The decision is therefore judged on funnel evidence, and "kill the factory" is an acceptable answer.

## 7. Telemetry and the definition of a winner

| Question | Source of truth |
|---|---|
| How many ideas were tried | `registry/trials.jsonl` (CI-written, hash-chained) |
| Did a strategy pass | `results/<trial id>/gate.json` (CI-written) |
| What happened on paper | Alpaca paper account, read by the journal script |
| Did live trading make money | Broker statement of the live account, only after `F-CAP-1` |
| What did it cost | `ledger/spend.jsonl`, GitHub Actions minutes |

Reported every week: cards written, mechanisms covered, clusters found, trials used against budget, kills by gate, holdout evaluations used, strategies on paper, fill divergence, heartbeat gaps, spend. The agent's own summary is never a metric source.

A **candidate** is a strategy at `paper_passed`. A **winner** exists only after live trading: net profit after all costs on the broker statement, over at least 60 trading days, with no auto-pause trigger fired [proposed]. Until then the factory has no winners and reports zero revenue.

## 8. Self-improvement

Two loops, kept separate.

1. **Strategy evolution** (`evolve`). Parameter changes inside pre-declared ranges, at most 10 trials per family, each one logged and each one making the deflated Sharpe bar higher. New rules or new parameters are a new hypothesis, not a variant.
2. **Factory review** (`weekly-review`). Examines: mechanism distribution and cluster collapse (is the scout producing one idea many times), which gate kills most, look-ahead audit hits by cause, paper versus backtest cost gap, runs that failed or were denied, rejected packets. It may propose changes to skills, agent prompts and the mechanism taxonomy, as PRs, one change per skill per week. It may not propose looser thresholds, a larger trial budget, a different cost model or a new venue except as an escalation (`F-ENG-1`, `F-VENUE-1`).

## 9. Tools and accounts

| Tool | Use | Status |
|---|---|---|
| Claude Code cloud scheduled tasks | All model stages | Already available |
| GitHub, GitHub Actions | Backtests, runner, journal, branch protection | Connector available. Repository must be created |
| Slack, Linear connectors | Notifications, escalation issues | Already available |
| Alpaca paper account and Trading / Market Data API | Paper orders, fills, historical bars | New account needed. Verified 2026-11-16: a paper-only account is free to anyone worldwide, and free Basic data is IEX only at 200 calls a minute. Full SIP data is $99 a month. The depth of free history and available order types are unverified, confirm at build time |
| Alpaca official MCP server (`alpacahq/alpaca-mcp-server`) | Not attached to any unattended run. Optional for the operator's own inspection with `ALPACA_PAPER_TRADE=true` and read-only `ALPACA_TOOLSETS` | Official (verified 2026-11-16, MIT). Alpaca also offers hosted MCP endpoints with OAuth, which are not used either. Exact read-only toolset names: confirm at build time |
| Web search: built-in, or Parallel Search or Exa connector | Scout research | Built-in is available. Connectors are one click. Choose one at build time |
| Backtest engine (in-repo Python or a pinned open-source library) | Backtests | Operator's build-time choice. Verified 2026-11-16: NautilusTrader is free under LGPL-3.0. VectorBT PRO is $25 a month under a personal, non-commercial licence. Maintenance status of each is unverified |
| QuantConnect and its MCP | Alternative backtest platform | First-party remote MCP, needs a paid agent node (verified 2026-11-16). Researcher seat about $84 a month per a secondary source. Not in the default design |
| Paid market data (Massive, Databento, Tiingo) | Survivorship-free single-stock data | Prices verified 2026-11-16. Massive (formerly Polygon.io): free Basic with end-of-day data and 2 years of history, Starter $29 a month, official MCP. Databento: $125 of free credits, Standard $199 a month. Tiingo: free Starter, Power $30 a month, commercial use $50 a month. Whether any plan is survivorship-free is unverified. Not used by default (`F-ACC-2`) |
| Alpaca or IBKR live account | Live trading | Alpaca live accounts are still unverified for Australian residents: no country list is published and Alpaca says to email support. IBKR has an Australian entity that lists its trading APIs (verified 2026-11-16). Escalation only (`F-LEGAL-1`) |
| Community IBKR MCP servers | None | Rejected: community code between an agent and a margin account. IBKR has had an official hosted MCP since 28 Jul 2026 (verified 2026-11-16). It is not attached to any run either |

## 10. Known failure modes and the design response

| Failure mode (source in research notes) | Design response |
|---|---|
| Idea homogeneity: 14 of 20 strategies were one idea | Mechanism taxonomy with quotas, text similarity check before any test, return-correlation clustering after it. Variants of one cluster count against one family budget |
| Multiple-testing overfit | Agent has no market data, so every test is a CI job and a registry line. Fixed trial budgets. Deflated Sharpe and PBO computed over all logged trials |
| Silently dropped failed trials | Registry written only by CI, hash-chained, verified weekly and at the capital gate. A break is `F-INT-1` and stops the factory |
| Rule-gaming: tuning until the gate passes | Gate checker and thresholds are off limits to the agent. Parameter ranges are fixed on the card before the first trial. The capital gate packet shows the whole trial log, not only the survivor |
| Look-ahead in code | Engine passes the strategy only data up to t-1. Import allowlist. Deterministic look-ahead audit. The playbook's seven-item audit list was not captured in the notes and must be taken from the source at build time |
| Look-ahead through the model's training memory | Cannot be removed in backtest. The holdout is necessary but not sufficient. Forward paper trading after today's date is the only uncontaminated test, which is why it is mandatory |
| Short-window results that do not replicate (Sharpe 2.68 replicating at 0.93) | Minimum trade counts, walk-forward over the longest available history, buy-and-hold benchmark, costs at 2x |
| Fabricated or misreported numbers (plausible, no documented case found) | Every number in a report or packet must be read from a CI-written file. `packet_check` compares them |
| LLM errors in live decisions (misordered series, arithmetic errors, rule-gaming) | No model in the order path. The runner is a script |
| Paper fills differ from live fills | Fill divergence gate, measured costs fed back into the cost model by the operator, first live allocation small and capped, slippage auto-pause |
| Survivorship bias | ETF-only default universe, bias stated in every report. Single stocks need point-in-time data and `F-VENUE-1` |
| Prompt injection from research pages | Scout has no credentials and one output file. Builder never reads raw pages |
| Strategy code leaking real data through CI logs | Strategy code runs with no network, its output discarded, and only engine-written files are published. Residual risk stated in `CLAUDE.md` |
