"""The pull request gate: code needs a test, protected files wait for the operator."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pr_gate  # noqa: E402


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd, check=True, capture_output=True)


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


def test_star_stays_inside_one_folder():
    patterns = pr_gate.protected_patterns("/factories/*/*.py @op\n/factories/*/tools/ @op\n/STOP @op\n")
    protected = ["factories/a/voice.py", "factories/a/tools/x/gate.py", "STOP"]
    free = ["factories/a/app/src/pay.py", "factories/a/skills/tools/x.md", "factories/a/STOP", "docs/STOP"]
    assert [p for p in protected + free if pr_gate.is_protected(p, patterns)] == protected


def test_a_factory_deny_list_is_protected_too():
    settings = '{"permissions": {"deny": ["Edit(lib/**)", "Write(lib/**)", "Edit(./requirements.txt)", "Bash(rm *)"]}}'
    patterns = pr_gate.deny_patterns("factories/c/.claude/settings.json", settings)
    assert patterns == ["/factories/c/**/requirements.txt", "/factories/c/lib/**", "/factories/c/requirements.txt"]
    assert pr_gate.is_protected("factories/c/lib/a/indicators.py", patterns)
    assert pr_gate.is_protected("factories/c/requirements.txt", patterns)
    assert not pr_gate.is_protected("factories/d/lib/indicators.py", patterns)
    assert pr_gate.deny_patterns("factories/c/.claude/settings.json", "not json") == []


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
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "CODEOWNERS").write_text("/factories/*/budget.yaml @op\n")
    (tmp_path / "factories" / "x\u00e9" / ".claude").mkdir(parents=True)
    (tmp_path / "factories" / "x\u00e9" / ".claude" / "settings.json").write_text(
        '{"permissions": {"deny": ["Edit(data/**)"]}}')
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "checkout", "-q", "-b", "change")
    (tmp_path / "factories" / "x").mkdir()
    (tmp_path / "factories" / "x" / "budget.yaml").write_text("cap: 1\n")
    # The change edits a deny-listed file and deletes the deny list. The base's deny list still applies.
    (tmp_path / "factories" / "x\u00e9" / "data").mkdir()
    (tmp_path / "factories" / "x\u00e9" / "data" / "prices.csv").write_text("1\n")
    (tmp_path / "factories" / "x\u00e9" / ".claude" / "settings.json").unlink()
    (tmp_path / "factories" / "caf\u00e9").mkdir()
    (tmp_path / "factories" / "caf\u00e9" / "budget.yaml").write_text("cap: 1\n")
    (tmp_path / "run.py").write_text("print('hi')\n")
    # The change also deletes the list that protects what it edits. The base's list still applies.
    (tmp_path / ".github" / "CODEOWNERS").unlink()
    (tmp_path / "na\u00efve.py").write_text("def f():  # pragma: no cover\n    return 1\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "code only")

    monkeypatch.setattr(pr_gate, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["pr_gate.py", "--base", "main"])
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert pr_gate.main() == 1
    out = capsys.readouterr().out
    assert "Add a test for: na\u00efve.py, run.py" in out
    assert "hides code from the coverage rule: def f():  # pragma: no cover" in out
    assert ("::notice::Waits for the operator to merge. Protected files changed: "
            "factories/caf\u00e9/budget.yaml, factories/x/budget.yaml, factories/x\u00e9/data/prices.csv") in out

    (tmp_path / "test_run.py").write_text("def test_run():\n    assert True\n")
    (tmp_path / "na\u00efve.py").write_text("def f():\n    return 1\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "with test")
    assert pr_gate.main() == 0


def test_a_deny_rule_with_no_slash_applies_at_any_depth():
    patterns = pr_gate.deny_patterns("factories/a/.claude/settings.json", '{"permissions": {"deny": ["Edit(STOP)"]}}')
    assert pr_gate.is_protected("factories/a/STOP", patterns)
    assert pr_gate.is_protected("factories/a/apps/x/STOP", patterns)
    assert not pr_gate.is_protected("factories/b/STOP", patterns)
    assert not pr_gate.is_protected("factories/a/STOPPED", patterns)


def test_a_deny_list_that_is_not_a_list_is_ignored():
    for deny in ("null", "5", '"Edit(x)"', "{}"):
        settings = '{"permissions": {"deny": %s}}' % deny
        assert pr_gate.deny_patterns("factories/a/.claude/settings.json", settings) == []


def test_comment_and_layout_edits_are_not_code_changes():
    old = "def pay(x):\n    return x + 1\n"
    assert pr_gate.same_python(old, "# why\ndef pay(x):\n\n    return x + 1  # note\n")
    assert pr_gate.same_python(old, "def pay(x):\n    return (x\n            + 1)\n")
    assert not pr_gate.same_python(old, "def pay(x):\n    return x + 2\n")
    assert not pr_gate.same_python(old, "def pay(x:\n")  # broken code is a change
    utf8, latin1 = "x = 'é'\n".encode(), "# -*- coding: latin-1 -*-\nx = 'é'\n".encode()
    assert not pr_gate.same_python(utf8, latin1)  # the coding line changes what the string holds


def test_removed_and_skipped_tests_are_named():
    diff = (
        "diff --git a/tests/test_pay.py b/tests/test_pay.py\n"
        "--- a/tests/test_pay.py\n+++ b/tests/test_pay.py\n"
        "-def test_rounds_to_cents():\n"
        "-def test_renamed():\n+def test_renamed():\n"
        "+@pytest.mark.skip(reason='flaky')\n"
        "+    pytest.xfail('later')\n"
        "diff --git a/web/pay.test.ts b/web/pay.test.ts\n"
        "+it.skip('charges once', () => {})\n"
        "+describe.only('pay', () => {})\n"
        "+    note = 'it.skip( and @pytest.mark.skip in a string are not skips'\n"
        "+pytestmark = pytest.mark.skip(reason='slow')\n"
        "+@mark.xfail\n"
        "+    @unittest.expectedFailure\n"
        "diff --git a/pay.py b/pay.py\n"
        "-def test_helper():\n+@pytest.mark.skip\n"
    )
    assert pr_gate.weakened_tests(diff) == [
        "tests/test_pay.py: test_rounds_to_cents removed",
        "tests/test_pay.py: @pytest.mark.skip(reason='flaky')",
        "tests/test_pay.py: pytest.xfail('later')",
        "web/pay.test.ts: it.skip('charges once', () => {})",
        "web/pay.test.ts: describe.only('pay', () => {})",
        "web/pay.test.ts: pytestmark = pytest.mark.skip(reason='slow')",
        "web/pay.test.ts: @mark.xfail",
        "web/pay.test.ts: @unittest.expectedFailure",
    ]


def test_a_deleted_test_file_is_named():
    diff = (
        "diff --git a/tools/tests/test_x.py b/tools/tests/test_x.py\ndeleted file mode 100644\n"
        "--- a/tools/tests/test_x.py\n+++ /dev/null\n-def test_one():\n-    async def test_two():\n"
    )
    assert pr_gate.weakened_tests(diff) == [
        "tools/tests/test_x.py: test_one removed",
        "tools/tests/test_x.py: test_two removed",
    ]


def test_end_to_end_comment_only_edit_and_removed_test(tmp_path, monkeypatch, capsys):
    (tmp_path / "pay.py").write_text("def pay(x):\n    return x + 1\n")
    (tmp_path / "test_pay.py").write_text("def test_pay():\n    assert True\n\n\ndef test_cents():\n    assert True\n")
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "checkout", "-q", "-b", "change")
    (tmp_path / "pay.py").write_text("# Adds one.\ndef pay(x):\n    return x + 1  # why\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "comments only")

    monkeypatch.setattr(pr_gate, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["pr_gate.py", "--base", "main"])
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert pr_gate.main() == 0
    assert "OK: code changes come with tests." in capsys.readouterr().out

    (tmp_path / "pay.py").write_text("def pay(x):\n    return x + 2\n")
    (tmp_path / "test_pay.py").write_text("def test_pay():\n    assert True\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "real change, one test gone")
    assert pr_gate.main() == 0  # a test file changed, so the rule passes; the reviewer is told what went
    out = capsys.readouterr().out
    assert "::warning::Test removed or skipped. test_pay.py: test_cents removed" in out


def test_a_comment_only_edit_to_a_protected_file_is_still_named(tmp_path, monkeypatch, capsys):
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "CODEOWNERS").write_text("/engine/ @op\n")
    (tmp_path / "engine").mkdir()
    (tmp_path / "engine" / "gate.py").write_text("# Max loss 2%, do not change.\nLIMIT = 2\n")
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "checkout", "-q", "-b", "change")
    (tmp_path / "engine" / "gate.py").write_text("# Max loss is advisory.\nLIMIT = 2\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "comment only")

    monkeypatch.setattr(pr_gate, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["pr_gate.py", "--base", "main"])
    assert pr_gate.main() == 0
    assert "Protected files changed: engine/gate.py" in capsys.readouterr().out


def test_the_committed_code_is_judged_not_the_working_tree(tmp_path, monkeypatch, capsys):
    """CI replaces the gate on disk with the base copy before it runs. The committed change still counts."""
    base = "SUFFIXES = {'.py', '.sql'}\n"
    (tmp_path / "gate.py").write_text(base)
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "checkout", "-q", "-b", "change")
    (tmp_path / "gate.py").write_text("SUFFIXES = {'.py'}\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "code change, no test")
    (tmp_path / "gate.py").write_text(base)  # what CI does with tools/pr_gate.py

    monkeypatch.setattr(pr_gate, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["pr_gate.py", "--base", "main"])
    assert pr_gate.main() == 1
    assert "Add a test for: gate.py" in capsys.readouterr().out


def test_a_non_ascii_test_path_is_named_plainly(tmp_path, monkeypatch, capsys):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_caf\u00e9.py").write_text("def test_one():\n    assert True\n")
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "checkout", "-q", "-b", "change")
    (tmp_path / "tests" / "test_caf\u00e9.py").unlink()
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "drop test")

    monkeypatch.setattr(pr_gate, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["pr_gate.py", "--base", "main"])
    pr_gate.main()
    assert "Check: tests/test_caf\u00e9.py: test_one removed" in capsys.readouterr().out


def test_a_test_removed_in_one_file_is_named_even_if_another_file_adds_one_with_its_name():
    diff = (
        "diff --git a/a/test_x.py b/a/test_x.py\n--- a/a/test_x.py\n+++ b/a/test_x.py\n-def test_pay():\n"
        "diff --git a/b/test_y.py b/b/test_y.py\n--- a/b/test_y.py\n+++ b/b/test_y.py\n+def test_pay():\n"
    )
    assert pr_gate.weakened_tests(diff) == ["a/test_x.py: test_pay removed"]


def test_a_very_deep_expression_counts_as_a_change():
    deep = "x = " + " + ".join(["1"] * 50000) + "\n"
    assert not pr_gate.same_python(deep, deep + "# note\n")


def test_gitattributes_cannot_hide_a_diff(tmp_path, monkeypatch, capsys):
    (tmp_path / "test_pay.py").write_text("def test_one():\n    assert True\n\n\ndef test_two():\n    assert True\n")
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "checkout", "-q", "-b", "change")
    (tmp_path / ".gitattributes").write_text("*.py -diff\n")
    (tmp_path / "test_pay.py").write_text("def test_one():\n    assert True\n")
    (tmp_path / "pay.py").write_text("def pay():  # pragma: no cover\n    return 1\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "hide it")

    monkeypatch.setattr(pr_gate, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["pr_gate.py", "--base", "main"])
    assert pr_gate.main() == 1
    out = capsys.readouterr().out
    assert "test_pay.py: test_two removed" in out
    assert "hides code from the coverage rule: def pay():  # pragma: no cover" in out
