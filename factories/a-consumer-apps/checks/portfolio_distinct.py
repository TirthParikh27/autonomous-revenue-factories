#!/usr/bin/env python3
"""Portfolio distinctness gate: a new spec must not be another version of something already in the pipeline.

    portfolio_distinct.py NEW_ITEM.json EXISTING_ITEM.json...

Item fields used: id, working_name, category, core_job (one sentence).
Fails when the name matches, when the core job is nearly the same sentence, or when the category
matches and the core jobs overlap heavily. Exit 0 distinct, 1 not.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import jaccard_pct, words

STOP = set("a an the to for of and or in on with your my you i it is that this app apps help helps "
           "people users so can by from at as be".split())
SAME_JOB_PCT = 60.0
SAME_CATEGORY_JOB_PCT = 40.0


def job_words(item: dict) -> set[str]:
    return {w for w in words(item.get("core_job", "")) if w not in STOP}


def problems(new: dict, existing: list[dict]) -> list[str]:
    out = []
    for other in existing:
        if other.get("id") == new.get("id"):
            continue
        if words(new.get("working_name", "")) and words(new.get("working_name", "")) == words(other.get("working_name", "")):
            out.append(f"same working name as {other['id']}")
        overlap = jaccard_pct(job_words(new), job_words(other))
        same_category = (new.get("category") or "").lower() == (other.get("category") or "").lower() != ""
        if overlap >= SAME_JOB_PCT:
            out.append(f"core job overlaps {overlap:.0f}% with {other['id']}")
        elif same_category and overlap >= SAME_CATEGORY_JOB_PCT:
            out.append(f"same category and core job overlaps {overlap:.0f}% with {other['id']}")
    return out


def main(argv: list[str]) -> int:
    new = json.loads(Path(argv[1]).read_text())
    existing = [json.loads(Path(p).read_text()) for p in argv[2:]]
    found = problems(new, existing)
    for line in found:
        print(f"FAIL portfolio_distinct: {line}")
    if not found:
        print(f"OK portfolio_distinct: distinct from {len(existing)} item(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
