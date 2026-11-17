"""The pull request gate: code needs a test, protected files wait for the operator."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pr_gate  # noqa: E402

PATTERNS = pr_gate.protected_patterns(
    "# comment\n\n/factories/*/budget.yaml  @op\n/.github/  @op\n/REVIEW.md @op\n"
)


def test_code_without_a_test_fails():
    untested, _ = pr_gate.judge([("M", "tools/factory_run.py"), ("M", "README.md")], PATTERNS)
    assert untested == ["tools/factory_run.py"]


def test_code_with_a_test_passes():
    changes = [("A", "factories/x/app/pay.ts"), ("A", "factories/x/app/pay.test.ts")]
    assert pr_gate.judge(changes, PATTERNS)[0] == []


def test_deleting_a_test_does_not_count_as_adding_one():
    changes = [("M", "tools/factory_run.py"), ("D", "tools/tests/test_factory_run.py")]
    assert pr_gate.judge(changes, PATTERNS)[0] == ["tools/factory_run.py"]


def test_a_file_moved_without_edits_needs_no_test_and_is_not_one():
    moved = pr_gate.parse_name_status("R100\0fetch.py\0fetch_reviews.py\0")
    assert moved == [("D", "fetch.py"), ("R", "fetch_reviews.py")]
    assert pr_gate.judge(moved, PATTERNS)[0] == []
    moved_test = pr_gate.parse_name_status("M\0run.py\0R100\0tests/test_a.py\0tests/test_b.py\0")
    assert pr_gate.judge(moved_test, PATTERNS)[0] == ["run.py"]


def test_new_coverage_opt_out_is_reported():
    diff = (
        "+++ b/run.py\n+def pay():  # pragma: no cover\n+    return 1\n-old  # pragma: no cover\n"
        "+def a():  # pragma no cover\n+def b():  # PRAGMA: NO COVER\n+def c():  #pragma:nocover\n"
    )
    assert pr_gate.coverage_opt_outs(diff) == [
        "def pay():  # pragma: no cover",
        "def a():  # pragma no cover",
        "def b():  # PRAGMA: NO COVER",
        "def c():  #pragma:nocover",
    ]


def test_docs_only_change_passes():
    assert pr_gate.judge([("M", "README.md"), ("A", "factories/x/skills/a/SKILL.md")], PATTERNS) == ([], [])


def test_protected_files_are_named_even_when_deleted():
    changes = [
        ("D", "factories/a-consumer-apps/budget.yaml"),
        ("M", ".github/workflows/checks.yml"),
        ("M", "REVIEW.md"),
        ("M", "docs/REVIEW.md"),
        ("M", "factories/a-consumer-apps/README.md"),
    ]
    assert pr_gate.judge(changes, PATTERNS)[1] == [
        ".github/workflows/checks.yml",
        "REVIEW.md",
        "factories/a-consumer-apps/budget.yaml",
    ]


def test_end_to_end_in_a_real_repository(tmp_path, monkeypatch, capsys):
    import subprocess

    def git(*args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
                       cwd=tmp_path, check=True, capture_output=True)

    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "CODEOWNERS").write_text("/factories/*/budget.yaml @op\n")
    git("init", "-q", "-b", "main")
    git("add", "-A")
    git("commit", "-q", "-m", "base")
    git("checkout", "-q", "-b", "change")
    (tmp_path / "factories" / "x").mkdir(parents=True)
    (tmp_path / "factories" / "x" / "budget.yaml").write_text("cap: 1\n")
    (tmp_path / "factories" / "caf\u00e9").mkdir()
    (tmp_path / "factories" / "caf\u00e9" / "budget.yaml").write_text("cap: 1\n")
    (tmp_path / "run.py").write_text("print('hi')\n")
    (tmp_path / "na\u00efve.py").write_text("def f():  # pragma: no cover\n    return 1\n")
    git("add", "-A")
    git("commit", "-q", "-m", "code only")

    monkeypatch.setattr(pr_gate, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["pr_gate.py", "--base", "main"])
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert pr_gate.main() == 1
    out = capsys.readouterr().out
    assert "Add a test for: na\u00efve.py, run.py" in out
    assert "hides code from the coverage rule: def f():  # pragma: no cover" in out
    assert ("::notice::Waits for the operator to merge. Protected files changed: "
            "factories/caf\u00e9/budget.yaml, factories/x/budget.yaml") in out

    (tmp_path / "test_run.py").write_text("def test_run():\n    assert True\n")
    (tmp_path / "na\u00efve.py").write_text("def f():\n    return 1\n")
    git("add", "-A")
    git("commit", "-q", "-m", "with test")
    assert pr_gate.main() == 0
