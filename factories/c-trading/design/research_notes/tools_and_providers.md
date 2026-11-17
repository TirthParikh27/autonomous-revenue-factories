# Tools and Providers for a Strategy Mining Factory (solo Python dev, Australia, verified 17 Nov 2026)

Method note: release dates and licences below were pulled directly from the PyPI JSON API (`https://pypi.org/pypi/<pkg>/json`) on 17 Nov 2026 unless another source is cited. The GitHub API was not reachable from this session, so commit dates come from third-party snapshots (cited, with their check date). Provider facts come from official docs or help centres where possible.

## 1. Backtesting engines: licence, maintenance, speed, sweep suitability, costs, multi-asset, walk-forward, LLM-friendliness, path to paper/live

### Takeaway
For thousands of backtests, use a vectorised engine (vectorbt open source, or VectorBT PRO if you will pay US$240/yr) for the mining stage. Then re-run the shortlisted winners in an event-driven engine that can trade paper/live with the same code: NautilusTrader (multi-venue, LGPL), Freqtrade (crypto, GPL, free dry-run), or LEAN (Apache-2.0; the official CLI needs a paid QC organisation). Backtrader is effectively unmaintained (last release April 2023). Jesse locks paper and live trading behind a paid plugin.

### Comparison table (status verified 17 Nov 2026)

| Engine | Licence | Latest release (PyPI) | Style / speed | Mass parameter sweeps | Costs model | Multi-asset / portfolio | Walk-forward | Same code to paper/live |
|---|---|---|---|---|---|---|---|---|
| vectorbt (OSS) | Apache 2.0 + Commons Clause (source-available, not OSI) | 1.2.1, 11 Nov 2026 | Vectorised NumPy/Numba; optional Rust backend since 1.0 | Best fit: param grids evaluated as array columns | fees, slippage (limit orders and leverage only in PRO) | Yes, columns plus optional cash sharing | Manual (split helpers) | No live trading |
| VectorBT PRO | Proprietary membership | Private repo (2026.9.5 referenced Sep 2026) | Vectorised plus Rust; stateful simulation | Strongest of the group | Richer order types | Yes | Yes (splitters/validation) | No broker routing or reconciliation |
| backtesting.py | AGPL-3.0 | 0.6.6, 22 Jul 2026 | Event-style loop per bar, one instrument per run | `Backtest.optimize` grid/SAMBO; fine for hundreds, slow for 10k+ | commission (rate, fixed + rate, or function), spread | One instrument per Backtest; MultiBacktest runs several separately | No built-in | No live |
| backtrader | GPL-3.0+ | 1.9.78.123, 19 Apr 2023 (no release since) | Pure-Python event-driven, slow | optstrategy (multiprocess) | commission schemes, slippage | Multi-feed | No | Legacy IB/Oanda integrations, unmaintained |
| zipline-reloaded | Apache-2.0 | 3.2.1, 25 Oct 2026 | Pure-Python event-driven, Pipeline API | None built in | commission and slippage models | US-equity universes | No | No maintained live path |
| bt | MIT | 1.4.1, 10 Oct 2026 | Portfolio tree-of-algos, rebalancing | Manual loops | basic commissions | Portfolio allocation focus | No | No |
| NautilusTrader | LGPL-3.0+ | 1.231.0, 2 Aug 2026; 2.0.0rc9, 10 Nov 2026 | Rust core, event-driven, ns resolution, L1/L2/L3 | None built in (run via Optuna/your own pool) | fill, latency and fee models; order-book replay | Yes, multi-venue | No built-in | Yes: same strategy through venue adapters (IB, Binance, Bybit, OKX, etc.) |
| QuantConnect LEAN | Apache-2.0 engine; CLI 1.0.233, 27 Oct 2026 | Continuous | C# core with Python API, event-driven, Docker | Cloud optimiser (credit-billed); local via CLI | Per-security fee, fill, slippage, margin, settlement models | Yes, all asset classes | Via code | Yes, 20+ brokerages plus QC paper |
| Freqtrade | GPL-3.0 | 2026.10, 30 Oct 2026 (monthly) | Pandas candle backtester | Hyperopt (Optuna NSGAIII sampler) | Fees; no slippage, limit orders fill if price is within the candle range | Crypto pairs | No (hyperopt only) | Yes: free dry-run plus live on ~12 tested exchanges via CCXT |
| Jesse | MIT core; paid live plugin | 3.6.1, 10 Nov 2026 | Candle backtester | Optuna plus Ray optimiser, train/test split | fees | Crypto, plus imported traditional candles | Train/test only | Paper and live need paid plan (US$899–1,599 lifetime as at Sep 2026); free plan is testnet-only |
| hftbacktest | MIT | 2.4.4, 10 Dec 2025 | Numba/Rust tick and L2/L3 replay; queue and latency models | Slow at full fidelity; "accelerated" mode ~260x faster | maker/taker fees, latency, queue position | Multi-asset, multi-exchange | No | Rust-only live bot for Binance Futures and Bybit |
| PyBroker (other) | Apache 2.0 + Commons Clause | 2.0.3, 15 Nov 2026 | Vectorised/ML-oriented | Yes | fees, slippage | Multi-symbol | Yes (retrains models) | No |
| Lumibot (other) | GPL-3.0 | 4.6.75, 17 Nov 2026 | Event-driven | Limited | basic | Multi-asset | No | Yes: Alpaca, IB, Tradier, Schwab, CCXT |

### Cited Findings
- PyPI latest versions and upload dates for vectorbt 1.2.1 (2026-11-11), backtesting 0.6.6 (2026-07-22, AGPL-3.0), backtrader 1.9.78.123 (2023-04-19, GPLv3+), zipline-reloaded 3.2.1 (2026-10-25, Apache-2.0), bt 1.4.1 (2026-10-10, MIT), nautilus_trader 1.231.0 (2026-08-02, LGPL-3.0-or-later), lean 1.0.233 (2026-10-27, Apache), freqtrade 2026.10 (2026-10-30, GPLv3), jesse 3.6.1 (2026-11-10, MIT), hftbacktest 2.4.4 (2025-12-10, MIT), lib-pybroker 2.0.3 (2026-11-15), lumibot 4.6.75 (2026-11-17, GPL-3.0). Queried 17 Nov 2026 — [PyPI vectorbt](https://pypi.org/project/vectorbt/), [PyPI backtesting](https://pypi.org/project/backtesting/), [PyPI backtrader](https://pypi.org/project/backtrader/), [PyPI zipline-reloaded](https://pypi.org/project/zipline-reloaded/), [PyPI bt](https://pypi.org/project/bt/), [PyPI nautilus_trader](https://pypi.org/project/nautilus_trader/), [PyPI lean](https://pypi.org/project/lean/), [PyPI freqtrade](https://pypi.org/project/freqtrade/), [PyPI jesse](https://pypi.org/project/jesse/), [PyPI hftbacktest](https://pypi.org/project/hftbacktest/)
- NautilusTrader 2.0.0 is in release candidates. PyPI shows rc5 (15 Sep), rc6 (5 Oct), rc7 (15 Oct), rc8 (29 Oct) and rc9 (10 Nov 2026). rc9 adds Python 3.15 support and a Kalshi adapter — [NautilusTrader releases](https://github.com/nautechsystems/nautilus_trader/releases)
- Stable 1.x is the production line. Rust-native 2.x "remains prerelease and is not recommended by its maintainers for live capital yet" — [python.financial frameworks guide (19 Sep 2026)](https://python.financial/guides/python-backtesting-frameworks/)
- NautilusTrader: about 30 breaking changes in 1.231.0 and about 50 in the 2.0 RC. No built-in parameter search. Order-book replay plus latency and fill models. Venue adapters for live trading — [Manifold-BT comparison (19 Sep 2026)](https://www.manifoldbt.com/guide/best-python-backtesting-libraries)
- vectorbt OSS is Apache 2.0 with Commons Clause (source-available). 1.0.0 shipped Apr 2026 and 1.2.0 on 19 Oct 2026, with an optional Rust backend since 1.0. Limit orders, leverage and parallelisation are in PRO only — [Manifold-BT](https://www.manifoldbt.com/guide/best-python-backtesting-libraries); [aiquantnav](https://aiquantnav.com/en/compare/backtrader-alternatives)
- VectorBT PRO pricing: from US$25/month, US$240 for 12 months (discounted from US$300), or US$500 lifetime. Includes the private GitHub repo, docs and Discord. The page says the price will rise with milestones — [vectorbt.pro membership](https://vectorbt.pro/become-a-member)
- VectorBT PRO has no bundled broker routing or reconciliation. It is proprietary, with individual and organisation terms — [python.financial VBT PRO vs LEAN](https://python.financial/comparisons/vectorbt-pro-vs-quantconnect-lean)
- backtrader: last master commit and PyPI release both 19 Apr 2023. Repo not archived (checked 25 Oct and 4 Nov 2026) — [fincodelabs](https://fincodelabs.com/en/blog/backtesting-python-libraries); [assetwhisper](https://assetwhisper.com/python-libraries-algorithmic-trading)
- backtesting.py: one instrument per Backtest, with MultiBacktest running several separately. Commission can be a rate, fixed plus rate, or a function, plus spread — [fincodelabs](https://fincodelabs.com/en/blog/backtesting-python-libraries)
- GitHub stars and last commits checked 4 Nov 2026: Freqtrade 56,421 (3 Nov), NautilusTrader 31,218 (4 Nov), Backtrader 23,663 (19 Apr 2023), VectorBT 9,676 (3 Nov), backtesting.py 9,192 (5 Aug 2026), zipline-reloaded 1,997 (2 Nov) — [assetwhisper](https://assetwhisper.com/python-libraries-algorithmic-trading)
- LEAN is Apache-2.0 (22,442 stars, last change 6 Nov 2026 as at 8 Nov 2026) — [kagels-trading QC review](https://kagels-trading.com/blog/quantconnect-review/)
- The official LEAN CLI ("To use the CLI, you must be a member in an organization on a paid tier") runs local backtests in Docker with your own data — [QC LEAN CLI docs](https://www.quantconnect.com/docs/v2/lean-cli/key-concepts/getting-started); [lean backtest](https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-backtest)
- Building LEAN from source is a separate, free self-hosted route — [python.financial](https://python.financial/comparisons/vectorbt-pro-vs-quantconnect-lean)
- LEAN provides fee, fill, slippage, settlement and margin models per security. The cloud optimiser handles up to three parameters, billed in credits — [Manifold-BT](https://www.manifoldbt.com/guide/best-python-backtesting-libraries)
- Freqtrade Hyperopt uses Optuna, starting with random combinations and then the NSGAIIISampler. It "will burn all your CPU cores" — [Freqtrade hyperopt docs](https://docs.freqtrade.io/en/stable/hyperopt)
- Freqtrade backtests assume no slippage, and limit orders fill whenever price is within the candle's high/low. There is no walk-forward, and backtest vs dry-run signal mismatches are a recurring issue (#12894, Mar 2026) — [Manifold-BT](https://www.manifoldbt.com/guide/best-python-backtesting-libraries)
- Jesse: MIT research core, with an Optuna plus Ray optimiser using train/test candles. Live and paper trading need a licensed plugin, listed at US$899/$999/$1,599 lifetime on 19 Sep 2026. The free plan is one route on testnet only, with no paper trading — [python.financial Freqtrade vs Jesse](https://python.financial/comparisons/freqtrade-vs-jesse/)
- hftbacktest models feed and order latency, queue position, and L2/L3 book reconstruction. Its live bot covers Binance Futures and Bybit and is Rust-only — [hftbacktest GitHub](https://github.com/nkaz001/hftbacktest)
- hftbacktest "accelerated" mode drops queue and response-latency modelling: 416 ms vs 1 min 49 s for a full backtest (~260x) — [hftbacktest Accelerated Backtesting](https://hftbacktest.readthedocs.io/en/latest/tutorials/Accelerated%20Backtesting.html)
- Lumibot runs the same code for backtest, paper and live across Alpaca, IB, Tradier, Schwab, Tradovate and CCXT. There are documented backtest-vs-live parity gotchas — [itjob review (Jun 2026)](https://itjob.work/blog/python-backtesting-tools-review)
- PyBroker is Apache 2.0 plus Commons Clause. Its walk-forward retrains models but does not optimise fixed rules — [python.financial](https://python.financial/guides/python-backtesting-frameworks/)

### Inferences
- Recommended two-tier architecture. Tier 1 (mining): vectorbt OSS or PRO, running thousands of parameter combos per strategy family as array columns. Tier 2 (confirmation): re-implement survivors in an event-driven engine that matches the paper venue. That means NautilusTrader for crypto/IB, Freqtrade for crypto-only, or LEAN for multi-asset via QC paper. Treat the same-code path to paper as a Tier 2 property only.
- Licence fit for a solo, internal-use project: Commons Clause (vectorbt, PyBroker) and AGPL/GPL (backtesting.py, Freqtrade) are all fine for private use. They only matter if the factory is later sold or offered as a hosted service.
- LLM-agent ease (judgement, not sourced). The easiest targets are backtesting.py (a small `Strategy` class with `init`/`next`) and Freqtrade (a single `IStrategy` file with populate_* methods; heavily documented, so LLMs know it well). vectorbt's signal-array API is compact but LLMs often misuse its broadcasting. NautilusTrader's API is the hardest: large surface, frequent breaking changes, and a v1-to-v2 transition. Pin versions.
- NautilusTrader has no built-in optimiser and churns between releases. Pin to 1.231.x for now and wrap with Optuna. Evaluate 2.0 once it goes GA.

### Gaps
- No independent, current benchmark of throughput (backtests/second) across engines was found. Vendor claims exist (Manifold-BT) but were not used.
- Exact walk-forward helpers in vectorbt OSS 1.2.x vs PRO were not verified from the docs.
- Jesse's November 2026 pricing was not re-verified; the latest figure is from 19 Sep 2026.

## 2. Optimisation helpers and overfitting statistics (CPCV / PBO / DSR)

### Takeaway
Use Optuna for search (5.1.0, released 16 Nov 2026), skfolio (BSD-3) for CombinatorialPurgedCV and walk-forward splitters, and purgedcv (MIT) for PBO/CSCV, DSR, PSR, MinTRL and an Optuna trial recorder. Avoid mlfinlab: it is paid and closed, with the repo stale since Oct 2023. scikit-optimize is effectively dormant (last release Jun 2024). pypbo is AGPL and not on PyPI.

### Cited Findings
- Optuna 5.1.0 was released 16 Nov 2026 (MIT). scikit-optimize's latest is 0.10.2, released 4 Jun 2024 — [PyPI optuna](https://pypi.org/project/optuna/); [PyPI scikit-optimize](https://pypi.org/project/scikit-optimize/)
- skfolio 1.12.17 was released 16 Nov 2026 under BSD-3-Clause — [PyPI skfolio](https://pypi.org/project/skfolio/). A Sep 2026 blog cites "v1.3.0", which conflicts with PyPI; PyPI is authoritative — [quantbrainai](https://quantbrainai.net/blog/purged-kfold-cross-validation-python)
- skfolio `CombinatorialPurgedCV(n_folds=10, n_test_folds=8, purged_size=0, embargo_size=0)` supports purging and embargo and recombines multiple test paths. It also offers WalkForward, MultipleRandomizedCV and `optimal_folds_number` — [skfolio API](https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html); [skfolio user guide](https://skfolio.org/user_guide/model_selection.html)
- skfolio is portfolio-optimisation-centric: CV runs over sklearn-style estimators on return matrices — [skfolio](https://skfolio.org/)
- mlfinlab costs £100 (+VAT) per month per user for a commercial licence — [Hudson & Thames](https://hudsonthames.org/mlfinlab). It "was relicensed as a paid closed-source product", its repo has had no push since 2023-10-02, and it is not on PyPI (confirmed by a PyPI query on 17 Nov 2026) — [quantbrainai](https://quantbrainai.net/blog/purged-kfold-cross-validation-python)
- purgedcv (MIT, pip/conda) covers PurgedKFold, CombinatorialPurgedCV, CombinatoriallySymmetricCV, reconstruct_paths, PSR, DSR, `probability_of_backtest_overfitting`, MinTRL, MinBTL, effective_n_trials and `optuna_integration.TrialSharpeRecorder` — [purgedcv GitHub](https://github.com/eslazarev/purged-cross-validation). It was at v0.1.6 with 35 stars and a last push of 4 Sep 2026 — [quantbrainai](https://quantbrainai.net/blog/purged-kfold-cross-validation-python)
- pypbo is AGPL-3.0, 68 commits, and implements PBO, PSR, MinTRL, MinBTL and DSR. It is not published on PyPI (confirmed 17 Nov 2026) — [pypbo GitHub](https://github.com/esvhd/pypbo)
- oos-lab (MIT, numpy plus scipy only) provides PSR, DSR, PBO/CSCV, WalkForward, CombinatorialPurgedKFold and the Harvey-Liu haircut — [oos-lab GitHub](https://github.com/OutOfSampleLab/oos-lab)
- Built-in optimisers: Freqtrade Hyperopt (Optuna), Jesse (Optuna plus Ray), the LEAN cloud optimiser (credits), and backtesting.py `optimize` — see section 1 sources

### Inferences
- The factory should log every trial's returns series. DSR and PBO need the number of trials and the cross-trial Sharpe variance, and purgedcv's TrialSharpeRecorder is designed exactly for Optuna.
- purgedcv and oos-lab are young, low-star projects. Vendor them or pin versions, and cross-check against a small reference implementation (the DSR formula is short; see the pypbo `dsr` code).

### Gaps
- PyPI dates for purgedcv and oos-lab were not queried directly.

## 3. Free paper-trading providers (Australian availability)

### Takeaway
Best free options for an Australian:
- **Alpaca Paper-Only:** anyone globally, email sign-up; US stocks/ETFs/options/crypto, IEX-only data.
- **OANDA demo:** OANDA Australia, v20 API; FX/CFD.
- **Binance Spot Testnet:** GitHub login.
- **OKX Demo:** OKX Australia exists, though AU derivatives are restricted.
- **IBKR Free Trial paper:** a full paper account needs a funded live account.

Three are now closed to new Australian users: Bybit (Australia added to excluded jurisdictions effective 16 Oct 2026), Tastytrade (ceased serving Australian residents, 1 Oct 2026) and Tradier (does not open accounts for Australian residents).

### Comparison table (verified 17 Nov 2026)

| Provider | Assets | API | Free? | Data / fill realism | Australian access | Limits / notes |
|---|---|---|---|---|---|---|
| Alpaca Paper | US stocks/ETFs, options, crypto | REST + WS, same spec as live; paper-api.alpaca.markets | Yes, "Paper Only Account" for anyone globally | Fills simulated from real-time quotes; paper-only users get IEX data only (~2.5% of volume) | Yes (paper). Live accounts for non-US residents are country-dependent | Free data: 200 calls/min, 30 WS symbols; $100k default, resettable; no borrow fees in paper |
| IBKR Paper | Everything IBKR trades | TWS API (paper port 7497/4002), Web API | Paper account only after the live account is funded; "Free Trial" simulated account available without funding | Sim fills from top of book; no VWAP/auction/pegged orders; market-data subs mirror live account | IBKR Australia exists (not re-verified here) | US$1M paper equity; inactivity closure; historical data is throttled |
| OANDA demo | FX, metals, indices, commodities, bonds, crypto CFDs (v20 account) | v20 REST + streaming, api-fxpractice.oanda.com | Yes, instant demo | Practice environment mirrors production endpoints | Yes, OANDA Australia division | History back to 2005, 5-second to monthly candles; oandapyV20 is a third-party wrapper (last release 2021) |
| Binance Spot Testnet | Spot crypto | testnet.binance.vision, /api only (no /sapi) | Yes, GitHub login | Independent order book and prices; monthly reset | Accessible (no Binance account needed) | Production-like limits and filters |
| Binance Demo Trading | Spot + USD-M futures | demo-api.binance.com, demo-fapi.binance.com | Yes, needs a Binance account | "Realistic market data is not equal to real" | Binance AU is spot-only (derivatives closed after AFSL cancellation, Apr 2023); futures demo access for AU users unverified | 3,000 USDT futures demo, faucet top-up |
| Bybit Demo | Spot + derivatives (UTA) | api-demo.bybit.com; public data is identical to mainnet | Yes, no KYC | Mainnet public prices; demo orders don't hit the book | **No: Australia added to Excluded Jurisdictions, T&Cs effective 16 Oct 2026** | Orders kept 7 days; rate limit not upgradable; no WS Trade |
| OKX Demo | Spot, margin, swaps, futures, options | Production REST plus `x-simulated-trading: 1` header; wspap.okx.com WS | Yes | Demo market data "has no connection to the live market" per OKX help | OKX Australia is AUSTRAC-registered; derivatives via AFS licensee and restricted | No sub-accounts; demo balance-adjust API added 2026 |
| Bitget Demo | Spot/futures (UTA) | Demo API key; wspap.bitget.com | Yes, **KYC required** | Real-market environment with virtual funds | Limited for AU | — |
| Hyperliquid testnet | Perps/spot (DEX) | api.hyperliquid-testnet.xyz; wallet-signed | Yes, but the faucet requires a prior **mainnet deposit** from the same address | Separate testnet book | Perps not barred by its terms for AU | 1,000 mock USDC per drip |
| Deribit testnet | Options/futures crypto | JSON-RPC, same as production | Yes | Deribit explicitly says testnet liquidity is NOT realistic; don't use it to evaluate bots | Not verified | Free synthetic coins |
| Tradier sandbox | US stocks/ETFs/options | sandbox.tradier.com, 15-min delayed, no streaming | Free with a brokerage account | Filled against delayed data | **No: Australian residents cannot open accounts** | 60 req/min sandbox |
| Tastytrade sandbox | Equities, options, futures, crypto | api.cert.tastyworks.com | Free | Simulator fills at mid; no REST market data; resets every 24h | **No: ceased AU service; new AU accounts not accepted** | — |
| QuantConnect Paper | US equities, options, futures, FX, crypto, CFDs | LEAN algorithms | Requires a paid live node (not on Free tier) | QC's own fill models on live data | Yes (cloud) | Researcher setup ~US$84/mo recommended; Free tier has no live node |

### Cited Findings
- "Anyone globally can create an Alpaca Paper Only Account!" (email sign-up). Paper-only holders get IEX market data only. Fills are simulated from real-time quotes; the default balance is $100k and resettable; same API spec as live; borrow fees are not simulated — [Alpaca paper docs](https://docs.alpaca.markets/docs/paper-trading)
- Alpaca serves 195+ countries. Non-US live accounts need a tax ID and proof of address. Canada is excluded; other countries must contact support (guide updated 11 Mar 2026) — [Alpaca non-US guide](https://alpaca.markets/learn/live-trading-account-non-us)
- Alpaca Basic (free) data: US stocks/ETFs, IEX real-time, 30 WS symbols, history since 2016, latest 15 minutes restricted for SIP, 200 historical calls/min. Algo Trader Plus is $99/mo for all US exchanges and 10,000/min — [Alpaca Market Data API (updated 6 Oct 2026)](https://docs.alpaca.markets/us/docs/about-market-data-api)
- Without a subscription, historical SIP bars can be queried as long as the end is at least 15 minutes old — [Alpaca Market Data FAQ](https://docs.alpaca.markets/docs/market-data-faq)
- IBKR: "A paper trading account will not be opened until your account has been funded". Paper starts with USD 1,000,000. Limitations include no VWAP/Auction/RFQ/Pegged orders, fills simulated from top of book, and stops always simulated. Use a Free Trial Account to explore before funding — [IBKR Guides (12 Nov 2026)](https://www.ibkrguides.com/clientportal/aboutpapertradingaccounts.htm); [IBKR FAQ free trial](https://www.interactivebrokers.com/faq?id=35803518)
- IBKR historical-data throttling: "60 requests per 10 minutes" — [marketparquet](https://marketparquet.com/guides/historical-intraday-data-providers)
- OANDA Australia offers a free demo environment and a personal access token. Its "fxTrade Practice" sandbox "exactly mirrors the production API endpoints". History goes back to 2005, from 5-second bars to monthly — [OANDA AU REST API](https://www.oanda.com/au-en/trading/platforms/rest-api/)
- Practice endpoint api-fxpractice.oanda.com; oandapyV20 is a third-party wrapper not supported by OANDA — [OANDA API user guide](https://help.oanda.com/us/en/faqs/api-user-guide.htm); [OANDA AU troubleshooting](https://help.oanda.com/au/en/faqs/rest-v20-api-troubleshooting-guide.htm)
- oandapyV20 last released 0.7.2 on 27 Aug 2021 — [PyPI oandapyV20](https://pypi.org/project/oandapyV20/)
- Binance has two separate environments. Spot Testnet (GitHub login, /api only, independent prices, monthly reset) and Demo Mode (demo-api.binance.com, keys from a normal account). USD-M testnet REST is demo-fapi.binance.com — [cotrading.io (23 Sep 2026)](https://cotrading.io/learn/testnet-environments-compared)
- Binance futures demo: 3,000 USDT, with a faucet top-up — [kevin-wu.org (Oct 2026)](https://kevin-wu.org/en/exchange-demo-trading-en)
- Binance Australia: spot only via AUSTRAC-registered Investbybit Pty Ltd. Derivatives are not offered to AU retail since ASIC cancelled the AFSL on 6 Apr 2023. The former derivatives arm was fined A$10M on 27 Mar 2026 — [OzCoinTrail (16 Oct 2026)](https://ozcointrail.com/exchanges/is-binance-legal-in-australia)
- Bybit T&Cs effective 16 Oct 2026, s11.3: "We also do not offer services or products to Users in a few excluded jurisdictions including the Australia, United States..." — [Bybit T&Cs PDF](https://www.bybit.com/common-static/compliance/legal/BYBIT/e4fc739f23ca334a136074f58a6c58ea.pdf). Conflict: the Bybit help-centre "Service Restricted Countries" page (also updated 16 Oct 2026) does not list Australia — [Bybit help](https://www.bybit.com/en/help-center/article/Service-Restricted-Countries). A third-party tracker reports Australia added on 16 Oct 2026 — [cryptorestrictions.com](https://cryptorestrictions.com/countries/australia)
- Bybit demo: api-demo.bybit.com. Public data is identical to mainnet; orders are kept for 7 days; the default rate limit is not upgradable; WS Trade is not supported — [Bybit demo docs](https://bybit-exchange.github.io/docs/v5/demo). No KYC; starting funds are 50k USDT, 50k USDC, 1 BTC and 1 ETH — [Bybit help FAQ](https://www.bybit.com/en/help-center/article/FAQ-Demo-Trading)
- OKX demo: REST needs header `x-simulated-trading: 1`; WS uses wspap.okx.com; no withdraw/deposit — [OKX API docs](https://www.okx.com/docs-v5/en?python). Demo market data "has no connection to the live market" (OKX help, updated 4 Sep 2026, via [kevin-wu.org](https://kevin-wu.org/en/exchange-demo-trading-en))
- OKX Australia is AUSTRAC-registered, and derivatives run through an AFS licensee. Retail terms via OKX Australia Financial took effect 6 Oct 2026 — [cryptorestrictions.com](https://cryptorestrictions.com/countries/australia)
- Bitget demo trading requires KYC and uses demo API keys plus wspap.bitget.com — [Bitget demo docs](https://www.bitget.com/docs/uta/demo-trading/websocket)
- Hyperliquid testnet API: api.hyperliquid-testnet.xyz. The faucet requires a mainnet deposit from the same address and gives 1,000 mock USDC — [ethyai blog (16 Nov 2026)](https://www.ethyai.app/blog/paper-trading-crypto)
- Deribit: testnet "does not accurately reflect the production environment in terms of liquidity", and clients should avoid treating it as a realistic simulation for bots — [Deribit support](https://support.deribit.com/hc/en-us/articles/28685393662365-Deribit-Testnet)
- Tradier sandbox: 15-min delayed data, paper fills against delayed data, no streaming — [Tradier docs](https://docs.tradier.com/brokerage-api/overview); [Tradier FAQ](https://docs.tradier.com/overview/faq). Tradier cannot open accounts for residents of Australia (KB read 6 Nov 2026). Sandbox limits are 60 req/min — [fincodelabs Tradier](https://fincodelabs.com/en/blog/tradier-api)
- Tastytrade "has decided to formally cease providing services to Australian resident accounts" (deadline 1 Oct 2026). "Australian residents are not currently eligible to open new accounts" — [tastytrade AU](https://tastytrade.com/en-au/)
- Tastytrade sandbox: api.cert.tastyworks.com, no REST market data (HTTP 502), resets every 24h, separate OAuth credentials — [tastytrade sandbox docs](https://developer.tastytrade.com/docs/sandbox)
- QC Paper Trading needs "an available live trading node for each live trading algorithm" and supports US equities, options, crypto, forex, CFD, futures, future options and index options — [QC paper trading docs](https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/brokerages/quantconnect-paper-trading). The pricing page shows no paper trading on the Free tier — [QC pricing](https://www.quantconnect.com/pricing). Free tier: one backtest node and one research node; the CLI and API need Quant Researcher tier or above — [QC tier features](https://www.quantconnect.com/docs/v2/cloud-platform/organizations/tier-features). Researcher setup is US$84/mo or US$888/yr (8 Nov 2026) — [kagels-trading](https://kagels-trading.com/blog/quantconnect-review/)

### Inferences
- Primary paper venues for an Australian solo dev, all free: Alpaca Paper for US equities (IEX-only data inflates the apparent fill quality on thin names), OANDA practice for FX, and Binance Spot Testnet or OKX Demo for crypto. IBKR paper is the most realistic multi-asset option but needs a funded account.
- Paper fills everywhere are optimistic: no queue, top-of-book only, no market impact. The factory should apply its own slippage haircut when comparing paper results to backtests.
- Testnets with independent books (Binance Spot Testnet, Deribit, Bybit testnet) are only for plumbing tests. Use mainnet-price demos (Bybit Demo, though now unavailable to AU; Binance Demo Mode; Alpaca; OANDA) for strategy confirmation.

### Gaps
- Bybit's own help page and its T&Cs PDF conflict on Australia. Treat Bybit as unavailable unless Bybit support confirms otherwise.
- Not verified: whether an Australian-resident Binance user can access Binance futures Demo Trading, and Deribit's Australian eligibility.
- No official rate-limit numbers were gathered for OANDA practice, the OKX demo or the Binance testnet.

## 4. Free/cheap historical data

### Takeaway
- **Crypto:** data.binance.vision is the clear free source (bulk 1s–1d klines, trades, futures). Its licence is non-commercial.
- **US equities, free:** Alpaca Basic (bars since 2016 via SIP if more than 15 min old, 200 calls/min) plus Massive Basic (grouped-daily, all US stocks, 2 years, 5 calls/min).
- **yfinance** (1.8.0, 3 Nov 2026) works for small pulls but is unofficial, rate-limited and for personal use only. It silently drops delisted tickers.
- **Survivorship-free daily data:** Norgate Platinum (US$630/yr).
- **One-off intraday archive:** FirstRate (US$499.95).
- **Futures/tick:** Databento usage-based, with a US$125 sign-up credit.

### Comparison table (prices as cited, USD)

| Source | Free tier | Paid entry | Depth | Survivorship / delisted | Licence / notes |
|---|---|---|---|---|---|
| yfinance 1.8.0 | Free, unofficial | — | Daily from 1980 for AAPL; 1-min last 30 days; hourly 730 days | Delisted tickers vanish (KVUE gone 2 days after acquisition) | Personal use only; undocumented rate limits (YFRateLimitError) |
| Alpaca Basic | Free | $99/mo Algo Trader Plus | Since 2016, minute bars | Not documented | 200 calls/min; IEX real-time only |
| Binance data.binance.vision | Free bulk zips + CHECKSUM | — | Spot klines 1s–1mo, trades, aggTrades, USD-M/COIN-M futures, mark/index/premium klines | Delisted pairs remain in archive (not verified) | Non-commercial use; timestamps in microseconds from 1 Jan 2025 |
| Stooq | Free bulk ASCII | — | Daily/hourly/5-min for US, UK, JP, HK, World (US daily zip 584 MB) | Unknown | Last update 3 Nov 2026 |
| Tiingo | Free: 500 symbols/mo, 50 req/hr, 1,000/day, 1 GB/mo | Power $30/mo | EOD; IEX intraday from Aug 2017 | Not verified | Internal use only |
| Massive (ex-Polygon) | Basic: 5 calls/min, 2 yrs, EOD, minute aggregates | Starter $29/mo (5 yrs, flat files, unlimited calls); Developer $79 (10 yrs); Advanced $199 (from 2003) | US trades/quotes back to 2003 on higher plans | Not verified | Python package renamed `massive` (2.10.0, 12 Nov 2026) |
| Databento | $125 credit, expires 6 months | Usage $/GB; Standard $199/mo | CME since 2010; Nasdaq equities since May 2018; OPRA since 2013 | n/a | No spot FX or crypto |
| FirstRate Data | Samples | Stocks Complete $499.95 one-time; updates $59.95/mo | 1-min from 2000 | Not verified | CSV per ticker |
| Norgate Data | Trial (not verified) | Silver $270/yr, Gold $360, Platinum $630, Diamond $787.50 | Platinum to 1990; Diamond to 1950 | Platinum+ include delisted plus historical index constituents | Windows .NET updater; `norgatedata` Python package; daily only |

### Cited Findings
- yfinance 1.8.0 was released 3 Nov 2026 under Apache-2.0 — [PyPI yfinance](https://pypi.org/project/yfinance/)
- yfinance test on 4 Nov 2026: 10 years of daily data for 498/500 US stocks in 17s. Rate limits are unpublished, with users reporting blocks over 24h, worse from VPNs and cloud servers. KVUE history vanished after delisting — [fruitstand.dev](https://fruitstand.dev/blog/is-yfinance-still-usable)
- yfinance intraday limits: 1-min for 30 days, 2–90-min for 60 days, hourly for 730 days. Past breakages: Jan 2023, Jul 2023, May 2025. Since 0.2.51, `download()` auto-adjusts prices — [Massive vs yfinance](https://massive.com/compare/massive-vs-yfinance) (vendor page; facts consistent with fruitstand)
- Binance spot klines: 1,000 per call; USD-M 1,500. data.binance.vision publishes daily files next day and monthly files on the first Monday. Spot timestamps are in microseconds since 1 Jan 2025; files are licensed non-commercial. 1mo folders lag — [fincodelabs Binance (6 Nov 2026)](https://fincodelabs.com/en/blog/binance-historical-data-api)
- Unauthenticated market data via data-api.binance.vision — [Binance docs](https://developers.binance.com/docs/binance-spot-api-docs/faqs/market_data_only)
- Stooq offers free bulk ASCII downloads (daily, hourly and 5-min) for world, US, UK, JP and HK. Last update shown: 3 Nov 2026 — [Stooq db/h](https://stooq.com/db/h)
- Massive Stocks Basic: $0, 5 calls/min, 2 years, EOD, minute aggregates. Starter $29/mo: unlimited calls, 5 years, 15-min delayed, flat files — [Massive pricing](https://massive.com/pricing/). The grouped-daily endpoint returns all US stocks for one date on the free plan (~500 requests for 2 years) — [stockmarketstack](https://stockmarketstack.com/compare/free-us-market-data-apis)
- Massive Python client `massive` 2.10.0 (12 Nov 2026); the old `polygon-api-client` was last released 1.16.3 on 30 Oct 2025 — [PyPI massive](https://pypi.org/project/massive/); [PyPI polygon-api-client](https://pypi.org/project/polygon-api-client/)
- Databento: $125 free credits that expire after 6 months; usage-based $/GB; Standard $199/mo — [Databento pricing](https://databento.com/pricing). Equities since 2018, no spot FX or crypto — [Massive vs Databento](https://massive.com/compare/massive-vs-databento) (competitor page)
- Tiingo Starter: $0, 500 symbols/mo, 50/hr, 1,000/day, 1 GB/mo, internal use only. Power is $30/mo — [waylandz data provider comparison (checked 30 Oct 2026)](https://waylandz.com/quant-book-en/Data-Provider-Comparison)
- Norgate tiers and survivorship (Platinum and Diamond include delisted stocks and historical index constituents); requires .NET 4.8 — [waylandz](https://waylandz.com/quant-book-en/Data-Provider-Comparison)
- FirstRate Stocks Complete: $499.95 one-time, 1-min from 2000, updates $59.95/mo — [marketparquet (8 Nov 2026)](https://marketparquet.com/guides/historical-intraday-data-providers); [marketparquet pricing](https://marketparquet.com/guides/market-data-api-pricing)

### Inferences
- For AU-relevant FX, OANDA's v20 candles (practice account, back to 2005) are the free FX history source, so no separate FX vendor is needed for the MVP.
- Survivorship bias is the biggest data risk for equity strategy mining. The free sources (yfinance, Alpaca, Massive Basic) do not reliably provide delisted constituents, so any equity cross-sectional strategy needs Norgate Platinum or equivalent before results can be trusted.
- yfinance should not be in the automated pipeline (rate limits on cloud IPs, silent delisting). Use it for ad-hoc checks only.

### Gaps
- Not covered: ASX equity data sources (Norgate covers ASX too, but this was not verified here), and Stooq's licence terms.
- Not found: FirstRate's and Tiingo's own pages (prices are from aggregators).

## 5. MCP servers (brief)

### Takeaway
Alpaca's official MCP server (MIT, v2.4.1, 4 Nov 2026) is free, defaults to paper, and can be restricted by toolset. QuantConnect's official remote MCP (announced 3 Nov 2026, 45+ tools including backtests, optimisations and paper deploys) requires a paid QC agent node. Tradier, tastytrade, Massive and Alpha Vantage also publish MCP servers.

### Cited Findings
- Alpaca MCP Server v2 is a complete FastMCP/OpenAPI rewrite. Env vars are `ALPACA_PAPER_TRADE=true` (default) and `ALPACA_TOOLSETS` for whitelisting (e.g. read-only data) — [alpaca-mcp-server GitHub](https://github.com/alpacahq/alpaca-mcp-server). It exposes 65 tools — [Alpaca docs Trading API MCP](https://docs.alpaca.markets/us/docs/trading-api-mcp). PyPI shows alpaca-mcp-server 2.4.1 (4 Nov 2026, MIT) — [PyPI](https://pypi.org/project/alpaca-mcp-server/)
- QuantConnect remote MCP lives at quantconnect.com/api/v2/mcp, with 45+ tools: projects, compile, backtests, optimisations, paper deploy, object store. It "requires a paid agent node (A1-1, A4-8, or A16-32)" — [QC MCP page](https://www.quantconnect.com/mcp); [QC announcement (3 Nov 2026)](https://www.quantconnect.com/announcements/21675/remote-mcp-for-quantconnect)
- A PyPI package `quantconnect-mcp` 1.0.0 (10 Nov 2026, MIT) exists; its relationship to QC's official server was not verified — [PyPI](https://pypi.org/project/quantconnect-mcp/)
- Tradier offers an MCP server — [Tradier docs](https://docs.tradier.com/brokerage-api/overview). Tastytrade publishes one — [jorgai](https://jorgai.com/blog/tastytrade-api-automated-trading-2026-oauth-sandbox-order-types-rate-limits-what-third-party-apps-can-do). Massive and Alpha Vantage have official MCPs; Databento has community ones — [tradingagentstack](https://tradingagentstack.com/market-data-api-pricing/)

### Inferences
- For an agent-driven factory, the Alpaca MCP with `ALPACA_TOOLSETS` limited to data plus trading on paper keys is a low-risk way to let an LLM agent inspect paper results. Order placement itself is better done by deterministic code, not the LLM.

### Gaps
- No NautilusTrader, vectorbt or Freqtrade MCP servers were checked.
