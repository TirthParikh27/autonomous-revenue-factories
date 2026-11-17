"""The final exam: one look at data the strategy has never been tested on.

Runs only inside the exam job (FACTORY_EXAM=1), on a clean copy of the engine.
It re-runs the gate on development data, then runs the strategy once across the
held-back window. The published result is pass or fail per check and nothing
else, so the held-back window cannot be learned from.

    python -m engine.exam <strategy>
"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import os
import sys

import numpy as np
from scipy.stats import norm

from . import CONFIG, GATE
from . import backtest, gate, stats, strategy as strat, trials
from .data import Bars, load as load_bars


def exam_dir():
    return trials.state_dir().parent / "exam"


def _closed_family(s: strat.Strategy, daily: np.ndarray) -> str | None:
    """A strategy that behaves like one that already failed the exam is the same family."""
    for path in sorted(exam_dir().glob("*.json")):
        old = json.loads(path.read_text())
        if old["pass"] or old["dataset"] != s.dataset or old["strategy"] == s.id:
            continue
        match = [t for t in trials.read(s.dataset) if t["id"] == old.get("trial")]
        if not match:
            continue
        other = trials.daily_returns(match[0])
        n = min(len(other), len(daily))
        if n > 30 and np.corrcoef(daily[-n:], other[-n:])[0, 1] >= GATE["trial_cluster_correlation"]:
            return old["strategy"]
    return None


def holdout(s: strat.Strategy, dev_bars: Bars, all_bars: Bars) -> dict[str, bool]:
    """The single look. Uses development data for warm-up and for the predicted
    range, and judges only the bars after the development window ends."""
    cutoff = dev_bars.close.index[-1].normalize()
    leaks = strat.leak_test(s, all_bars, s.chosen)
    run = backtest.run(strat.compute(s, all_bars, s.chosen), all_bars, s.dataset, band=s.band)
    full = run.daily
    bench = backtest.buy_and_hold(all_bars, s.dataset).daily
    seen, unseen = full.index <= cutoff, full.index > cutoff
    if unseen.sum() < 60:
        raise ValueError(f"only {int(unseen.sum())} held-back days: too few for an exam")

    # Market exposure is estimated on development data, so nothing is fitted to the unseen window.
    dev_alpha, beta = stats.market_adjusted(full[seen].to_numpy(), bench[seen].to_numpy())
    alpha = full[unseen].to_numpy() - beta * bench[unseen].to_numpy()

    # The lowest Sharpe the development result makes plausible over a window this short
    # (Lo 2002 standard error of the Sharpe ratio).
    expected = stats.sharpe(dev_alpha)
    floor = expected - norm.ppf(1 - GATE["exam_range_tail"]) * np.sqrt((1 + 0.5 * expected ** 2) / len(alpha))
    return {
        "leak_test_on_unseen_data": not leaks,
        "positive_after_costs_on_unseen_data": bool(alpha.mean() > 0),
        "never_liquidated": not run.liquidated,
        "inside_predicted_range": bool(stats.sharpe(alpha) >= floor),
    }


def evaluate(strategy: str | strat.Strategy, dev_bars: Bars | None = None, all_bars: Bars | None = None) -> dict:
    s = strat.load(strategy) if isinstance(strategy, str) else strategy
    gate_path = trials.state_dir() / "gate" / f"{s.id}.json"
    local = json.loads(gate_path.read_text()) if gate_path.exists() else {}
    logged = {t["id"] for t in trials.read(s.dataset) if t["strategy"] == s.id and t["code_hash"] == s.code_hash}
    checks = {
        # The strategy as submitted is the one whose trials were counted.
        "local_trials_in_log": bool(local) and local.get("code_hash") == s.code_hash
        and local.get("params") == s.chosen and local.get("trial") in logged,
    }
    out = {"strategy": s.id, "dataset": s.dataset, "code_hash": s.code_hash, "params": s.chosen,
           "trial": local.get("trial"), "engine_version": CONFIG["engine_version"],
           "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    if checks["local_trials_in_log"]:
        dev_bars = dev_bars or load_bars(s.dataset, s.symbols)
        again = gate.evaluate(s, dev_bars)
        checks["gate_on_development_data"] = bool(again["pass"])
        daily = trials.daily_returns(next(t for t in trials.read(s.dataset) if t["id"] == again["trial"]))
        closed = _closed_family(s, daily)
        checks["family_not_already_failed"] = closed is None
        if all(checks.values()):       # the unseen window is looked at only when everything else holds
            all_bars = all_bars or load_bars(s.dataset, s.symbols, window="all")
            out["unseen_from"] = str(dev_bars.close.index[-1].normalize().date() + dt.timedelta(days=1))
            out["unseen_to"] = str(all_bars.close.index[-1].date())
            checks.update(holdout(s, dev_bars, all_bars))
    out["pass"] = all(checks.values())
    out["checks"] = checks
    return out


def main(argv: list[str] | None = None) -> int:
    if os.environ.get("FACTORY_EXAM") != "1":
        print("refused: the exam runs only inside the final exam job", file=sys.stderr)
        return 2
    strategy_id = (argv or sys.argv[1:])[0]
    path = exam_dir() / f"{strategy_id}.json"
    if path.exists():
        print(f"refused: {strategy_id} has already taken the exam", file=sys.stderr)
        return 2
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            out = evaluate(strategy_id)                 # strategy code cannot print what it sees
    except Exception as e:                              # the message could carry data, the type cannot
        print(f"{strategy_id}: the exam could not run ({type(e).__name__})")
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n")

    item = trials.state_dir() / "items" / f"{strategy_id}.json"
    if item.exists():
        doc = json.loads(item.read_text())
        failed = [k for k, ok in out["checks"].items() if not ok]
        to = "paper" if out["pass"] else "killed"
        doc["history"].append({"at": out["at"], "from": doc["stage"], "to": to, "run": "exam job",
                               "note": "passed the final exam" if out["pass"] else "failed the final exam: " + ", ".join(failed)})
        doc["stage"], doc["updated"] = to, out["at"][:10]
        item.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"{strategy_id}: {'pass' if out['pass'] else 'fail'}")
    for name, ok in out["checks"].items():
        print(f"  {name}: {'pass' if ok else 'fail'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
