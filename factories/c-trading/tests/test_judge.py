"""Essential tests of the judge: the things that, if wrong, make every result wrong."""
import numpy as np
import pandas as pd
import pytest

from engine import CONFIG, backtest, stats, strategy as strat, trials, validate
from engine.data import Bars

DATASET = "crypto-1h"


def make_bars(n=3000, m=3, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=n, freq="1h", tz="UTC")
    close = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, 0.004, (n, m)), axis=0)),
                         index=idx, columns=[f"S{j}" for j in range(m)])
    open_ = close.shift(1).fillna(100.0) * np.exp(rng.normal(0, 0.0005, (n, m)))
    return Bars(open_, np.maximum(open_, close), np.minimum(open_, close), close, close * 0 + 1.0)


def reference_equity(bars, weights, fee, slip):
    """A plain loop: decide at close of t, trade at open of t+1, pay fee and slippage."""
    O, C, W = bars.open.to_numpy(), bars.close.to_numpy(), weights.to_numpy()
    n, m = C.shape
    cash, pos, held, equity = 1.0, np.zeros(m), np.zeros(m), np.empty(n)
    for t in range(n):
        if t > 0 and not np.array_equal(W[t - 1], held):
            value = cash + (pos * O[t]).sum()
            delta = np.where(W[t - 1] != held, W[t - 1] * value / O[t] - pos, 0.0)
            for i in np.argsort(delta):                     # sells before buys
                if delta[i] != 0:
                    px = O[t, i] * (1 + slip * np.sign(delta[i]))
                    cash -= delta[i] * px + abs(delta[i]) * px * fee
                    pos[i] += delta[i]
            held = W[t - 1].copy()
        equity[t] = cash + (pos * C[t]).sum()
    return equity


def test_backtest_matches_an_independent_reference():
    bars = make_bars()
    fast, slow = bars.close.rolling(20).mean(), bars.close.rolling(100).mean()
    weights = ((fast > slow) * 0.3).astype(float)           # steps of 0.3, far above the rebalance band
    costs = CONFIG["costs"]["crypto"]
    result = backtest.run(weights, bars, DATASET)
    ours = np.cumprod(1 + result.returns.to_numpy())
    ref = reference_equity(bars, weights, costs["fee"], costs["slippage"])
    assert result.orders > 20
    assert np.allclose(ours, ref, rtol=1e-3)
    # Costs bite: the same weights with costs doubled must do worse.
    assert backtest.run(weights, bars, DATASET, 2.0).returns.sum() < result.returns.sum()


def test_backtest_refuses_leverage_and_shorts():
    bars = make_bars(200)
    ok = pd.DataFrame(0.2, index=bars.close.index, columns=bars.symbols)
    with pytest.raises(ValueError, match="gross exposure"):
        backtest.run(ok * 3, bars, DATASET)
    with pytest.raises(ValueError, match="short"):
        backtest.run(-ok, bars, DATASET)


def _strategy(fn):
    return strat.Strategy("t", fn, DATASET, None, {"n": {"low": 5, "high": 50}}, {"n": 20}, "h")


def test_leak_test_catches_a_strategy_that_uses_the_future():
    bars = make_bars()

    def clean(b, p):
        return (b.close > b.close.rolling(p["n"]).mean()).astype(float) / 3

    def leaky(b, p):                                         # trades on the next bar's close
        return (b.close.shift(-1) > b.close).astype(float).fillna(0.0) / 3

    def subtle(b, p):                                        # normalises with the full-sample mean
        return (b.close > b.close.mean()).astype(float) / 3

    assert strat.leak_test(_strategy(clean), bars, {"n": 20}) == []
    assert strat.leak_test(_strategy(leaky), bars, {"n": 20})
    assert strat.leak_test(_strategy(subtle), bars, {"n": 20})


def test_lint_blocks_files_network_and_clock():
    assert strat.lint("import pandas as pd\nfrom lib import indicators\n") == []
    for bad in ("import os", "import requests", "from datetime import datetime", "x = open('f')",
                "import importlib", "y = eval('1')", "z = (1).__class__"):
        assert strat.lint(bad), bad


def test_statistics_match_an_independent_library():
    pc = pytest.importorskip("purgedcv")
    rng = np.random.default_rng(1)
    R = rng.normal(0.0002, 0.01, (40, 1500))                 # (trials, days)
    R[7] += 0.0008
    sharpes = np.array([stats.sharpe(r) for r in R])
    best = int(sharpes.argmax())
    ours = stats.deflated_sharpe(R[best], 40, float(sharpes.var(ddof=1)))
    theirs = pc.deflated_sharpe_ratio(R[best], 40, float(sharpes.var(ddof=1)))
    assert ours == pytest.approx(theirs, abs=1e-3)       # the two differ only in moment-estimator conventions
    assert stats.pbo(R, 8) == pytest.approx(pc.probability_of_backtest_overfitting(R, 8).pbo, abs=1e-9)


def test_near_identical_trials_count_as_one_idea():
    rng = np.random.default_rng(2)
    base = rng.normal(0, 0.01, (3, 1000))
    variants = np.vstack([base[0] + rng.normal(0, 0.001, (20, 1000)), base[1:]])
    assert len(np.unique(stats.cluster_trials(variants, 0.5))) == 3


def test_every_trial_is_logged_once_and_ranges_are_enforced(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTORY_STATE_DIR", str(tmp_path))
    bars = make_bars(1000)
    s = _strategy(lambda b, p: (b.close > b.close.rolling(p["n"]).mean()).astype(float) / 3)
    first, _ = trials.evaluate(s, {"n": 20}, bars)
    again, _ = trials.evaluate(s, {"n": 20}, bars)
    trials.evaluate(s, {"n": 30}, bars)
    assert first["id"] == again["id"]
    assert [t["id"] for t in trials.read(DATASET)] == ["t000001", "t000002"]
    with pytest.raises(ValueError, match="outside its declared range"):
        trials.evaluate(s, {"n": 500}, bars)


def test_gate_passes_a_strong_planted_edge_and_fails_a_weak_one(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTORY_STATE_DIR", str(tmp_path / "strong"))
    assert validate.planted(3.0)["pass"]
    monkeypatch.setenv("FACTORY_STATE_DIR", str(tmp_path / "weak"))
    assert not validate.planted(0.5)["pass"]
