import numpy as np
import pandas as pd

from lib import indicators


def selection_days(valid, every):
    """True on the first bar with a full volatility estimate and every `every` bars after it."""
    out = np.zeros(len(valid), dtype=bool)
    first = np.flatnonzero(valid)
    if len(first):
        out[first[0]::every] = True
    return out


def weights(bars, params):
    close = bars.close
    vol = indicators.volatility(close, int(params["risk_lookback"]))   # trailing, past bars only
    k = int(params["bottom_k"])
    valid = vol.notna().all(axis=1).to_numpy()
    days = selection_days(valid, int(params["rebalance"]))

    # Lowest volatility gets rank 1. Ties break by column order, so the choice is deterministic.
    rank = vol.rank(axis=1, method="first").to_numpy()
    w = np.full(close.shape, np.nan)
    w[0] = 0.0                                   # cash until the first full estimate
    w[days] = np.where(rank[days] <= k, 1.0 / k, 0.0)
    # Between selection days the same coins are held at the same target, so nothing trades.
    return pd.DataFrame(w, index=close.index, columns=close.columns).ffill()
