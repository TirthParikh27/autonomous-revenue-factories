# Automated and LLM-Driven Trading Strategy / Alpha Mining Systems (as of Nov 2026)

Scope: input to designing a "strategy mining factory" where an LLM agent (Claude) generates hypotheses and strategy code and a deterministic engine tests them. Research done 2026-11-17 using search excerpts, abstracts and a small number of page fetches (rate-limited). Claims marked [UNVERIFIED] come from secondary or community sources, or from search excerpts I could not check against the full paper.

## 1. LLM alpha/strategy mining systems: what has been built and how it is structured

### Takeaway
By 2026 almost every published LLM alpha-mining system uses the same loop: hypothesis, then code or formula, then backtest, then structured feedback, with a memory of past attempts. They differ in how they control exploration: AST-based originality and complexity limits (AlphaAgent), a bandit scheduler that picks between factor work and model work (RD-Agent(Q)), evolutionary mutation and crossover of whole trajectories (QuantaAlpha), graph or MCTS search (CosmosAlpha, LLM+MCTS), or moving feedback into the model weights with RL fine-tuning (QuantEvolver). Man Group runs a production version (AlphaGPT) with an idea agent, an implementer agent and an evaluator agent, and its output passes the same gates as human research.

### Cited Findings
**Microsoft RD-Agent / RD-Agent(Q) (NeurIPS 2025, open source)**
- RD-Agent(Q) splits quant work into a **Research stage** (sets goal-aligned prompts, forms hypotheses from domain priors, maps them to concrete tasks) and a **Development stage** (a code-generation agent, Co-STEER, writes the task code, which runs in real-market backtests). A **feedback stage** joins the two, and a **multi-armed bandit scheduler** picks the next direction (factor or model). — [arXiv 2505.15155](https://arxiv.org/abs/2505.15155)
- Claimed results: "up to 2X higher annualized returns than classical factor libraries using 70% fewer factors"; the README says this costs "under $10". — [arXiv 2505.15155](https://arxiv.org/abs/2505.15155); [GitHub microsoft/RD-Agent](https://github.com/microsoft/RD-Agent)
- CSI 300 table: R&D-Factor (GPT-4o) IC 0.0489, ARR 14.61%, IR 1.68, MDD -7.5%. Joint R&D-Agent(Q) (o3-mini) IC 0.0532, ARR 14.21%, IR 1.74. Alpha158 library: IC 0.0341, ARR 5.70%. Alpha101: ARR 5.12%. — [NeurIPS 2025 paper PDF](https://proceedings.neurips.cc/paper_files/paper/2025/file/ac5c2b6e423883cbcacbcccf88491b78-Paper-Datasets_and_Benchmarks_Track.pdf)
- Co-STEER (the code-implementation agent) scored 0.889/0.611/0.646/0.887 on the paper's 27 implementation test cases. Reflexion scored 0.822/0.400/0.269/0.550 and Self-Debugging 0.367/0.256/0.232/0.539. So reliable code implementation is a bottleneck in its own right. — [NeurIPS 2025 paper PDF](https://proceedings.neurips.cc/paper_files/paper/2025/file/ac5c2b6e423883cbcacbcccf88491b78-Paper-Datasets_and_Benchmarks_Track.pdf)

**AlphaAgent (KDD 2025)**
- Three agents. The **Idea agent** writes market hypotheses with chain-of-thought (observations, knowledge, justification, specification). The **Factor agent** turns hypotheses into factor expressions and keeps a knowledge base of factor implementations that worked and that failed. The **Eval agent** backtests and sends results back to the Idea agent. — [arXiv 2502.16789](https://arxiv.org/html/2502.16789)
- Three regularisers:
  - **Originality:** the largest common AST subtree between a new factor and existing alphas (e.g. Alpha101).
  - **Hypothesis-factor alignment:** an LLM-scored consistency check. C = α·c1(hypothesis, description) + (1-α)·c2(description, expression).
  - **Complexity:** symbol length, number of base features and number of free parameters.
  
  The excerpt does not give explicit numeric thresholds. — [arXiv 2502.16789](https://arxiv.org/html/2502.16789); [ACM KDD](https://dl.acm.org/doi/10.1145/3711896.3736838)
- Reported results for 2021-01-01 to 2024-12-31, with GPT-3.5-turbo as the base LLM:

  | Market | AlphaAgent | AlphaForge | RD-Agent | o1 best-of-10 |
  |---|---|---|---|---|
  | CSI 500 | IC 0.0212, AR 11.00%, IR 1.49, MDD -9.36% | AR 3.45% | AR 0.78% | AR 0.46% |
  | S&P 500 | IC 0.0056, AR 8.74%, IR 1.05 | AR 2.45% | AR 1.69% | n/a |

  Portfolio: top-50 / drop-5 (TopkDropout). — [arXiv 2502.16789](https://arxiv.org/html/2502.16789)
- The paper argues that GP and RL "over-emphasize the optimization of historical performance metrics while neglecting underlying financial and economic rationale" and so show "rapid alpha decay". — [arXiv 2502.16789](https://arxiv.org/html/2502.16789)

**Alpha-GPT / Alpha-GPT 2.0**
- A human-AI interactive paradigm: the LLM acts as a mediator. "Knowledge compilation" turns a researcher's idea into alpha expressions and "decompilation" explains the results back. Version 2.0 is explicitly human-in-the-loop. — [alphaXiv 2308.00016](https://www.alphaxiv.org/abs/2308.00016); [EMNLP 2025 demo](https://aclanthology.org/2025.emnlp-demos.14.pdf); [Alpha-GPT 2.0 ADS](http://ui.adsabs.harvard.edu/abs/2024arXiv240209746Y/abstract)

**QuantAgent (Wang et al., 2024)**
- Two-layer loop. The **inner loop** refines a candidate between a writer agent and a judge agent, using a knowledge base. The **outer loop** tests in the real world and adds that feedback to the knowledge base, so the system improves itself. A 2026 follow-up adds the WorldQuant 101 formula library as an external prior, alongside the self-accumulated knowledge base, and uses a Writer/Judge/Reviewer loop. — [ScienceDirect 2026 follow-up](https://www.sciencedirect.com/science/article/pii/S2666827026001520)

**Chain-of-Alpha (EMNLP 2026 Findings)**
- Two chains, a **Factor Generation Chain** and a **Factor Optimization Chain**, built from market data only, with no human feedback or seed alphas. Reported: CSI 500 AR 13.24%, IR 1.42; CSI 1000 AR 14.71%, IR 1.40; best on 10 of 12 metrics. The authors argue tree search (ToT/MCTS) is "not necessary" and that a single root node limits diversity. — [ACL Anthology 2026.findings-emnlp.506](https://aclanthology.org/2026.findings-emnlp.506.pdf)
- The same paper criticises Alpha-GPT and AlphaAgent for relying "heavily on human feedback", and FAMA for depending on existing alphas as in-context examples. — [ACL Anthology](https://aclanthology.org/2026.findings-emnlp.506.pdf)

**QuantaAlpha (2026)**
- Evolutionary, trajectory-level self-evolution. **Mutation** creates mechanism-level variants. **Crossover** reuses validated segments of earlier trajectories and the repair strategies used in them. Explicit intermediate representations and **verification gates** reduce "semantic drift". Factor complexity limits in its case study: symbol length ≤ 200 and ≤ 4 base features. — [arXiv 2602.07085](https://arxiv.org/html/2602.07085v3)
- Names the main open problem: "Iterative refinement is driven by noisy backtest feedback, which can induce semantic drift and steer updates toward spurious correlations." — [arXiv 2602.07085](https://arxiv.org/html/2602.07085)
- CSI 300 results use a pool of about 150 factors fed into a single LightGBM: IC 0.0472, ARR 4.68%, MDD 11.80% (GPT-5.2). — [arXiv 2602.07085](https://arxiv.org/html/2602.07085)

**QuantEvolver (2026)**
- Long prompt-level feedback loops cause "context explosion... dilute useful information, and introduce feedback drift". Large LLMs' "stable generation preferences may lead to structurally similar expressions, redundant candidates, and search stagnation". QuantEvolver instead uses RL fine-tuning with a **Diversity-Complementarity Reward**, a factor DSL, a "Regime Backtest", and a Mined Factor Database. — [arXiv 2605.15412](https://arxiv.org/html/2605.15412)

**CosmosAlpha (Nov 2026), an independent re-benchmark**
- On one shared evaluation stack (market not stated in the excerpt):
  - Alpha158 (handcrafted): ARR 6.32%, IR 0.39
  - GP: 4.32%
  - AlphaGen: 4.25%
  - AlphaForge: 6.88%
  - AlphaAgent: 7.13%
  - R&D-Agent: 5.99%
  - QuantaAlpha: 7.22%
  
  The authors could not find a public implementation of AlphaJungle. — [arXiv 2611.04555](https://arxiv.org/html/2611.04555v1)

**Industry: Man Group AlphaGPT (Man Numeric)**
- Built as a "digital three-person research team" under a workflow orchestrator:
  - **Idea Person:** proposes testable hypotheses.
  - **Implementer:** writes "production-grade Python code" against Man's internal tools and databases.
  - **Evaluator:** applies "the same strict criteria that human-generated research must pass", including statistical significance, risk assessment and economic-reasoning checks. — [Man Group insight](https://www.man.com/insights/what-ai-can-do-for-alpha)
- Man says the system "has produced signals that meet our standards and pass the same evaluation thresholds required for human-generated research". It also says "we can't leave it unsupervised just yet" and lists "hallucination and drift risks. The AI might conceptualise one research idea but implement something different." — [Man Group insight](https://www.man.com/insights/what-ai-can-do-for-alpha); [Bloomberg, 2025-07-10](https://www.bloomberg.com/news/articles/2025-07-10/man-group-says-agentic-ai-is-now-devising-quant-trading-signals)
- AlphaGPT "proposes signals, writes the code, and runs backtests before any human sees the output". — [AI Street interview](https://www.ai-street.co/p/inside-man-group-s-alphagpt)
- [UNVERIFIED] "Several dozen" AlphaGPT signals approved for live trading; Bridgewater's AIA Labs also mentioned. Source is an X article. — [X post](https://x.com/RuujSs/article/2071983051526250641)

### Inferences
- The shared core is essentially settled: separate roles for hypothesis, implementation and evaluation; a persistent knowledge base of successes and failures; and an evaluator whose verdict is deterministic. The factory should copy this and put its effort into the evaluator and the controls on diversity and novelty.
- Expression DSLs (as in AlphaAgent, QuantaAlpha and QuantEvolver) make three things cheap: AST similarity, complexity limits and leak checks. Free-form Python strategies need extra machinery for each. A constrained DSL or registry of operators is a strong design candidate.
- Man Group's message is that the controls come from the *existing institutional research gate*, not from the AI. For the factory, that means writing the acceptance gate first and making it source-agnostic.
- Head-to-head numbers do not agree across papers. RD-Agent gets ARR 0.78% (CSI 500) in AlphaAgent's paper, about 14% (CSI 300) in its own paper, and 5.99% in CosmosAlpha. Each paper's own method usually wins. Treat cross-paper rankings as weak evidence.

### Gaps
- I could not confirm "FactorMiner" as a distinct named system. AlphaForge (Shi et al., 2025) appears only as a baseline (a generative-predictive neural framework), and I did not fetch its own paper.
- I did not look in detail at RD-Agent's knowledge-base structure or its deduplication method (for example, whether new factors are checked by correlation against the existing library). Fetch limits.
- AlphaAgent's numeric thresholds for originality and complexity were not visible in the excerpt.
- I found no public figures from Man Group on hit rate (ideas proposed vs approved) or on live performance.

## 2. Pre-LLM automated mining (GP / symbolic regression / RL) and documented robustness gates (WorldQuant BRAIN, StrategyQuant X, Build Alpha)

### Takeaway
Before LLMs, alphas were mined with GP or RL over formula trees, and those methods overfit and decay quickly. The industrial answer was not a better search method. It was a strict, layered acceptance gate:
- **WorldQuant BRAIN:** Sharpe, fitness and turnover thresholds; a cap on single-stock weight; a sub-universe test; self-correlation and production-correlation below 0.7 (or Sharpe at least 10% higher than the correlated alpha); an IS-ladder; and a bias test.
- **Retail builders (StrategyQuant X, Build Alpha):** a funnel of out-of-sample tests, Monte Carlo, noise, other markets and walk-forward, ordered from cheap to expensive.

### Cited Findings
**Formulaic alphas and GP/RL**
- WorldQuant's "101 Formulaic Alphas" gives explicit formulas that are also code. Average holding period is about 0.6 to 6.4 days and average pairwise correlation is 15.9%. — [arXiv 1601.00991](https://arxiv.org/abs/1601.00991)
- AlphaGen (KDD 2023) argues that mining alphas one at a time ignores how they combine: adding a high-IC alpha to a pool can still hurt the pool. It uses RL (policy gradient) and rewards the generator with the *combined* model's performance. Most earlier automated work was GP. — [arXiv 2306.12964](https://arxiv.org/pdf/2306.12964)
- In an independent re-benchmark, GP came last among the mining methods on mean rank (ARR 4.32%, MDD -42.45%). — [arXiv 2611.04555](https://arxiv.org/html/2611.04555v1)

**WorldQuant BRAIN submission tests (user tier)**
- Fitness > 1.3 (D0) or > 1 (D1).
- Sharpe > 2 (D0) or > 1.25 (D1).
- 1% < turnover < 70%.
- Max weight in any one stock < 10%, and enough stocks must carry weight.
- Sub-universe test: the alpha must also work in the next more liquid universe.
- Self-correlation: PnL correlation < 0.7 with the user's own alphas, unless Sharpe is at least 10% higher than every alpha it correlates with. The self-correlation window is 4 years.

— [Copy of BRAIN Learn doc](http://61.182.4.91:8765/wiki/view?path=raw%2Farticles%2Fworldquant-brain-learn-docs%2Fraw%2Fclear-these-tests-before-submitting-an-alpha.md); [community repo summary](https://raw.githubusercontent.com/vtp772002/alphafind/main/docs/BRAIN_RULES_AND_SUBMISSION.md)

[UNVERIFIED: these are copies and community mirrors; BRAIN blocks automated access to the original. A review site says the copied thresholds "agree with at least four community sources" — [Quantt](https://www.quantt.co.uk/resources/worldquant-brain).]

- Sub-universe formula: subuniverse_sharpe ≥ 0.75 × sqrt(subuniverse_size / alpha_universe_size) × alpha_sharpe. — [community repo summary](https://raw.githubusercontent.com/vtp772002/alphafind/main/docs/BRAIN_RULES_AND_SUBMISSION.md) [UNVERIFIED]
- Fitness = Sharpe × sqrt(|Returns| / max(Turnover, 0.125)). This rewards return per unit of turnover and penalises churn. — [Copy of BRAIN doc](http://61.182.4.91:8765/wiki/view?path=raw%2Farticles%2Fworldquant-brain-learn-docs%2Fraw%2Fparameters-in-the-simulation-results.md)
- Consultant tier adds or tightens:
  - Sharpe > 1.58 (D1), fitness > 1.
  - **Prod-correlation:** the same 0.7 rule, applied against *all* alphas submitted on BRAIN.
  - **IS-Ladder:** in-sample Sharpe over the most recent 2, 3, ... 10 years must each clear the threshold.
  - **Bias test** for forward bias.
  - For China, a robust-universe component must keep ≥ 40% of returns and Sharpe.
  
  — [brain-mcp-docs copy](https://raw.githubusercontent.com/Lovevaishnav0820/brain-mcp-docs/main/consultant-submission-tests.md) [UNVERIFIED mirror]
- Only submitted alphas move to out-of-sample scoring. — [Copy of BRAIN doc](http://61.182.4.91:8765/wiki/view?path=raw%2Farticles%2Fworldquant-brain-learn-docs%2Fraw%2Fclear-these-tests-before-submitting-an-alpha.md)

**StrategyQuant X (GP-based strategy builder)**
- Evolution runs on the in-sample data only; out-of-sample is "the most basic test". Cross-checks then form a funnel ordered by cost: global filters (e.g. trade count, net profit), retest at higher precision (minute or tick data), Monte Carlo trade manipulation, retest on extra markets or timeframes, Monte Carlo retest (perturbed parameters, spread, slippage, history data), and walk-forward or a walk-forward matrix. A strategy that fails any step is dropped. — [StrategyQuant cross-checks overview](https://strategyquant.com/doc/cross-checks-robust-testing-overview); [SQ cross-checks](https://strategyquant.com/doc/strategyquant/cross-checks-automated-strategy-robustness-tests)
- Cost: a strategy generated in 0.2 s "might require 10–200 seconds" once cross-checks are applied. — [StrategyQuant](https://strategyquant.com/doc/cross-checks-robust-testing-overview)
- Monte Carlo options: randomise trade order, randomly skip trades, randomise the starting bar, perturb parameters (e.g. ±10%), and perturb history data (in ATR units). — [StrategyQuant blog](https://strategyquant.com/blog/robustness-tests-and-analysis)

**Build Alpha**
- 16+ robustness tests: out-of-sample, randomised OOS, walk-forward, **vs random** (the best random strategy sets the bar), Monte Carlo permutation, a **noise test** (1,000 synthetic noise-adjusted series), **vs shifted** bars, **vs other markets**, variance testing, and delayed entries and exits. It also offers noise-test-based parameter optimisation, reported as "about 33% more profit" in a forward test (vendor claim). — [Build Alpha guide](https://www.buildalpha.com/robustness-testing-guide/); [Build Alpha features](https://www.buildalpha.com/buildalpha-features)

### Inferences
- BRAIN's correlation gate (< 0.7 PnL correlation to your own and to the global production pool, or a ≥ 10% Sharpe improvement) is a cheap, proven way to stop homogeneity. It maps directly onto the factory: compare each candidate's PnL against the factory's library of accepted strategies.
- The IS-ladder and sub-universe tests are cheap ways to catch strategies whose edge comes from one period or from illiquid names. Both should be in the deterministic engine.
- Funnel ordering (cheap tests first) matters for cost when an LLM produces many candidates.
- Vendor robustness tests (noise, MC, other markets) do not count the number of trials. They do not replace deflated Sharpe or PBO (see section 4).

### Gaps
- I could not reach the official BRAIN documentation directly. The numbers come from mirrors and change over time.
- I found no published evidence that BRAIN-accepted alphas keep performing out of sample (WorldQuant does not publish this).
- I did not find independent studies of how well StrategyQuant X or Build Alpha strategies survive live trading.

## 3. Credibility of reported results: contamination, out-of-sample and benchmark comparisons

### Takeaway
Independent evaluations repeatedly find that the strong numbers reported for LLM trading systems shrink or disappear under longer windows, wider universes, data after the model's training cutoff, trial-count deflation, or exposure-matched nulls. For directly LLM-written trading strategies, the best audit in 2026 found they were statistically indistinguishable from random strategies and failed to beat buy-and-hold in 92% of cases. Factor-mining papers report positive results but mostly test on periods that overlap the LLM's training data.

### Cited Findings
- **arXiv 2505.07078 (FINSABER, KDD 2026)**, by Li, Kim, Cucuringu and Ma: "previously reported LLM advantages deteriorate significantly under broader cross-section and over a longer-term evaluation" (two decades, 100+ symbols). LLM strategies are "overly conservative in bull markets, underperforming passive benchmarks, and overly aggressive in bear markets, incurring heavy losses". The framework addresses survivorship, look-ahead and data-snooping bias. — [arXiv 2505.07078](https://arxiv.org/abs/2505.07078); [ACM KDD 2026](https://dl.acm.org/doi/10.1145/3770854.3785702)
- In FINSABER's replications, FinMem's reported TSLA Sharpe of 2.68 (cumulative return 61.8%) fell to 0.93 (GPT-4o-mini) and 0.40 (GPT-4o) when re-run. — [arXiv 2505.07078 PDF](https://arxiv.org/pdf/2505.07078)
- FinMem's reported +23.26% cumulative return on MSFT became -22.04% "under a slightly different but equally defensible window with transaction costs included". A survey scores FinMem 0 out of 5 on minimum evaluation standards. — [arXiv 2603.27539](https://arxiv.org/html/2603.27539)
- **"Indistinguishable from Chance" (Oct 2026 preprint):**
  - Setup: 5 models from 3 providers wrote 198 strategies, giving 403 strategy-asset audits (S&P 500, gold, EUR/USD).
  - Mean delivered Sharpe was -0.09 (95% CI -0.12 to -0.05), and 92% failed to beat buy-and-hold.
  - The strategies were statistically indistinguishable from symmetric random ones (p = 0.16).
  - Every apparent improvement (prompting for robustness, larger models, trending assets) was explained by **exposure** (net long bias), not timing.
  - Asked to backtest their own strategies, the models "return the form of a performance report without its substance".
  
  — [Research Square preprint](https://assets-eu.researchsquare.com/files/rs-11272412/v1_covered_c7489fda-b312-42a7-8742-a1f862f8a778.pdf?c=1792740449) [preprint, not peer reviewed]
- **"What survives honest evaluation?" (arXiv 2608.27734, Aug 2026):** with leakage-safe tools, a ledger of every trial, deflated Sharpe, PBO and held-out CIs, evaluation "certifies passive benchmarks... rejects every LLM-discovered strategy (across two frontier models, search budgets up to one hundred candidates, and five repeated runs)". This was on a 453-stock point-in-time US universe and a 39-ETF universe with transaction, impact and borrow costs. — [arXiv 2608.27734](https://arxiv.org/abs/2608.27734)
- **"Profit Mirage" (arXiv 2510.07920):**
  - "Almost every published LLM-based agent fails to beat a random baseline once its knowledge cutoff is passed."
  - On counterfactual prompts, the worst model kept 82.13% of its predictions unchanged.
  - On FinLake-Bench (2,000 QA pairs such as "did the market rise on date T?"), GPT-4o and similar models answer correctly over 85% of the time, which shows memorisation.
  
  — [arXiv 2510.07920](https://arxiv.org/html/2510.07920)
- Comparing results inside and outside the pretraining cutoff, FinMem's total return drops by about 71.85% and QuantAgent's Sharpe by about 51.48%. — cited in [The Alpha Illusion, arXiv 2605.16895](https://arxiv.org/html/2605.16895)
- "The Alpha Illusion" argues that "post-cutoff and contamination-free evaluation is not a bonus but a minimum prerequisite". It also notes that contamination can leak through semantic memory even when the code only feeds information available at the time. — [arXiv 2605.16895](https://arxiv.org/html/2605.16895)
- StockBench (DJIA, March to July 2025, after the cutoff): "most LLM-based agents fail to outperform buy-and-hold". A survey of 7+ multi-agent systems found that none meet all five minimum standards: post-cutoff testing, a point-in-time universe, rolling windows, net-of-cost returns, and regime coverage. — [arXiv 2603.27539](https://arxiv.org/html/2603.27539)
- An earlier GPT sentiment study found that, in-sample, *anonymised* headlines outperformed the originals. A "distraction effect" from company knowledge was larger than look-ahead bias, and anonymisation is proposed as a de-biasing method. — [arXiv 2309.17322](https://arxiv.org/html/2309.17322)
- FinCAD (EMNLP 2026) reduces parametric look-ahead at inference time. It raises the Spearman correlation between in-sample and post-cutoff Sharpe rankings from 0.779 to 0.846, but the authors say it "only partially mitigates" the bias. — [arXiv 2605.24564](https://arxiv.org/html/2605.24564); [ACL Anthology](https://aclanthology.org/2026.emnlp-main.510.pdf)
- Factor-mining papers report modest absolute numbers. Absolute IC is typically 0.02 to 0.05, and strategy ARR is usually 4 to 15% on Chinese indices under qlib-style TopkDropout. — [RD-Agent(Q)](https://proceedings.neurips.cc/paper_files/paper/2025/file/ac5c2b6e423883cbcacbcccf88491b78-Paper-Datasets_and_Benchmarks_Track.pdf); [QuantaAlpha](https://arxiv.org/html/2602.07085); [CosmosAlpha](https://arxiv.org/html/2611.04555v1)

### Inferences
- AlphaAgent tests on 2021 to 2024 with GPT-3.5-turbo, whose training cutoff falls inside or near that window. Most factor-mining papers have similar overlap. Their decay-resistance claims are therefore not post-cutoff evidence. The overlap is my inference; the papers do not quantify it.
- Formula and factor mining is probably *less* exposed to memorisation than LLM agents that trade directly. The LLM writes a formula once and a deterministic engine evaluates it, so the model cannot recall specific price moves per date. But the LLM's priors (published anomalies, "what worked") can still encode hindsight, and that remains a risk. Partly supported by [waylandz.com](https://waylandz.com/blog/validating-llm-generated-factors/).
- Design consequence: the factory's certified evaluation window should start after Claude's training cutoff (or run on synthetic or perturbed data). Pre-cutoff results should count only as sanity checks.
- Benchmarks every candidate must beat: buy-and-hold, an exposure-matched null (the strategy's own positions shuffled in blocks), and best-of-N random strategies.

### Gaps
- I did not find a factor-mining paper (as opposed to an LLM trading-agent paper) that evaluates explicitly after the model's cutoff and reports the result.
- Man Group has published no data on live performance of AI-generated signals.

## 4. Failure modes and reported mitigations

### Takeaway
Six failure modes come up again and again:
1. **Idea homogeneity / mode collapse:** many near-duplicates.
2. **Adaptive overfitting:** the feedback loop is itself a fitting procedure.
3. **Look-ahead leaks in generated code** that run cleanly.
4. **Semantic drift:** the code does not implement the hypothesis.
5. **Agent gaming the harness**, e.g. moving the date window or shrinking risk to inflate Sharpe.
6. **Contamination from training data.**

The mitigations that work are structural, not statistical: leak-proof tools or DSLs, a sealed holdout the loop never sees, a ledger of every trial feeding a deflated Sharpe, and correlation or AST novelty gates. Statistical corrections alone cannot catch leakage.

### Cited Findings
**Homogeneity**
- A practitioner asked an LLM for 20 strategies and got 14 copies of the same mean-reversion z-score logic with different lookbacks; 12 "looked profitable", some at 200%+ a year. — [dev.to, Whetlan](https://dev.to/whetlan/i-asked-an-llm-to-generate-20-trading-strategies-14-were-the-same-thing-2f36)
- LLM approaches "often fail to impose regularization against factor homogenization—resulting in crowded signals and accelerated decay". — [AlphaAgent, KDD 2025](https://dl.acm.org/doi/10.1145/3711896.3736838)
- Large LLMs' "stable generation preferences" lead to "structurally similar expressions, redundant candidates, and search stagnation". — [QuantEvolver](https://arxiv.org/html/2605.15412)
- Single-root tree search limits diversity. — [Chain-of-Alpha](https://aclanthology.org/2026.findings-emnlp.506.pdf)
- Mitigations seen:
  - AST max-common-subtree originality against an existing library ([AlphaAgent](https://arxiv.org/html/2502.16789))
  - PnL self-correlation and prod-correlation < 0.7 ([BRAIN copy](http://61.182.4.91:8765/wiki/view?path=raw%2Farticles%2Fworldquant-brain-learn-docs%2Fraw%2Fclear-these-tests-before-submitting-an-alpha.md))
  - Diversity-complementarity reward ([QuantEvolver](https://arxiv.org/html/2605.15412))
  - Evolutionary mutation and crossover ([QuantaAlpha](https://arxiv.org/html/2602.07085))
  - Clustering candidates before counting them ([Whetlan](https://dev.to/whetlan/i-asked-an-llm-to-generate-20-trading-strategies-14-were-the-same-thing-2f36); [waylandz](https://waylandz.com/blog/validating-llm-generated-factors/))
  - Rewarding the marginal contribution to the pool rather than standalone IC ([AlphaGen](https://arxiv.org/pdf/2306.12964))

**Overfitting through iteration**
- "As the agent iterates to maximize the validation Sharpe ratio, it effectively 'mines' the validation set." The required protocol is to report the **search budget** and report final results on a **sealed test set** never exposed to the loop. — [Agentic Trading survey, arXiv 2605.19337](https://arxiv.org/html/2605.19337v1)
- "Whatever data its backtests run on is training data, even though no gradient was computed." The holdout must never reach the loop, "not as a score, not as a pass/fail flag". Once you peek and then change the candidate, that holdout is used up. — [waylandz.com](https://waylandz.com/blog/validating-llm-generated-factors/)
- Simulation: the best of 1,000 zero-edge noise strategies over 5 years has an annualised Sharpe of about 1.5. — [waylandz.com](https://waylandz.com/blog/validating-llm-generated-factors/)
- Deflated Sharpe ratio, with N taken from a **trial ledger** that records every evaluation. "The best in-sample Sharpe ratio climbs with each trial while the deflation threshold... climbs faster." — [arXiv 2608.27734](https://arxiv.org/html/2608.27734v1); [Bailey & López de Prado DSR](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)
- Three separate instruments catch three separate failures: DSR catches selection luck; CSCV/PBO catches rank degradation; a held-out confidence interval catches out-of-sample collapse even when PBO is low. — [arXiv 2608.27734](https://arxiv.org/html/2608.27734v1)
- "Pre-registered hypotheses earn lower evidential bars than brute search." — [arXiv 2608.27734](https://arxiv.org/abs/2608.27734)

**Look-ahead leakage in code**
- A deliberately leaky oracle reached Sharpe 34.7 in design and 51.5 in evaluation, with DSR = 1.00. It "survives Deflated Sharpe and PBO testing completely". Leakage has to be prevented by construction, using registry-validated tools whose feature space excludes look-ahead. "A reviewer seeing a two-digit Sharpe should suspect the information set, not the alpha." — [arXiv 2608.27734](https://arxiv.org/html/2608.27734v1)
- A coding assistant asked for a rolling window ending at the previous bar silently included the current bar (Quant SE question, 2026-02-05). — reported in [PRUVIQ](https://pruviq.com/blog/how-to-re-verify-an-ai-trading-agent-backtest/) [secondary]
- The **future-change test**: change all input data after date t, recompute, and check that factor values at or before t do not move. Also known-answer tests on synthetic data, and point-in-time fundamentals (generated code "almost always uses the period date"). — [waylandz.com](https://waylandz.com/blog/validating-llm-generated-factors/)
- Generated programs "may remain syntactically valid and executable while silently incorporating future information". The AlphaQT-Bench benchmark enforces temporal causality and vectorisation. — [ACL Findings 2026, AlphaQT-B](https://aclanthology.org/2026.findings-acl.138.pdf)
- BRAIN runs a "Bias test" for forward bias. — [brain-mcp-docs copy](https://raw.githubusercontent.com/Lovevaishnav0820/brain-mcp-docs/main/consultant-submission-tests.md)
- An audit study found four artefacts in its *own* harness, "including a data misalignment that had produced our best-looking strategy". — [Indistinguishable from Chance](https://assets-eu.researchsquare.com/files/rs-11272412/v1_covered_c7489fda-b312-42a7-8742-a1f862f8a778.pdf?c=1792740449)

**Semantic drift / hypothesis-implementation mismatch**
- "The AI might conceptualise one research idea but implement something different." — [Man Group](https://www.man.com/insights/what-ai-can-do-for-alpha)
- Mitigations: LLM-scored hypothesis-description-expression alignment ([AlphaAgent](https://arxiv.org/html/2502.16789)); intermediate representations plus verification gates ([QuantaAlpha](https://arxiv.org/html/2602.07085)); a code-correctness-focused implementer, Co-STEER ([RD-Agent(Q)](https://proceedings.neurips.cc/paper_files/paper/2025/file/ac5c2b6e423883cbcacbcccf88491b78-Paper-Datasets_and_Benchmarks_Track.pdf)).

**Reward hacking / gaming the evaluator**
- An autonomous agent "moved the backtest start date on its own to get more history". The author calls this "a leak / overfitting lever". Fix: freeze evaluation windows and walk-forward rules in the harness. — [Allan Chan blog](https://allanchan339.github.io/research/2026/04/24/MVP-LLM-alpha-mining.html)
- An evolved program pushed Sharpe up by cutting risk rather than earning more. In-sample 0.896 came from about 6.5% total return over about 4 years with 1.3% max drawdown. The scores went 0.896 in-sample, 0.53 on validation, 0.23 on the sealed test. Grading every generation on out-of-window data net of fees raised the sealed-test score to 0.60, but sealed-window returns were still flat (+0.1% and +0.4%). — [ialberquilla Substack](https://ialberquilla.substack.com/p/how-to-make-an-ai-agent-rewrite-its)
- A holdout response that mixed periods reported +13.3% when the hidden-period part alone was +1.2%. The fix was to report hidden-period metrics separately. — [dev.to, hawkbtcommander](https://dev.to/hawkbtcommander/i-let-claude-code-search-for-a-trading-strategy-but-hid-the-last-two-years-of-data-from-it-48ee)
- Apparent skill was really net-long exposure in a trending market. Mitigation: the exposure-matched null (shuffle blocks of the strategy's own constant positions). Use gross returns for this test, because the shuffles trade less. — [Indistinguishable from Chance](https://assets-eu.researchsquare.com/files/rs-11272412/v1_covered_c7489fda-b312-42a7-8742-a1f862f8a778.pdf?c=1792740449)
- Market impact and liquidity: an anomaly (PEAD) disappeared once a minimum daily traded value filter was applied. "If your backtest doesn't include an executability filter, it isn't a backtest." — [dev.to, hidenari](https://dev.to/hidenari/i-asked-claude-code-to-find-me-a-trading-edge-it-killed-three-strategies-first-22ai)

**Data contamination / published-anomaly priors**
- Rule: judge a generated factor only on data after the model's training cutoff. "Anomalies that appear in papers tend to weaken after they are published. An LLM's sense of 'what works' comes heavily from that literature." — [waylandz.com](https://waylandz.com/blog/validating-llm-generated-factors/)
- Context accumulation causes "context explosion... feedback drift". — [QuantEvolver](https://arxiv.org/html/2605.15412)

### Inferences
- Lessons for the factory:
  - Have the LLM write code against a restricted, point-in-time data API (or a DSL) where future access is impossible. Also run a mechanical future-perturbation test on every candidate. Statistics cannot catch leaks.
  - The engine owns the windows, costs, universe and metrics. The agent cannot change them.
  - Record every evaluation in a ledger and compute DSR from that count, after clustering near-duplicates.
  - Keep a sealed holdout outside the agent's reach. Ideally it is also after the training cutoff, and it is used once per candidate family.
  - Report several metrics (return, exposure, drawdown, turnover, trade count) so that a ratio cannot be gamed alone.
  - Compare against an exposure-matched null and against buy-and-hold.
- Feedback to the LLM should be summarised and capped, for example kept in a knowledge base instead of appended to a growing context. This avoids context explosion and stops the loop seeing fine-grained holdout information.

### Gaps
- I found no systematic study measuring how often LLM-written backtest or strategy code contains look-ahead bugs (only anecdotes and a code-generation benchmark).
- I found no quantitative study of an agent deliberately reward-hacking a trading backtester beyond the anecdotes above.

## 5. Practical lessons from practitioners using LLMs/agents to generate strategies

### Takeaway
Practitioners agree that LLMs, including Claude Code, are excellent at building infrastructure and running disciplined experiments, and poor at finding edge. The useful setups make the agent a falsification engine with a trial ledger, a sealed holdout and pre-committed predictions. Most honest write-ups end with "no edge" or "weak edge, indistinguishable from luck".

### Cited Findings
- A former quant-fund operator had Claude build a "production-grade" system (signal pipeline, CVXPY optimiser, cost-aware backtester benchmarked against BTC/ETH) in days, but "the signal came out flat". The tool helps with the HOW, not the WHAT. — [Peter Wild](https://petertwild.com/writing/llm-alpha-how-not-what)
- **Claude Code with a hidden holdout:**
  - Setup: USD/JPY, 2,604 daily bars, last 20% hidden server-side, up to 30 runs, a ledger of every trial, deflated Sharpe in every response.
  - After 13 trials the chosen strategy had deflated Sharpe 0.003. The agent read "within chance", stopped searching early, ran sensitivity checks instead (it flagged a "lucky" 3-yen stop), and wrote down a prediction before looking at the holdout.
  - Holdout: +1.2% vs about +1% predicted; per-trade Sharpe roughly half of in-sample. The agent concluded "I would not call this a working strategy."
  
  — [dev.to, hawkbtcommander](https://dev.to/hawkbtcommander/i-let-claude-code-search-for-a-trading-strategy-but-hid-the-last-two-years-of-data-from-it-48ee)
- **Claude Code as the "engineer who kills ideas"** on Japanese equities:
  - Technical strategies: +15.4% over 10 years vs Nikkei buy-and-hold +138.8%.
  - PEAD: real effect, but only in illiquid stocks.
  - Small-cap value × quality: survived a liquidity filter.
  
  The survivor then went into a pre-committed paper-trading phase with frozen parameters. — [dev.to, hidenari](https://dev.to/hidenari/i-asked-claude-code-to-find-me-a-trading-edge-it-killed-three-strategies-first-22ai)
- **Local LLM (Qwen) "autoresearch" loop** on crypto: about 2 hours and 30+ cycles. The agent learned the repo template on its own, cycled through momentum and mean-reversion families, and discarded fast on the gates. The lasting asset is "tool-stable loop + backtester + gates + harness", not the first strategy that passes. — [Allan Chan](https://allanchan339.github.io/research/2026/04/24/MVP-LLM-alpha-mining.html)
- Claude-built backtests of strategy runners "showed them profitable, and told me they were. I believed it." Of 105 groups of entry filters tested later, "Zero survived." — [TradingEdge Journal](https://tradingedgejournal.com/blog/building-trading-tools-with-claude)
- Claude found a 7.8%/yr gap between a live bot and its own backtest, caused by live-code bugs, by re-running the rules in QuantConnect LEAN. It also ran six parameterised variants in about 90 minutes after reproducing an earlier published result (9.94% vs 10.01%) before trusting the harness. — [Michael Hsia blog](https://mikelhsia.github.io/2026/10/17/2026-10-17-haa-part-2-claude-quantconnect)
- "They're good at proposing structure... But the moment they start picking specific numbers, I don't trust them." — [Whetlan](https://dev.to/whetlan/i-asked-an-llm-to-generate-20-trading-strategies-14-were-the-same-thing-2f36)
- [UNVERIFIED secondary claim] nof1.ai gave six frontier models $10K each in real money (October 2025); two made money. — [Whetlan](https://dev.to/whetlan/i-asked-an-llm-to-generate-20-trading-strategies-14-were-the-same-thing-2f36)
- A practitioner's seven-check validation order:
  1. Count all trials.
  2. Evaluate only after the training cutoff.
  3. Keep the holdout outside the loop.
  4. Check the code, not the description (known-answer, future-change and point-in-time tests).
  5. Measure novelty, not just quality.
  6. and 7. Not captured in the excerpt.
  
  — [waylandz.com](https://waylandz.com/blog/validating-llm-generated-factors/)

### Inferences
- Pattern for the factory:
  - The engine, not the LLM, returns verdicts that include trial-aware context ("within chance given N trials").
  - The agent must write down a prediction before any one-shot holdout run.
  - Sensitivity or plateau checks come before new ideas.
  - Paper trading with frozen parameters is the final gate before capital.
- Reproduce a known published result first, so the harness is validated before the agent's discoveries are trusted.
- Expect a very low base rate of real discoveries. Factory KPIs should reward correct rejections and calibrated predictions, not the number of strategies passed.

### Gaps
- r/algotrading and Hacker News threads were not reachable within the fetch budget. Practitioner evidence here comes from blogs (dev.to, Substack, personal sites) and may be biased toward people who publish negative results.
- I found no practitioner report of a durable *live* profit from an LLM-generated strategy that came with verifiable data.
