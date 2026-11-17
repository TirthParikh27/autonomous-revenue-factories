"""The trial log. Every evaluation on market data is written here before its
result is returned. Append-only: the gate's bar rises with what this holds."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from . import CONFIG, ROOT
from . import backtest, stats, strategy as strat
from .data import Bars, load as load_bars


def state_dir() -> Path:
    return Path(os.environ.get("FACTORY_STATE_DIR", ROOT / "state"))


def log_path(dataset: str) -> Path:
    return state_dir() / "trials" / f"{dataset}.jsonl"


def read(dataset: str) -> list[dict]:
    path = log_path(dataset)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def daily_returns(trial: dict) -> np.ndarray:
    return np.load(state_dir() / "trials" / trial["dataset"] / f"{trial['id']}.npy")


def returns_matrix(trials: list[dict]) -> np.ndarray:
    return np.array([daily_returns(t) for t in trials], dtype=float)


def evaluate(s: strat.Strategy, params: dict, bars: Bars | None = None) -> tuple[dict, backtest.Result]:
    """Run one trial and log it. An identical trial (same code, params, data) is not counted twice."""
    strat.check_params(s, params)
    bars = bars or load_bars(s.dataset, s.symbols)
    key = hashlib.sha256(json.dumps(
        [s.id, s.code_hash, sorted(params.items()), s.dataset, bars.symbols, len(bars.close), CONFIG["engine_version"]]
        + ([s.band] if s.band is not None else []),
        default=str).encode()).hexdigest()[:16]
    result = backtest.run(strat.compute(s, bars, params), bars, s.dataset, band=s.band)
    existing = [t for t in read(s.dataset) if t["key"] == key]
    if existing:
        return existing[0], result

    spec = CONFIG["datasets"][s.dataset]
    daily = result.daily.to_numpy()
    trial = {
        "id": f"t{len(read(s.dataset)) + 1:06d}",
        "key": key,
        "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "dataset": s.dataset,
        "strategy": s.id,
        "code_hash": s.code_hash,
        "params": params,
        "engine_version": CONFIG["engine_version"],
        "days": len(daily),
        "sharpe": round(stats.annual_sharpe(daily, spec["days_per_year"]), 4),
        "total_return": round(float(np.prod(1 + daily) - 1), 4),
        "max_drawdown": round(stats.max_drawdown(daily), 4),
        "orders": result.orders,
        "turnover_per_year": round(result.turnover_per_year, 2),
        "cost_per_year": round(result.cost_per_year, 4),
        "exposure": round(result.exposure, 3),
        "margin": result.margin,
        "liquidated": result.liquidated,
    }
    folder = state_dir() / "trials" / s.dataset
    folder.mkdir(parents=True, exist_ok=True)
    np.save(folder / f"{trial['id']}.npy", daily.astype(np.float32))
    with log_path(s.dataset).open("a") as f:      # logged before the caller sees anything
        f.write(json.dumps(trial, sort_keys=True) + "\n")
    return trial, result
