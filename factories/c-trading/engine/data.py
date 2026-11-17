"""Load fixed data snapshots. A strategy sees prices only through Bars."""
from __future__ import annotations

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
    base = ROOT / "data" / window / f"{market}-15m"   # every bar size is built from the 15-minute snapshot
    frames = {}
    for s in symbols:
        df = pd.read_csv(base / f"{s}.csv.gz", parse_dates=["ts"]).set_index("ts")
        if spec["bar"] != "15min":
            df = df.resample(spec["bar"]).agg(AGG).dropna(subset=["close"])
        frames[s] = df
    out = {f: pd.DataFrame({s: frames[s][f] for s in symbols}).dropna() for f in FIELDS}
    idx = out["close"].index
    return Bars(*(out[f].loc[idx] for f in FIELDS))
