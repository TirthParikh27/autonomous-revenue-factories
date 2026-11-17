"""Statistics the gate uses. Implemented from the primary papers and cross-checked
against purgedcv in tests.

Deflated Sharpe ratio: Bailey and Lopez de Prado (2014), "The Deflated Sharpe Ratio".
Probability of backtest overfitting: Bailey, Borwein, Lopez de Prado and Zhu (2017).
Counting trials: after Lopez de Prado (2019). Trials are clustered by return
correlation, each cluster counts as one idea and is judged on the average of
its members, so picking the luckiest of many near-identical variants gains
nothing. Hierarchical clustering stands in for his ONC algorithm.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from scipy.stats import kurtosis, norm, rankdata, skew

EULER = 0.5772156649015329


def sharpe(r: np.ndarray) -> float:
    """Per-period Sharpe ratio (not annualised)."""
    sd = r.std(ddof=1)
    return float(r.mean() / sd) if sd > 0 else 0.0


def annual_sharpe(r: np.ndarray, periods_per_year: float) -> float:
    return sharpe(r) * float(np.sqrt(periods_per_year))


def max_drawdown(r: np.ndarray) -> float:
    equity = np.cumprod(1.0 + r)
    return float((equity / np.maximum.accumulate(equity) - 1.0).min())


def describe(r: np.ndarray, periods_per_year: float) -> dict:
    """Plain descriptions of a daily return series. Evidence for a reader, never a pass mark."""
    equity = np.cumprod(1.0 + r)
    under = equity < np.maximum.accumulate(equity)
    longest = run = 0
    for u in under:
        run = run + 1 if u else 0
        longest = max(longest, run)
    sd = r.std(ddof=1)
    return {
        "annual_return": round(float(equity[-1] ** (periods_per_year / len(r)) - 1), 4) if equity[-1] > 0 else -1.0,
        "annual_volatility": round(float(sd * np.sqrt(periods_per_year)), 4),
        "skew": round(float(((r - r.mean()) ** 3).mean() / r.std() ** 3), 2) if sd > 0 else 0.0,
        "worst_day": round(float(r.min()), 4),
        "longest_drawdown_days": int(longest),
    }


def expected_max_sharpe(n_trials: float, var_sharpe: float) -> float:
    """Best per-period Sharpe expected from n zero-skill trials (False Strategy Theorem)."""
    if n_trials <= 1 or var_sharpe <= 0:
        return 0.0
    z = (1 - EULER) * norm.ppf(1 - 1 / n_trials) + EULER * norm.ppf(1 - 1 / (n_trials * np.e))
    return float(np.sqrt(var_sharpe) * z)


def probabilistic_sharpe(r: np.ndarray, benchmark: float) -> float:
    """Probability that the true per-period Sharpe exceeds the benchmark."""
    s, n = sharpe(r), len(r)
    denom = np.sqrt(max(1e-12, 1 - skew(r) * s + (kurtosis(r, fisher=False) - 1) / 4 * s * s))
    return float(norm.cdf((s - benchmark) * np.sqrt(n - 1) / denom))


def deflated_sharpe(r: np.ndarray, n_trials: float, var_sharpe: float) -> float:
    return probabilistic_sharpe(r, expected_max_sharpe(n_trials, var_sharpe))


def cluster_trials(returns: np.ndarray, corr_threshold: float) -> np.ndarray:
    """Group trials whose returns move together. returns is (trials, periods).

    Returns one cluster label per trial. Trials that never traded share label 0.
    """
    labels = np.zeros(len(returns), dtype=int)
    live = np.flatnonzero(returns.std(axis=1) > 0)
    if len(live) == 1:
        labels[live] = 1
    elif len(live) > 1:
        corr = np.clip(np.corrcoef(returns[live]), -1, 1)
        dist = np.sqrt(0.5 * (1 - corr))
        np.fill_diagonal(dist, 0.0)
        tree = linkage(squareform(dist, checks=False), method="average")
        labels[live] = fcluster(tree, t=np.sqrt(0.5 * (1 - corr_threshold)), criterion="distance")
    return labels


def pbo(returns: np.ndarray, blocks: int = 16) -> float:
    """Probability of backtest overfitting by CSCV. returns is (trials, periods)."""
    n_trials, n_obs = returns.shape
    if n_trials < 2 or n_obs < blocks:
        return float("nan")
    parts = np.array_split(np.arange(n_obs), blocks)
    cnt = np.array([len(p) for p in parts], dtype=float)
    s1 = np.array([returns[:, p].sum(axis=1) for p in parts])
    s2 = np.array([(returns[:, p] ** 2).sum(axis=1) for p in parts])

    def block_sharpe(ix: list[int]) -> np.ndarray:
        n = cnt[ix].sum()
        mean = s1[ix].sum(axis=0) / n
        var = (s2[ix].sum(axis=0) - n * mean * mean) / (n - 1)
        return np.where(var > 0, mean / np.sqrt(np.maximum(var, 1e-300)), 0.0)

    every = set(range(blocks))
    below = 0
    combos = list(combinations(range(blocks), blocks // 2))
    for c in combos:
        best = int(block_sharpe(list(c)).argmax())
        rank = rankdata(block_sharpe(sorted(every - set(c))))[best] / (n_trials + 1)
        below += np.log(rank / (1 - rank)) <= 0
    return below / len(combos)


def market_adjusted(r: np.ndarray, benchmark: np.ndarray) -> tuple[np.ndarray, float]:
    """Remove the part of a return series explained by holding the benchmark.

    Returns r - beta * benchmark and beta, with beta from a least-squares fit.
    A long-only strategy in a rising market earns a positive Sharpe by exposure
    alone. What is left after this adjustment is what the strategy's timing added.
    """
    var = benchmark.var()
    beta = float(np.cov(r, benchmark, ddof=0)[0, 1] / var) if var > 0 else 0.0
    return r - beta * benchmark, beta


def subperiod_sharpes(r: np.ndarray, periods_per_year: float, parts: int = 5) -> list[float]:
    return [round(annual_sharpe(p, periods_per_year), 2) for p in np.array_split(r, parts)]
