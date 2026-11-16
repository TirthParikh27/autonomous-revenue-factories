#!/usr/bin/env python3
"""Synthetic screen: turn three LLM rankings into kills. The script decides, not the model.

Each run file: {"card_order": [ids as shown], "ranking": [ids, best first]}.
Kills the bottom `screen_kill_fraction` by median rank. Ties at the cut line survive.
Exit 0 and write result.json, or exit 1 with the reason.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

from _common import load_budget


def evaluate(runs: list[dict], expected_runs: int, kill_fraction: float) -> dict:
    if len(runs) != expected_runs:
        raise ValueError(f"expected {expected_runs} run files, found {len(runs)}")
    ids = sorted(runs[0]["ranking"])
    if len(ids) != len(set(ids)):
        raise ValueError("run 1 ranks an idea twice")
    for n, run in enumerate(runs, 1):
        if sorted(run["ranking"]) != ids:
            raise ValueError(f"run {n} does not rank every idea exactly once")
        if sorted(run["card_order"]) != ids:
            raise ValueError(f"run {n} card_order does not list every idea exactly once")
    orders = [tuple(r["card_order"]) for r in runs]
    if len(ids) > 1 and len(set(orders)) != len(orders):
        raise ValueError("card order must differ between runs")

    median = {i: statistics.median(r["ranking"].index(i) + 1 for r in runs) for i in ids}
    ordered = sorted(ids, key=lambda i: (median[i], i))
    to_kill = int(len(ids) * kill_fraction)
    killed: list[str] = []
    if to_kill:
        cut = median[ordered[-to_kill]]            # best median rank inside the kill zone
        survivor_edge = median[ordered[-to_kill - 1]] if to_kill < len(ids) else None
        for i in ordered[-to_kill:]:
            if survivor_edge is not None and median[i] == survivor_edge and median[i] == cut:
                continue                            # tied with a survivor at the cut line
            killed.append(i)
    return {
        "median_rank": median,
        "screened": [i for i in ordered if i not in killed],
        "killed": killed,
        "reasons": {i: f"synthetic screen, rank {ordered.index(i) + 1} of {len(ids)}" for i in killed},
    }


def main(argv: list[str]) -> int:
    batch = Path(argv[1])
    budget = load_budget()["pipeline"]
    runs = [json.loads(p.read_text()) for p in sorted(batch.glob("run-*.json"))]
    try:
        result = evaluate(runs, int(budget["screen_runs"]), float(budget["screen_kill_fraction"]))
    except (ValueError, KeyError) as why:
        print(f"FAIL screen_rank: {why}")
        return 1
    (batch / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    for i in result["screened"]:
        print(f"{i}: discovered -> screened (median rank {result['median_rank'][i]})")
    for i in result["killed"]:
        print(f"{i}: discovered -> killed ({result['reasons'][i]})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
