#!/usr/bin/env python3
"""Pull request gate (REVIEW.md, "What CI enforces").

Fails when a pull request changes code but no test.
Also names the changed files that only the operator may merge (.github/CODEOWNERS).

    python tools/pr_gate.py [--base origin/main]
"""
import argparse
import fnmatch
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
CODE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".swift", ".sh", ".sql"}


def is_test(path: str) -> bool:
    p = PurePosixPath(path)
    return (
        "tests" in p.parts
        or "__tests__" in p.parts
        or p.name.startswith("test_")
        or p.name == "conftest.py"
        or ".test." in p.name
        or ".spec." in p.name
    )


def is_code(path: str) -> bool:
    return PurePosixPath(path).suffix in CODE_SUFFIXES and not is_test(path)


def protected_patterns(codeowners: str) -> list[str]:
    lines = (line.strip() for line in codeowners.splitlines())
    return [line.split()[0] for line in lines if line and not line.startswith("#")]


def is_protected(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        pattern = pattern.lstrip("/")
        if pattern.endswith("/"):
            pattern += "*"
        if fnmatch.fnmatchcase(path, pattern):
            return True
    return False


def judge(changes: list[tuple[str, str]], patterns: list[str]) -> tuple[list[str], list[str]]:
    """changes: (git status letter, path). Returns (code changed without a test, protected paths)."""
    live = [path for status, path in changes if status != "D"]
    code = [path for path in live if is_code(path)]
    has_test = any(is_test(path) for path in live)
    protected = sorted({path for _, path in changes if is_protected(path, patterns)})
    return ([] if has_test else code), protected


def changed(base: str) -> list[tuple[str, str]]:
    out = subprocess.run(
        ["git", "diff", "--name-status", "--no-renames", f"{base}...HEAD"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout
    return [tuple(line.split("\t", 1)) for line in out.splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="origin/main")
    args = parser.parse_args()

    patterns = protected_patterns((ROOT / ".github" / "CODEOWNERS").read_text())
    untested, protected = judge(changed(args.base), patterns)

    if protected:
        note = "Waits for the operator to merge. Protected files changed: " + ", ".join(protected)
        print(note)
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::notice::{note}")
    else:
        print("No protected files changed.")

    if untested:
        print("FAIL: code changed but no test did. Add a test for: " + ", ".join(untested))
        return 1
    print("OK: code changes come with tests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
