#!/usr/bin/env python3
"""Spec and differentiation gate (skills/spec-differentiation).

    spec_gate.py SPEC.md SCOUT.json [--earlier SPECS_DIR]

The spec is markdown with YAML front matter between two `---` lines:
  id:                        item id
  working_name:              the app's working name
  category:                  must not be in data/excluded_categories.yaml
  core_job:                  the single job, one sentence (also used by portfolio_distinct)
  proposed_price_usd_month:  a positive number, shown on the demand-test page
  differentiator:            the capability that sets it apart, one sentence
  differentiator_type:       e.g. capability, workflow, data, integration. Never `visual` or `price`
  competitors:               list of {name, store_url}; at least
                             account_protection.min_named_competitors_in_spec, each store_url taken
                             from the scout file's competitors
  complaint_refs:            ids (or 0-based list indexes) of scout complaints; at least 3 distinct
                             complaints about at least 3 different apps
The body must have the sections named in the skill as headings (any level) and be under 600 words.
With --earlier, the core_job must not equal (normalised) the core_job of any other spec there.
Exit 0 on pass, 1 on fail.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from _common import load_budget, words
from gap_schema import excluded_match, load_excluded

MAX_WORDS = 600
MIN_COMPLAINT_REFS = 3
MIN_COMPLAINT_APPS = 3
BANNED_DIFFERENTIATOR_TYPES = {"visual", "price"}
FIELDS = ("id", "working_name", "category", "core_job", "proposed_price_usd_month", "differentiator",
          "differentiator_type", "competitors", "complaint_refs")
SECTIONS = ("job", "differentiation statement", "competitor table", "core features", "not building",
            "monetisation", "target market", "demand test plan", "review risk", "claims")


def split_front_matter(text: str) -> tuple[dict | None, str]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*(\n|\Z)", text, re.S)
    if not match:
        return None, text
    try:
        front = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None, text[match.end():]
    return (front if isinstance(front, dict) else None), text[match.end():]


def headings(body: str) -> list[str]:
    return [h.strip().strip("*:").strip().lower() for h in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", body, re.M)]


def resolve_complaint(ref, complaints: list[dict]) -> dict | None:
    for c in complaints:
        if "id" in c and str(c["id"]) == str(ref):
            return c
    if isinstance(ref, int) and not isinstance(ref, bool) and 0 <= ref < len(complaints):
        return complaints[ref]
    return None


def problems(text: str, scout: dict, min_competitors: int, excluded: list[str],
             earlier_jobs: dict[str, str] | None = None) -> list[str]:
    front, body = split_front_matter(text)
    if front is None:
        return ["no YAML front matter"]
    out = [f"missing {f}" for f in FIELDS if front.get(f) in (None, "", [])]

    hit = excluded_match(str(front.get("category", "")), excluded)
    if hit:
        out.append(f"category '{front.get('category')}' is excluded ({hit})")

    price = front.get("proposed_price_usd_month")
    if price is not None and (isinstance(price, bool) or not isinstance(price, (int, float)) or price <= 0):
        out.append(f"proposed_price_usd_month must be a positive number, got {price!r}")

    dtype = str(front.get("differentiator_type") or "").strip().lower()
    if dtype in BANNED_DIFFERENTIATOR_TYPES:
        out.append(f"differentiator_type is '{dtype}', which is not a capability")

    scout_urls = {c.get("store_url") for c in scout.get("competitors") or []}
    competitors = front.get("competitors") or []
    if len(competitors) < min_competitors:
        out.append(f"{len(competitors)} named competitor(s), need at least {min_competitors}")
    for comp in competitors:
        comp = comp if isinstance(comp, dict) else {}
        if not comp.get("name"):
            out.append("a competitor has no name")
        if comp.get("store_url") not in scout_urls:
            out.append(f"competitor URL not in scout file: {comp.get('store_url')}")

    complaints = scout.get("complaints") or []
    refs = front.get("complaint_refs") or []
    cited = {}
    for ref in refs:
        found = resolve_complaint(ref, complaints)
        if found is None:
            out.append(f"complaint ref {ref!r} is not in the scout file")
        else:
            cited[id(found)] = found
    apps = {str(c.get("app", "")).strip().lower() for c in cited.values()}
    if len(cited) < MIN_COMPLAINT_REFS or len(apps) < MIN_COMPLAINT_APPS:
        out.append(f"cites {len(cited)} complaint(s) from {len(apps)} app(s), "
                   f"need {MIN_COMPLAINT_REFS} from {MIN_COMPLAINT_APPS} different apps")

    present = headings(body)
    for section in SECTIONS:
        if not any(h.startswith(section) for h in present):
            out.append(f"missing section '{section}'")
    count = len(words(body))
    if count >= MAX_WORDS:
        out.append(f"body is {count} words, must be under {MAX_WORDS}")

    job = " ".join(words(str(front.get("core_job") or "")))
    for label, other in (earlier_jobs or {}).items():
        if job and job == " ".join(words(other)):
            out.append(f"core_job matches {label}")
    return out


def earlier(specs_dir: Path | None, skip: Path) -> dict[str, str]:
    jobs = {}
    if specs_dir and specs_dir.is_dir():
        for path in sorted(specs_dir.glob("*.md")):
            if path.resolve() == skip.resolve():
                continue
            front, _ = split_front_matter(path.read_text())
            if front and front.get("core_job"):
                jobs[path.name] = str(front["core_job"])
    return jobs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("scout", type=Path)
    parser.add_argument("--earlier", type=Path, help="directory of earlier specs (state/specs/)")
    args = parser.parse_args(argv)
    minimum = int(load_budget()["account_protection"]["min_named_competitors_in_spec"])
    scout = json.loads(args.scout.read_text())
    found = problems(args.spec.read_text(), scout, minimum, load_excluded(), earlier(args.earlier, args.spec))
    for line in found:
        print(f"FAIL spec_gate: {line}")
    if not found:
        print(f"OK spec_gate: {args.spec.name} passes")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
