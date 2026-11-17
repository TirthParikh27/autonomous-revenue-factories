# Validating Trading Strategies and Guarding Against Backtest Overfitting (for an automated strategy-mining factory)

Research date: 2026-11-17. Tool budget: about 17 calls (8 page fetches, the rest searches). Primary sources are used where possible. Secondary sources (blogs, vendor pages, calculators) are marked **[secondary]**. Items written from background knowledge and not checked in this session are marked **[unverified]**. They appear only under Inferences or Gaps.

---

## 1. Walk-forward analysis, purged k-fold with embargo, and Combinatorial Purged Cross-Validation (CPCV)

### Takeaway
Walk-forward (WF) analysis tests only one historical path and is easy to overfit. Purged k-fold with embargo removes label leakage. CPCV builds many out-of-sample (OOS) backtest paths from one history, so you get a distribution of OOS performance instead of a single number. In a controlled synthetic study (Arian, Norouzi & Seco 2024), CPCV beat k-fold, purged k-fold and especially WF on PBO and on the DSR test statistic. CPCV is ready to use in open-source code (skfolio, purgedcv).

### Cited Findings
- **Purging**: drop training observations whose label windows overlap the test set. **Embargo**: also drop training rows in a buffer right after each test block, which catches leakage that purging misses. Example code computes the embargo as a fraction of the sample (`pct_embargo=0.01`) and applies it before purging — [QuantInsti blog [secondary]](https://blog.quantinsti.com/cross-validation-embargo-purging-combinatorial/); [Towards AI [secondary]](https://towardsai.com/p/l/the-combinatorial-purged-cross-validation-method)
- CPCV "creates multiple training and testing combinations, ensuring that each data segment is used for training and validation". It was introduced by López de Prado (2018) to fix the single-path weakness of WF and ordinary CV, and it builds in purging — [Arian, Norouzi, Seco (Scribd copy)](https://www.scribd.com/document/741626696/Backtest-Overfitting-in-the-Machine-Learning-Era-A-Comparison-of-Out-of-Sample-Testing-Methods-in-a-Synthetic-Controlled-Environment)
- Arian, Norouzi & Seco (*Knowledge-Based Systems*, 2024; SSRN 4778909) report "the marked superiority of the Combinatorial Purged (CPCV) method in mitigating overfitting risks, outperforming traditional methods like K-Fold, Purged K-Fold, and especially Walk-Forward, as evidenced by its lower PBO and superior DSR Test Statistic". WF "exhibits notable shortcomings in false discovery prevention, characterized by increased temporal variability and weaker stationarity" — [SSRN abstract](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4778909); [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110)
- **skfolio** `CombinatorialPurgedCV(n_folds=10, n_test_folds=8, purged_size=0, embargo_size=0)` follows the scikit-learn API. `cross_val_predict` returns a Population of multi-period portfolios, one per test path. `optimal_folds_number(n_observations, target_n_test_paths, target_train_size)` picks the fold counts. Example: 1006 observations with 9 folds and 7 test folds gives 36 training combinations and 28 test paths. skfolio also offers `WalkForward` and `MultipleRandomizedCV` (WF on random asset and time subsamples) — [skfolio API](https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html); [skfolio user guide](https://skfolio.org/user_guide/model_selection.html); [skfolio NCO example](https://skfolio.org/auto_examples/clustering/plot_5_nco_grid_search.html)
- **purgedcv** (eslazarev/purged-cross-validation) is scikit-learn compatible. It provides `PurgedKFold` (with prediction_times, evaluation_times, purge_horizon and embargo), `apply_embargo`, CPCV with `reconstruct_paths`, `minimum_backtest_length`, PSR and DSR. Its example notebook audits a 400-trial Optuna search with PBO, effective-trial DSR, MinBTL and CPCV paths — [GitHub](https://github.com/eslazarev/purged-cross-validation)
- Practitioner critique of WF (Carver): "A year is a very, very short period of time to actually find any sort of statistical evidence about whether something is working or not." Fitting on one year and testing on the next mostly tests whether a regime persists — [Better System Trader ep. 26 [secondary interview]](https://bettersystemtrader.com/026-robert-carver/)
- Carver's "no time machine" rule: "a parameter set should only be tested on a period of data if it has been fitted only on data that was available ... in the past of the testing period." He prefers an **expanding window** (fit 2000, test 2001; fit 2000–2001, test 2002; and so on) to a rolling window, and pools data across instruments — [Carver, "The three kinds of (over) fitting"](https://qoppac.blogspot.com/2015/11/the-three-kinds-of-overfitting.html)
- Summary of Carver's *Systematic Trading*: fit with rolling or expanding windows, and avoid windows that are too short — [awesome-quant-ai book notes [secondary]](https://github.com/leoncuhk/awesome-quant-ai/blob/main/book/Systematic%20Trading%20A%20unique%20new%20method%20for%20designing%20trading%20and%20investing%20systems.md)
- A practitioner objection to CPCV: it "breaks the path into different combinations but does not seem to preserve the time series aspect", because training data can come after test data — [r/quant thread [secondary, forum]](https://www.reddit.com/r/quant/comments/15oskjh/combinatorial_purged_cv_question/)

### Inferences
- **Anchored vs rolling WF.** Anchored (expanding) WF uses all past data. That gives lower estimation variance, and Carver recommends it for robust, low-parameter fits. Rolling WF adapts to regime change but uses less data. A factory can run both and flag strategies whose rolling-WF results swing widely. **[general practice; not checked against a primary source this session]**
- CPCV path count **[unverified, AFML ch.12]**: with N groups and k test groups there are C(N,k) splits and φ = (k/N)·C(N,k) paths. For example, N=6 and k=2 give 15 splits and 5 paths. This matches the "5 backtest paths from 1 historical path" examples in the QuantInsti and Towards AI posts above.
- For a factory, the main benefit of CPCV is a *distribution* of OOS Sharpe per candidate (median, 5th percentile). That supports rules like "5th-percentile path Sharpe > 0" instead of a single WF number. CPCV only applies when the strategy has a fit step. Rule-based strategies with fixed parameters can just be run on each path.
- The embargo should be at least the longest label or holding horizon plus the longest feature lookback that could reach across a split.

### Gaps
- The exact CPCV path-construction algorithm and recommended N and k could not be confirmed against AFML in this session (book is not online).
- No primary-source head-to-head comparison of anchored vs rolling WF was found.

---

## 2. Probability of Backtest Overfitting (PBO) via Combinatorially Symmetric Cross-Validation (CSCV)

### Takeaway
PBO is the probability that the configuration ranked best in-sample (IS) ranks *below the median* OOS. It is computed over all C(S, S/2) symmetric half-splits of a T×N matrix of per-period P&L, one column per trial. It assesses the **search process** (the whole family of N trials), not a single strategy. It needs the complete trial log.

### Cited Findings (exact procedure from the primary paper, [Bailey, Borwein, López de Prado, Zhu, "The Probability of Backtest Overfitting"](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf))
1. Build **M**, a T×N matrix of P&L. Each column is one trial (one model configuration) over the same T observations. Columns must be synchronous, and the performance metric must be computable on subsamples.
2. Split M by rows into an **even number S** of disjoint, equal-sized blocks M_s, each (T/S)×N.
3. Form every combination C_S of the blocks taken S/2 at a time. There are C(S, S/2) combinations.
4. For each combination c:
   - (a) Training set J = the S/2 chosen blocks joined in their original order, size T/2 × N.
   - (b) Test set J̄ = the complement, size T/2 × N.
   - (c) Compute the performance vector R^c on J (e.g., Sharpe for each column) and its ranks r^c.
   - (d) Compute the same on J̄ to get R̄^c and its ranks r̄^c.
   - (e) n* = the IS-best column.
   - (f) Relative OOS rank ω̄_c = r̄_{n*}/(N+1).
   - (g) Logit λ_c = ln(ω̄_c/(1−ω̄_c)).
5. Build the distribution f(λ) from all λ_c. **PBO = share of λ_c ≤ 0**, i.e. the IS-best is at or below the OOS median. Formally, PBO = Σ_n Prob[r̄_n < N/2 | r ∈ Ω*_n]·Prob[r ∈ Ω*_n].

- **Recommended S = 16.** On 4 years of daily data this gives quarterly blocks, which preserves serial correlation, and 12,780 logits with σ[f(λ)] < 0.0045 — [same paper](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
- **Other outputs from the same run:**
  - *performance degradation*: regress the OOS performance of the IS-best on its IS performance; a negative slope means overfitting;
  - *probability of loss*: Prob[R̄_{n*} < 0];
  - *stochastic dominance*: whether the OOS distribution of the selected strategy dominates that of all trials, first- and second-order — [same paper](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
- **Limitations stated by the authors:**
  - The symmetric split may not suit every strategy or metric.
  - Strongly autocorrelated metrics combined with large S cause problems.
  - All trials are weighted equally.
  - The researcher must report *all* trials. Hiding trials understates PBO, and adding doomed trials biases it. Guided searches should contribute converged outcomes only.
  - It does not check whether the backtest itself is correct (costs, data availability).
  - It covers only structural breaks inside the sample.
  - A high PBO does not mean no trial has skill.
  - **"CSCV should not be applied to guide the search"**: PBO must not be the objective function.
  — [same paper](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
- **Implementations:**
  - **pypbo** (Python): PBO, PSR, MinTRL — [GitHub esvhd/pypbo](https://github.com/esvhd/pypbo)
  - R package **pbo** on CRAN: any metric (e.g. Omega); PBO, degradation, probability of loss, stochastic dominance; parallel option; 12,780 combinations at S=16 — [CRAN pbo README](https://cran.r-project.org/web/packages/pbo/readme/README.html)
  - purgedcv also computes PBO — [GitHub](https://github.com/eslazarev/purged-cross-validation)

### Inferences
- In a factory, PBO is a natural **batch-level / family-level health metric**. Compute it per research campaign (one strategy family × one parameter grid) from the stored per-period P&L of every trial. Reject or deprioritize whole families with PBO above a threshold (e.g. > 0.3–0.5; the threshold is a design choice, not from the paper).
- Store full T×N daily return matrices for every trial, including failures. Both PBO and DSR depend on a complete trial ledger.
- Cost scales as C(S, S/2) × N ranking operations. S=16 gives 12,870 combinations (C(16,8) = 12,870; the paper's figure of 12,780 is likely a typo carried into the R package README — **[arithmetic check, not sourced]**). This is cheap for N up to roughly 10⁴.

### Gaps
- No authoritative guidance was found on PBO thresholds for go/no-go decisions.
- pypbo maintenance status (last commit) was not checked.

---

## 3. Deflated Sharpe Ratio (DSR), Probabilistic Sharpe Ratio (PSR), effective number of trials, MinBTL, MinTRL

### Takeaway
PSR is the probability that the true Sharpe exceeds a threshold SR*, adjusted for sample length, skewness and kurtosis. DSR is PSR with SR* set to the *expected maximum Sharpe of N independent zero-skill trials* (the False Strategy Theorem). N should be the **effective** number of independent trials. López de Prado (2019) estimates it by clustering the correlation matrix of trial returns (ONC algorithm), and computes DSR on cluster-level returns. MinBTL bounds how many trials a given data length can support. MinTRL gives the live or paper record length needed before a Sharpe is statistically meaningful.

### Cited Findings
- **PSR**:

  PSR(SR*) = Φ( (SR̂ − SR*)·√(T−1) / √(1 − γ̂₃·SR̂ + ((γ̂₄−1)/4)·SR̂²) )

  Use per-period (non-annualized) SR. γ₃ is skewness and γ₄ is raw (non-excess) kurtosis — [portfolio-lab [secondary]](https://portfolio-lab.net/knowledge/deflated-sharpe-ratio); [Portfolio Optimizer [secondary]](https://portfoliooptimizer.io/blog/the-probabilistic-sharpe-ratio-bias-adjustment-confidence-intervals-hypothesis-testing-and-minimum-track-record-length)
- PSR is 1 minus the p-value of the corresponding hypothesis test — [Portfolio Optimizer [secondary]](https://portfoliooptimizer.io/blog/the-probabilistic-sharpe-ratio-bias-adjustment-confidence-intervals-hypothesis-testing-and-minimum-track-record-length)
- **Expected maximum Sharpe (False Strategy Theorem)**:

  E[max SR̂_n] ≈ E[SR̂_n] + √V[SR̂_n] · ((1−γ)·Z⁻¹[1−1/N] + γ·Z⁻¹[1−1/(N·e)])

  γ ≈ 0.5772 is the Euler–Mascheroni constant, V is the variance of the estimated Sharpe ratios *across trials*, and N is the number of independent trials. With E=0 and V=1, 1,000 trials give an expected max of about 3.26 — [Bailey & López de Prado, DSR paper (2014)](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf?review=c20); [Quantdare [secondary]](https://quantdare.com/deflated-sharpe-ratio-how-to-avoid-been-fooled-by-randomness)
- **DSR = PSR(SR̂₀)** with SR̂₀ = E[max SR̂_n]: "Essentially, DSR is a PSR where the rejection threshold is adjusted to reflect the multiplicity of trials." Inputs: SR̂ of the selected strategy, T, skewness, kurtosis, N, and V[SR̂_n] across trials — [DSR paper](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf?review=c20)
- False Strategy Theorem (*American Mathematical Monthly* 2021): "there is no Sharpe ratio threshold above which we may reject the hypothesis that a strategy is false. With enough number of trials, any false strategy may achieve a Sharpe ratio as high as a researcher demands." — [quantresearch.org publications](https://quantresearch.org/Publications.htm)
- The rule of thumb of halving the backtest Sharpe "has no scientific basis" — [Bailey & López de Prado, *Significance* 2021](https://academic.oup.com/jrssig/article/18/6/22/7038278)
- **Worked numbers** [secondary]:
  - 50 independent trials on a 5-year daily backtest give an expected best zero-skill Sharpe of about 1.01 (annualized).
  - A best-of-50 Sharpe of 1.0 has DSR ≈ 0.495, a coin flip. About 1.74 is needed for DSR ≥ 0.95.
  - In simulation, when one of 50 variants had a true SR of 0.5, the genuine one won only 15.3% of the time. The winner's average true SR was 0.076.
  — [Risk Hub [secondary]](https://riskhub.org/blogs/multiple-comparisons-in-backtesting)
- **Effective number of trials (López de Prado 2019, "A Data Science Solution to the Multiple-Testing Crisis in Financial Research", *JFDS* 1(1):99–110)**:
  - Cluster the correlation matrix of trial returns with **ONC** (Optimal Number of Clusters, López de Prado & Lewis 2018), choosing k to maximize a cluster-quality score q_k.
  - Build **one return series per cluster using minimum-variance weights** so that volatile trials do not dominate.
  - Compute each cluster's SR, skewness, kurtosis and T, plus √V[SR_k] *across clusters*.
  - E[max SR_k] then comes from the False Strategy Theorem with N = number of clusters K, and DSR is computed for the selected strategy's cluster.
  - Worked example: 6,385 trials collapsed to k=4 clusters. The selected cluster had aSR 2.03 (daily SR 0.1255) against E[max SR_k] = 0.027 daily, giving DSR ≈ 1.0. The author attributes the low cluster count to theory-constrained search and says arbitrary searches would yield "perhaps in the hundreds" of clusters.
  — [AQR-hosted JFDS PDF](https://www.aqr.com/-/media/AQR/Documents/Journal-Articles/JFDS_Winter2019_A-Data-Science-Solution-to-Multiple-Testing-Crisis---Lopez_de_Prado.pdf?sc_lang=en); [SSRN 3177057](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3177057)
- **MinTRL**:

  MinTRL = 1 + (1 − γ₃·SR + ((γ₄−1)/4)·SR²)·(Z_α/(SR − SR*))²

  This is in observations, at per-period SR. If SR ≤ SR*, no length is enough — [Finance Toolkit docs [secondary]](https://www.jeroenbouma.com/projects/financetoolkit/docs/performance/minimum-track-record-length); [thequant.space [secondary]](https://thequant.space/tools/deflated-sharpe-calculator)
- **MinTRL worked example (monthly data, annual SR 1.0, 95%)** [secondary]:
  - Against SR* = 0: 34.8 months under normal returns, 44.3 months (3.7 yr) with skew and kurtosis.
  - Against SR* = 0.5 p.a.: 136–174 months (11–14.5 yr).
  — [portfolio-lab [secondary]](https://portfolio-lab.net/knowledge/deflated-sharpe-ratio)
- **MinBTL** (Bailey, Borwein, López de Prado, Zhu, "Pseudo-mathematics and financial charlatanism"). Approximation: MinBTL ≈ 2·ln(N)/SR*² years, an upper bound. The exact version uses the Gumbel expected maximum. For a target annual SR of 1.0: N=10 → about 2.5 yr; 100 → about 6.4 yr; 1,000 → about 10.6 yr; 10⁶ → about 23.7 yr — [Quant Memo [secondary]](https://quantmemo.com/concepts/minimum-backtest-length); [Risk Hub [secondary]](https://riskhub.org/blogs/multiple-comparisons-in-backtesting)
- MinBTL is a population-selection approximation, and correlated configurations reduce effective N. "Estimate the null maximum from the actual search structure when possible" — [Stochastly [secondary]](https://stochastly.com/library/backtest-overfitting/minimum-backtest-length-and-track-record)

### Inferences
- **Factory implementation:**
  - (1) Log every trial's daily return series.
  - (2) Per campaign, compute the trial correlation matrix and cluster it (ONC, or hierarchical clustering plus silhouette as a cheaper substitute) to get K_eff.
  - (3) Compute DSR for each candidate using K_eff and the cross-cluster V[SR].
  - (4) Track cumulative trials across the whole factory's lifetime, not just per campaign. A factory that keeps mining the same dataset grows N without limit, and the False Strategy Theorem says any threshold will eventually be beaten.
- MinBTL gives a **trial budget per dataset**. With 10 years of data and a target SR of 1, only roughly 10³ effective independent trials are justified. That argues for capping trials per dataset and using fresh data (new markets, new periods) instead of more search.
- Because E[max] grows only like √(2 ln N), getting N roughly right matters much less than not pretending N = 1.

### Gaps
- No well-maintained open-source ONC implementation was confirmed. mlfinlab had one but is now paid (see section 8). Code in López de Prado's *Machine Learning for Asset Managers* is a possible source **[unverified]**.
- The DSR formula in some secondary sources uses an extra "+½SR²" term (the Quantdare version) while others use the "(γ₄−1)/4" form. These are algebraically equivalent when γ₄ is raw kurtosis (1 + ½SR² + (γ₄−3)/4·SR² = 1 + (γ₄−1)/4·SR²). Implementers must still be consistent about raw vs excess kurtosis.

---

## 4. Multiple-testing corrections: Harvey–Liu–Zhu, Bonferroni/Holm/BHY, White's Reality Check, Hansen's SPA, Romano–Wolf StepM, permutation tests

### Takeaway
Two families exist:
- **Analytic p-value adjustments** (Bonferroni and Holm for the family-wise error rate (FWER), BHY for the false discovery rate (FDR)). Harvey, Liu & Zhu used these to argue that new factors need t > 3.0.
- **Bootstrap tests that keep the dependence between strategies**: White's Reality Check, then Hansen's SPA (more powerful, less hurt by bad models), then Romano–Wolf StepM (identifies *all* superior strategies with FWER control). Hsu–Hsu–Kuan's Step-SPA is more powerful again.

The Python package `arch` implements SPA, StepM and MCS. Masters-style Monte Carlo permutation tests are the nonparametric option for practitioners and can include the whole optimization step.

### Cited Findings
- Harvey, Liu & Zhu (*Review of Financial Studies* 29(1), 2016):
  - "a newly discovered factor today should have a t-ratio that exceeds 3.0", which corresponds to p ≈ 0.27%. The authors "also argue that there are good reasons to expect that 3.0 is too low."
  - They use Holm (FWER, 5%) and BHY (FDR, 1%).
  - Adjusting for unpublished tests raised the BHY-implied t from 3.39 to 3.68 at 1% and from 2.78 to 3.18 at 5%.
  - About 70% of factors deemed true have SR < 0.5.
  — [NBER w20592](https://www.nber.org/system/files/working_papers/w20592/w20592.pdf); [Duke PDF](https://people.duke.edu/~charvey/Research/Published_Papers/P118_and_the_cross.PDF)
- Holm step-down: order the p-values and reject H_(j) while p_(j) < α/(K−j+1). It is "universally" more powerful than Bonferroni (α/K), but such methods "do not incorporate the dependence structure of the test statistics" and often have low power — [Romano & Wolf, "Stepwise Multiple Testing as Formalized Data Snooping"](https://econ-papers.upf.edu/papers/712.pdf)
- **White's Reality Check (2000)** tests whether the *best* of K strategies beats a benchmark after data snooping, using a bootstrap that accounts for dependence. Sullivan, Timmermann & White (1999) used it to show technical rules lost predictive power on US indices after the mid-1980s — [Hsu, Hsu, Kuan Step-SPA paper](https://homepage.ntu.edu.tw/~ckuan/pdf/Step-SPA-20090720.pdf)
- **Hansen's SPA (2005)**: the RC uses the least-favorable configuration (μ=0) and "may lose power dramatically when many poor models are included". SPA re-centres the null to avoid this and is more powerful. Both RC and SPA only say *whether any* model is significant, not *which* — [Step-SPA paper](https://homepage.ntu.edu.tw/~ckuan/pdf/Step-SPA-20090720.pdf)
- **Romano–Wolf StepM**:
  - A stepwise procedure that asymptotically controls the FWER and "implicitly captures the joint dependence structure of the test statistics". It is more powerful than single-step methods and extends the RC to find all strategies that beat the benchmark.
  - The authors recommend **studentized** statistics and circular block bootstrap, with B = 1,000.
  - Non-studentized versions "can fail to control the FWE in finite samples when there is notable dependence over time".
  — [Romano & Wolf](https://econ-papers.upf.edu/papers/712.pdf)
- **Step-SPA** (Hsu, Hsu & Kuan, *Journal of Empirical Finance* 2010) is more powerful than Step-RC. It was applied to 9,120 moving-average and 7,260 filter rules and uses the stationary bootstrap — [Step-SPA paper](https://homepage.ntu.edu.tw/~ckuan/pdf/Step-SPA-20090720.pdf); [RePEc](https://ideas.repec.org/a/eee/empfin/v17y2010i3p471-484.html)
- **arch (Python, K. Sheppard)**:
  - `SPA` (also exposed as `RealityCheck`), `StepM` and `MCS` (model confidence set).
  - Inputs are T×k *loss* matrices plus benchmark losses. For returns, use loss = −return.
  - Bootstraps: stationary (default), circular block or moving block. Block size defaults to √T. reps defaults to 1000.
  — [arch multiple-comparison docs](https://bashtage.github.io/arch/multiple-comparison/multiple-comparison_examples.html); [arch MCS API](https://arch.readthedocs.io/en/stable/multiple-comparison/generated/arch.bootstrap.MCS.html); [GitHub bashtage/arch](https://github.com/bashtage/arch)
- **Reported caveat**: a third-party MQL5 port says that in arch 8.0 the SPA `studentize` option "does not divide by the standard deviations, so it returns the test without studentization whatever the option". This is **[secondary, unverified — check against current arch source before relying on studentized SPA]** — [MQL5 DataSnooping library](https://www.mql5.com/en/code/78806)
- Illustration from the same port: across 100 moving-average rules on US30 daily data, the best rule had a standalone p = 0.043 but a Reality Check p = 0.244 and SPA p = 0.187 as the best of 100. Neighbouring parameter sets are highly correlated, so Bonferroni "would be far too strict" — [MQL5 [secondary]](https://www.mql5.com/en/code/78806)
- **Monte Carlo permutation test (Masters)**:
  - Masters' book *Permutation and Randomization Tests for Trading System Development* covers Monte Carlo tests to separate skill from luck. A newer edition adds "an alternative permutation test for selection bias that is substantially superior to the traditional test" — [timothymasters.info](https://timothymasters.info/market-trading)
  - Core idea: "permute your training data – shuffle it in ways that destroy temporal patterns – and retrain the system on each permuted version", instead of spending OOS data.
  - Masters warns that comparing candidates on the same OOS data makes the result "the better of John and Mary's systems" and contaminates the OOS set.
  — [Better System Trader interview with Masters [secondary]](https://bettersystemtrader.com/185-how-to-avoid-creating-trading-strategies-that-degrade-quickly-timothy-masters/)
  - Typical implementation [secondary, vendor]:
    1. Convert OHLC to log returns, including intrabar moves.
    2. Shuffle their order.
    3. Rebuild prices by cumulative sum and exponentiation.
    4. Re-run the strategy, ideally including its optimization.
    5. Repeat about 1,000 times (10,000 if p < 0.001 is needed).
    6. p = (# permutations ≥ real) / total.

    Running the test only on the best of thousands of mined strategies "still [has] a selection-bias problem" — [Build Alpha [secondary, vendor]](https://www.buildalpha.com/monte-carlo-permutation/)

### Inferences
- For a factory with thousands of correlated candidates, the **bootstrap family (SPA/StepM/MCS) on the full T×k return matrix** suits better than Bonferroni or Holm, because it keeps the cross-strategy correlation. BHY (FDR) fits better when the aim is a *portfolio* of discoveries rather than one winner.
- A permutation test that **re-runs the whole search on each permuted series** (re-mine, then take the best) gives a null distribution of "best-of-search" performance. This is the most honest test of training plus selection bias, but it costs roughly 1,000 times the search. Use it only on shortlisted families.
- Permuting returns destroys autocorrelation *and* volatility clustering. Strategies that exploit volatility clustering (not direction) may be unfairly penalized or passed. Block permutation or bar-relative permutation partly helps **[general knowledge, unverified]**.

### Gaps
- Masters' exact algorithm, including the "superior" selection-bias test in the newer edition, could not be read; the book is not online.
- No head-to-head comparison of DSR vs SPA/StepM in strategy-mining settings was found.

---

## 5. Parameter robustness, noise injection and synthetic data, regime robustness, holdout discipline

### Takeaway
Primary academic sources say less here; this area is mostly practitioner craft. The consistent messages:
- prefer parameter **plateaus** to peaks and restrict degrees of freedom;
- perturb the data (noise, permutation, synthetic generation) and require performance to degrade gracefully;
- check performance across sub-periods and regimes;
- treat any holdout as single-use, because each look at OOS data turns it into in-sample data.

### Cited Findings
- Carver's "three kinds of (over)fitting" — **explicit** (parameter optimization), **implicit** (dropping ideas that failed, which overstates the backtest) and **tacit** (choices informed by prior knowledge of history). His remedies:
  - restrict degrees of freedom: A<B, B = k·A, or parameters on a doubling grid {1,2,4,…,256};
  - use the same parameters across all instruments in an asset class;
  - keep a "fund level" backtest "in which every single idea we've ever considered is stored".
  — [Carver blog](https://qoppac.blogspot.com/2015/11/the-three-kinds-of-overfitting.html)
- Carver weights rules by the uncertainty of their Sharpe estimates instead of dropping weak rules ("Poor rules get lower weight but are rarely excluded entirely"), and warns that negative-skew rules show inflated Sharpe ratios — [Systematic Trading notes [secondary]](https://github.com/leoncuhk/awesome-quant-ai/blob/main/book/Systematic%20Trading%20A%20unique%20new%20method%20for%20designing%20trading%20and%20investing%20systems.md)
- Carver's handcrafting Sharpe adjustment: with 2 years of data the lowest possible weight for a bad rule is about 0.5. With 30+ years it is almost zero. Performance-based weighting only becomes decisive with decades of data — [Carver blog 2019](https://qoppac.blogspot.com/2019/12/new-and-improved-sharpe-ratio.html)
- **Noise test** (vendor practice): add or subtract small amounts of volatility on every bar while keeping the historical sequence. Pair it with a "Vs Random" benchmark (random entries) and walk-forward — [Build Alpha [secondary, vendor]](https://www.buildalpha.com/monte-carlo-permutation/)
- **Synthetic data**: skfolio includes `SyntheticData` with a vine-copula estimator and entropy-pooling stress tests, e.g. imposing a CVaR view on a factor — [skfolio](https://skfolio.org/)
- **Holdout discipline (Masters)**: "Every time you look at the out-of-sample results and decide to keep or discard a variant, you have used that data. It is no longer truly out-of-sample... This is why systems that perform beautifully in backtests often fail immediately when traded live." — [Better System Trader / Masters [secondary]](https://bettersystemtrader.com/185-how-to-avoid-creating-trading-strategies-that-degrade-quickly-timothy-masters/)
- PBO must not be used as an objective to guide the search, since that would turn the test into a target — [Bailey et al.](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)

### Inferences
Concrete factory checks (design suggestions built from the sources above, not from one source):
- (a) **Neighbourhood stability**: the median Sharpe of the ±1-grid-step neighbours should be at least about 70% of the peak. A *smoothed* sensitivity surface is the selection criterion, not the peak.
- (b) Noise injection and parameter jitter, with a pass rate over around 100 perturbations.
- (c) Sub-period and regime breakdown (bull/bear, high/low volatility, rate regimes). Require a positive contribution in most regimes, or an explicit regime gate.
- (d) Cross-market generalization: the same parameters on related instruments, following Carver's pooling.
- (e) **Final holdout touched once per candidate family**, with access logged by the system. A holdout that has been touched is retired or renamed "validation".

### Gaps
- No primary academic paper was found that defines a standard "parameter plateau" metric.
- No primary study quantifying noise-test effectiveness was found; only vendor claims.

---

## 6. How long paper/forward trading must run to distinguish skill from luck

### Takeaway
Under roughly normal returns, the t-stat of a Sharpe is about SR·√years. So 95% one-sided significance against zero needs about (1.645/SR)² years, or (1.96/SR)² two-sided:
- SR 1.0: about 2.7–3.8 years;
- SR 0.5: about 11–15 years;
- SR 2.0: under 1 year.

Negative skew and fat tails lengthen this, and so does a positive hurdle (e.g. the DSR-implied SR₀). Paper trading of a few months therefore **cannot** statistically confirm a typical strategy. Its real role is to catch implementation, execution and cost errors and gross decay.

### Cited Findings
- The track record needed is about (1.96/SR)² years (t ≈ SR·√T, two-sided 95%). In a 4,843-replication sample with a median backtest of 33.5 years, only 48% of strategies cleared the bar — [Papers With Backtest [secondary]](https://paperswithbacktest.com/strategies/systematic-trading-strategies)
- MinTRL examples (annual SR 1.0, monthly data, 95%): 3.7 years against 0 with realistic skew and kurtosis; about 14.5 years against a 0.5 hurdle — [portfolio-lab [secondary]](https://portfolio-lab.net/knowledge/deflated-sharpe-ratio)
- MinTRL formula and the fact that it is undefined when SR ≤ SR* — [Finance Toolkit [secondary]](https://www.jeroenbouma.com/projects/financetoolkit/docs/performance/minimum-track-record-length)
- The thequant.space calculator also reports "the length needed to beat the luck ceiling itself", i.e. MinTRL against the expected-max SR of N trials. One year of daily data gives σ_SR ≈ 1.0 annualized, so 100 trials produce a best-by-luck Sharpe near 2.5 — [thequant.space [secondary]](https://thequant.space/tools/deflated-sharpe-calculator)
- Kevin Davey: after the walk-forward and Monte Carlo stages, strategies are **incubated** in live markets without real money for **6–12 months** — [AlgoAdvantage interview summary [secondary]](https://algoadvantage.substack.com/p/036-kevin-davey-part-i-its-all-about)

### Inferences
- In a factory, incubation cannot be a significance test for SR ≤ 1.5. Use it as:
  - (1) an implementation check (live vs simulated fills, slippage, data parity);
  - (2) a *consistency* check: is the incubation return inside the backtest's predictive distribution (e.g. above the 5th percentile of CPCV path outcomes or bootstrapped 6-month windows)?
  - (3) a sequential test (e.g. a CUSUM or sequential probability ratio test (SPRT) on Sharpe) that keeps updating after go-live with small capital. **[design suggestion]**
- Running many strategies in parallel lets portfolio-level statistics accumulate evidence faster than single-strategy records, provided they are not highly correlated.

### Gaps
- No primary study was found on the optimal incubation length or on sequential-testing designs for live strategy monitoring.

---

## 7. How sophisticated retail practitioners actually do it, and what is overkill

### Takeaway
Practitioners (Davey, Carver, Masters, Pardo-style WF users) use a simpler, sequential funnel:
1. idea / hypothesis;
2. limited-DOF in-sample fit;
3. walk-forward;
4. Monte Carlo (trade reshuffling, permutation, noise);
5. 6–12 months of incubation;
6. small live allocation.

Carver avoids heavy optimization and keeps every idea in a fund-level backtest. The full academic stack (CPCV + PBO + DSR with ONC + StepM) is rarely used by retail traders, but an automated factory is exactly where it pays off, because trial counts are huge and logging is free.

### Cited Findings
- Davey's book covers the full path "from the idea to strategy creation, walk-forward testing, incubation, and eventually" live trading — [Goodreads](https://www.goodreads.com/en/book/show/22675886-building-winning-algorithmic-trading-systems); [Wiley](https://www.wiley.com/en-us/building-winning-algorithmic-trading-systems-a-trader%27s-journey-from-data-mining-to-monte-carlo-simulation-to-live-trading-website-p-9781118778883)
- Davey's sequence: walk-forward ("walks forward through the data, ensuring each out-of-sample test reflects unseen conditions"), then Monte Carlo, then 6–12 months of no-money live monitoring — [AlgoAdvantage [secondary]](https://algoadvantage.substack.com/p/036-kevin-davey-part-i-its-all-about)
- Carver:
  - expanding-window fits, pooled across instruments, with few degrees of freedom;
  - keep every idea in a fund-level backtest, so dropped ideas are not hidden;
  - skeptical of 1-year walk-forward windows.
  — [Carver blog](https://qoppac.blogspot.com/2015/11/the-three-kinds-of-overfitting.html); [Better System Trader [secondary]](https://bettersystemtrader.com/026-robert-carver/)
- Masters: permutation tests instead of repeatedly reusing OOS data — [Better System Trader [secondary]](https://bettersystemtrader.com/185-how-to-avoid-creating-trading-strategies-that-degrade-quickly-timothy-masters/)
- Vendors aimed at retail data-miners (Build Alpha, StrategyQuant) build in MCPT, noise tests, "vs random" and WF, and acknowledge selection bias when mining thousands of strategies — [Build Alpha [secondary]](https://www.buildalpha.com/monte-carlo-permutation/); [StrategyQuant forum [secondary]](https://strategyquant.com/forum/topic/monte-carlo-permutation-test-of-timothy-masters/)

### Inferences
**What is likely overkill for a factory:**
- running StepM *and* SPA *and* MCS on everything; one bootstrap family test per campaign is enough;
- full re-search permutation tests on every candidate (expensive), which should be reserved for finalists;
- exact ONC when hierarchical clustering on correlation gives a similar K_eff;
- CPCV for fixed-rule strategies with no fitted parameters, where simple sub-period splits plus PBO across the parameter grid cover it.

**What is *not* overkill for a factory:** a complete trial ledger, DSR with effective N, PBO per family, a single-use holdout, and cost-realistic simulation. These are cheap once automated, and they address the main risk.

### Gaps
- r/algotrading consensus was not sampled directly within the budget, so no direct forum citations are available.
- Ernie Chan's specific validation recommendations were not retrieved.

---

## 8. Open-source implementations (Python), status as of November 2026

### Takeaway
Usable, free building blocks exist:
- **skfolio**: CPCV, walk-forward, synthetic data; BSD-style, scikit-learn API;
- **purgedcv**: purged k-fold, embargo, CPCV paths, PSR/DSR, MinBTL, PBO;
- **pypbo**: PBO, PSR, MinTRL;
- **arch**: SPA/RealityCheck, StepM, MCS, block bootstraps;
- R **pbo**: reference CSCV implementation.

**mlfinlab** is commercial (£100/month per user). Its old open-source GitHub version is outdated.

### Cited Findings
- skfolio: `CombinatorialPurgedCV`, `WalkForward`, `MultipleRandomizedCV`, `optimal_folds_number`, `SyntheticData` — [skfolio](https://skfolio.org/); [API](https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html)
- purgedcv: `PurgedKFold`, `apply_embargo`, `reconstruct_paths`, `minimum_backtest_length`, plus DSR/PSR and a PBO audit notebook — [GitHub](https://github.com/eslazarev/purged-cross-validation)
- pypbo: PBO, PSR, MinTRL — [GitHub](https://github.com/esvhd/pypbo)
- arch: SPA, StepM, MCS; stationary, circular and moving-block bootstraps — [docs](https://bashtage.github.io/arch/multiple-comparison/multiple-comparison_examples.html); [GitHub](https://github.com/bashtage/arch)
- R pbo (CRAN) — [README](https://cran.r-project.org/web/packages/pbo/readme/README.html)
- mlfinlab is priced at "£100 (+VAT) per month, per user" — [Hudson & Thames](https://hudsonthames.org/mlfinlab/)
- "much of the content has moved to a subscription model" — [r/algoprojects [secondary]](https://www.reddit.com/r/algoprojects/comments/1h315jy/mlfinlab_open_source_library_maintained_by_hudson/)
- The GitHub repo still exists — [GitHub hudson-and-thames/mlfinlab](https://github.com/hudson-and-thames/mlfinlab)
- Finance Toolkit includes MinTRL and probabilistic Sharpe — [Finance Toolkit](https://www.jeroenbouma.com/projects/financetoolkit/docs/performance/minimum-track-record-length)
- GitHub topic "backtest-overfitting" lists 16 repositories (DSR, PBO, permutation-test tools of varying maturity) — [GitHub topics](https://github.com/topics/backtest-overfitting)
- `timeseriescv` (purged / combinatorial CV) was named in the brief but **not verified in this session**; see Gaps.

### Inferences
- Recommended stack:
  - skfolio or purgedcv for splitting;
  - an in-house PBO/DSR module (about 200 lines, using pypbo and purgedcv as references; vendoring them is low risk);
  - arch for SPA/StepM;
  - a custom permutation harness tied to the factory's backtest engine.
- Avoid depending on mlfinlab because of its licence.

### Gaps
- Licences and last-commit dates for pypbo, purgedcv and timeseriescv were not checked.
- The claimed arch SPA studentization bug needs checking against current arch source.

---

## 9. Recommended end-to-end validation pipeline order (synthesis)

### Takeaway
The order below is assembled from the primary and practitioner sources above. It is a synthesis; no single source prescribes it exactly. The principle: cheap, high-rejection filters first; statistics computed on the **complete trial ledger**; data that has never been looked at kept for last; incubation treated as an implementation and consistency check rather than proof of skill.

### Cited Findings (supporting each stage)
- **Stage 0 – Pre-registration and data hygiene.** Record the hypothesis, parameter grid and trial count before running. CSCV and DSR require *all* trials to be reported; omissions understate overfitting — [Bailey et al. PBO](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf). Keep a fund-level ledger of every idea — [Carver](https://qoppac.blogspot.com/2015/11/the-three-kinds-of-overfitting.html)
- **Stage 1 – Hold back a final holdout once**, touched once only — [Masters [secondary]](https://bettersystemtrader.com/185-how-to-avoid-creating-trading-strategies-that-degrade-quickly-timothy-masters/)
- **Stage 2 – Development-set search with a trial budget sized by MinBTL** — [MinBTL [secondary]](https://quantmemo.com/concepts/minimum-backtest-length); restrict degrees of freedom — [Carver](https://qoppac.blogspot.com/2015/11/the-three-kinds-of-overfitting.html)
- **Stage 3 – OOS estimation via purged/embargoed CV or CPCV**, giving a distribution of path Sharpes — [Arian et al.](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4778909); [skfolio](https://skfolio.org/user_guide/model_selection.html). Expanding-window WF is an acceptable simpler option — [Carver](https://qoppac.blogspot.com/2015/11/the-three-kinds-of-overfitting.html)
- **Stage 4 – Family-level overfitting check: PBO via CSCV** on the T×N trial matrix — [Bailey et al.](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
- **Stage 5 – Candidate-level significance: DSR with effective N from clustering** — [López de Prado 2019](https://www.aqr.com/-/media/AQR/Documents/Journal-Articles/JFDS_Winter2019_A-Data-Science-Solution-to-Multiple-Testing-Crisis---Lopez_de_Prado.pdf?sc_lang=en). Optionally add a bootstrap SPA/StepM across survivors against a benchmark (cash or buy-and-hold) — [Romano & Wolf](https://econ-papers.upf.edu/papers/712.pdf); [arch](https://bashtage.github.io/arch/multiple-comparison/multiple-comparison_examples.html). Or apply the HLZ-style t > 3 hurdle as a quick filter — [HLZ](https://www.nber.org/system/files/working_papers/w20592/w20592.pdf)
- **Stage 6 – Robustness**: parameter-neighbourhood stability, noise injection, Monte Carlo permutation (including re-optimization for finalists), regime and sub-period splits, cross-instrument transfer — [Build Alpha [secondary]](https://www.buildalpha.com/monte-carlo-permutation/); [Masters](https://timothymasters.info/market-trading)
- **Stage 7 – Single-look holdout test.** Pass or fail, with no iteration — [Masters [secondary]](https://bettersystemtrader.com/185-how-to-avoid-creating-trading-strategies-that-degrade-quickly-timothy-masters/)
- **Stage 8 – Incubation (paper or tiny live) for 6–12 months**, checking implementation and distributional consistency — [Davey [secondary]](https://algoadvantage.substack.com/p/036-kevin-davey-part-i-its-all-about). Statistical confirmation via MinTRL takes years at SR ≈ 1 — [portfolio-lab [secondary]](https://portfolio-lab.net/knowledge/deflated-sharpe-ratio)
- **Stage 9 – Live with small capital, sequential monitoring and kill-switches.** Keep updating PSR as the live track record grows — [PSR/MinTRL sources above](https://portfoliooptimizer.io/blog/the-probabilistic-sharpe-ratio-bias-adjustment-confidence-intervals-hypothesis-testing-and-minimum-track-record-length)

### Inferences
- **Order rationale for automation:**
  - Stages 2–5 run fully in batch on stored return matrices and are cheap.
  - Stage 6 permutation-with-re-optimization is costly and should run only on the top few percent.
  - Stage 7 must be enforced by the system: holdout data stays inaccessible to search code, access is logged, and there is one evaluation per candidate family.
- **Global multiple-testing ledger:** the factory's cumulative N grows forever. Either (a) refresh data (new markets, new time periods) to restore untouched holdouts, or (b) keep raising the DSR hurdle as K_eff grows. Otherwise the False Strategy Theorem guarantees false positives eventually.
- Backtest correctness (costs, look-ahead, survivorship) must be validated *before* any of these statistics, because "a leaked backtest deflates beautifully and is still fiction" — [thequant.space [secondary]](https://thequant.space/tools/deflated-sharpe-calculator); [Bailey et al.](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)

### Gaps
- No single primary source prescribes this exact ordering; it is a synthesis.
- No empirical study was found that measures the false-discovery rate of a full multi-stage funnel like this one.
