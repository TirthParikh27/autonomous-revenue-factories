#!/usr/bin/env python3
"""Pull request gate (REVIEW.md, "What CI enforces").

Fails when a pull request changes code but no test, or adds a coverage opt-out.
Also names the changed files that only the operator may merge: .github/CODEOWNERS and each
factory's deny list in factories/<name>/.claude/settings.json.

    python tools/pr_gate.py [--base origin/main]
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

from coverage.config import DEFAULT_EXCLUDE

ROOT = Path(__file__).resolve().parents[1]
# The same comment forms coverage itself treats as "do not measure this".
OPT_OUT = re.compile(DEFAULT_EXCLUDE[0])  # the other defaults hide no runtime code
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
    """CODEOWNERS matching for paths written from the root: * stays inside one folder, ** does not."""
    for pattern in patterns:
        parts = re.split(r"(\*\*|\*)", pattern.strip("/"))
        body = "".join({"**": ".*", "*": "[^/]*"}.get(part, re.escape(part)) for part in parts)
        if re.fullmatch(body + "(/.*)?", path):
            return True
    return False


def deny_patterns(settings_path: str, settings_text: str) -> list[str]:
    """A factory's own deny list: what its runs may not edit, a session may not merge either."""
    factory = settings_path.split("/.claude/")[0]
    try:
        deny = json.loads(settings_text).get("permissions", {}).get("deny", [])
    except (ValueError, AttributeError):
        return []
    found = (re.fullmatch(r"(?:Edit|Write)\((.+)\)", str(rule)) for rule in deny)
    return sorted({f"/{factory}/{match.group(1).lstrip('/')}" for match in found if match})


def factory_settings(base: str) -> list[tuple[str, str]]:
    """Every factories/<name>/.claude/settings.json, on the base and in the checkout."""
    show = lambda *args: subprocess.run(  # noqa: E731
        ["git", *args], cwd=ROOT, capture_output=True, text=True, errors="replace",
    ).stdout
    listed = show("ls-tree", "-r", "--name-only", base, "--", "factories").splitlines()
    files = [(path, show("show", f"{base}:{path}")) for path in listed if path.endswith("/.claude/settings.json")]
    for here in sorted(ROOT.glob("factories/*/.claude/settings.json")):
        files.append((here.relative_to(ROOT).as_posix(), here.read_text(errors="replace")))
    return files


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


def git_diff(base: str, *args: str, paths: tuple[str, ...] = ()) -> str:
    return subprocess.run(
        ["git", "diff", *args, f"{base}...HEAD", "--", *paths],
        cwd=ROOT, check=True, capture_output=True, text=True, errors="replace",
    ).stdout


def coverage_opt_outs(diff: str) -> list[str]:
    """Added lines that hide code from the coverage rule."""
    return [
        line[1:].strip() for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++") and OPT_OUT.search(line)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="origin/main")
    args = parser.parse_args()

    # The list on the base branch counts too, as on GitHub, so a pull request cannot unprotect its own files.
    on_base = subprocess.run(
        ["git", "show", f"{args.base}:.github/CODEOWNERS"],
        cwd=ROOT, capture_output=True, text=True, errors="replace",
    ).stdout
    here = ROOT / ".github" / "CODEOWNERS"
    patterns = protected_patterns(on_base + "\n" + (here.read_text() if here.exists() else ""))
    for path, text in factory_settings(args.base):
        patterns += deny_patterns(path, text)
    changes = parse_name_status(git_diff(args.base, "-z", "--name-status", "-M100%"))
    untested, protected = judge(changes, patterns)
    opt_outs = coverage_opt_outs(git_diff(
        args.base, "-U0", paths=("*.py", ":(exclude,glob)**/tests/**", ":(exclude,glob)**/test_*.py")
    ))

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
