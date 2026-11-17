#!/usr/bin/env python3
"""Download Binance spot klines from the public archive into fixed snapshots.

Writes data/<window>/crypto-15m/<SYMBOL>.csv.gz, where window is "dev"
(bars up to the development cutoff) or "exam" (bars after it). The exam
window may only be fetched inside the final exam job, which sets FACTORY_EXAM=1.

Usage: python data/fetch_binance.py [--window dev|exam] [--verify] [--symbols BTCUSDT ...]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import gzip
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
URL_DAY = "https://data.binance.vision/data/spot/daily/klines/{s}/15m/{s}-15m-{d}.zip"   # published a few hours after each UTC day
COLS = ["ts", "open", "high", "low", "close", "volume"]


def months(start: dt.date, end: dt.date) -> list[str]:
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(f"{y}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def fetch(url: str) -> pd.DataFrame | None:
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # not published yet, or symbol not listed
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
    ap.add_argument("--verify", action="store_true", help="fail if the download differs from the committed manifest")
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
            parts = [p for p in pool.map(lambda ym: fetch(URL.format(s=symbol, ym=ym)), months(start, end)) if p is not None]  # noqa: B023 (used up inside the loop)
            if args.window == "exam":       # days after the last whole month come from the daily files
                first = max(p["ts"].max() for p in parts).date() + dt.timedelta(days=1) if parts else start
                days = [first + dt.timedelta(days=i) for i in range((end - first).days)]
                parts += [p for p in pool.map(lambda d: fetch(URL_DAY.format(s=symbol, d=d)), days) if p is not None]  # noqa: B023 (used up inside the loop)
        df = pd.concat(parts).drop_duplicates("ts").sort_values("ts")
        lo = pd.Timestamp(start, tz="UTC")
        hi = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
        df = df[(df["ts"] >= lo) & (df["ts"] < hi)]
        path = out_dir / f"{symbol}.csv.gz"
        df.to_csv(path, index=False)
        manifest[symbol] = {
            "bars": len(df), "first": str(df["ts"].iloc[0]), "last": str(df["ts"].iloc[-1]),
            "sha256": hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest(),   # of the CSV text
        }
        print(symbol, manifest[symbol]["bars"], manifest[symbol]["first"], "to", manifest[symbol]["last"])
    path = out_dir / "manifest.json"
    if args.verify:
        if json.loads(path.read_text()) != manifest:
            print("refused: the download does not match the committed manifest", file=sys.stderr)
            return 1
        return 0
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
