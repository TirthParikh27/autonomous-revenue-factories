#!/usr/bin/env python3
"""Gap evidence gate: one scout file per candidate must carry enough sourced, recent evidence.

    gap_schema.py SCOUT.json [--today YYYY-MM-DD]

Scout file (written by agents/market-scout.md, one candidate per file, state/scout/<id>.json):
  {"id": "2026-11-16-slug",
   "category": "Productivity",
   "unmet_job": "one sentence",
   "competitors": [{"name": "App", "store_url": "https://apps.apple.com/..."}],         at least 3
   "complaints": [{"id": "c1", "quote": "...", "app": "App", "source_url": "https://...",
                   "date": "2026-10-01"}],                                                 at least 15
   "keyword_popularity": [{"term": "...", "figure": 42, "source": "tool or url", "date": "..."}],  at least 1
   "trend_signals": [{"signal": "...", "source": "...", "date": "..."}],                   optional
   "not_found": ["..."], "injection_suspected": [{"url": "...", "text": "..."}]}           optional
Any object anywhere in the file with "estimate": true must also carry a non-empty "source".

Exit 1 if: a required field is missing, the category is in data/excluded_categories.yaml, fewer than
15 complaints or fewer than 3 distinct apps among them, a complaint lacks an http(s) source URL or a
date within the 12 months before --today, a competitor store URL is repeated, there is no keyword
popularity entry, or an estimate has no source.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml

from _common import FACTORY_DIR

MIN_COMPLAINTS = 15
MIN_COMPLAINT_APPS = 3
MIN_COMPETITORS = 3
MAX_AGE_DAYS = 365
EXCLUDED_FILE = FACTORY_DIR / "data" / "excluded_categories.yaml"


def load_excluded(path: Path | None = None) -> list[str]:
    loaded = yaml.safe_load((path or EXCLUDED_FILE).read_text()) or {}
    return [str(c).lower() for c in loaded.get("excluded", [])]


def excluded_match(category: str, excluded: list[str]) -> str | None:
    low = (category or "").lower()
    for phrase in excluded:
        if re.search(r"\b" + re.escape(phrase) + r"\b", low):
            return phrase
    return None


def is_url(value) -> bool:
    return isinstance(value, str) and re.match(r"https?://\S+$", value.strip()) is not None


def blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip()) or value == [] or value == {}


def estimates_without_source(node, where: str = "$") -> list[str]:
    out = []
    if isinstance(node, dict):
        if node.get("estimate") is True and blank(node.get("source")):
            out.append(where)
        for key, value in node.items():
            out += estimates_without_source(value, f"{where}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            out += estimates_without_source(value, f"{where}[{i}]")
    return out


def problems(scout: dict, today: dt.date, excluded: list[str]) -> list[str]:
    out = []
    for field in ("id", "category", "unmet_job", "competitors", "complaints", "keyword_popularity"):
        if blank(scout.get(field)):
            out.append(f"missing {field}")
    hit = excluded_match(str(scout.get("category", "")), excluded)
    if hit:
        out.append(f"category '{scout.get('category')}' is excluded ({hit})")

    competitors = scout.get("competitors") or []
    if len(competitors) < MIN_COMPETITORS:
        out.append(f"{len(competitors)} competitor(s), need at least {MIN_COMPETITORS}")
    seen_urls = set()
    for i, comp in enumerate(competitors):
        if blank(comp.get("name")):
            out.append(f"competitor {i} has no name")
        url = comp.get("store_url")
        if not is_url(url):
            out.append(f"competitor {i} has no http(s) store_url")
        elif url in seen_urls:
            out.append(f"competitor store_url repeated: {url}")
        else:
            seen_urls.add(url)

    complaints = scout.get("complaints") or []
    if len(complaints) < MIN_COMPLAINTS:
        out.append(f"{len(complaints)} complaint(s), need at least {MIN_COMPLAINTS}")
    apps = {str(c.get("app", "")).strip().lower() for c in complaints if not blank(c.get("app"))}
    if len(apps) < MIN_COMPLAINT_APPS:
        out.append(f"complaints cover {len(apps)} app(s), need at least {MIN_COMPLAINT_APPS}")
    oldest = today - dt.timedelta(days=MAX_AGE_DAYS)
    for i, c in enumerate(complaints):
        label = c.get("id", i)
        for field in ("quote", "app"):
            if blank(c.get(field)):
                out.append(f"complaint {label} has no {field}")
        if not is_url(c.get("source_url")):
            out.append(f"complaint {label} has no http(s) source_url")
        try:
            when = dt.date.fromisoformat(str(c.get("date", ""))[:10])
        except ValueError:
            out.append(f"complaint {label} has no valid date")
            continue
        if when < oldest:
            out.append(f"complaint {label} is dated {when}, older than 12 months")
        elif when > today:
            out.append(f"complaint {label} is dated {when}, after {today}")

    for i, k in enumerate(scout.get("keyword_popularity") or []):
        for field in ("term", "figure", "source", "date"):
            if blank(k.get(field)):
                out.append(f"keyword_popularity {i} has no {field}")

    for where in estimates_without_source(scout):
        out.append(f"estimate without a source at {where}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("scout", type=Path)
    parser.add_argument("--today", default=dt.date.today().isoformat())
    args = parser.parse_args(argv)
    try:
        scout = json.loads(args.scout.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL gap_schema: cannot read {args.scout}: {exc}")
        return 1
    found = problems(scout, dt.date.fromisoformat(args.today[:10]), load_excluded())
    for line in found:
        print(f"FAIL gap_schema: {line}")
    if not found:
        apps = {str(c["app"]).strip().lower() for c in scout["complaints"]}
        print(f"OK gap_schema: {len(scout['complaints'])} complaints across {len(apps)} apps")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
