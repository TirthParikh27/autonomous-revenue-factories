#!/usr/bin/env python3
"""Copy lint for pages, ads and content (FACTORY_SPEC.md section 3.3).

    copy_lint.py [--pre-build] [--has-price] [--claims claims.yaml] FILE...

Exit 0 if every file is clean, 1 otherwise. Each problem is printed with its file.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

BANNED = [
    (r"\b(users?|customers?|people|parents|students)\s+(say|says|love|loves|are loving|rave)\b", "speaks for customers"),
    (r"\bi\s+(love|loved|use|used|tried|lost|saved|made|switched)\b", "first-person customer statement"),
    (r"\b(changed|saved)\s+my\s+life\b", "first-person customer statement"),
    (r"\btestimonials?\b|\breviews?\s+from\b", "testimonial format"),
    (r"[★⭐]|\b[1-5](\.\d)?\s*(/|out of)\s*5\b|\b[1-5](\.\d)?[- ]stars?\b|\bfive[- ]stars?\b", "star rating"),
    (r"\b[\d,.]+\s*[km]?\+?\s+(reviews|ratings|downloads|installs|users|customers)\b", "review, download or user count"),
    (r"#1\b|\bnumber one\b|\bbest[- ]rated\b|\btop[- ]rated\b", "ranking claim"),
]
AVAILABLE_NOW = r"\b(download (it )?(now|today)|available (now|today)|get it on the app store|out now|install now)\b"
PRE_BUILD_MARK = r"\bin development\b|\bearly access\b"
NO_CHARGE_MARK = r"\bnothing is charged today\b|\bno charge today\b|\byou will not be charged\b"
NUMERIC_CLAIM = r"\b\d+(\.\d+)?\s?(%|x\b|times\b)"


def lint(text: str, pre_build: bool = False, has_price: bool = False, claims: list[str] | None = None) -> list[str]:
    problems = []
    low = text.lower()
    for pattern, label in BANNED:
        hit = re.search(pattern, low)
        if hit:
            problems.append(f"{label}: '{hit.group(0)}'")
    allowed = " ".join(claims or []).lower()
    for hit in re.finditer(NUMERIC_CLAIM, low):
        if hit.group(0) not in allowed:
            problems.append(f"numeric claim not in claims.yaml: '{hit.group(0)}'")
    if pre_build:
        if not re.search(PRE_BUILD_MARK, low):
            problems.append("pre-build copy must say 'in development' or 'early access'")
        hit = re.search(AVAILABLE_NOW, low)
        if hit:
            problems.append(f"implies the app is available: '{hit.group(0)}'")
    if has_price and not re.search(NO_CHARGE_MARK, low):
        problems.append("a page that shows a price must say nothing is charged today")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-build", action="store_true")
    parser.add_argument("--has-price", action="store_true")
    parser.add_argument("--claims", type=Path)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args(argv)
    claims = []
    if args.claims:
        loaded = yaml.safe_load(args.claims.read_text()) or {}
        claims = [c if isinstance(c, str) else str(c.get("claim", "")) for c in loaded.get("claims", [])]
    failed = False
    for path in args.files:
        for problem in lint(path.read_text(), args.pre_build, args.has_price, claims):
            failed = True
            print(f"FAIL {path}: {problem}")
    if not failed:
        print(f"OK copy_lint: {len(args.files)} file(s) clean")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
