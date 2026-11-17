"""The gate: four coded checks, plus evidence reported for judgement."""
from __future__ import annotations

import json

import numpy as np

from . import CONFIG, GATE
from . import backtest, stats, strategy as strat, trials
from .data import Bars, load as load_bars


def evaluate(strategy: str | strat.Strategy, bars: Bars | None = None) -> dict:
    s = strat.load(strategy) if isinstance(strategy, str) else strategy
    if not s.chosen:
        raise ValueError("params.yaml has no 'chosen' parameters")
    spec = CONFIG["datasets"][s.dataset]
    ppy = spec["days_per_year"]
    bars = bars or load_bars(s.dataset, s.symbols)

    leaks = strat.leak_test(s, bars, s.chosen)
    trial, result = trials.evaluate(s, s.chosen, bars)
    daily = result.daily.to_numpy()

    # Judge what the strategy adds beyond holding the market, not raw return.
    bench = backtest.buy_and_hold(bars, s.dataset).daily.to_numpy()
    alpha, beta = stats.market_adjusted(daily, bench)

    # Every trial ever run on this dataset counts, grouped into distinct ideas.
    log = trials.read(s.dataset)
    matrix = np.array([stats.market_adjusted(r, bench)[0] for r in trials.returns_matrix(log)])
    labels = stats.cluster_trials(matrix, GATE["trial_cluster_correlation"])
    mine = labels[[t["id"] for t in log].index(trial["id"])]
    clusters = [matrix[labels == k].mean(axis=0) for k in np.unique(labels)]
    cluster_alpha = matrix[labels == mine].mean(axis=0)     # the idea, not its luckiest variant
    cluster_sharpes = np.array([stats.sharpe(c) for c in clusters])
    n_eff = len(clusters)
    var_sharpe = float(cluster_sharpes.var(ddof=1)) if n_eff > 1 else 0.0
    dsr = stats.deflated_sharpe(cluster_alpha, n_eff, var_sharpe)

    stressed = backtest.run(strat.compute(s, bars, s.chosen), bars, s.dataset, GATE["cost_stress_multiplier"], band=s.band)
    stressed_alpha = stats.market_adjusted(stressed.daily.to_numpy(), bench)[0]
    sr, bench_sr = stats.annual_sharpe(daily, ppy), stats.annual_sharpe(bench, ppy)

    checks = {
        "leak_test": {"pass": not leaks, "detail": leaks or "past decisions unchanged when the future is removed"},
        "deflated_sharpe": {
            "pass": bool(dsr >= GATE["deflated_sharpe_min"]), "value": round(dsr, 4), "min": GATE["deflated_sharpe_min"],
            "measured_on": "returns after removing market exposure",
            "measured_over": f"the average of the {int((labels == mine).sum())} logged trials that behave like this one",
            "market_adjusted_sharpe": round(stats.annual_sharpe(cluster_alpha, ppy), 2),
            "this_variant_market_adjusted_sharpe": round(stats.annual_sharpe(alpha, ppy), 2),
            "market_beta": round(beta, 2),
            "trials_logged": len(log), "distinct_ideas": n_eff,
            "sharpe_to_beat_by_luck": round(stats.expected_max_sharpe(n_eff, var_sharpe) * np.sqrt(ppy), 2),
        },
        "positive_at_stressed_costs": {
            "pass": bool(stressed_alpha.mean() > 0),
            "market_adjusted_return_per_year": round(float(stressed_alpha.mean() * ppy), 4),
            "cost_multiplier": GATE["cost_stress_multiplier"],
        },
        "never_liquidated": {"pass": not (result.liquidated or stressed.liquidated),
                             "uses_shorts_or_borrowing": result.margin},
        "beats_buy_and_hold": {"pass": bool(sr > bench_sr), "sharpe": round(sr, 2), "benchmark_sharpe": round(bench_sr, 2)},
    }

    own = [t for t in log if t["strategy"] == s.id and t["code_hash"] == s.code_hash]
    own_matrix = trials.returns_matrix(own)
    own_sharpes = sorted(t["sharpe"] for t in own)
    others = [t for t in log if t["strategy"] != s.id]
    closest = None
    if others and daily.std() > 0:
        corr = [(float(np.corrcoef(daily, trials.daily_returns(t))[0, 1]), t) for t in others
                if trials.daily_returns(t).std() > 0]
        if corr:
            c, t = max(corr, key=lambda x: x[0])
            closest = {"strategy": t["strategy"], "trial": t["id"], "correlation": round(c, 2)}

    out = {
        "strategy": s.id, "trial": trial["id"], "dataset": s.dataset, "params": s.chosen,
        "engine_version": CONFIG["engine_version"], "code_hash": s.code_hash,
        "pass": all(c["pass"] for c in checks.values()),
        "checks": checks,
        "evidence": {
            "sweep_overfitting_probability": (round(stats.pbo(own_matrix, GATE["pbo_blocks"]), 2)
                                              if len(own) >= 10 else "needs at least 10 trials of this strategy"),
            "sweep_trials": len(own),
            "sweep_sharpe_quartiles": [round(float(q), 2) for q in np.percentile(own_sharpes, [0, 25, 50, 75, 100])],
            "subperiod_sharpes": stats.subperiod_sharpes(daily, ppy),
            "max_drawdown": trial["max_drawdown"], "total_return": trial["total_return"],
            "orders": trial["orders"], "turnover_per_year": trial["turnover_per_year"],
            "cost_per_year": trial["cost_per_year"], "exposure": trial["exposure"],
            "average_weight_by_symbol": {k: round(float(v), 3) for k, v in
                                         strat.compute(s, bars, s.chosen).fillna(0.0).mean().items()},
            "closest_other_strategy": closest,
            "known_biases": "universe chosen with hindsight; cost model is assumed, not measured",
        },
    }
    path = trials.state_dir() / "gate" / f"{s.id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n")
    return out
