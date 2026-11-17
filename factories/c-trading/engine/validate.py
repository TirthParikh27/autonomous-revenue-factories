"""Test the judge before trusting it (FACTORY_SPEC.md section 9).

    python -m engine.validate

1. Noise: random strategies on the real development data. The gate should pass
   close to none of them.
2. Planted edge: a synthetic market where one signal really predicts returns.
   The gate should pass a strong edge and say honestly that a weak one cannot
   be told from luck.

Runs in a temporary state folder, so nothing here is added to the real trial log.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd

from . import CONFIG, ROOT
from . import gate, strategy as strat, trials
from .data import Bars, load as load_bars

DATASET = "crypto-1h"


def _strategy(name: str, fn, chosen: dict) -> strat.Strategy:
    ranges = {k: {"low": v, "high": v} for k, v in chosen.items()}
    return strat.Strategy(id=name, fn=fn, dataset=DATASET, symbols=None, ranges=ranges, chosen=chosen, code_hash=name)


def random_weights(bars: Bars, params: dict) -> pd.DataFrame:
    """Random long-only positions held for random stretches. Causal by construction."""
    rng = np.random.default_rng(params["seed"])
    n, m = bars.close.shape
    w = np.zeros((n, m))
    for j in range(m):
        i = 0
        while i < n:
            hold = int(rng.exponential(params["hold"])) + 1
            if rng.random() < 0.5:
                w[i:i + hold, j] = 1.0 / m
            i += hold
    return pd.DataFrame(w, index=bars.close.index, columns=bars.symbols)


def noise(n: int = 200) -> dict:
    bars = load_bars(DATASET)
    for seed in range(n):
        s = _strategy(f"noise-{seed:03d}", random_weights, {"seed": seed, "hold": 24 * (1 + seed % 14)})
        trials.evaluate(s, s.chosen, bars)
    log = sorted(trials.read(DATASET), key=lambda t: -t["sharpe"])
    passed, best = 0, None
    for t in log[:25]:                      # if the best 25 fail, the rest would too
        s = _strategy(t["strategy"], random_weights, t["params"])
        out = gate.evaluate(s, bars)
        best = best or out
        passed += out["pass"]
    return {"random_strategies": n, "gated": 25, "passed": passed,
            "best_raw_sharpe": log[0]["sharpe"],
            "best_deflated_sharpe": best["checks"]["deflated_sharpe"]["value"],
            "distinct_ideas_counted": best["checks"]["deflated_sharpe"]["distinct_ideas"]}


BLOCK = 24 * 14      # the planted regime switches every two weeks


def synthetic_market(years: int, edge_sharpe: float, seed: int) -> tuple[Bars, np.ndarray]:
    """Hourly random-walk prices for five symbols. The first symbol drifts up
    during "on" regimes, which a strategy can see. Holding it only when the
    regime is on earns the given annual Sharpe before costs."""
    rng = np.random.default_rng(seed)
    n, m, vol = years * 8760, 5, 0.006
    idx = pd.date_range("2018-01-01", periods=n, freq="1h", tz="UTC")
    regime = np.repeat(rng.random(n // BLOCK + 1) < 0.5, BLOCK)[:n].astype(float)
    r = rng.normal(0, vol, (n, m))
    r[:, 0] += regime * edge_sharpe * vol / np.sqrt(8760 * 0.5)
    close = pd.DataFrame(100 * np.exp(np.cumsum(r, axis=0)), index=idx, columns=[f"S{j}" for j in range(m)])
    open_ = close.shift(1).fillna(100.0)
    bars = Bars(open_, np.maximum(open_, close), np.minimum(open_, close), close, close * 0 + 1.0)
    return bars, regime


def planted(edge_sharpe: float, years: int = 5, seed: int = 0) -> dict:
    bars, regime = synthetic_market(years, edge_sharpe, seed)

    def informed(b: Bars, params: dict) -> pd.DataFrame:
        w = pd.DataFrame(0.0, index=b.close.index, columns=b.symbols)
        # The regime for the coming bar is known at this bar's close.
        w["S0"] = np.roll(regime, -1)[: len(w)]
        return w

    s = _strategy(f"planted-{edge_sharpe}", informed, {"k": 1})
    out = gate.evaluate(s, bars)
    return {"planted_annual_sharpe_before_costs": edge_sharpe, "years": years, "pass": out["pass"],
            "deflated_sharpe": out["checks"]["deflated_sharpe"]["value"],
            "measured_sharpe_after_costs": out["checks"]["beats_buy_and_hold"]["sharpe"],
            "failed": [k for k, c in out["checks"].items() if not c["pass"]]}


def main() -> int:
    report = {"engine_version": CONFIG["engine_version"]}
    if "--planted-only" not in sys.argv:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["FACTORY_STATE_DIR"] = tmp
            report["noise"] = noise()
    report["planted"] = []
    for edge in (0.5, 1.0, 2.0, 3.0):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["FACTORY_STATE_DIR"] = tmp
            report["planted"].append(planted(edge))
    os.environ.pop("FACTORY_STATE_DIR")
    print(json.dumps(report, indent=2))
    if "noise" in report:
        (ROOT / "engine" / "VALIDATION.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
