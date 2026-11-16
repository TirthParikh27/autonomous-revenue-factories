#!/usr/bin/env python3
"""Kill and winner rules. A script decides every transition from numbers and budget.yaml.

    decide.py METRICS.json [--out DECISIONS.json]

Metrics: {"items": [{"id": "...", "stage": "...", ...numbers for that stage...}]}
Fields per stage are listed next to each rule below. A rule whose inputs are missing or not yet
mature prints `insufficient data` and moves nothing. Thresholds are never rounded.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from _common import load_budget


class Missing(Exception):
    pass


def need(item: dict, *fields: str) -> list:
    absent = [f for f in fields if item.get(f) is None]
    if absent:
        raise Missing("missing " + ", ".join(absent))
    return [item[f] for f in fields]


def decision(item: dict, action: str, to: str | None, rule: str, packet: str | None = None) -> dict:
    return {"id": item["id"], "from": item["stage"], "action": action, "to": to, "rule": rule, "packet": packet}


def hold(item: dict, why: str) -> dict:
    return decision(item, "insufficient data", None, why)


def demand_t1(batch: list[dict], rules: dict) -> list[dict]:
    """Needs per item: tranche_ended, spend_usd, impressions, link_clicks, landing_page_views.
    Ranked inside the batch on cost per landing-page view. Decided only when the whole batch has ended."""
    try:
        for item in batch:
            need(item, "tranche_ended", "spend_usd", "impressions", "link_clicks", "landing_page_views")
    except Missing as why:
        return [hold(i, f"batch not readable: {why}") for i in batch]
    if not all(i["tranche_ended"] for i in batch):
        return [hold(i, "tranche 1 still running for part of the batch") for i in batch]

    def cost_per_view(i):
        return i["spend_usd"] / i["landing_page_views"] if i["landing_page_views"] else math.inf

    ranked = sorted(batch, key=lambda i: (cost_per_view(i), i["id"]))
    keep = math.ceil(len(batch) * rules["keep_top_fraction_of_batch"])
    out = []
    for position, item in enumerate(ranked, 1):
        ctr = 100.0 * item["link_clicks"] / item["impressions"] if item["impressions"] else 0.0
        detail = f"rank {position} of {len(batch)} on cost per view ({cost_per_view(item):.2f}), CTR {ctr:.2f}%"
        if position > keep:
            out.append(decision(item, "kill", "killed", f"outside top {keep}: {detail}"))
        elif ctr < rules["min_link_ctr_pct"]:
            out.append(decision(item, "kill", "killed", f"CTR under {rules['min_link_ctr_pct']}%: {detail}"))
        else:
            out.append(decision(item, "advance", "demand_t2", detail))
    return out


def demand_t2(item: dict, rules: dict) -> dict:
    """Needs: tranche_ended, visitors, committed_signups, spend_usd, top_ups_used."""
    ended, visitors, signups, spend, top_ups = need(
        item, "tranche_ended", "visitors", "committed_signups", "spend_usd", "top_ups_used")
    if not ended:
        return hold(item, "tranche 2 still running")
    can_top_up = top_ups < rules["top_ups_allowed"]
    if visitors < rules["min_visitors"]:
        if can_top_up:
            return decision(item, "top_up", "demand_t2", f"only {visitors} visitors, need {rules['min_visitors']}")
        return decision(item, "kill", "killed", f"only {visitors} visitors after the top-up")
    pct = 100.0 * signups / visitors
    cost = spend / signups if signups else math.inf
    detail = f"{signups}/{visitors} committed ({pct:.2f}%), cost per signup {cost:.2f}"
    if pct < rules["kill_below_committed_pct"]:
        return decision(item, "kill", "killed", f"under {rules['kill_below_committed_pct']}%: {detail}")
    if pct < rules["pass_at_committed_pct"]:
        if can_top_up:
            return decision(item, "top_up", "demand_t2", f"between kill and pass bars: {detail}")
        return decision(item, "kill", "killed", f"still under {rules['pass_at_committed_pct']}% after the top-up: {detail}")
    if cost > rules["max_cost_per_committed_signup_usd"]:
        return decision(item, "kill", "killed", f"cost per signup over {rules['max_cost_per_committed_signup_usd']}: {detail}")
    return decision(item, "advance", "demand_validated", detail)


def stale(item: dict, rules: dict) -> dict | None:
    """Needs: days_since_validated."""
    (days,) = need(item, "days_since_validated")
    if days > rules["stale_after_days"]:
        return decision(item, "kill", "killed", f"validated {days} days ago with no build slot")
    return None


def paid_t1(item: dict, rules: dict) -> dict:
    """Needs: tranche_ended, spend_usd, trials."""
    ended, spend, trials = need(item, "tranche_ended", "spend_usd", "trials")
    if trials == 0 and spend >= rules["kill_if_zero_trials_at_spend_usd"]:
        return decision(item, "sunset", "awaiting_human", f"zero trials at ${spend:.0f} spent", "A-SUN-1")
    if not ended:
        return hold(item, "paid tranche 1 still running")
    cost = spend / trials if trials else math.inf
    if cost > rules["max_cost_per_trial_usd"]:
        return decision(item, "sunset", "awaiting_human", f"cost per trial {cost:.2f} over {rules['max_cost_per_trial_usd']}", "A-SUN-1")
    return decision(item, "advance", "paid_t2", f"{trials} trials at {cost:.2f} each")


def paid_t2(item: dict, rules: dict, winner: dict) -> dict:
    """Needs: tranche_ended, spend_usd (both tranches), matured_trials, payers, d7_revenue_usd, refund_rate_pct."""
    ended, spend, matured, payers, revenue, refunds = need(
        item, "tranche_ended", "spend_usd", "matured_trials", "payers", "d7_revenue_usd", "refund_rate_pct")
    if not ended:
        return hold(item, "paid tranche 2 still running")
    if matured < rules["min_matured_trials"]:
        if item.get("all_trials_matured"):
            return decision(item, "sunset", "awaiting_human", f"only {matured} trials from the whole test", "A-SUN-1")
        return hold(item, f"{matured} matured trials, need {rules['min_matured_trials']}")
    paid_pct = 100.0 * payers / matured
    cost = spend / payers if payers else math.inf
    roas = 100.0 * revenue / spend if spend else 0.0
    detail = f"trial to paid {paid_pct:.1f}%, cost per payer {cost:.2f}, day-7 return {roas:.0f}%, {payers} payers, refunds {refunds}%"
    if paid_pct < rules["min_trial_to_paid_pct"] or cost > rules["max_cost_per_payer_usd"] or roas < rules["min_d7_roas_pct"]:
        return decision(item, "sunset", "awaiting_human", f"paid test kill rule: {detail}", "A-SUN-1")
    if (cost <= winner["max_cost_per_payer_usd"] and roas >= winner["min_d7_roas_pct"]
            and payers >= winner["min_payers"] and refunds <= winner["max_refund_rate_pct"]):
        return decision(item, "winner", "winner", detail, "A-WIN-1")
    return decision(item, "sunset", "awaiting_human", f"passed the kill rules but not the winner rule: {detail}", "A-SUN-1")


def winner_hold(item: dict, winner: dict) -> dict | None:
    """Needs: weekly_d7_roas_pct (list, oldest first), refund_rate_pct."""
    weekly, refunds = need(item, "weekly_d7_roas_pct", "refund_rate_pct")
    weeks = winner["hold"]["consecutive_weeks_below"]
    floor = winner["hold"]["min_d7_roas_pct"]
    if refunds > winner["max_refund_rate_pct"]:
        return decision(item, "sunset", "awaiting_human", f"refunds {refunds}% over {winner['max_refund_rate_pct']}%", "A-SUN-1")
    if len(weekly) >= weeks and all(w < floor for w in weekly[-weeks:]):
        return decision(item, "sunset", "awaiting_human", f"day-7 return under {floor}% for {weeks} weeks: {weekly[-weeks:]}", "A-SUN-1")
    return None


def decide(metrics: dict, budget: dict) -> list[dict]:
    out: list[dict] = []
    batches: dict[str, list[dict]] = defaultdict(list)
    for item in metrics.get("items", []):
        stage = item.get("stage")
        try:
            if stage == "demand_t1":
                batches[str(item.get("batch"))].append(item)
                continue
            result = {
                "demand_t2": lambda: demand_t2(item, budget["demand_test"]["t2"]),
                "demand_validated": lambda: stale(item, budget["demand_test"]),
                "paid_t1": lambda: paid_t1(item, budget["paid_test"]["t1"]),
                "paid_t2": lambda: paid_t2(item, budget["paid_test"]["t2"], budget["winner"]),
                "winner": lambda: winner_hold(item, budget["winner"]),
            }.get(stage, lambda: None)()
        except Missing as why:
            result = hold(item, str(why))
        if result:
            out.append(result)
    for batch in batches.values():
        out.extend(demand_t1(batch, budget["demand_test"]["t1"]))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("metrics", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    decisions = decide(json.loads(args.metrics.read_text()), load_budget())
    for d in decisions:
        target = f" -> {d['to']}" if d["to"] else ""
        packet = f" [{d['packet']}]" if d["packet"] else ""
        print(f"{d['id']}: {d['from']} {d['action']}{target}{packet}: {d['rule']}")
    if args.out:
        args.out.write_text(json.dumps(decisions, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
