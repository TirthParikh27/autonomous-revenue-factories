#!/usr/bin/env python3
"""Ad plan and read-back gate. No campaign may exist that is active, over budget or outside the plan.

    ads_paused.py PLAN.json [--readback READBACK.json] [--ledger spend.jsonl] [--month YYYY-MM]

Plan:     {"tranche": "demand_t1", "campaigns": [{"ref": "idea-1", "lifetime_budget_usd": 30, "days": 3, "country": "US"}]}
Readback: {"campaigns": [{"ref": "idea-1", "id": "123", "status": "PAUSED", "lifetime_budget_usd": 30}]}
Without --readback it validates the plan only (before the approval packet is raised).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from _common import load_budget, read_jsonl


def check_plan(plan: dict, budget: dict, ads_spent_this_month: float) -> list[str]:
    ads = budget["ads"]
    out = []
    tranche = plan.get("tranche")
    ceiling = ads.get(tranche)
    if not isinstance(ceiling, dict):
        return [f"unknown tranche '{tranche}'"]
    campaigns = plan.get("campaigns", [])
    if not campaigns:
        out.append("plan has no campaigns")
    if tranche.startswith("demand") and len(campaigns) > ads["max_ideas_per_batch"]:
        out.append(f"{len(campaigns)} ideas in the batch, limit is {ads['max_ideas_per_batch']}")
    refs = [c.get("ref") for c in campaigns]
    if len(refs) != len(set(refs)):
        out.append("duplicate campaign ref in plan")
    for c in campaigns:
        b = float(c.get("lifetime_budget_usd", 0))
        if b <= 0 or b > float(ceiling["lifetime_budget_usd"]):
            out.append(f"{c.get('ref')}: lifetime budget {b} is outside 0 to {ceiling['lifetime_budget_usd']}")
        if int(c.get("days", 0)) <= 0 or int(c.get("days", 0)) > int(ceiling["days"]):
            out.append(f"{c.get('ref')}: duration must be 1 to {ceiling['days']} days")
        if not c.get("country"):
            out.append(f"{c.get('ref')}: one country is required")
    total = sum(float(c.get("lifetime_budget_usd", 0)) for c in campaigns)
    cap = float(budget["monthly_caps_usd"]["ads"])
    if ads_spent_this_month + total > cap:
        out.append(f"batch total {total:.0f} plus {ads_spent_this_month:.0f} already spent exceeds the monthly ads cap of {cap:.0f}")
    return out


def check_readback(plan: dict, readback: dict) -> list[str]:
    out = []
    planned = {c["ref"]: c for c in plan.get("campaigns", [])}
    seen = set()
    for c in readback.get("campaigns", []):
        ref = c.get("ref")
        if ref not in planned:
            out.append(f"campaign {c.get('id')} ({ref}) is not in the plan")
            continue
        if ref in seen:
            out.append(f"{ref}: more than one campaign exists")
        seen.add(ref)
        if str(c.get("status", "")).upper() != "PAUSED":
            out.append(f"{ref}: status is {c.get('status')}, must be PAUSED")
        if float(c.get("lifetime_budget_usd", -1)) != float(planned[ref]["lifetime_budget_usd"]):
            out.append(f"{ref}: budget {c.get('lifetime_budget_usd')} differs from plan {planned[ref]['lifetime_budget_usd']}")
    for ref in planned.keys() - seen:
        out.append(f"{ref}: planned campaign was not read back")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("--readback", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--month", default=dt.date.today().strftime("%Y-%m"))
    args = parser.parse_args(argv)
    budget = load_budget()
    spent = sum(float(l.get("usd", 0)) for l in read_jsonl(args.ledger) if l.get("category") == "ads"
                and str(l.get("at", "")).startswith(args.month)) if args.ledger else 0.0
    plan = json.loads(args.plan.read_text())
    found = check_plan(plan, budget, spent)
    if args.readback:
        found += check_readback(plan, json.loads(args.readback.read_text()))
    for line in found:
        print(f"FAIL ads_paused: {line}")
    if not found:
        print(f"OK ads_paused: {len(plan['campaigns'])} campaign(s), {'read back paused' if args.readback else 'plan only'}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
