"""The paper stage: a forward test on prices that did not exist when the strategy was built.

Runs daily inside the judge's GitHub job (FACTORY_EXAM=1). Every strategy that
passed the exam is run, at the exact code and parameters that passed, across all
data up to yesterday. Only the days after its exam count as its paper record.
Fills and costs are the engine's own, the same as in the backtest, so the paper
record and the backtest are directly comparable.

It also does the health watch: each record is compared with the range its
development result predicts, and the result is written to health/<id>.json.

    python -m engine.paper
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import norm

from . import CONFIG, GATE
from . import backtest, stats, strategy as strat, trials
from .data import Bars, load as load_bars

MIN_DAYS = 30        # a shorter record is reported but not judged


def _dir(name: str):
    return trials.state_dir().parent / name


def record(s: strat.Strategy, dev_bars: Bars, all_bars: Bars, started: str) -> tuple[dict, dict]:
    """The paper record from `started` (the first day the exam did not see), and its health."""
    cutoff = dev_bars.close.index[-1].normalize()
    full = backtest.run(strat.compute(s, all_bars, s.chosen), all_bars, s.dataset).daily
    bench = backtest.buy_and_hold(all_bars, s.dataset).daily
    seen = full.index <= cutoff
    dev_alpha, beta = stats.market_adjusted(full[seen].to_numpy(), bench[seen].to_numpy())
    live = full.index >= pd.Timestamp(started, tz="UTC")
    r, b = full[live].to_numpy(), bench[live].to_numpy()
    alpha = r - beta * b
    n, ppy = len(r), CONFIG["datasets"][s.dataset]["days_per_year"]

    paper = {
        "strategy": s.id, "code_hash": s.code_hash, "params": s.chosen, "started": started, "days": n,
        "last_day": str(full.index[live][-1].date()) if n else None,
        "paper_result": round(float(np.prod(1 + r) - 1), 4) if n else 0.0,
        "benchmark_result": round(float(np.prod(1 + b) - 1), 4) if n else 0.0,
        "market_adjusted_result": round(float(alpha.sum()), 4) if n else 0.0,
        "max_drawdown": round(stats.max_drawdown(r), 4) if n else 0.0,
        "sharpe": round(stats.annual_sharpe(r, ppy), 2) if n >= MIN_DAYS else None,
        "development_daily_volatility": round(float(full[seen].std(ddof=1)), 6),
        "note": "Forward test with the engine's own fills and costs. A paper result is not profit.",
        "daily": [[str(d.date()), round(float(x), 6), round(float(y), 6), round(float(a), 6)]
                  for d, x, y, a in zip(full.index[live], r, b, alpha)],      # date, strategy, benchmark, market-adjusted
    }

    # What development data predicts for a record this long, and whether the record is inside it.
    mu, sd = float(dev_alpha.mean()), float(dev_alpha.std(ddof=1))
    z = norm.ppf(1 - GATE["health_range_tail"])
    low, high = n * mu - z * sd * np.sqrt(n), n * mu + z * sd * np.sqrt(n)
    total = float(alpha.sum()) if n else 0.0
    status = "too_early" if n < MIN_DAYS else "below_range" if total < low else "above_range" if total > high else "in_range"
    health = {
        "strategy": s.id, "days": n, "status": status,
        "market_adjusted_result": round(total, 4),
        "predicted_range": [round(float(low), 4), round(float(high), 4)],
        "predicted_middle": round(n * mu, 4),
        "days_below_range_in_a_row": 0,
        "how_to_read": "below_range means the record is worse than all but the worst 5% of outcomes the "
                       "backtest predicts. in_range triggers nothing, however bad a stretch looks.",
    }
    return paper, health


def book(papers: list[dict]) -> dict:
    """The combined book: confirmed strategies at equal risk, so that a calm strategy and a
    wild one contribute the same. Weights are set from development volatility, never from paper results."""
    days = sorted({d[0] for p in papers for d in p["daily"]})
    series = {p["strategy"]: {d[0]: (d[1], d[3]) for d in p["daily"]} for p in papers}
    risk = {p["strategy"]: 1.0 / p["development_daily_volatility"] for p in papers if p["development_daily_volatility"] > 0}
    daily = []
    for day in days:
        live = [k for k in risk if day in series[k]]
        total = sum(risk[k] for k in live)
        daily.append([day, round(sum(risk[k] / total * series[k][day][0] for k in live), 6),
                      round(sum(risk[k] / total * series[k][day][1] for k in live), 6), len(live)])
    r = np.array([d[1] for d in daily])
    return {"strategies": sorted(risk), "days": len(daily),
            "paper_result": round(float(np.prod(1 + r) - 1), 4) if len(r) else 0.0,
            "market_adjusted_result": round(float(sum(d[2] for d in daily)), 4),
            "max_drawdown": round(stats.max_drawdown(r), 4) if len(r) else 0.0,
            "note": "Equal-risk combination of confirmed strategies. A paper result is not profit.",
            "daily": daily}       # date, book, market-adjusted, strategies live that day


def main() -> int:
    if os.environ.get("FACTORY_EXAM") != "1":
        print("refused: the paper stage runs only inside the judge's job", file=sys.stderr)
        return 2
    confirmed = []
    for path in sorted(_dir("exam").glob("*.json")):
        exam = json.loads(path.read_text())
        item_path = trials.state_dir() / "items" / f"{exam['strategy']}.json"
        item = json.loads(item_path.read_text()) if item_path.exists() else {}
        if not exam["pass"] or item.get("stage") not in ("paper", "confirmed", "paused", "awaiting_human"):
            continue
        sid = exam["strategy"]
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                s = strat.load(sid)
                if s.code_hash != exam["code_hash"] or s.chosen != exam["params"]:
                    raise PermissionError("the strategy is not the version that passed the exam")
                dev = load_bars(s.dataset, s.symbols)
                started = str((pd.Timestamp(exam["unseen_to"]) + pd.Timedelta(days=1)).date())
                paper, health = record(s, dev, load_bars(s.dataset, s.symbols, window="all"), started)
        except Exception as e:
            print(f"{sid}: paper run failed ({type(e).__name__})")
            continue
        old = _dir("health") / f"{sid}.json"
        if health["status"] == "below_range":
            before = json.loads(old.read_text()) if old.exists() else {}
            same_day = before.get("last_day") == paper["last_day"]
            health["days_below_range_in_a_row"] = before.get("days_below_range_in_a_row", 0) + (0 if same_day else 1)
        health["last_day"] = paper["last_day"]
        for folder, doc in (("paper", paper), ("health", health)):
            _dir(folder).mkdir(parents=True, exist_ok=True)
            (_dir(folder) / f"{sid}.json").write_text(json.dumps(doc, indent=2) + "\n")
        if item.get("stage") in ("confirmed", "awaiting_human"):
            confirmed.append(paper)
        print(f"{sid}: {paper['days']} paper days, {health['status']}")
    if confirmed:
        (_dir("paper") / "book.json").write_text(json.dumps(book(confirmed), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
