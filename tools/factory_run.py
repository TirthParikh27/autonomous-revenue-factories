#!/usr/bin/env python3
"""Run wrapper for every headless factory run (ARCHITECTURE.md section 4.3).

Its job is to make failure loud. It refuses to start when a kill switch or a
budget cap says no, starts Claude with explicit caps, and afterwards fails the
run unless there is evidence that the stage did its work.

Usage:
    factory_run.py --factory a-consumer-apps --stage gap-mining

Exit codes: 0 run passed, 1 run failed its checks, 2 refused to start.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
REFUSED, FAILED, PASSED = 2, 1, 0
# Stages that stop while state/SUBMISSIONS_FROZEN exists (ESCALATION.md, A-ACCT-1).
FROZEN_STAGES = ("mvp-build", "release-readiness")


class Refused(Exception):
    """The run must not start."""


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def next_id(path: Path, prefix: str) -> str:
    return f"{prefix}-{len(read_jsonl(path)) + 1:06d}"


def month_spend(ledger: Path, month: str) -> dict[str, float]:
    """Spend for one month (YYYY-MM) by category, plus 'total'."""
    totals: dict[str, float] = {"total": 0.0}
    for line in read_jsonl(ledger):
        if str(line.get("at", "")).startswith(month):
            usd = float(line.get("usd", 0))
            category = line.get("category", "other")
            totals[category] = totals.get(category, 0.0) + usd
            totals["total"] += usd
    return totals


def preflight(repo_root: Path, factory_dir: Path, state_dir: Path, budget: dict, stage: str,
              now: dt.datetime) -> dict:
    """Raise Refused if the run must not start. Returns the stage's caps."""
    for stop in (repo_root / "STOP", factory_dir / "STOP", state_dir / "STOP"):
        if stop.exists():
            raise Refused(f"STOP file present: {stop}")
    frozen = state_dir / "state" / "SUBMISSIONS_FROZEN"
    if stage in FROZEN_STAGES and frozen.exists():
        raise Refused(f"submissions frozen (A-ACCT-1): {frozen} exists, so '{stage}' may not run")
    caps = (budget.get("per_run") or {}).get(stage)
    if not caps:
        raise Refused(f"stage '{stage}' has no per_run caps in budget.yaml")
    if not (factory_dir / "skills" / stage / "SKILL.md").exists():
        raise Refused(f"no skill for stage '{stage}'")
    spent = month_spend(state_dir / "ledger" / "spend.jsonl", now.strftime("%Y-%m"))
    monthly = budget.get("monthly_caps_usd") or {}
    if spent.get("tokens", 0.0) >= float(monthly.get("tokens", 0)):
        raise Refused(f"monthly token cap reached: {spent.get('tokens', 0.0):.2f} of {monthly.get('tokens')}")
    if spent["total"] >= float(monthly.get("total", 0)):
        raise Refused(f"monthly total cap reached: {spent['total']:.2f} of {monthly.get('total')}")
    return {"model": budget.get("model"), **caps}


def build_command(stage: str, caps: dict, run_id: str, factory_dir: Path | None = None) -> list[str]:
    """The Claude command line. FACTORY_CLAUDE_CMD replaces the binary in tests.

    The factory's allow and deny lists are passed as flags, because a headless run in a
    directory nobody has opened interactively ignores the allow list in .claude/settings.json.
    """
    settings = (factory_dir / ".claude" / "settings.json") if factory_dir else None
    perms = json.loads(settings.read_text()).get("permissions", {}) if settings and settings.exists() else {}
    tools = []
    if perms.get("allow"):
        tools += ["--allowedTools", *perms["allow"]]
    if perms.get("deny"):
        tools += ["--disallowedTools", *perms["deny"]]
    binary = os.environ.get("FACTORY_CLAUDE_CMD", "claude").split()
    prompt = (
        f"You are run {run_id}. Do exactly one stage: {stage}. Read CLAUDE.md, then follow "
        f"skills/{stage}/SKILL.md. End with the run-report skill, writing journal/<date>/{run_id}.md."
    )
    return binary + [
        "-p", prompt,
        "--output-format", "json",
        "--max-turns", str(caps["max_turns"]),
        "--max-budget-usd", str(caps["max_budget_usd"]),
        "--permission-prompts", "none",
    ] + (["--model", str(caps["model"])] if caps.get("model") else []) + tools


def evidence_ok(report: Path) -> bool:
    """A run report must have a non-empty Evidence section and both mandatory sections."""
    if not report.exists():
        return False
    text = report.read_text()
    for heading in ("## Not done", "## Denied or blocked"):
        if heading not in text:
            return False
    match = re.search(r"^## Evidence\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return bool(match and re.search(r"^\s*-\s*\S+", match.group(1), re.M))


def judge(returncode: int, output: dict | None, report: Path) -> list[str]:
    """Reasons the run failed. Empty means it passed."""
    reasons = []
    if returncode != 0:
        reasons.append(f"claude exited with code {returncode}")
    if output is None:
        reasons.append("claude output was not valid JSON")
    else:
        if output.get("is_error"):
            reasons.append("claude reported is_error")
        denials = output.get("permission_denials") or []
        if denials:
            reasons.append(f"{len(denials)} permission denial(s)")
    if not report.exists():
        reasons.append(f"run report missing: {report.name}")
    elif not evidence_ok(report):
        reasons.append("run report has no evidence block or lacks a mandatory section")
    return reasons


def record_failures(state_dir: Path, stage: str, failed: bool) -> int:
    """Track consecutive failures per stage. Returns the current streak."""
    path = state_dir / "state" / "run_failures.json"
    streaks = json.loads(path.read_text()) if path.exists() else {}
    streaks[stage] = streaks.get(stage, 0) + 1 if failed else 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(streaks, indent=2, sort_keys=True) + "\n")
    return streaks[stage]


def run(factory: str, stage: str, repo_root: Path = REPO_ROOT, state_root: Path | None = None,
        now: dt.datetime | None = None) -> int:
    now = now or utcnow()
    factory_dir = repo_root / "factories" / factory
    state_dir = state_root or factory_dir
    budget = yaml.safe_load((factory_dir / "budget.yaml").read_text())
    run_id = f"{now.strftime('%Y%m%dT%H%M%SZ')}-{stage}-{uuid.uuid4().hex[:6]}"
    outbox = state_dir / "outbox" / "pending.jsonl"
    ledger = state_dir / "ledger" / "spend.jsonl"

    try:
        caps = preflight(repo_root, factory_dir, state_dir, budget, stage, now)
    except Refused as why:
        print(f"REFUSED {run_id}: {why}")
        return REFUSED

    # No run may outlast this, so a lock older than it belongs to a killed run.
    timeout_s = 60 * float(budget.get("run_timeout_minutes", 60))
    lock = state_dir / "state" / "worker.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    if lock.exists() and now.timestamp() - lock.stat().st_mtime > timeout_s:
        append_jsonl(outbox, {"id": next_id(outbox, "o"), "at": now.isoformat(), "run": run_id,
                              "priority": "digest", "link": None,
                              "text": f"cleared stale lock left by run {lock.read_text().strip() or 'unknown'}"})
        lock.unlink()
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        print(f"REFUSED {run_id}: another worker holds {lock}")
        return REFUSED
    os.write(fd, run_id.encode())
    os.close(fd)

    try:
        try:
            proc = subprocess.run(build_command(stage, caps, run_id, factory_dir), cwd=factory_dir, timeout=timeout_s,
                                  capture_output=True, text=True, env={**os.environ, "FACTORY_RUN_ID": run_id})
            returncode, stdout = proc.returncode, proc.stdout
        except subprocess.TimeoutExpired:
            returncode, stdout = 124, ""
        try:
            output = json.loads(stdout)
        except (json.JSONDecodeError, TypeError):
            output = None

        cost = float((output or {}).get("total_cost_usd") or 0.0)
        if cost:
            append_jsonl(ledger, {
                "id": next_id(ledger, "s"), "at": now.isoformat(), "run": run_id, "item": None,
                "category": "tokens", "vendor": "anthropic", "usd": round(cost, 6),
                "source": "total_cost_usd from run output",
            })

        report = state_dir / "journal" / now.strftime("%Y-%m-%d") / f"{run_id}.md"
        reasons = judge(returncode, output, report)
        limit = int((budget.get("escalation") or {}).get("consecutive_failures_before_stop", 3))
        streak = record_failures(state_dir, stage, bool(reasons))

        if not reasons:
            append_jsonl(outbox, {"id": next_id(outbox, "o"), "at": now.isoformat(), "run": run_id,
                                  "priority": "digest", "text": f"{stage} passed (${cost:.2f})",
                                  "link": str(report.relative_to(state_dir))})
            print(f"PASSED {run_id}")
            return PASSED

        text = f"{stage} failed: " + "; ".join(reasons)
        priority = "digest"
        if streak >= limit:
            (state_dir / "STOP").write_text(f"{run_id}: {streak} consecutive failures of {stage}\n")
            text += f". STOP written after {streak} consecutive failures (RUN-3)"
            priority = "now"
        append_jsonl(outbox, {"id": next_id(outbox, "o"), "at": now.isoformat(), "run": run_id,
                              "priority": priority, "text": text, "link": None})
        print(f"FAILED {run_id}: {text}")
        return FAILED
    finally:
        lock.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--factory", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--state-root", type=Path, help="checkout of the factory-state branch for this factory")
    args = parser.parse_args(argv)
    return run(args.factory, args.stage, state_root=args.state_root)


if __name__ == "__main__":
    sys.exit(main())
