import math

import numpy as np
import pandas as pd

# Unit conversion, not a tuning choice: crypto trades every calendar day, and the
# card states vol_target in annualised terms (engine/config.yaml crypto-1d: 365 bars a year).
BARS_PER_YEAR = 365


def basket_volatility(close, lookback):
    """Annualised trailing volatility of the equal-weight basket's daily returns (past bars only)."""
    basket = close.pct_change().mean(axis=1)
    return basket.rolling(lookback).std() * math.sqrt(BARS_PER_YEAR)


def banded_exposure(target, band):
    """Move exposure to target only when target leaves the band around current exposure."""
    out = np.zeros(len(target))
    current = 0.0
    for i, t in enumerate(target):
        if abs(t - current) > band:
            current = t
        out[i] = current
    return out


def weights(bars, params):
    close = bars.close
    vol = basket_volatility(close, int(params["vol_lookback"]))
    target = (params["vol_target"] / vol).clip(upper=1.0).fillna(0.0)   # no estimate yet: cash
    exposure = pd.Series(banded_exposure(target.to_numpy(), params["band"]), index=close.index)
    w = pd.DataFrame(1.0 / close.shape[1], index=close.index, columns=close.columns)
    w = w.mul(exposure, axis=0)
    return w.where(close.notna(), 0.0)   # a missing bar holds nothing
