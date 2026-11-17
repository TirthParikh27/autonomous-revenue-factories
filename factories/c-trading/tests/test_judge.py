"""Essential tests of the judge: the things that, if wrong, make every result wrong."""
import json

import numpy as np
import pandas as pd
import pytest

from engine import CONFIG, backtest, exam, gate, paper, stats, strategy as strat, trials, validate
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
    wiggly = weights + 0.005 * (np.arange(len(weights)) % 2)[:, None] * (weights > 0)    # changes under the default band
    assert backtest.run(wiggly, bars, DATASET).orders == result.orders
    assert backtest.run(wiggly, bars, DATASET, band=0.0).orders > result.orders        # a strategy may set its own band


def flat_bars(n=50, m=1):
    idx = pd.date_range("2022-01-01", periods=n, freq="1h", tz="UTC")
    one = pd.DataFrame(100.0, index=idx, columns=[f"S{j}" for j in range(m)])
    return Bars(one.copy(), one.copy(), one.copy(), one.copy(), one.copy())


def test_shorts_and_leverage_follow_the_market_terms(monkeypatch):
    costs = CONFIG["costs"]["crypto"]
    margin = costs["margin"]
    bars = make_bars()
    fast, slow = bars.close.rolling(20).mean(), bars.close.rolling(100).mean()
    long_short = ((fast > slow) * 0.6 - (fast < slow) * 0.6).astype(float)

    # With borrowing free, a long-short book at the margin fee matches the independent loop.
    free = margin | {"borrow_cash_per_year": 0.0, "borrow_asset_per_year": 0.0, "maintenance_margin": 0.0}
    monkeypatch.setitem(costs, "margin", free)
    result = backtest.run(long_short, bars, DATASET)
    ref = reference_equity(bars, long_short, margin["fee"], costs["slippage"])
    assert result.margin and np.allclose(np.cumprod(1 + result.returns.to_numpy()), ref, rtol=1e-3)
    monkeypatch.setitem(costs, "margin", margin)
    assert backtest.run(long_short, bars, DATASET).returns.sum() < result.returns.sum()      # borrowing costs money

    # Long only inside the account's equity keeps the plain terms. One short moves the whole strategy to margin terms.
    plain = (fast > slow).astype(float) * 0.3
    assert not backtest.run(plain, bars, DATASET).margin
    assert backtest.terms("crypto", plain - 0.01)["fee"] == margin["fee"]

    # Limits: gross exposure above the venue's cap, and any margin use where the venue offers none.
    with pytest.raises(ValueError, match="gross exposure"):
        backtest.run(plain * 0 + margin["max_gross_exposure"], bars, DATASET)
    monkeypatch.delitem(costs, "margin")
    with pytest.raises(ValueError, match="not available"):
        backtest.run(-plain, bars, DATASET)


def test_borrowing_cost_and_liquidation_by_hand():
    costs = CONFIG["costs"]["crypto"]
    margin, slip = costs["margin"], costs["slippage"]
    per_bar = 1 / CONFIG["datasets"][DATASET]["bars_per_year"]

    # Flat prices, 2x long: pays to get in, then interest each bar on the borrowed half.
    bars = flat_bars()
    w = pd.DataFrame(2.0, index=bars.close.index, columns=bars.symbols)
    equity = np.cumprod(1 + backtest.run(w, bars, DATASET).returns.to_numpy())
    entry = 1 - 2 * (slip + margin["fee"] * (1 + slip))
    assert equity[1] == pytest.approx(entry - margin["borrow_cash_per_year"] * per_bar * (2 - entry), rel=1e-6)
    assert equity[11] - equity[10] == pytest.approx(-margin["borrow_cash_per_year"] * per_bar * (2 - equity[10]), rel=1e-3)

    # A 1x short gains when the price falls, and pays interest on the borrowed coins.
    bars = flat_bars()
    for f in (bars.open, bars.high, bars.low, bars.close):
        f.iloc[10:] = 90.0
    short = backtest.run(-w / 2, bars, DATASET)
    assert not short.liquidated
    assert np.prod(1 + short.returns.to_numpy()) == pytest.approx(1.1, abs=0.01)

    # 3x long, and the price touches -40% inside one bar: the venue closes the account. It does not recover.
    bars = flat_bars()
    bars.low.iloc[20] = 60.0
    wiped = backtest.run(w * 1.5, bars, DATASET)
    assert wiped.liquidated and np.prod(1 + wiped.returns.to_numpy()) < 0.01
    assert (wiped.returns.iloc[21:] == 0).all()
    # A gap through the requirement at the open is a liquidation too, even if the strategy cuts its target that bar.
    bars = flat_bars()
    for f in (bars.open, bars.high, bars.low, bars.close):
        f.iloc[20:] = 70.0
    cut = w * 1.5
    cut.iloc[19:] = 0.0
    assert backtest.run(cut, bars, DATASET).liquidated
    # An account that may not borrow buys only what its cash covers: fully invested, it never goes below zero cash.
    bars = make_bars(m=2)
    switch = pd.DataFrame({"S0": 1.0, "S1": 0.0}, index=bars.close.index)
    switch.iloc[1000:] = [0.0, 1.0]
    full = backtest.run(switch, bars, DATASET)
    fee = costs["fee"] + costs["slippage"]
    assert not full.margin and full.exposure <= 1.0
    ref = reference_equity(bars, switch * (1 - 2.5 * fee), costs["fee"], costs["slippage"])   # the same switch, slightly under-invested
    assert np.prod(1 + full.returns.to_numpy()) == pytest.approx(ref[-1], rel=5e-3)
    # The same spike upward does the same to a 2x short.
    bars = flat_bars()
    bars.high.iloc[20] = 150.0
    assert backtest.run(-w, bars, DATASET).liquidated


def test_every_market_has_usable_terms():
    w = pd.DataFrame({"A": [0.5, -0.5]})
    for market, costs in CONFIG["costs"].items():
        t = backtest.terms(market, w)
        assert t["margin"] and t["max_gross_exposure"] >= 1 and 0 <= t["maintenance_margin"] < 1 / t["max_gross_exposure"]
        assert not backtest.terms(market, w.abs())["margin"] or market == "fx"


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
                "import importlib", "y = eval('1')", "z = (1).__class__",
                # numpy and pandas can reach files, the network, the clock and the shell on their own
                "bars.close.to_csv('x.csv')", "pd.read_csv('https://example.com/x')", "pd.read_pickle('x')",
                "pd.Timestamp.now()", "np.random.rand(3)", "pd.io.common.os.system('ls')", "np.save('x', a)",
                "np.load('x.npy')", "df.eval('a + b')", "bars.close.to_pickle('x')", "vars(pd)",
                "from pandas import read_csv", "from numpy import random", "from lib.indicators import talib",
                "from numpy import *", "__builtins__['open']('x')", "pd.core.generic.pickle.loads(b'')",
                "pd.core.common.builtins", "np.lib.format.open_memmap('x')", "np.fromregex('x', 'a', float)",
                "bars._private", "s.agg('to_csv', path_or_buf='x')", "(x for x in ()).gi_frame.f_builtins", "a.dump('x')", "match np:\n    case object(random=r):\n        pass"):
        assert strat.lint(bad), bad
    assert strat.lint("w = bars.close.rolling(5).mean().to_numpy()\nd = pd.to_datetime(x)\n"
                      "from lib import indicators\nfrom lib.indicators import ema\nfrom numpy import sqrt\n") == []


def test_code_hash_covers_universe_and_band(tmp_path):
    def version(extra):
        folder = tmp_path / "s"
        folder.mkdir(exist_ok=True)
        (folder / "strategy.py").write_text("def weights(bars, params):\n    return bars.close * 0\n")
        (folder / "params.yaml").write_text("dataset: crypto-1h\nranges: {n: {low: 1, high: 9}}\nchosen: {n: 3}\n" + extra)
        return strat.load("s", tmp_path).code_hash

    plain = version("")
    assert version("") == plain and version("chosen: {n: 4}\n") == plain          # tuning is not a new version
    assert len({plain, version("symbols: [BTCUSDT]\n"), version("rebalance_band: 0.1\n")}) == 3


def test_a_file_in_the_factory_folder_cannot_shadow_a_library(tmp_path):
    import subprocess, sys, shutil
    root = tmp_path / "f"
    shutil.copytree(strat.ROOT / "engine", root / "engine")
    (root / "yaml.py").write_text("raise SystemExit('shadowed')\n")
    out = subprocess.run([sys.executable, "-c", "import engine, yaml; print(yaml.__file__)"], cwd=root,
                         capture_output=True, text=True)
    assert out.returncode == 0 and "site-packages" in out.stdout, out.stderr


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


def test_exam_judges_only_unseen_data_and_publishes_no_numbers(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTORY_STATE_DIR", str(tmp_path / "state"))
    bars, regime = validate.synthetic_market(6, 3.0, seed=0)
    dev = bars.until(5 * 8760)

    def informed(b, p):                                      # the edge stops when the seen data ends
        w = pd.DataFrame(0.0, index=b.close.index, columns=b.symbols)
        w["S0"] = np.roll(regime, -1)[: len(w)]
        return w

    def fades(b, p):
        w = informed(b, p)
        w.iloc[5 * 8760:, 0] = 1.0 - w.iloc[5 * 8760:, 0]   # after the cutoff it holds the wrong regime
        return w

    with pytest.raises(PermissionError):                     # outside the exam job the later data is unreadable
        from engine.data import load
        load(DATASET, window="all")

    good = validate._strategy("good", informed, {"k": 1})
    assert not exam.evaluate(good, dev, bars)["pass"]        # no logged gate result: refused before any look
    gate.evaluate(good, dev)
    out = exam.evaluate(good, dev, bars)
    assert out["pass"] and all(isinstance(v, bool) for v in out["checks"].values())

    bad = validate._strategy("bad", fades, {"k": 1})
    assert gate.evaluate(bad, dev)["pass"]
    out = exam.evaluate(bad, dev, bars)
    assert not out["pass"] and out["checks"]["gate_on_development_data"]
    assert not out["checks"]["positive_after_costs_on_unseen_data"]

    # The paper record starts where it is told to, and the health watch flags only the strategy that broke.
    started = str((dev.close.index[-1] + pd.Timedelta(days=1)).date())
    record, health = paper.record(good, dev, bars, started)
    assert record["daily"][0][0] == started and record["days"] == len(record["daily"]) == 365
    assert health["status"] == "in_range"
    broken = paper.record(bad, dev, bars, started)
    assert broken[1]["status"] == "below_range"
    # A watched strategy: the job stamps the start itself, on new days only, whatever the gate file says,
    # keeps it out of the book, and a stale or broken gate file for another item does not stop the run.
    state = tmp_path / "state"
    (state / "items").mkdir(exist_ok=True)
    for sid in ("good", "stale"):
        (state / "items" / f"{sid}.json").write_text('{"stage": "watch"}')
    (state / "gate" / "stale.json").write_text('{"pass": false}')
    verdict = json.loads((state / "gate" / "good.json").read_text()) | {"only_luck_score_failed": True, "judged_on": "2000-01-01"}
    (state / "gate" / "good.json").write_text(json.dumps(verdict))
    monkeypatch.setenv("FACTORY_EXAM", "1")
    monkeypatch.setattr(paper.strat, "load", lambda sid: good)
    month = 24 * 30
    for held, days in ((bars.until(len(bars.close) - month), 0), (bars, 30)):
        monkeypatch.setattr(paper, "load_bars", lambda d, s=None, window="dev", held=held: held if window == "all" else dev)
        assert paper.main() == 0
        seen = json.loads((tmp_path / "paper" / "good.json").read_text())
        assert seen["watched"] and seen["days"] == days
        assert seen["started"] == str((bars.close.index[-month - 1] + pd.Timedelta(days=1)).date())
    assert not (tmp_path / "paper" / "book.json").exists() and not (tmp_path / "paper" / "stale.json").exists()

    out = gate.evaluate(good, dev)                           # evidence a reader needs, none of it a pass mark
    assert {"annual_return", "annual_volatility", "skew", "worst_day", "longest_drawdown_days"} <= set(out["evidence"])
    assert set(out["evidence"]["half_universe"]) == {"first_half", "second_half"} and not out["only_luck_score_failed"]
    both = paper.book([record, broken[0]])                   # equal risk: the two cancel after the cutoff
    assert both["days"] == 365 and abs(both["paper_result"]) < abs(record["paper_result"])
