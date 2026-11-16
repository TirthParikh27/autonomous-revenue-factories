#!/usr/bin/env python3
"""Release cadence gate. Reads state/submissions.jsonl, which only the operator writes.

    cadence.py SUBMISSIONS.jsonl --live-apps N [--today YYYY-MM-DD]

Line format: {"date": "2026-12-01", "app": "id", "kind": "new_app|update|resubmission",
              "outcome": "pending|approved|rejected", "citation": "4.3"}
A freeze is lifted only by an operator line {"date": ..., "kind": "freeze_lifted"} (after A-ACCT-1).
Exit 0 if a new-app submission is allowed today, 1 if not. Prints the reason and the earliest date.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from _common import load_budget, read_jsonl

FREEZE_WORDS = {"guideline_4_3": ("4.3",), "spam": ("spam",), "dpla_3_2_f": ("3.2(f)", "3.2f"),
                "fraud": ("fraud",), "account_warning": ("warning",)}


def d(value: str) -> dt.date:
    return dt.date.fromisoformat(value[:10])


def frozen(subs: list[dict], rules: dict) -> str | None:
    triggers = [w for key in rules.get("freeze_submissions_on", []) for w in FREEZE_WORDS.get(key, (key,))]
    reason = None
    for s in sorted(subs, key=lambda s: s["date"]):
        if s.get("kind") == "freeze_lifted":
            reason = None
            continue
        citation = str(s.get("citation", "")).lower()
        if (s.get("outcome") == "rejected" or s.get("kind") == "account_notice") and any(t in citation for t in triggers):
            reason = f"frozen by {s['date']} {s.get('app', 'account')}: {s.get('citation')}"
    return reason


def blockers(subs: list[dict], rules: dict, live_apps: int, day: dt.date) -> list[str]:
    """Why a new-app submission is not allowed on `day`. Empty means allowed."""
    why = []
    freeze = frozen(subs, rules)
    if freeze:
        return [freeze]
    past = [s for s in subs if s.get("kind") in ("new_app", "update", "resubmission") and d(s["date"]) <= day]
    new_apps = [s for s in past if s["kind"] == "new_app"]
    if live_apps >= rules["max_live_apps"]:
        why.append(f"{live_apps} live apps, cap is {rules['max_live_apps']}")
    if sum(1 for s in past if d(s["date"]) == day) >= rules["max_submissions_of_any_kind_per_day"]:
        why.append("a submission was already made today")
    approved = sum(1 for s in new_apps if s.get("outcome") == "approved")
    ramped = approved >= rules["clean_approvals_before_ramp"]
    per_month = rules["new_app_submissions_per_month_after_ramp" if ramped else "new_app_submissions_per_month_initial"]
    this_month = sum(1 for s in new_apps if (d(s["date"]).year, d(s["date"]).month) == (day.year, day.month))
    if this_month >= per_month:
        why.append(f"{this_month} new-app submission(s) this month, limit is {per_month}")
    if new_apps:
        gap = (day - max(d(s["date"]) for s in new_apps)).days
        if gap < rules["min_days_between_new_app_submissions"]:
            why.append(f"{gap} days since the last new app, minimum is {rules['min_days_between_new_app_submissions']}")
    rolling = sum(1 for s in new_apps if (day - d(s["date"])).days < 365)
    if rolling >= rules["max_new_apps_rolling_12_months"]:
        why.append(f"{rolling} new apps in the last 12 months, cap is {rules['max_new_apps_rolling_12_months']}")
    return why


def earliest(subs: list[dict], rules: dict, live_apps: int, start: dt.date) -> dt.date | None:
    for offset in range(0, 400):
        day = start + dt.timedelta(days=offset)
        if not blockers(subs, rules, live_apps, day):
            return day
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("submissions", type=Path)
    parser.add_argument("--live-apps", type=int, required=True)
    parser.add_argument("--today", default=dt.date.today().isoformat())
    args = parser.parse_args(argv)
    rules = load_budget()["account_protection"]
    subs = read_jsonl(args.submissions)
    today = d(args.today)
    why = blockers(subs, rules, args.live_apps, today)
    if not why:
        print("OK cadence: a new-app submission is allowed today")
        return 0
    for reason in why:
        print(f"WAIT cadence: {reason}")
    when = None if frozen(subs, rules) or args.live_apps >= rules["max_live_apps"] else earliest(subs, rules, args.live_apps, today)
    print(f"earliest allowed date: {when.isoformat() if when else 'none until the operator acts'}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
