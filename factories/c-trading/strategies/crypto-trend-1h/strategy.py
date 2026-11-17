import pandas as pd

from lib import indicators as ind


def weights(bars, params):
    close = bars.close
    up = ind.ema(close, params["fast"]) > ind.ema(close, params["slow"])
    inv_vol = 1.0 / ind.volatility(close, params["vol_window"])
    share = inv_vol.div(inv_vol.sum(axis=1), axis=0)      # each coin's share of the whole book
    return share.where(up, 0.0).fillna(0.0)
