#!/usr/bin/env python3
"""Pull request gate (REVIEW.md, "What CI enforces").

Fails when a pull request changes code but no test, or adds a coverage opt-out.
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
    """changes: (git status letter, path). Returns (code changed without a test, protected paths).

    D is a deleted file and R is the new name of a file moved without edits: neither needs a test,
    and neither counts as one.
    """
    edited = [path for status, path in changes if status not in ("D", "R")]
    code = [path for path in edited if is_code(path)]
    has_test = any(is_test(path) for path in edited)
    protected = sorted({path for _, path in changes if is_protected(path, patterns)})
    return ([] if has_test else code), protected


def parse_name_status(raw: str) -> list[tuple[str, str]]:
    """Reads `git diff -z --name-status -M100%`. -z keeps non-ASCII paths unquoted."""
    fields = [field for field in raw.split("\0") if field]
    changes, i = [], 0
    while i < len(fields):
        status = fields[i][0]
        if status == "R":
            changes += [("D", fields[i + 1]), ("R", fields[i + 2])]
            i += 3
        else:
            changes.append((status, fields[i + 1]))
            i += 2
    return changes


def git_diff(base: str, *args: str) -> str:
    return subprocess.run(
        ["git", "diff", *args, f"{base}...HEAD"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout


def coverage_opt_outs(diff: str) -> list[str]:
    """Added lines that hide code from the coverage rule."""
    return [
        line[1:].strip() for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++") and "pragma: no cover" in line
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="origin/main")
    args = parser.parse_args()

    patterns = protected_patterns((ROOT / ".github" / "CODEOWNERS").read_text())
    changes = parse_name_status(git_diff(args.base, "-z", "--name-status", "-M100%"))
    untested, protected = judge(changes, patterns)
    opt_outs = coverage_opt_outs(git_diff(args.base, "-U0", "--", "*.py", ":(exclude)tools/tests/test_pr_gate.py"))

    if protected:
        note = "Waits for the operator to merge. Protected files changed: " + ", ".join(protected)
        print(note)
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::notice::{note}")
    else:
        print("No protected files changed.")

    failed = False
    if untested:
        print("FAIL: code changed but no test did. Add a test for: " + ", ".join(untested))
        failed = True
    if opt_outs:
        print("FAIL: new 'pragma: no cover' hides code from the coverage rule: " + " | ".join(opt_outs))
        failed = True
    if not failed:
        print("OK: code changes come with tests.")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
