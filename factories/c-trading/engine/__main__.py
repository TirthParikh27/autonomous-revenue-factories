"""Command line for the engine.

    python -m engine check <strategy>            lint and leak test
    python -m engine trial <strategy> k=v ...    one counted trial
    python -m engine sweep <strategy> -n 40      search the declared ranges (every run counted)
    python -m engine gate <strategy>             the four checks on the chosen parameters
"""
from __future__ import annotations

import argparse
import json
import sys

from . import gate, strategy as strat, trials
from .data import load as load_bars


def _suggest(trial, ranges: dict) -> dict:
    out = {}
    for name, r in ranges.items():
        if isinstance(r["low"], float) or isinstance(r["high"], float):
            out[name] = trial.suggest_float(name, r["low"], r["high"], step=r.get("step"))
        else:
            out[name] = trial.suggest_int(name, r["low"], r["high"], step=r.get("step", 1))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="engine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "trial", "sweep", "gate"):
        p = sub.add_parser(name)
        p.add_argument("strategy")
        if name == "trial":
            p.add_argument("params", nargs="*")
        if name == "sweep":
            p.add_argument("-n", type=int, default=40)
            p.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    if args.cmd == "gate":
        out = gate.evaluate(args.strategy)
        print(json.dumps(out, indent=2))
        return 0 if out["pass"] else 1

    s = strat.load(args.strategy)
    bars = load_bars(s.dataset, s.symbols)

    if args.cmd == "check":
        params = s.chosen or {k: r["low"] for k, r in s.ranges.items()}
        problems = strat.leak_test(s, bars, params)
        print("lint: pass")
        print("leak test:", "pass" if not problems else "FAIL")
        for p in problems:
            print("  ", p)
        return 1 if problems else 0

    if args.cmd == "trial":
        params = {k: json.loads(v) for k, v in (p.split("=", 1) for p in args.params)} or s.chosen
        t, _ = trials.evaluate(s, params, bars)
        print(json.dumps(t, indent=2))
        return 0

    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objective(trial):
        t, _ = trials.evaluate(s, _suggest(trial, s.ranges), bars)
        return t["sharpe"]

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=args.seed))
    study.optimize(objective, n_trials=args.n)
    own = sorted((t for t in trials.read(s.dataset) if t["strategy"] == s.id and t["code_hash"] == s.code_hash),
                 key=lambda t: -t["sharpe"])
    print(f"{len(own)} trials of {s.id} logged on {s.dataset}. Top 10 by Sharpe:")
    for t in own[:10]:
        print(f"  {t['id']} sharpe {t['sharpe']:6.2f} return {t['total_return']:7.2%} "
              f"drawdown {t['max_drawdown']:7.2%} orders {t['orders']:5d} {t['params']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
