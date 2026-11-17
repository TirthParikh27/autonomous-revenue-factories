# Realistic Backtesting: Costs, Biases, Data Quality and the Backtest-to-Live Gap

Research date: 2026-11-17. Scope: input to the design of a paper-trading-only "strategy mining factory" run by an Australian operator. Search excerpts were the main evidence; few full pages were fetched. Fee figures change often, so check them again before relying on them.

## 1. Transaction cost components and typical 2025-2026 figures per asset class

### Takeaway
For a small retail-sized trader, explicit commissions are now close to zero on US equities (Alpaca, IBKR Lite) and small on futures and FX at IBKR. Crypto exchange fees are the largest explicit cost: about 10 bps per side for spot at entry tiers, and 2 bps maker / 5-5.5 bps taker on perps. Implicit costs dominate everywhere else: the spread (about 1 bp for mega-caps, 20-100+ bps for small caps), slippage, and holding costs (perp funding, margin interest, borrow). Academic work finds that round-trip costs for small liquidity-demanding traders of equity anomalies are above 50 bps.

### Cited Findings

**US equities and ETFs: commissions and regulatory fees**
- Alpaca charges no commission on US stocks and ETFs for retail order flow. Commissions apply only to index options, the optional "Elite Smart Router" ($0.0040/share all-in fixed, or $0.0025 to $0.0005/share tiered) and non-retail flow. — [Alpaca Brokerage Fee Schedule (rev. Oct 12, 2026)](https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf)
- Pass-through regulatory fees: SEC fee of $0.0000206 × trade value on sells only (about 0.2 bps); FINRA TAF currently $0 per share on sells; FINRA CAT fee of $0.000003 per share on buys and sells. — [Alpaca fee schedule](https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf); same rates at [IBKR stock commissions](https://www.interactivebrokers.com/en/pricing/commissions-stocks.php)
- Alpaca earns payment for order flow. Market orders are routed to Citadel Securities, Jane Street, Virtu and GTS (Q2 2026 Rule 606), which pay up to 12% of the spread, capped at 5c/share. Alpaca crypto: 0.15% maker / 0.25% taker below $100k monthly volume. Margin interest is 6.50%/yr. — [Kagels Trading Alpaca review, Oct 2026 (secondary source citing Alpaca fee schedule)](https://kagels-trading.com/blog/alpaca-review)
- IBKR Pro Tiered: $0.0035/share for 300k shares/month or fewer (min $0.35/order, max 1% of trade value), plus exchange, clearing (NSCC/DTC $0.00020/share) and pass-through fees. IBKR Pro Fixed: $0.005/share (min $1.00). IBKR Lite: $0 (US residents only). — [IBKR Commissions Stocks](https://www.interactivebrokers.com/en/pricing/commissions-stocks.php)
- Note for an Australian operator: IBKR Lite is listed as available to US residents only, so an Australian IBKR account would pay Pro rates. — [IBKR Commissions Stocks](https://www.interactivebrokers.com/en/pricing/commissions-stocks.php)

**US equities: spreads**
- SPY's 30-day median bid-ask spread is shown as 0.00% (rounded, so below 0.5 bp). — [SSGA SPY fund page, Nov 2026](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-500-etf-trust-spy)
- Typical spreads by tier: mega-cap (AAPL, MSFT) about 1 bp; S&P 500 portfolio average about 4.5 bps (attributed to 2024 Nasdaq research); top-100 stocks about 3.7 bps; mid-caps 5-20 bps; small-cap or illiquid 20-100+ bps. — [Equicurious (secondary, cites Nasdaq 2024)](http://equicurious.com/learn/investing-basics/market-mechanics/bid-ask-spreads-and-liquidity-in-us-equities). The underlying Nasdaq study was not checked.
- Small-cap equities (<$500M) can carry spreads of 0.5-5%+ of price per round trip. — [FundedFast (secondary; low authority)](https://fundedfast.com/learn/trading-101/bid-ask-spread)

**Academic evidence on all-in equity trading costs**
- Novy-Marx and Velikov: round-trip transaction costs for typical value-weighted anomaly strategies average more than 50 bps. Costs reduce realised spreads by more than 1% of monthly one-sided turnover: 20% monthly turnover costs at least 20 bps/month. Equal-weighted strategies cost 2-3x as much. Only 2 strategies with more than 50% monthly turnover keep significant net spreads. — [Novy-Marx & Velikov, "A Taxonomy of Anomalies and their Trading Costs" (RFS 2016; working paper)](https://mysimon.rochester.edu/novy-marx/research/ToAatTC.pdf)
- Average monthly costs from 1963-2013: size about 5.7 bps, value about 5.5 bps, momentum about 48.4 bps per month (long/short factors). — [Alpha Architect summary of Novy-Marx & Velikov](https://alphaarchitect.com/trading-costs-destroy-factor-investing)
- Novy-Marx and Velikov find that a buy/hold spread (hysteresis) is the most effective simple way to cut costs. — [Novy-Marx & Velikov](https://academic.oup.com/rfs/article/29/1/104/1843825)
- Frazzini, Israel and Moskowitz (AQR, more than $1 trillion of live institutional trades): average market impact of 9.4 bps against the pre-trade price, or 3.7 bps against VWAP. The effective spread paid was only 1.53 bps, because a large institution mostly trades passively with limit orders. They say their costs are about one tenth of earlier academic estimates. — [Frazzini, Israel, Moskowitz, "Trading Costs of Asset Pricing Anomalies"](https://www.hbs.edu/faculty/Shared%20Documents/events/328/TradingCostEfficiency_FULL_112912.pdf); [2015 version](https://spinup-000d1a-wp-offload-media.s3.amazonaws.com/faculty/wp-content/uploads/sites/3/2019/09/TradingCostofAssetPricingAnomalies.pdf)
- FIM state that the Novy-Marx/Velikov effective-spread costs "should be interpreted as the costs faced by a small liquidity demander". — [FIM 2015](https://spinup-000d1a-wp-offload-media.s3.amazonaws.com/faculty/wp-content/uploads/sites/3/2019/09/TradingCostofAssetPricingAnomalies.pdf). A retail bot sending market orders sits much closer to the Novy-Marx/Velikov case than to AQR's.
- Chen and Velikov (120 anomalies, effective spreads): after publication, the average equal-weighted long-short portfolio nets **-3 bps/month** after costs. Cost-optimised versions net only 4-13 bps/month. — [Chen & Velikov, "Accounting for the Anomaly Zoo"](https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2019/09/Accounting-for-the-Anomaly-Zoo.pdf)

**Market impact: the square-root law**
- Commercial impact models (Salomon StockFacts since about 1991, Barra since about 1998, Bloomberg TCA since 2005) share the form ΔP = spread cost + α·σ·√(Q/V). Here σ is daily volatility, V is daily volume, Q is order size and α is of order one. — [Gatheral, "Three models of market impact" (Baruch slides)](https://mfe.baruch.cuny.edu/wp-content/uploads/2012/09/Chicago2016OptimalExecution.pdf)
- Measured Y (the α constant) for stocks and futures is in the range 0.5 to 1. — [Tóth, Bouchaud et al., CFM, "The square-root impact law also holds for option markets"](https://www.cfm.com/wp-content/uploads/2022/12/287-2016-The-square-root-impact-law-also-holds-for-option-markets.pdf)
- FIM's live trade data shows impact that is concave in the fraction of daily volume, fitted with a square-root function. A linear model is rejected. — [FIM 2015](https://spinup-000d1a-wp-offload-media.s3.amazonaws.com/faculty/wp-content/uploads/sites/3/2019/09/TradingCostofAssetPricingAnomalies.pdf)

**Crypto (spot and perps)**
- Binance spot, regular user (VIP 0, <$1M 30-day volume): 0.100% maker / 0.100% taker, or 0.075% when fees are paid in BNB. VIP 9: 0.011% / 0.023%. — [Binance Spot Fee page](https://www.binance.com/en/fee/trading)
- Binance USDⓈ-M futures, regular user: 0.0200% maker / 0.0500% taker (0.018% / 0.045% with BNB). Fees are charged on notional, not margin, so leverage scales the cost. — [Binance Futures Fee page](https://www.binance.com/en/fee/futureFee); [FeeFlux, checked Nov 11 2026](https://feeflux.com/en/articles/binance-fees-guide)
- Binance Australia is a separate company, and its fees were not checked by the secondary source. — [BrokerSift](https://brokersift.com/exchanges/binance/fees). **Unverified for an AU operator.**
- Bybit VIP 0: spot 0.10% / 0.10%; perpetual & futures 0.055% taker / 0.020% maker. — [Bybit Trading Fee Structure](https://www.bybit.com/en/help-center/article/Trading-Fee-Structure); [Bybit futures fee page](https://www.bybit.com/en/fee/futures)
- Coinbase Advanced (fees changed Sept 16, 2026): entry spot tiers are US 0.50% maker / 0.90% taker; EU and UK 0.25% / 0.50%; "Brazil, India, and other international markets" 0.09% / 0.10%. — [Coinbase blog, 2026-09-16](https://www.coinbase.com/blog/were-lowering-fees-for-many-active-traders-on-coinbase-advanced). Which bucket applies to Australia is **unverified**.
- Bitcoin spreads on major exchanges are roughly 0.005-0.02%. Small-cap altcoins are 1-5%+. — [Quantt (secondary)](https://www.quantt.co.uk/resources/bid-ask-spread-explained). This is a rough secondary estimate.
- A secondary source reports a "Binance October 2026 security breach" and a Bybit February 2025 breach. — [Coin Bureau, Nov 2026](https://coinbureau.com/analysis/best-crypto-exchange-with-lowest-fees). **The October 2026 Binance breach is unverified.** The Bybit Feb 2025 hack is widely reported but was not checked here.

**Perpetual funding rates**
- Funding = premium index + interest rate. On Binance the interest component defaults to 0.03%/day, which is 0.01% per 8-hour interval. — [Binance FAQ: Funding Rates](https://www.binance.com/en/support/faq/detail/360033525031); [Coinbase Learn](https://www.coinbase.com/learn/perpetual-futures/understanding-funding-rates-in-perpetual-futures)
- Coinglass displays 0.01% per interval as the "baseline rate". BTC OI-weighted funding at the time of the search was 0.0028% per interval. — [Coinglass Funding Rates](https://www.coinglass.com/FundingRate)
- Default funding times are every 8 hours (00:00, 08:00, 16:00 UTC), though some contracts use other intervals. A position pays or receives only if it is open at the funding timestamp. Positive funding means longs pay shorts. — [BrokerSift on Binance](https://brokersift.com/exchanges/binance/fees)
- Derived figure: 0.01% × 3 per day × 365 ≈ 10.95%/yr carry for a long perp at the baseline rate (my arithmetic, not sourced).

**FX**
- IBKR spot FX commission is 0.20 bp × trade value (tiered, at or below $1B monthly). — [IBKR Spot Currencies commissions](https://www.interactivebrokers.com/en/pricing/commissions-spot-currencies.php). The $2 minimum per order is from memory and was **not verified** in this search.
- Retail EUR/USD: raw/ECN accounts cost about 0.0-0.2 pips plus about $3-3.50 per lot per side (about $6-7 round turn). Standard accounts cost about 0.8-1.4 pips with no commission. The all-in cost is often similar either way. — [BrokerSift Forex spreads](https://brokersift.com/posts/forex-spreads-and-commissions-explained); [ForexBrokerList (IC Markets/Pepperstone)](https://forexbrokerlist.io/blog/what-is-forex-spread-fixed-vs-variable)
- Live-account EUR/USD average spreads range from about 0.1 pip (Admiral, FXCM) to about 1.7 pips (FxPro). Asia-session maximums widen to 3-9 pips. — [Investing.com EUR/USD broker spreads](https://www.investing.com/currencies/eur-usd-spreads). Note: 1 pip on EUR/USD at about 1.08 is about 0.9 bp.
- Swap/rollover fees are a separate overnight cost on top of spread and commission. — [BrokerSift](https://brokersift.com/posts/forex-spreads-and-commissions-explained). No numeric typical swap markup was found (see Gaps).

**Futures**
- IBKR ES (E-mini S&P) futures: IBKR execution fee $0.85 per contract plus exchange and regulatory fees. — [IBKR Futures commissions](https://www.interactivebrokers.com/en/pricing/commissions-futures.php); [IBKR AU commissions](https://www.interactivebrokers.com.au/en/pricing/commissions-home.php)
- Nasdaq-100 index futures spread is about 0.25-0.5 points (about 0.001% of price). — [FundedFast (low-authority secondary)](https://fundedfast.com/learn/trading-101/bid-ask-spread)

**Short borrow**
- No sourced figures were found for general-collateral vs hard-to-borrow fees (the search was rate-limited). See Gaps.

### Inferences
- A defensible default per-side cost table for a small retail paper-trading factory (spread/2 + fees + slippage), before stress-testing:
  - US mega-cap or liquid ETFs: 1-3 bps
  - S&P 500 average: 3-5 bps
  - Mid-caps: 5-15 bps
  - Small caps: 25-75+ bps
  - Crypto spot majors: about 10-12 bps taker at Binance/Bybit VIP 0, and much more on Coinbase US
  - Crypto perps majors: about 5-6 bps taker plus funding
  - EUR/USD: about 0.5-1 bp
  - ES futures: about 1 bp (fees are negligible; the half-tick spread is about 0.5 bp)
  These numbers combine the cited figures. They are not taken from any single source.
- Turnover is the multiplier that matters most. Novy-Marx/Velikov's rule of thumb (cost ≥ 1% of one-sided monthly turnover for value-weighted equity long/short) can serve as a quick screening check.
- Because Alpaca's revenue comes from PFOF with execution at or inside the NBBO, explicit fees are near zero. The real cost is the spread plus any adverse move between signal and fill.

### Gaps
- Typical stock-borrow fees (GC around 0.25-0.5%/yr; hard-to-borrow much higher) were not found with a source.
- No typical retail FX swap/rollover markup figure was found.
- Fees for Binance Australia, Bybit's availability in AU, and the Coinbase AU bucket are unverified.
- No recent primary-source measurement of small-cap effective spreads (e.g., TAQ-based 2024-2026) was found. The figures above come from secondary sites.

## 2. Slippage models and cost stress-testing

### Takeaway
Use a layered model: half-spread (observed or estimated) + fees + a size-dependent impact term (square-root of participation, scaled by volatility) + a cap on participation per bar. Run every strategy again at a multiple of costs (2x, 3x) and keep only those that survive. Industrial engines such as QuantConnect LEAN offer constant, volume-share and market-impact slippage models, and those make useful templates.

### Cited Findings
- QuantConnect `VolumeShareSlippageModel`: slippage = price impact constant × (order quantity / bar volume)². The default `volumeLimit` is 0.025, meaning at most 2.5% of bar volume can fill per bar. QuantConnect also ships a `MarketImpactSlippageModel` and a constant model, and lets users write custom ones. — [QuantConnect docs: Slippage supported models](https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/slippage/supported-models)
- QuantConnect's example custom model caps slippage at 2% of price, scaled linearly by order quantity / bar volume. Another example uses price × 0.0001 × log10(2 × quantity). — [QuantConnect: Slippage key concepts](https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/slippage/key-concepts)
- LEAN fill models differ by asset class. The FutureFillModel fills a triggered stop at the bar close plus slippage. The EquityFillModel fills at max(open, stop) plus slippage, which handles gaps. — [QuantConnect forum citing docs](https://www.quantconnect.com/forum/discussion/19752/high-slippage-with-future-fill-model/)
- Square-root impact: cost ≈ spread + Y·σ_daily·√(Q/ADV), with Y ≈ 0.5-1. — [Gatheral](https://mfe.baruch.cuny.edu/wp-content/uploads/2012/09/Chicago2016OptimalExecution.pdf); [CFM/Bouchaud](https://www.cfm.com/wp-content/uploads/2022/12/287-2016-The-square-root-impact-law-also-holds-for-option-markets.pdf)
- Alpaca developer relations: paper fills use live quotes (buy at ask, sell at bid), so a "last trade price + slippage factor" is not needed to replicate them. Impact matters mainly for large orders relative to liquidity. — [Alpaca forum (Dan Whitnable, Alpaca)](https://forum.alpaca.markets/t/paper-trading-order-fulfillment-delay/13324/5)
- Costs reduce statistical significance in proportion to their size. Novy-Marx/Velikov find many anomalies keep net t > 2 but far fewer keep net t > 3. — [Novy-Marx & Velikov](https://www.nber.org/system/files/working_papers/w20721/w20721.pdf)

### Inferences
- Recommended factory cost model per fill:
  - `cost_bps = half_spread_bps(asset, time-of-day, vol regime) + fee_bps(venue, maker/taker) + Y·σ_daily·sqrt(order/ADV)·1e4`
  - Hard cap: order ≤ 1-2.5% of bar volume (following the LEAN default), otherwise fill partially or reject.
  - Where bid/ask is not available (daily bars), estimate the spread with a volatility- or price-tier proxy, or use a fixed-bps table by liquidity bucket.
- Stress gates: report Sharpe and CAGR at 1x, 2x and 3x the cost model. Reject strategies whose net Sharpe falls by more than about 50% at 2x, or whose break-even cost (the per-side cost that drives net return to 0) is under about 2-3x the estimated cost. These thresholds are a design suggestion and are not sourced.
- Add a "next-bar open" execution rule plus a delay of N bars as a sensitivity test.

### Gaps
- No authoritative published standard for a "2x cost" stress test was found. It is widespread practitioner folklore and was not sourced here.
- The exact formula of QuantConnect's MarketImpactSlippageModel was not retrieved.

## 3. Biases that make backtests lie

### Takeaway
The largest threats to a strategy factory are data snooping and multiple testing, and they grow with every strategy the factory mines. Next come look-ahead (including fill-at-signal-close), survivorship, and corporate-action errors. Published evidence shows in-sample Sharpe barely predicts out-of-sample Sharpe, and anomaly returns fall by about half after publication. Every trial must be recorded and the winners deflated.

### Cited Findings

**Data snooping, selection bias and overfitting**
- Wiecki et al. (Quantopian, 888 algorithms): commonly reported backtest metrics such as the Sharpe ratio "offer little value in predicting out of sample performance (R² < 0.025)". — [SSRN abstract](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2745220); [Quantpedia summary](https://quantpedia.com/quantopians-academic-paper-about-in-vs-out-of-sample-performance-of-trading-alg/)
- The same paper finds that the more backtests a user ran, the larger the gap between in-sample and out-of-sample Sharpe (overfitting). Its figure shows the IS-OOS shortfall reaching about 1.6 at very high backtest counts. Volatility and drawdown were more predictable OOS than Sharpe. — [Wiecki et al. PDF (Portfolio123 mirror)](https://community.portfolio123.com/uploads/short-url/3WHpAUOzhCG8QAUez71HpoWnA62.pdf); [ResearchGate abstract](https://www.researchgate.net/publication/307553701_All_That_Glitters_Is_Not_Gold_Comparing_Backtest_and_Out-of-Sample_Performance_on_a_Large_Cohort_of_Trading_Algorithms). The exact chart values come from extracted text and should be treated as approximate.
- Bailey and López de Prado's Deflated Sharpe Ratio corrects for selection bias under multiple testing, non-normal returns and short samples. It needs the number of independent trials and the variance of Sharpe ratios across those trials. — [Bailey & López de Prado, "The Deflated Sharpe Ratio"](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)
- With E[SR]=0 and V[SR]=1, the expected maximum Sharpe after 1,000 independent backtests is about 3.26 even when no strategy has any skill. In a worked example, a PSR of 0.99 shrank to a DSR of 0.82 once all trials were counted. — [QuantDare explainer](https://quantdare.com/deflated-sharpe-ratio-how-to-avoid-been-fooled-by-randomness/)
- The Probability of Backtest Overfitting (PBO) uses combinatorially symmetric cross-validation, and the "minimum backtest length" guards against short samples. Recommendation: "Keep track of the number of backtests conducted on a dataset." — [Portfolio Optimization book, §8.3](https://portfoliooptimizationbook.com/book/8.3-dangers-backtesting.html); [Bailey et al., Statistical Overfitting](https://sdm.lbl.gov/oapapers/ssrn-id2507040-bailey.pdf)
- Harvey, Liu and Zhu: given hundreds of factors tested, a newly discovered factor today should clear a t-ratio above 3.0, not the usual 2.0. — [Harvey, Liu & Zhu (NBER w20592)](https://www.nber.org/system/files/working_papers/w20592/w20592.pdf); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2249314)
- McLean and Pontiff (97 characteristics): portfolio returns are 26% lower out-of-sample and 58% lower post-publication. — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623); [Journal of Finance](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365)

**Survivorship bias**
- A backtest of an equal-weight portfolio of *current* S&P 500 members from 2014 "easily beat" the RSP equal-weight ETF. With approximately point-in-time constituents (from IVV holdings), the simulated curve matched RSP almost exactly. Yahoo usually has no data for delisted stocks, and ticker changes are poorly documented. — [Teddy Koker, "Creating a Survivorship Bias-Free S&P 500 Dataset"](https://teddykoker.com/2019/05/creating-a-survivorship-bias-free-sp-500-dataset-with-python/)
- Using real delisted-stock history is "the only reliable way" to estimate survivorship impact, because delisting rates vary widely over time (e.g., 2008-09). — [Quant.SE answer](https://quant.stackexchange.com/questions/81631/simple-approach-to-estimate-survivorship-bias-in-backtest)

**Corporate actions and adjustments**
- Yahoo has rounded adjusted prices to 2 decimals with cumulative adjustment, missed dividends (e.g., VWINX 2011) and recorded phantom splits (e.g., a double 2:1 split for EPD in Aug 2014 that left the series off by 2x for months). It also applies adjustments on the US calendar for non-US exchanges. — [Quant.SE: Yahoo adjusted close bugs](https://quant.stackexchange.com/questions/942/any-known-bugs-with-yahoo-finance-adjusted-close-data). These are older anecdotes, but they show the failure modes to test for.
- In yfinance, `auto_adjust=True` is the default. OHLC comes back adjusted for splits and dividends and there is no separate "Adj Close" column, so a "Close" column may silently be a total-return price. — [Medium: Why Adj Close disappeared in yfinance](https://medium.com/@josue.monte/why-adj-close-disappeared-in-yfinance-and-how-to-adapt-6baebf1939f6); [yfinance issue #1749](https://github.com/ranaroussi/yfinance/issues/1749)

**Timezone and bar alignment; look-ahead**
- Free-data pitfalls include timezones that do not line up with trading hours, gaps from holidays or halts, and missing delisted names. — [IBKR Campus / PyQuant News](https://www.interactivebrokers.com/campus/ibkr-quant-news/the-insiders-guide-to-clean-financial-market-data-with-python-and-yahoo-finance/)
- Binance klines carry explicit open-time and close-time fields in ms. Newer spot files appear to use μs timestamps: the example open time is 1735689600000000, compared with 13-digit ms values in the futures examples. — [binance-public-data README](https://github.com/binance/binance-public-data). A mixed-unit timestamp is a ready-made alignment bug.
- No source was fetched specifically on the "signal on close, filled at the same close" look-ahead. It is standard practice knowledge (see Inferences).

**Unrealistic limit-order fills**
- Alpaca paper fills a non-marketable limit only once the NBBO crosses its price (buy when ask ≤ limit). It does not model queue position. — [Alpaca Paper Trading docs](https://docs.alpaca.markets/us/docs/paper-trading). A backtest that fills limits whenever the price touches the limit overstates fills, and the paper engine will not reveal this either.

**Capacity**
- Strategy capacity is inversely related to turnover. Estimated capacities: size about $170B, value about $50B, momentum about $5B. — [Novy-Marx & Velikov via Alpha Architect](https://alphaarchitect.com/trading-costs-destroy-factor-investing). For a small paper account, capacity matters only for microcaps and illiquid altcoins, where the per-bar participation cap above applies.

### Inferences
- Look-ahead checklist for the factory engine:
  - A signal computed on bar t's close executes no earlier than bar t+1's open, or t's close plus a delay.
  - Fundamentals are lagged to the filing or availability date.
  - Universe membership is point-in-time.
  - Indicators use no centred windows.
  - Normalisation and scaling are fit on the train window only.
  - Adjusted prices (which embed future dividends) are used only for returns, never for price-level thresholds.
- The factory should log every generated and tested variant (the trial count N and the Sharpe variance) so that it can compute DSR/PBO. It should require net-of-cost t > 3 or DSR > 0.95 before promoting to paper.
- Expect live or paper returns of a mined strategy to be about 50% or less of backtest returns. The McLean-Pontiff and Wiecki results both point that way.

### Gaps
- No full-page source was retrieved on point-in-time fundamentals or restatements (e.g., Compustat PIT vs restated data). This is well known but unsourced here.
- No quantitative measurement was found of how much "fill at the signal bar's close" inflates returns.

## 4. Data quality of free sources and survivorship-free options

### Takeaway
Free data is fine for prototyping daily strategies on liquid instruments. It is not survivorship-free and has corporate-action errors. Alpaca's free tier shows only IEX, which is about 3-5% of US volume. For crypto, Binance's public bulk dump is the best free source (all symbols, 1s to 1mo klines, trades, futures). Survivorship-free US equities need a paid vendor such as Norgate.

### Cited Findings
- yfinance is unofficial and "not necessarily maintained", some methods are fragile, and heavy use can get a client rate-limited or blacklisted. — [AlgoTrading101 yfinance guide](https://algotrading101.com/learn/yfinance-guide/)
- Yahoo generally lacks delisted stocks, so yfinance-based equity universes carry survivorship bias. — [Teddy Koker](https://teddykoker.com/2019/05/creating-a-survivorship-bias-free-sp-500-dataset-with-python/); [Quant.SE](https://quant.stackexchange.com/questions/942/any-known-bugs-with-yahoo-finance-adjusted-close-data)
- Alpaca's free "Basic" plan gives real-time equity data from IEX only. Paper-only account holders are entitled to IEX data only. Algo Trader Plus ($99/month) gives all US exchanges. Paper fills are simulated against the NBBO, so IEX-based signals can trigger on prices that differ from the fill reference. — [TradersPost on Alpaca paper trading](https://blog.traderspost.io/article/alpaca-paper-trading); [Alpaca Paper Trading docs](https://docs.alpaca.markets/us/docs/paper-trading)
- IEX market share was about 3.8-5.1% of US equity volume in early Nov 2026 (daily stats), and about 4.8% on a 10-day average in Nasdaq's summary. — [IEX stats](https://iextrading.com/stats/); [Nasdaq Trader volume summary](https://www.nasdaqtrader.com/trader.aspx?id=FullVolumeSummary); [IEX blog: passed 4% share](https://www.iex.io/article/iex-market-share-growth)
- Binance Data Collection (data.binance.vision) provides free daily and monthly files for all symbols: spot and futures klines (1s to 1mo), trades and aggTrades. New daily data appears the next day. — [binance-public-data GitHub](https://github.com/binance/binance-public-data); [data.binance.vision](https://data.binance.vision/)
- Stooq offers free bulk historical downloads (daily, hourly, 5-minute) for the US, UK, Japan, HK, Poland, world indices and macro. — [Stooq Historical Data](https://stooq.com/db/h/). Its survivorship status was not verified.
- Tiingo provides EOD prices, 20+ years of fundamentals, crypto and FX from 2020 for 140+ pairs. — [Tiingo](https://www.tiingo.com/). The free-tier limits were not retrieved.
- Norgate Data supports building a survivorship-free US database with both active and delisted symbols, plus historical index membership (S&P 500, Russell 3000) on each date and total-return prices. — [Concretum Group Norgate tutorial](https://concretumgroup.com/how-to-construct-a-survivorship-bias-free-database-in-norgate-using-python/)
- Free approximate workaround: rebuild point-in-time S&P 500 constituents from monthly iShares IVV holdings (since 2006). Some acquired names will still be missing. — [Teddy Koker](https://teddykoker.com/2019/05/creating-a-survivorship-bias-free-sp-500-dataset-with-python/)

### Inferences
- Recommended stack:
  - Crypto: Binance public data (free, high quality, includes futures, so funding history can be paired with it).
  - US ETFs and macro, daily: yfinance or Stooq plus automated sanity checks, such as flagging any |daily return| > X% and checking it against splits.
  - US single stocks: start from a survivorship-free paid source (Norgate) if cross-sectional stock strategies are in scope. Otherwise restrict the universe to ETFs and futures, where survivorship matters little.
  - FRED for the risk-free rate (not researched here).
- Treat Alpaca IEX bars as non-representative for intraday volume-based signals. IEX carries about 4-5% of volume, so volume and high/low will differ from SIP.

### Gaps
- FRED, Tiingo free-tier quotas and Stooq survivorship handling were not checked in detail.
- Sharadar and other survivorship-free vendor prices were not retrieved.

## 5. Gaps between backtest, paper and live trading; documented failures

### Takeaway
Paper engines (Alpaca, IBKR) are more optimistic than live trading. They fill against the top of book or NBBO without checking size, have no queue modelling, no market impact and no latency slippage, and on Alpaca they apply no regulatory fees and pay no dividends. So paper P&L is an upper bound, not a validation. The larger gap is between backtest and any forward period, driven by overfitting.

### Cited Findings
- Alpaca paper does **not** account for market impact, information leakage, latency slippage, queue position for non-marketable limits, price improvement, regulatory fees, or dividends. — [Alpaca Paper Trading docs (updated 2026-07-07)](https://docs.alpaca.markets/us/docs/paper-trading)
- Alpaca paper does not check order quantity against NBBO size, so an order of any size can fill. A random partial fill happens 10% of the time. — [Alpaca Paper Trading docs](https://docs.alpaca.markets/us/docs/paper-trading); an Alpaca staff member confirms a million-share order in a 500k-ADV stock "gladly" fills — [Alpaca forum](https://forum.alpaca.markets/t/paper-trading-order-fulfillment-delay/13324)
- In a test on Oct 21, 2026, a $100 BTC paper order filled in about 2 ms in three parts. A SPY market order filled at $769.94 at 9:32 ET, while the first IEX trade was at $771.20. — [Kagels Trading Alpaca review](https://kagels-trading.com/blog/alpaca-review)
- The lack of dividend simulation in Alpaca paper makes income strategies look materially different from live. — [TradersPost](https://blog.traderspost.io/article/alpaca-paper-trading)
- IBKR paper simulates fills from top of book only, with no deep-book access. Stops and complex orders are always simulated. It rejects the remainder of partially filled exchange-directed market orders. VWAP, Auction and Pegged-to-Market orders are not supported. Paper accounts start with $1M. — [IBKR Campus glossary](https://www.interactivebrokers.com/campus/glossary-terms/paper-trading-account/); [IBKR Guides](https://www.ibkrguides.com/brokerportal/aboutpapertradingaccounts.htm); [IBKR Campus: Paper vs Live](https://www.interactivebrokers.com/campus/trading-lessons/paper-trading-vs-live-trading-whats-the-difference/)
- A user thread complains that IBKR paper sell fills are unrealistic and says it "is not designed to be an accurate simulation". — [r/interactivebrokers](https://www.reddit.com/r/interactivebrokers/comments/1hvvf20/daytraders_actively_using_ibkr_paper_sell_fills/) (anecdotal)
- Documented large-sample failures:
  - Quantopian's 888 algorithms: in-sample Sharpe has R² < 0.025 for out-of-sample Sharpe. — [Wiecki et al.](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2745220)
  - 97 published anomalies: returns 58% lower after publication. — [McLean & Pontiff](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623)
  - 120 anomalies net -3 bps/month post-publication after costs. — [Chen & Velikov](https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2019/09/Accounting-for-the-Anomaly-Zoo.pdf)

### Inferences
- Since the factory is paper-only, its "live" stage inherits the paper engine's optimism. The factory should apply its own cost model to paper fills: re-price each paper fill with half-spread, fees, impact, dividends and borrow. It should not take broker paper P&L at face value.
- A good diagnostic is to track per-strategy "implementation shortfall" (backtest-expected fill vs paper fill), so that the bias in each layer is measured separately.
- For crypto paper trading, note that Alpaca's crypto fees (0.15/0.25%) differ from Binance/Bybit. Each venue needs its own fee model.

### Gaps
- No documented named cases of individual funds or strategies failing live (e.g., specific blow-ups) were gathered within the fetch budget.
- No quantitative study of Alpaca or IBKR paper-vs-live slippage was found.

## 6. Benchmarks and net-of-cost comparison

### Takeaway
Every mined strategy should be compared after costs, on the same dates, against:
- the risk-free rate
- buy-and-hold of the traded asset or universe
- a simple 60/40 or equal-weight passive alternative

Many anomalies and backtests that beat benchmarks before costs do not do so after costs.

### Cited Findings
- After costs and post-publication, the average anomaly earns about 0 (-3 bps/month for equal-weighted), and cost-optimised versions earn only 0.48-1.56%/yr. That is less than a cash rate. — [Chen & Velikov](https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2019/09/Accounting-for-the-Anomaly-Zoo.pdf)
- Momentum's gross vs net returns in published estimates: Novy-Marx/Velikov gross 15.96% vs net 8.16% per year; FIM momentum gross 2.26 vs net -0.77 in Patton-Weller's comparison table. — [Patton & Weller, "What You See is Not What You Get"](https://public.econ.duke.edu/~ap172/Patton_Weller_MF_31oct17.pdf) (table values extracted from search excerpt; column mapping somewhat uncertain)
- Novy-Marx/Velikov propose a performance metric that measures whether an asset improves the investment opportunity set *net of frictions*, because conventional alpha can mislead when trading has costs. — [Novy-Marx & Velikov NBER](https://www.nber.org/system/files/working_papers/w20721/w20721.pdf)
- Coinbase pays 3.5% APY on USDC to Coinbase One members, which is a relevant hurdle for crypto strategies. — [Coinbase blog](https://www.coinbase.com/blog/were-lowering-fees-for-many-active-traders-on-coinbase-advanced). IBKR advertises 3.38% on uninvested USD cash. — [IBKR commissions home (search snippet)](https://www.interactivebrokers.com/en/pricing/commissions-home.php)

### Inferences
- Benchmarks should match the asset class:
  - US equity strategies: SPY total return; 60/40 (SPY/AGG or similar); T-bill rate from FRED.
  - Crypto strategies: BTC buy-and-hold, and the stablecoin yield or perp basis carry as the risk-free equivalent.
  - FX: the carry implied by the interest differential.
  - Australian operator: possibly also AUD cash rate and AUD-hedged vs unhedged returns. Currency conversion costs are not covered here.
- Report net excess return over risk-free, information ratio vs buy-and-hold, and the DSR together. A strategy that does not beat buy-and-hold after costs should be rejected even if its Sharpe looks high.

### Gaps
- No up-to-date 2025-2026 sourced figures for 60/40 or buy-and-hold returns were collected.
- AUD-specific considerations (FX conversion costs on IBKR/Alpaca for an AU resident, and AU tax treatment for future live trading) were not researched.

## Method note
- The Parallel search tool hit its free-tier rate limit after 4 queries, and the rest of the searching used Firecrawl search.
- No full-page fetches were made. All evidence comes from search excerpts.
- Figures labelled "secondary" come from broker-review or education sites and should be checked against primary sources before they are hard-coded.
