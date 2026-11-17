#!/usr/bin/env python3
"""Pull request gate (REVIEW.md, "What CI enforces").

Fails when a pull request changes code but no test, or adds a coverage opt-out.
Names the changed files that only the operator may merge: .github/CODEOWNERS and each
factory's deny list in factories/<name>/.claude/settings.json.
Names the tests a pull request removes or skips, for the reviewer to check.

    python tools/pr_gate.py [--base origin/main]
"""
import argparse
import ast
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
    if not isinstance(deny, list):
        return []
    patterns = set()
    for rule in deny:
        match = re.fullmatch(r"(?:Edit|Write)\((.+)\)", str(rule))
        if not match:
            continue
        path = match.group(1).removeprefix("./").lstrip("/")
        patterns.add(f"/{factory}/{path}")
        if "/" not in path:  # like .gitignore, a rule with no slash applies at any depth
            patterns.add(f"/{factory}/**/{path}")
    return sorted(patterns)


def factory_settings(base: str) -> list[tuple[str, str]]:
    """Every factories/<name>/.claude/settings.json, on the base and in the checkout."""
    show = lambda *args: subprocess.run(  # noqa: E731
        ["git", *args], cwd=ROOT, capture_output=True, text=True, errors="replace",
    ).stdout
    listed = show("ls-tree", "-r", "-z", "--name-only", base, "--", "factories").split("\0")
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


def same_python(old: str, new: str) -> bool:
    """True when two versions of a .py file differ only in comments, blank lines or layout."""
    try:
        return ast.dump(ast.parse(old)) == ast.dump(ast.parse(new))
    except (SyntaxError, ValueError):
        return False


TEST_SKIP = re.compile(
    r"pytest\.mark\.(skip|skipif|xfail)\b|pytest\.(skip|xfail)\(|unittest\.skip"
    r"|\b(it|test|describe)\.(skip|only)\(|\bx(it|describe)\("
)
TEST_DEF = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w+)")


def weakened_tests(diff: str) -> list[str]:
    """From a `git diff -U0`: test functions that are gone and new skip markers, for the reviewer."""
    removed, added, skips, path = {}, set(), [], ""
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            path = line.split(" b/", 1)[-1]
        elif not is_test(path) or line.startswith(("+++", "---")):
            continue
        elif line.startswith("-") and (match := TEST_DEF.match(line[1:])):
            removed.setdefault(match.group(1), path)
        elif line.startswith("+"):
            if match := TEST_DEF.match(line[1:]):
                added.add(match.group(1))
            if TEST_SKIP.search(line):
                skips.append(f"{path}: {line[1:].strip()}")
    gone = [f"{path}: {name} removed" for name, path in removed.items() if name not in added]
    return gone + skips


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


def comment_only(merge_base: str, status: str, path: str) -> bool:
    """A modified .py file whose code is the same as on the merge base."""
    if status != "M" or not path.endswith(".py") or not (ROOT / path).exists():
        return False
    old = subprocess.run(
        ["git", "show", f"{merge_base}:{path}"], cwd=ROOT, capture_output=True, text=True, errors="replace",
    )
    return old.returncode == 0 and same_python(old.stdout, (ROOT / path).read_text(errors="replace"))


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
    merge_base = subprocess.run(
        ["git", "merge-base", args.base, "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()
    changes = [(status, path) for status, path in changes if not comment_only(merge_base, status, path)]
    untested, protected = judge(changes, patterns)
    opt_outs = coverage_opt_outs(git_diff(
        args.base, "-U0", paths=("*.py", ":(exclude,glob)**/tests/**", ":(exclude,glob)**/test_*.py")
    ))

    for note in weakened_tests(git_diff(args.base, "-U0")):
        print(f"Check: {note}")
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::warning::Test removed or skipped. {note}")

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
