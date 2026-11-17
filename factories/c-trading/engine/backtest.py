"""Backtest target weights with next-bar execution and costs on every trade.

The strategy decides at the close of bar t. The order fills at the open of bar
t+1, at a price moved against the trade by slippage, and pays the fee. Short
positions and leverage are allowed where the market's venue offers them. A
strategy that uses either pays that venue's fees and borrowing costs throughout,
and is closed out if the account would have been liquidated. A strategy cannot
change any of this.

The simulator is our own loop, because vectorbt has no leverage or borrowing
cost. Tests check it against a hand-written reference.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from numba import njit

from . import CONFIG
from .data import Bars


@dataclass
class Result:
    returns: pd.Series          # portfolio return per bar, net of costs
    daily: pd.Series            # the same, compounded per calendar day
    orders: int
    turnover_per_year: float    # traded value / equity, annualised
    cost_per_year: float        # fees, slippage and borrowing cost as a fraction of equity, annualised
    exposure: float             # average gross exposure
    liquidated: bool = False    # the account fell below the venue's margin requirement and was closed out
    margin: bool = False        # traded under the market's margin terms (it shorts or borrows)


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


@njit(cache=True)
def _simulate(open_, high, low, close, target, fee, slip, cash_rate, short_rate, hold_rate, maintenance, may_borrow):
    """One account, starting with 1.0 of cash. target[t, j] is the weight to move symbol j to at the
    open of bar t, or NaN to leave it alone. Rates are per bar. Returns equity at each close,
    traded value, trading cost, borrowing cost, order count and the bar of liquidation (-1 if none)."""
    n, m = close.shape
    pos = np.zeros(m)
    cash = 1.0
    equity = np.empty(n)
    traded = cost = borrow = 0.0
    orders = 0
    dead = -1
    for t in range(n):
        if dead < 0:
            value = cash
            for j in range(m):
                value += pos[j] * open_[t, j]
            # Sells first, then buys. An account that may not borrow buys only what its cash covers.
            for buying in (False, True):
                scale = 1.0
                if buying and not may_borrow:
                    need = 0.0
                    for j in range(m):
                        if not np.isnan(target[t, j]):
                            delta = target[t, j] * value / open_[t, j] - pos[j]
                            if delta > 0:
                                need += delta * open_[t, j] * (1.0 + slip) * (1.0 + fee)
                    if need > cash and need > 0.0:
                        scale = max(cash, 0.0) / need
                for j in range(m):
                    if not np.isnan(target[t, j]):
                        delta = target[t, j] * value / open_[t, j] - pos[j]
                        if delta != 0.0 and (delta > 0) == buying:
                            delta *= scale
                            px = open_[t, j] * (1.0 + slip if delta > 0 else 1.0 - slip)
                            cash -= delta * px + abs(delta) * px * fee
                            pos[j] += delta
                            traded += abs(delta) * open_[t, j]
                            cost += abs(delta) * open_[t, j] * (fee + slip)
                            orders += 1
            # The worst moment inside the bar: every long at its low, every short at its high.
            worst, gross = cash, 0.0
            for j in range(m):
                px = low[t, j] if pos[j] > 0 else high[t, j]
                worst += pos[j] * px
                gross += abs(pos[j]) * px
            if gross > 0.0 and worst < maintenance * gross:
                cash = max(0.0, worst - gross * (fee + slip))      # closed out by the venue at those prices
                pos[:] = 0.0
                dead = t
            else:
                longs = shorts = 0.0
                for j in range(m):
                    v = pos[j] * close[t, j]
                    if v > 0:
                        longs += v
                    else:
                        shorts -= v
                owed = (cash_rate * max(0.0, longs - (cash + longs - shorts)) + short_rate * shorts
                        + hold_rate * (longs + shorts))
                cash -= owed
                borrow += owed
        e = cash
        for j in range(m):
            e += pos[j] * close[t, j]
        equity[t] = e
    return equity, traded, cost, borrow, orders, dead


def terms(market: str, weights: pd.DataFrame) -> dict:
    """The costs and limits this strategy trades under. Long-only weights that never exceed the
    account's equity get the market's plain terms. Anything else gets its margin terms, throughout."""
    costs = CONFIG["costs"][market]
    w = weights.to_numpy(dtype=float)
    plain = {"fee": costs["fee"], "slippage": costs["slippage"], "financing_per_year": costs["financing_per_year"],
             "max_gross_exposure": 1.0, "borrow_cash_per_year": 0.0, "borrow_asset_per_year": 0.0,
             "maintenance_margin": 0.0, "margin": False}
    if (w >= 0).all() and w.sum(axis=1).max() <= 1.0 + 1e-9:
        return plain
    if "margin" not in costs:
        raise ValueError(f"short positions and leverage are not available in {market}")
    return plain | costs["margin"] | {"margin": True}


def check_weights(weights: pd.DataFrame, bars: Bars, market: str) -> dict:
    if not weights.index.equals(bars.close.index) or list(weights.columns) != bars.symbols:
        raise ValueError("weights must have the same index and columns as the bars")
    w = weights.to_numpy(dtype=float)
    if not np.isfinite(w).all():
        raise ValueError("weights contain NaN or infinite values")
    t = terms(market, weights)
    if np.abs(w).sum(axis=1).max() > t["max_gross_exposure"] + 1e-9:
        raise ValueError(f"gross exposure above the {market} limit of {t['max_gross_exposure']}")
    return t


def run(weights: pd.DataFrame, bars: Bars, dataset: str, cost_multiplier: float = 1.0,
        band: float | None = None) -> Result:
    spec = CONFIG["datasets"][dataset]
    costs = check_weights(weights, bars, spec["market"])

    # Decision at close of t, fill at open of t+1.
    band = CONFIG["execution"]["rebalance_band"] if band is None else float(band)
    target = _band(weights.shift(1).fillna(0.0).to_numpy(dtype=float), band)
    per_bar = cost_multiplier / spec["bars_per_year"]
    equity, traded, cost, borrow, orders, dead = _simulate(
        *(getattr(bars, f).to_numpy(dtype=float) for f in ("open", "high", "low", "close")), target,
        costs["fee"] * cost_multiplier, costs["slippage"] * cost_multiplier,
        costs["borrow_cash_per_year"] * per_bar, costs["borrow_asset_per_year"] * per_bar,
        costs["financing_per_year"] * per_bar, costs["maintenance_margin"], costs["margin"])
    before = np.concatenate(([1.0], equity[:-1]))
    returns = pd.Series(np.where(before > 0, equity / np.where(before > 0, before, 1.0) - 1.0, 0.0), index=weights.index)
    held = pd.DataFrame(target, index=weights.index, columns=weights.columns).ffill().fillna(0.0)
    if dead >= 0:
        held.iloc[dead:] = 0.0

    years = len(returns) / spec["bars_per_year"]
    avg_equity = max(float(equity.mean()), 1e-12)
    daily = (1.0 + returns).groupby(returns.index.normalize()).prod() - 1.0
    return Result(
        returns=returns, daily=daily, orders=int(orders),
        turnover_per_year=traded / avg_equity / years,
        cost_per_year=(cost + borrow) / avg_equity / years,
        exposure=float(held.abs().sum(axis=1).mean()),
        liquidated=dead >= 0, margin=costs["margin"],
    )


def buy_and_hold(bars: Bars, dataset: str) -> Result:
    """Equal weight across the symbols, bought once. The benchmark every strategy must beat."""
    n = len(bars.symbols)
    w = pd.DataFrame(1.0 / n, index=bars.close.index, columns=bars.symbols)
    return run(w, bars, dataset)
