"""Indicators for strategies. Thin wrappers over TA-Lib that take and return
DataFrames (one column per symbol). Agents may add to this file. Every function
must use past bars only; the engine's leak test checks each strategy for that.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import talib


def _each(df: pd.DataFrame, fn) -> pd.DataFrame:
    return pd.DataFrame({c: fn(df[c].to_numpy(dtype=float)) for c in df.columns}, index=df.index)


def sma(close: pd.DataFrame, n: int) -> pd.DataFrame:
    return _each(close, lambda x: talib.SMA(x, n))


def ema(close: pd.DataFrame, n: int) -> pd.DataFrame:
    return _each(close, lambda x: talib.EMA(x, n))


def rsi(close: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    return _each(close, lambda x: talib.RSI(x, n))


def atr(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    return pd.DataFrame({c: talib.ATR(high[c].to_numpy(float), low[c].to_numpy(float), close[c].to_numpy(float), n)
                         for c in close.columns}, index=close.index)


def bollinger(close: pd.DataFrame, n: int = 20, k: float = 2.0) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Upper, middle and lower bands."""
    bands = {c: talib.BBANDS(close[c].to_numpy(float), n, k, k) for c in close.columns}
    return tuple(pd.DataFrame({c: bands[c][i] for c in close.columns}, index=close.index) for i in range(3))


def returns(close: pd.DataFrame, n: int = 1) -> pd.DataFrame:
    return close.pct_change(n)


def volatility(close: pd.DataFrame, n: int) -> pd.DataFrame:
    """Rolling standard deviation of one-bar returns."""
    return close.pct_change().rolling(n).std()


def zscore(x: pd.DataFrame, n: int) -> pd.DataFrame:
    return (x - x.rolling(n).mean()) / x.rolling(n).std().replace(0, np.nan)


def channel_high(high: pd.DataFrame, n: int) -> pd.DataFrame:
    """Highest high of the previous n bars, not including the current bar."""
    return high.shift(1).rolling(n).max()


def channel_low(low: pd.DataFrame, n: int) -> pd.DataFrame:
    return low.shift(1).rolling(n).min()
