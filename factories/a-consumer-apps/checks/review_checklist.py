#!/usr/bin/env python3
"""App Review checklist gate (skills/release-readiness step 4).

    review_checklist.py CHECKLIST.json --root DIR [--template data/review_checklist.yaml]

Checklist: {"rows": [{"id", "group", "result": "pass|fail",
                      "evidence": {"type": "file|test|screenshot", "ref": "path or test id"},
                      "unverified": false}]}
Exit 1 if: any row is not a pass; a row has no evidence or an unknown evidence type; a file or
screenshot ref is not an existing file under --root; a row is still `unverified: true`; a row id is
duplicated; or a row id in the template is absent from the checklist. A test ref must be non-empty;
the test result itself is CI's to prove.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from _common import FACTORY_DIR

TEMPLATE = FACTORY_DIR / "data" / "review_checklist.yaml"
EVIDENCE_TYPES = {"file", "test", "screenshot"}


def template_ids(path: Path | None = None) -> list[str]:
    loaded = yaml.safe_load((path or TEMPLATE).read_text()) or {}
    return [str(r["id"]) for r in loaded.get("rows", [])]


def under_root(root: Path, ref: str) -> bool:
    root = root.resolve()
    target = (root / ref).resolve()
    return (target == root or root in target.parents) and target.is_file()


def problems(checklist: dict, root: Path, required: list[str]) -> list[str]:
    out = []
    rows = checklist.get("rows") or []
    seen = set()
    for i, row in enumerate(rows):
        rid = row.get("id") or f"row {i}"
        if rid in seen:
            out.append(f"{rid}: duplicate id")
        seen.add(rid)
        if row.get("result") != "pass":
            out.append(f"{rid}: result is {row.get('result')!r}")
        if row.get("unverified") is True:
            out.append(f"{rid}: still marked unverified")
        evidence = row.get("evidence") or {}
        kind, ref = evidence.get("type"), str(evidence.get("ref") or "").strip()
        if kind not in EVIDENCE_TYPES or not ref:
            out.append(f"{rid}: no evidence")
        elif kind in ("file", "screenshot") and not under_root(root, ref):
            out.append(f"{rid}: {kind} evidence '{ref}' does not exist under {root}")
    for rid in required:
        if rid not in seen:
            out.append(f"{rid}: required by the checklist template but absent")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checklist", type=Path)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--template", type=Path, default=TEMPLATE)
    args = parser.parse_args(argv)
    checklist = json.loads(args.checklist.read_text())
    found = problems(checklist, args.root, template_ids(args.template))
    for line in found:
        print(f"FAIL review_checklist: {line}")
    if not found:
        print(f"OK review_checklist: {len(checklist['rows'])} row(s) pass with evidence")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
