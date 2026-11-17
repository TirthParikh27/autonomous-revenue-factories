"""Load fixed data snapshots. A strategy sees prices only through Bars."""
from __future__ import annotations

import os
from dataclasses import dataclass

import pandas as pd

from . import CONFIG, ROOT

FIELDS = ("open", "high", "low", "close", "volume")
AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}


@dataclass(frozen=True)
class Bars:
    """One DataFrame per field: index is bar open time (UTC), columns are symbols."""
    open: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    close: pd.DataFrame
    volume: pd.DataFrame

    def until(self, n: int) -> "Bars":
        """The first n bars only. Used by the leak test."""
        return Bars(*(getattr(self, f).iloc[:n] for f in FIELDS))

    @property
    def symbols(self) -> list[str]:
        return list(self.close.columns)


def load(dataset: str, symbols: list[str] | None = None, window: str = "dev") -> Bars:
    spec = CONFIG["datasets"][dataset]
    market = spec["market"]
    symbols = symbols or CONFIG["universe"][market]
    unknown = set(symbols) - set(CONFIG["universe"][market])
    if unknown:
        raise ValueError(f"symbols outside the {market} universe: {sorted(unknown)}")
    if window not in ("dev", "all"):
        raise ValueError("window is 'dev', or 'all' inside the exam job")
    if window == "all" and os.environ.get("FACTORY_EXAM") != "1":
        raise PermissionError("data after the development cutoff is read only inside the final exam job")
    folders = [ROOT / "data" / w / f"{market}-15m" for w in (("dev", "exam") if window == "all" else ("dev",))]
    frames = {}
    for s in symbols:   # every bar size is built from the 15-minute snapshot
        df = pd.concat(pd.read_csv(f / f"{s}.csv.gz", parse_dates=["ts"]) for f in folders).set_index("ts")
        if spec["bar"] != "15min":
            df = df.resample(spec["bar"]).agg(AGG).dropna(subset=["close"])
        frames[s] = df
    out = {f: pd.DataFrame({s: frames[s][f] for s in symbols}).dropna() for f in FIELDS}
    idx = out["close"].index
    return Bars(*(out[f].loc[idx] for f in FIELDS))
