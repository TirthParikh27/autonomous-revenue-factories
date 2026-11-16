#!/usr/bin/env python3
"""Feature-code overlap gate (CLAUDE.md hard rule 5, skills/mvp-build).

    overlap.py NEW_APP_DIR OTHER_APP_DIR...

Counts the new app's normalised source lines that also appear anywhere in the other app's source,
as a percent of the new app's lines. A line is normalised by removing all whitespace. Skipped:
blank lines, comment-only lines, import/require/re-export lines, and lines under 12 characters
after normalising. Skipped files: anything in a folder named or pathed as an entry of
account_protection.shared_scaffold_paths (at any depth, e.g. auth/ or src/auth/), hidden
paths, node_modules, build output, lockfiles, tests and config files; only source extensions count.
Exit 1 if the overlap with any other app is over account_protection.max_feature_code_overlap_pct.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from _common import load_budget

SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".swift", ".kt", ".java", ".py", ".sql"}
SKIP_DIRS = {"node_modules", "dist", "build", "ios", "android", "coverage", "test", "tests", "__tests__",
             "__mocks__", "e2e"}
LOCKFILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "podfile.lock"}
TEST_NAME = re.compile(r"\.(test|spec)\.[a-z]+$|^test_.*\.py$|_test\.py$", re.I)
CONFIG_NAME = re.compile(r"config|rc\.[a-z]+$|^babel\.|^metro\.|^jest\.|^eas\.|^app\.json$", re.I)
COMMENT = re.compile(r"^(//|/\*|\*|\*/|#|--|<!--)")
IMPORT = re.compile(r"^(import\b|from\s+\S+\s+import\b|export\s+(\*|\{[^}]*\})\s+from\b|"
                    r"(const|let|var)\s+[\w{},\s]+=\s*require\()")
MIN_LINE = 12


def included(rel: Path, scaffold: set[str]) -> bool:
    parts = [p.lower() for p in rel.parts]
    if any(p.startswith(".") for p in parts):
        return False
    if any(p in SKIP_DIRS for p in parts[:-1]):
        return False
    # a scaffold path may sit at any depth (auth/, src/auth/, app/(tabs)/settings/)
    joined = "/" + "/".join(parts[:-1]) + "/"
    if any(f"/{s}/" in joined for s in scaffold):
        return False
    name = parts[-1]
    if name in LOCKFILES or name.endswith(".lock") or TEST_NAME.search(name) or CONFIG_NAME.search(name):
        return False
    return rel.suffix.lower() in SOURCE_SUFFIXES


def normalise(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or COMMENT.match(stripped) or IMPORT.match(stripped):
        return None
    flat = re.sub(r"\s+", "", stripped)
    return flat if len(flat) >= MIN_LINE else None


def source_lines(root: Path, scaffold: list[str]) -> list[str]:
    scaffold_set = {s.strip("/").lower() for s in scaffold}
    out = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and included(path.relative_to(root), scaffold_set):
            for line in path.read_text(errors="ignore").splitlines():
                norm = normalise(line)
                if norm:
                    out.append(norm)
    return out


def overlap_pct(new_lines: list[str], other_lines: list[str]) -> float:
    if not new_lines:
        return 0.0
    other = set(other_lines)
    return 100.0 * sum(1 for line in new_lines if line in other) / len(new_lines)


def evaluate(new: Path, others: list[Path], scaffold: list[str], limit: float) -> tuple[dict[str, float], list[str]]:
    new_lines = source_lines(new, scaffold)
    scores = {str(o): overlap_pct(new_lines, source_lines(o, scaffold)) for o in others}
    fails = [f"{pct:.1f}% of {new.name} feature lines also in {label} (limit {limit:g}%)"
             for label, pct in scores.items() if pct > limit]
    return scores, fails


def main(argv: list[str]) -> int:
    rules = load_budget()["account_protection"]
    limit = float(rules["max_feature_code_overlap_pct"])
    new, others = Path(argv[1]), [Path(p) for p in argv[2:]]
    scores, fails = evaluate(new, others, rules["shared_scaffold_paths"], limit)
    for line in fails:
        print(f"FAIL overlap: {line}")
    for label, pct in scores.items():
        if pct <= limit:
            print(f"OK overlap: {pct:.1f}% with {label} (limit {limit:g}%)")
    if not others:
        print("OK overlap: no other apps to compare")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
