#!/usr/bin/env python3
"""Download Binance spot klines from the public archive into fixed snapshots.

Writes data/<window>/crypto-15m/<SYMBOL>.csv.gz, where window is "dev"
(bars up to the development cutoff) or "exam" (bars after it). The exam
window may only be fetched inside the final exam job, which sets FACTORY_EXAM=1.

Usage: python data/fetch_binance.py [--window dev|exam] [--symbols BTCUSDT ...]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import io
import json
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
URL = "https://data.binance.vision/data/spot/monthly/klines/{s}/15m/{s}-15m-{ym}.zip"
COLS = ["ts", "open", "high", "low", "close", "volume"]


def months(start: dt.date, end: dt.date) -> list[str]:
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(f"{y}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def fetch_month(symbol: str, ym: str) -> pd.DataFrame | None:
    try:
        with urllib.request.urlopen(URL.format(s=symbol, ym=ym), timeout=120) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # month not published yet, or symbol not listed
        raise
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        df = pd.read_csv(z.open(z.namelist()[0]), header=None, usecols=range(6), names=COLS)
    # The archive switched from milliseconds to microseconds in 2025.
    unit = "us" if df["ts"].iloc[0] > 1e14 else "ms"
    df["ts"] = pd.to_datetime(df["ts"], unit=unit, utc=True)
    return df


def main() -> int:
    cfg = yaml.safe_load((ROOT / "engine" / "config.yaml").read_text())
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", choices=["dev", "exam"], default="dev")
    ap.add_argument("--symbols", nargs="*", default=cfg["universe"]["crypto"])
    args = ap.parse_args()

    cutoff = dt.date.fromisoformat(cfg["dev_cutoff"])
    if args.window == "exam":
        if os.environ.get("FACTORY_EXAM") != "1":
            print("refused: the exam window is fetched only inside the final exam job", file=sys.stderr)
            return 2
        start, end = cutoff + dt.timedelta(days=1), dt.date.today()
    else:
        start, end = dt.date.fromisoformat(cfg["dev_start"]), cutoff

    out_dir = ROOT / "data" / args.window / "crypto-15m"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for symbol in args.symbols:
        with cf.ThreadPoolExecutor(8) as pool:
            parts = list(pool.map(lambda ym: fetch_month(symbol, ym), months(start, end)))
        df = pd.concat([p for p in parts if p is not None]).drop_duplicates("ts").sort_values("ts")
        lo = pd.Timestamp(start, tz="UTC")
        hi = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
        df = df[(df["ts"] >= lo) & (df["ts"] < hi)]
        path = out_dir / f"{symbol}.csv.gz"
        df.to_csv(path, index=False)
        manifest[symbol] = {
            "bars": len(df), "first": str(df["ts"].iloc[0]), "last": str(df["ts"].iloc[-1]),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        print(symbol, manifest[symbol]["bars"], manifest[symbol]["first"], "to", manifest[symbol]["last"])
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
