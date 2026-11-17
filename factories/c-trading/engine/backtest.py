"""Backtest target weights with next-bar execution and costs on every trade.

The strategy decides at the close of bar t. The order fills at the open of bar
t+1, at a price moved against the trade by slippage, and pays the fee. A wrapper
around vectorbt that fixes these settings so a strategy cannot change them.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import vectorbt as vbt
from numba import njit

from . import CONFIG
from .data import Bars


@dataclass
class Result:
    returns: pd.Series          # portfolio return per bar, net of costs
    daily: pd.Series            # the same, compounded per calendar day
    orders: int
    turnover_per_year: float    # traded value / equity, annualised
    cost_per_year: float        # fees and slippage as a fraction of equity, annualised
    exposure: float             # average gross exposure


@njit(cache=True)
def _band(w: np.ndarray, band: float) -> np.ndarray:
    """Hold the previous target unless the new one differs by more than the band."""
    out = np.full(w.shape, np.nan)
    for j in range(w.shape[1]):
        held = 0.0
        for i in range(w.shape[0]):
            x = w[i, j]
            if abs(x - held) > band or (x == 0.0 and held != 0.0):
                held = x
                out[i, j] = x
    return out


def check_weights(weights: pd.DataFrame, bars: Bars, market: str) -> None:
    costs = CONFIG["costs"][market]
    if not weights.index.equals(bars.close.index) or list(weights.columns) != bars.symbols:
        raise ValueError("weights must have the same index and columns as the bars")
    w = weights.to_numpy(dtype=float)
    if not np.isfinite(w).all():
        raise ValueError("weights contain NaN or infinite values")
    if not costs["allow_short"] and (w < 0).any():
        raise ValueError(f"short positions are not allowed in {market}")
    if np.abs(w).sum(axis=1).max() > CONFIG["execution"]["max_gross_exposure"] + 1e-9:
        raise ValueError("gross exposure above the limit (no leverage)")


def run(weights: pd.DataFrame, bars: Bars, dataset: str, cost_multiplier: float = 1.0) -> Result:
    spec = CONFIG["datasets"][dataset]
    costs = CONFIG["costs"][spec["market"]]
    check_weights(weights, bars, spec["market"])

    # Decision at close of t, fill at open of t+1.
    target = _band(weights.shift(1).fillna(0.0).to_numpy(dtype=float), CONFIG["execution"]["rebalance_band"])
    size = pd.DataFrame(target, index=weights.index, columns=weights.columns)
    pf = vbt.Portfolio.from_orders(
        bars.close, size=size, size_type="targetpercent", price=bars.open,
        fees=costs["fee"] * cost_multiplier, slippage=costs["slippage"] * cost_multiplier,
        init_cash=1.0, cash_sharing=True, group_by=True, call_seq="auto", freq=spec["bar"],
    )
    value = pf.value()
    returns = pf.returns()
    held = pd.DataFrame(target, index=weights.index, columns=weights.columns).ffill().fillna(0.0)
    gross = held.abs().sum(axis=1)
    if costs["financing_per_day"]:
        per_bar = costs["financing_per_day"] * cost_multiplier * spec["days_per_year"] / spec["bars_per_year"]
        returns = returns - gross * per_bar

    years = len(returns) / spec["bars_per_year"]
    orders = pf.orders.records_readable
    traded = float((orders["Size"] * orders["Price"]).sum())
    slip_cost = traded * costs["slippage"] * cost_multiplier
    avg_equity = float(value.mean())
    daily = (1.0 + returns).groupby(returns.index.normalize()).prod() - 1.0
    return Result(
        returns=returns, daily=daily, orders=len(orders),
        turnover_per_year=traded / avg_equity / years,
        cost_per_year=(float(orders["Fees"].sum()) + slip_cost) / avg_equity / years,
        exposure=float(gross.mean()),
    )


def buy_and_hold(bars: Bars, dataset: str) -> Result:
    """Equal weight across the symbols, bought once. The benchmark every strategy must beat."""
    n = len(bars.symbols)
    w = pd.DataFrame(1.0 / n, index=bars.close.index, columns=bars.symbols)
    return run(w, bars, dataset)
