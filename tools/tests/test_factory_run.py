"""The wrapper's failure paths are proven first (ARCHITECTURE.md section 7, step 2)."""
import datetime as dt
import json
import os
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import factory_run  # noqa: E402

NOW = dt.datetime(2026, 11, 20, 9, 0, tzinfo=dt.timezone.utc)

GOOD_REPORT = """# Run {run}
## Did
- ranked ideas -> 5 kept
## Evidence
- checks/copy_lint -> exit 0
## Not done
- none
## Denied or blocked
- none
## Next
- spec
"""

FAKE_CLAUDE = """#!/usr/bin/env python3
import json, os, pathlib, sys
mode = os.environ.get("FAKE_MODE", "ok")
if mode == "hang":
    import time; time.sleep(5)
run = os.environ["FACTORY_RUN_ID"]
report = pathlib.Path("journal") / "2026-11-20" / (run + ".md")
out = {"total_cost_usd": 0.42, "permission_denials": [], "is_error": False}
if mode in ("ok", "denied", "crash"):
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(os.environ["FAKE_REPORT"].replace("{run}", run))
if mode == "denied":
    out["permission_denials"] = [{"tool_name": "Bash", "tool_input": {"command": "adb devices"}}]
if mode == "garbage":
    print("not json"); sys.exit(0)
print(json.dumps(out))
sys.exit(3 if mode == "crash" else 0)
"""


@pytest.fixture
def repo(tmp_path, monkeypatch):
    factory = tmp_path / "factories" / "demo"
    (factory / "skills" / "screen").mkdir(parents=True)
    (factory / "skills" / "screen" / "SKILL.md").write_text("# screen\n")
    (factory / "budget.yaml").write_text(
        "monthly_caps_usd: {tokens: 10, total: 20}\n"
        "per_run: {screen: {max_turns: 5, max_budget_usd: 1.0}}\n"
        "escalation: {consecutive_failures_before_stop: 3}\n"
    )
    fake = tmp_path / "fake_claude.py"
    fake.write_text(FAKE_CLAUDE)
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("FACTORY_CLAUDE_CMD", f"{sys.executable} {fake}")
    monkeypatch.setenv("FAKE_REPORT", GOOD_REPORT)
    monkeypatch.setenv("FAKE_MODE", "ok")
    return tmp_path


def run(repo, stage="screen"):
    return factory_run.run("demo", stage, repo_root=repo, now=NOW)


def lines(path):
    return [json.loads(x) for x in path.read_text().splitlines()]


def test_pass_records_cost_and_digest_line(repo):
    assert run(repo) == factory_run.PASSED
    factory = repo / "factories" / "demo"
    (spend,) = lines(factory / "ledger" / "spend.jsonl")
    assert spend["usd"] == 0.42 and spend["category"] == "tokens"
    (note,) = lines(factory / "outbox" / "pending.jsonl")
    assert note["priority"] == "digest"
    assert not (factory / "state" / "worker.lock").exists()


@pytest.mark.parametrize("where", ["root", "factory"])
def test_stop_file_refuses(repo, where):
    target = repo if where == "root" else repo / "factories" / "demo"
    (target / "STOP").write_text("halt\n")
    assert run(repo) == factory_run.REFUSED
    assert not (repo / "factories" / "demo" / "ledger").exists()


def test_budget_exceeded_refuses(repo):
    ledger = repo / "factories" / "demo" / "ledger" / "spend.jsonl"
    factory_run.append_jsonl(ledger, {"at": "2026-11-03T00:00:00+00:00", "category": "tokens", "usd": 10})
    assert run(repo) == factory_run.REFUSED


def test_held_lock_refuses(repo):
    lock = repo / "factories" / "demo" / "state" / "worker.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("other run")
    os.utime(lock, (NOW.timestamp() - 600,) * 2)
    assert run(repo) == factory_run.REFUSED
    assert lock.exists()


def test_stale_lock_is_cleared_and_reported(repo):
    factory = repo / "factories" / "demo"
    lock = factory / "state" / "worker.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("dead-run")
    os.utime(lock, (NOW.timestamp() - 2 * 3600,) * 2)
    assert run(repo) == factory_run.PASSED
    assert "dead-run" in lines(factory / "outbox" / "pending.jsonl")[0]["text"]
    assert not lock.exists()


def test_report_without_evidence_fails(repo, monkeypatch):
    monkeypatch.setenv("FAKE_REPORT", GOOD_REPORT.replace("- checks/copy_lint -> exit 0\n", ""))
    assert run(repo) == factory_run.FAILED


def test_permission_denial_fails(repo, monkeypatch):
    monkeypatch.setenv("FAKE_MODE", "denied")
    assert run(repo) == factory_run.FAILED


def test_three_consecutive_failures_write_stop_and_alert_now(repo, monkeypatch):
    factory = repo / "factories" / "demo"
    monkeypatch.setenv("FAKE_MODE", "silent")
    assert run(repo) == factory_run.FAILED
    assert run(repo) == factory_run.FAILED
    assert not (factory / "STOP").exists()
    assert run(repo) == factory_run.FAILED
    assert (factory / "STOP").exists()
    assert lines(factory / "outbox" / "pending.jsonl")[-1]["priority"] == "now"
    monkeypatch.setenv("FAKE_MODE", "ok")
    assert run(repo) == factory_run.REFUSED


@pytest.mark.parametrize("stage", ["mvp-build", "release-readiness"])
def test_submission_freeze_refuses_build_and_release(repo, stage):
    factory = repo / "factories" / "demo"
    (factory / "skills" / stage).mkdir(parents=True)
    (factory / "skills" / stage / "SKILL.md").write_text(f"# {stage}\n")
    (factory / "budget.yaml").write_text(
        "monthly_caps_usd: {tokens: 10, total: 20}\n"
        f"per_run: {{screen: {{max_turns: 5, max_budget_usd: 1.0}}, {stage}: {{max_turns: 5, max_budget_usd: 1.0}}}}\n"
    )
    assert run(repo, stage=stage) == factory_run.PASSED
    (factory / "state" / "SUBMISSIONS_FROZEN").write_text("A-ACCT-1 2026-11-20\n")
    assert run(repo, stage=stage) == factory_run.REFUSED
    assert run(repo, stage="screen") == factory_run.PASSED  # other stages keep running


def test_factory_allow_and_deny_lists_are_passed_as_flags(repo):
    factory = repo / "factories" / "demo"
    (factory / ".claude").mkdir()
    (factory / ".claude" / "settings.json").write_text('{"permissions": {"allow": ["Read"], "deny": ["Edit(budget.yaml)"]}}')
    cmd = factory_run.build_command("screen", {"max_turns": 5, "max_budget_usd": 1}, "r1", factory)
    assert cmd[-4:] == ["--allowedTools", "Read", "--disallowedTools", "Edit(budget.yaml)"]
    (factory / ".mcp.json").write_text("{}")
    cmd = factory_run.build_command("screen", {"max_turns": 5, "max_budget_usd": 1}, "r1", factory)
    assert cmd[-3:] == ["--mcp-config", str(factory / ".mcp.json"), "--strict-mcp-config"]
