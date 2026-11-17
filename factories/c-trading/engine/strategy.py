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
BANNED_NAMES = {"open", "exec", "eval", "compile", "__import__", "globals", "locals", "vars", "getattr", "setattr",
                "delattr", "input", "breakpoint"}
# numpy and pandas can themselves reach files, the network, the clock and the shell. These attribute
# names are refused wherever they appear. This is a lint, not a sandbox: the reviewer agent reads the
# code as well, and the judge's job runs strategy code with read-only access to the repository.
BANNED_ATTRS = {"gi_frame", "cr_frame", "ag_frame", "tb_frame", "dump", "dumps", "talib", "core", "lib", "compat", "util", "api", "errors", "plotting", "tseries", "arrays", "builtins", "pickle",
                "fromregex", "open_memmap", "format", "io", "os", "sys", "system", "popen", "subprocess", "now", "today", "utcnow", "random", "eval", "query",
                "load", "save", "savez", "savez_compressed", "savetxt", "loadtxt", "genfromtxt", "fromfile", "tofile",
                "memmap", "DataSource", "ctypeslib", "f2py", "testing", "HDFStore", "ExcelWriter", "ExcelFile", "pipe"}
ALLOWED_TO = {"to_numpy", "to_frame", "to_series", "to_list", "to_dict", "to_period", "to_timestamp", "to_datetime",
              "to_numeric", "to_timedelta", "to_pydatetime"}


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


def _bad_attr(a: str) -> bool:
    return (a.startswith("_") or a.startswith("f_") or a in BANNED_ATTRS or a.startswith("read_")
            or (a.startswith("to_") and a not in ALLOWED_TO))


def lint(source: str) -> list[str]:
    """Problems that would let strategy code reach files, the network, the clock or the shell."""
    problems = []
    for node in ast.walk(ast.parse(source)):
        line = getattr(node, "lineno", 0)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = [node.module or ""] if isinstance(node, ast.ImportFrom) else [a.name for a in node.names]
            for name in module:
                if name not in ALLOWED_IMPORTS:
                    problems.append(f"line {line}: import of '{name}' is not allowed")
            if isinstance(node, ast.ImportFrom):       # `from pandas import read_csv` is the same as `pd.read_csv`
                for a in node.names:
                    if a.name == "*" or (_bad_attr(a.name) and (node.module, a.name) != ("lib", "indicators")):
                        problems.append(f"line {line}: import of '{a.name}' from '{node.module}' is not allowed")
        elif isinstance(node, ast.Name) and (node.id in BANNED_NAMES or node.id.startswith("__")):
            problems.append(f"line {line}: use of '{node.id}' is not allowed")
        elif isinstance(node, ast.Attribute) and _bad_attr(node.attr):
            problems.append(f"line {line}: use of '.{node.attr}' is not allowed")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and _bad_attr(node.value):
            problems.append(f"line {line}: the text '{node.value}' names a call that is not allowed")   # .agg("to_csv")
        elif isinstance(node, (ast.Match, ast.Global, ast.Nonlocal)):
            problems.append(f"line {line}: this statement is not allowed in a strategy")
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
    band = _band(cfg.get("rebalance_band"))
    # The hash covers everything that fixes the strategy's behaviour apart from its tuned parameters,
    # so a change of universe or band after a verdict is a different version.
    fixed = repr([cfg["dataset"], cfg.get("symbols"), band, cfg.get("ranges") or {}])
    return Strategy(
        id=strategy_id, fn=module.weights, dataset=cfg["dataset"], symbols=cfg.get("symbols"),
        ranges=cfg.get("ranges") or {}, chosen=cfg.get("chosen"),
        code_hash=hashlib.sha256((source + fixed).encode()).hexdigest()[:16],
        band=band,
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
