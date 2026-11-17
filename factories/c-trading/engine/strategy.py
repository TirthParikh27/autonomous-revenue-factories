"""Load a strategy and check it before it is allowed near data.

A strategy is strategies/<id>/strategy.py with one function:

    def weights(bars, params) -> pandas.DataFrame

It returns the target weight of each symbol at each bar, decided with data up
to and including that bar. The engine trades the target at the next bar's open.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import yaml

from . import GATE, ROOT
from .data import Bars

ALLOWED_IMPORTS = {"numpy", "pandas", "math", "lib", "lib.indicators"}
BANNED_NAMES = {"open", "exec", "eval", "compile", "__import__", "globals", "locals", "getattr", "setattr", "input"}


@dataclass
class Strategy:
    id: str
    fn: Callable[[Bars, dict], pd.DataFrame]
    dataset: str
    symbols: list[str] | None
    ranges: dict
    chosen: dict | None
    code_hash: str
    band: float | None = None      # the strategy's own no-trade band; None means the engine default


def lint(source: str) -> list[str]:
    """Problems that would let strategy code reach files, the network or the clock."""
    problems = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            if isinstance(node, ast.Name) and node.id in BANNED_NAMES:
                problems.append(f"line {node.lineno}: use of '{node.id}' is not allowed")
            if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
                problems.append(f"line {node.lineno}: dunder attribute access is not allowed")
            continue
        for name in names:
            if name not in ALLOWED_IMPORTS:
                problems.append(f"line {node.lineno}: import of '{name}' is not allowed")
    return problems


def load(strategy_id: str, root: Path | None = None) -> Strategy:
    folder = (root or ROOT / "strategies") / strategy_id
    source = (folder / "strategy.py").read_text()
    problems = lint(source)
    if problems:
        raise ValueError("strategy failed lint:\n  " + "\n  ".join(problems))
    spec = importlib.util.spec_from_file_location(f"strategy_{strategy_id.replace('-', '_')}", folder / "strategy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cfg = yaml.safe_load((folder / "params.yaml").read_text())
    return Strategy(
        id=strategy_id, fn=module.weights, dataset=cfg["dataset"], symbols=cfg.get("symbols"),
        ranges=cfg.get("ranges") or {}, chosen=cfg.get("chosen"),
        code_hash=hashlib.sha256(source.encode()).hexdigest()[:16],
        band=_band(cfg.get("rebalance_band")),
    )


def _band(value) -> float | None:
    if value is not None and not 0.0 <= float(value) <= 1.0:
        raise ValueError("rebalance_band must be between 0 and 1")
    return None if value is None else float(value)


def check_params(strategy: Strategy, params: dict) -> None:
    """Parameters must sit inside the ranges declared before the first test."""
    if set(params) != set(strategy.ranges):
        raise ValueError(f"params {sorted(params)} do not match declared ranges {sorted(strategy.ranges)}")
    for name, value in params.items():
        r = strategy.ranges[name]
        if not r["low"] <= value <= r["high"]:
            raise ValueError(f"{name}={value} is outside its declared range {r['low']} to {r['high']}")


def compute(strategy: Strategy, bars: Bars, params: dict) -> pd.DataFrame:
    w = strategy.fn(bars, dict(params))
    if not isinstance(w, pd.DataFrame):
        raise ValueError("weights() must return a DataFrame")
    return w.reindex(index=bars.close.index, columns=bars.symbols).astype(float)


def leak_test(strategy: Strategy, bars: Bars, params: dict) -> list[str]:
    """Remove the future and check that past decisions do not change.

    Weights computed on the full history must equal weights computed on a
    history cut short, for every bar before the cut.
    """
    full = compute(strategy, bars, params).to_numpy()
    n = len(full)
    problems = []
    for frac in np.linspace(0.5, 0.95, GATE["leak_cut_points"]):
        cut = int(n * frac)
        part = compute(strategy, bars.until(cut), params).to_numpy()
        if not np.allclose(full[:cut], part, atol=1e-9, equal_nan=True):
            bad = int(np.argmax(~np.isclose(full[:cut], part, atol=1e-9, equal_nan=True).all(axis=1)))
            problems.append(f"decisions before bar {cut} change when later bars are removed (first at bar {bad})")
    return problems
