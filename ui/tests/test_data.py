"""The UI shows what the factory files say. These build a small factory on disk and read it back."""
import datetime as dt
import json
import time

import pytest

from ui import data

NOW = dt.datetime(2026, 11, 20, 9, 0, tzinfo=dt.timezone.utc)
RUN = "20261117T075608Z-demand-test-dce705"
PACKET = "A-AD-1-20261117-demand-test-dce705.md"


@pytest.fixture(autouse=True)
def utc(monkeypatch):
    monkeypatch.setenv("TZ", "UTC")
    time.tzset()


def item(folder, item_id, stage, history, run=None, **extra):
    """An item file. `run` is the run that made its last move."""
    steps = [{"at": f"2026-11-17T{n:02}:00:00Z", "from": None, "to": to, "note": f"to {to}"} for n, to in enumerate(history, 7)]
    if steps:
        steps[-1]["run"] = run
    doc = {"id": item_id, "stage": stage, "summary": f"about {item_id}", "history": steps, **extra}
    (folder / "state" / "items").mkdir(parents=True, exist_ok=True)
    (folder / "state" / "items" / f"{item_id}.json").write_text(json.dumps(doc))


@pytest.fixture
def root(tmp_path):
    apps = tmp_path / "factories" / "a-consumer-apps"
    item(apps, "2026-11-17-photo-fix", "specced", ["discovered", "screened", "specced"],
         category="Photo", platform="web", scores={"complaints": 12, "note": "text is not a number", "ok": True})
    item(apps, "2026-11-17-lecture", "awaiting_human", ["discovered", "screened", "specced", "awaiting_human"], run=RUN,
         blocked_by=f"escalations/open/{PACKET}", evidence=[{"claim": "10 complaints", "source": "state/scout/x.json"}])
    item(apps, "2026-11-17-bills", "killed", ["discovered", "killed"], killed_reason="ranked last")
    (apps / "escalations" / "open").mkdir(parents=True)
    (apps / "escalations" / "open" / PACKET).write_text(
        "# Approve the first batch: $30 each\n"
        "Factory: a-consumer-apps   Item: batch b1   Trigger: A-AD-1   Raised: 2026-11-17   Expires: 2026-11-24\n\n"
        "## What I want to do\nDeploy three pages\nand three paused campaigns.\n\n| Idea | Job |\n|---|---|\n\n## Why now\nBecause.\n"
    )
    (apps / "ledger").mkdir()
    (apps / "ledger" / "spend.jsonl").write_text("".join(json.dumps(line) + "\n" for line in [
        {"at": "2026-11-17T07:56:08Z", "run": RUN, "category": "tokens", "usd": 1.01},
        {"at": "2026-11-18T07:00:00Z", "run": None, "category": "ads", "usd": 30},
        {"at": "2026-11-30T23:30:00Z", "run": "20261130T233000Z-gap-mining-bbbbbb", "category": "tokens", "usd": 2},
        {"at": "2026-10-30T07:00:00Z", "run": "20261030T070000Z-gap-mining-aaaaaa", "category": "tokens", "usd": 99},
    ]))
    (apps / "outbox").mkdir()
    (apps / "outbox" / "pending.jsonl").write_text("".join(json.dumps(line) + "\n" for line in [
        {"at": "2026-11-17T07:20:00Z", "run": "20261117T071857Z-gap-mining-c6852b", "text": "gap-mining failed: no evidence block"},
        {"at": "2026-11-17T07:56:08Z", "run": RUN, "text": "demand-test passed ($1.01)"},
        {"at": "2026-11-17T08:00:00Z", "run": None, "text": "digest sent"},
    ]))
    (apps / "budget.yaml").write_text("monthly_caps_usd:\n  tokens: 300\n  ads: 0\n  total: 420\n  warn_at_fraction: 0.8\n")
    (tmp_path / "factories" / "_shared").mkdir()
    (tmp_path / "factories" / "g-marketplace-tools").mkdir()
    (tmp_path / "factories" / "b-ecommerce").mkdir()
    return tmp_path


def by_id(rows):
    return {row["id"]: row for row in rows}


def test_a_factory_is_read_from_its_files(root):
    built = data.build(root, NOW)
    assert built["asOf"] == "20 Nov 2026, 09:00 AM"
    apps, ecommerce = built["factories"]            # _shared is not a factory, g-marketplace-tools is hidden
    assert (apps["id"], apps["name"], apps["planned"], apps["on"]) == ("a-consumer-apps", "App factory", False, True)
    assert (ecommerce["id"], ecommerce["planned"], ecommerce["items"]) == ("b-ecommerce", True, [])

    items = by_id(apps["items"])
    photo, lecture, bills = (items[f"2026-11-17-{name}"] for name in ("photo-fix", "lecture", "bills"))
    assert (photo["name"], photo["stage"], photo["state"]) == ("Photo fix", "spec", "running")
    assert photo["facts"] == {"complaints": 12}     # only numbers become tiles
    # an item waiting on a decision sits at the stage that asked for it, not where it last was
    assert (lecture["stage"], lecture["state"], lecture["blockedBy"]) == ("demand", "waiting", "A-AD-1")
    assert lecture["evidence"] == [{"claim": "10 complaints", "source": "state/scout/x.json"}]
    assert lecture["history"][0] == ["7:00 am", "Discovered", "to discovered"]
    assert (bills["stage"], bills["state"], bills["killed"]) == ("mine", "killed", "ranked last")

    assert apps["approvals"] == [{
        "id": "A-AD-1", "title": "Approve the first batch: $30 each",
        "detail": "Deploy three pages and three paused campaigns.", "expires": "2026-11-24", "stage": "demand",
        "file": f"factories/a-consumer-apps/escalations/open/{PACKET}", "items": ["2026-11-17-lecture"],
    }]
    stages = by_id(apps["stages"])
    assert [stages[name]["reached"] for name in ("mine", "screen", "spec", "demand")] == [3, 2, 2, 0]
    assert stages["demand"]["last"] == {"t": "7:56 am", "text": "demand-test passed ($1.01)"}
    assert stages["build"]["last"] is None

    newest, demand, mining = apps["events"]         # newest first
    assert (newest["skill"], newest["stage"], newest["cost"]) == ("wrapper", None, 0)
    assert (demand["stage"], demand["cost"], demand["failed"]) == ("demand", 1.01, False)
    assert (mining["stage"], mining["failed"]) == ("mine", True)
    # October's line is not this month's spend. Each dollar cap in budget.yaml gets its own line; warn_at_fraction is not one
    assert apps["spend"] == {"month": 33.01, "monthBudget": 420, "runs": 2, "caps": [
        {"kind": "tokens", "spent": 3.01, "cap": 300}, {"kind": "ads", "spent": 30, "cap": 0}]}


def test_the_month_is_the_utc_month_the_wrapper_budgets_by(root):
    """23:30 UTC on 30 Nov is already December in Sydney. It still counts against November, as in tools/factory_run.py."""
    sydney = dt.datetime(2026, 11, 30, 23, 45, tzinfo=dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=11)))
    assert data.build(root, sydney)["factories"][0]["spend"]["month"] == 33.01
    ledger = root / "factories" / "a-consumer-apps" / "ledger" / "spend.jsonl"
    from tools import factory_run
    assert factory_run.month_spend(ledger, "2026-11")["total"] == pytest.approx(33.01)


def test_a_packet_that_blocks_no_item_sits_at_the_stage_whose_run_raised_it(root):
    apps = root / "factories" / "a-consumer-apps"
    (apps / "escalations" / "open" / "SEC-1-20261117-gap-mining-b18d5b.md").write_text("# SEC-1: a key in a review\n")
    (apps / "escalations" / "open" / "2026-11-16-pick-a-niche.md").write_text("# Pick a niche\n")
    item(apps, "2026-11-17-odd", "awaiting_human", ["discovered", "awaiting_human"], blocked_by="escalations/open/2026-11-16-pick-a-niche.md")
    built = data.build(root, NOW)["factories"][0]
    stage = {a["title"]: a["stage"] for a in built["approvals"]}
    assert stage["SEC-1: a key in a review"] == "mine"
    # no run is named anywhere, so the packet and its item stay where the item last was
    assert stage["Pick a niche"] == "mine"
    assert by_id(built["items"])["2026-11-17-odd"]["stage"] == "mine"


def test_a_factory_with_no_entry_gets_its_columns_from_its_items(root):
    new = root / "factories" / "z-new-thing"
    item(new, "one", "polished", ["found", "polished"])
    item(new, "two", "found", [])                    # no history yet: the stage itself still counts
    item(new, "three", "killed", [])                 # killed before it reached anything
    shown = by_id(data.build(root, NOW)["factories"])["z-new-thing"]
    assert shown["name"] == "Z new thing"
    assert [(col["id"], col["name"], col["reached"]) for col in shown["stages"]] == [("found", "Found", 2), ("polished", "Polished", 1)]
    items = by_id(shown["items"])
    assert (items["one"]["stage"], items["two"]["stage"], items["three"]["stage"]) == ("polished", "found", None)
    assert items["three"]["killed"] == "No reason recorded"


def test_a_stage_no_column_holds_gets_its_own_column(root):
    item(root / "factories" / "a-consumer-apps", "odd", "parked", ["discovered", "parked"])
    apps = data.build(root, NOW)["factories"][0]
    assert apps["stages"][-1]["id"] == "parked"
    assert by_id(apps["items"])["odd"]["stage"] == "parked"


@pytest.mark.parametrize("stop", ["STOP", "factories/a-consumer-apps/STOP", "factories/a-consumer-apps/state/STOP"])
def test_any_stop_file_shows_the_factory_as_off(root, stop):
    (root / stop).write_text("halt\n")
    apps = data.build(root, NOW)["factories"][0]
    assert (apps["on"], apps["stopped_by"]) == (False, [{"file": stop, "why": "halt"}])


def test_a_broken_file_is_named_not_skipped(root):
    bad = root / "factories" / "a-consumer-apps" / "state" / "items" / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(ValueError, match="bad.json"):
        data.build(root, NOW)
    bad.unlink()
    ledger = root / "factories" / "a-consumer-apps" / "ledger" / "spend.jsonl"
    ledger.write_text("{}\nnot json\n")
    with pytest.raises(ValueError, match="spend.jsonl"):
        data.build(root, NOW)


def test_packets_are_read_whatever_their_shape(tmp_path):
    plain = tmp_path / "2026-11-16-pick-a-niche.md"
    plain.write_text("no heading here\n")
    assert data.read_packet(plain) == {
        "trigger": "2026-11-16-pick-a-niche", "title": "Pick a niche", "detail": "", "expires": None,
    }
    named = tmp_path / "BUD-1-20261117-demand-test-b59554.md"
    named.write_text("# BUD-1: ads cap is 0\nFactory: a   Expires: 2026-11-24\n")      # no Trigger in the header
    packet = data.read_packet(named)
    assert (packet["trigger"], packet["title"], packet["expires"]) == ("BUD-1", "BUD-1: ads cap is 0", "2026-11-24")


def test_two_packets_with_one_trigger_stay_apart(root):
    again = root / "factories" / "a-consumer-apps" / "escalations" / "open" / "A-AD-1-20261118-demand-test-aaaaaa.md"
    again.write_text("# Approve the second batch\nTrigger: A-AD-1\n")
    ids = [a["id"] for a in data.build(root, NOW)["factories"][0]["approvals"]]
    assert ids == ["A-AD-1", "A-AD-1 (2)"]


def test_a_paper_record_becomes_a_running_percentage(tmp_path):
    assert data.paper_line(tmp_path, "s1") is None
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper" / "s1.json").write_text(json.dumps({"daily": [["2026-11-18", 0.01, 0, 0], ["2026-11-19", -0.02, 0, 0]]}))
    assert data.paper_line(tmp_path, "s1") == [0.0, 1.0, -1.02]


def test_the_real_config_matches_the_real_factories():
    """Every configured factory exists, and every column names item stages and has a unique id."""
    repo = data.CONFIG.parents[1]
    for name, shown in data.yaml.safe_load(data.CONFIG.read_text()).items():
        assert (repo / "factories" / name).is_dir(), name
        ids = [col["id"] for col in shown.get("stages", [])]
        assert len(ids) == len(set(ids)), name
        assert all(col["from"] and col["name"] for col in shown.get("stages", [])), name
        skills = repo / "factories" / name / "skills"
        if skills.is_dir():                         # a column's runs are real skills, or its events never land on it
            missing = [skill for col in shown.get("stages", []) for skill in col.get("runs", []) if not (skills / skill).exists()]
            assert not missing, (name, missing)
    assert [f["id"] for f in data.build(repo, NOW)["factories"]]     # the checkout itself reads without error


@pytest.mark.parametrize("path, text", [
    ("state/items/list.json", "[1, 2]"),
    ("state/items/no-stage.json", '{"id": "x"}'),
    ("state/items/null-history.json", '{"id": "x", "stage": "discovered", "history": 7}'),
    ("state/items/odd-block.json", '{"id": "x", "stage": "discovered", "blocked_by": 3}'),
    ("state/items/odd-spend.json", '{"id": "x", "stage": "discovered", "spend_usd": "1"}'),
    ("state/items/odd-step.json", '{"id": "x", "stage": "discovered", "history": ["moved"]}'),
    ("budget.yaml", "monthly_caps_usd: [unclosed"),
    ("budget.yaml", "monthly_caps_usd:\n  ads: lots\n"),
    ("budget.yaml", "- a list\n"),
    ("ledger/spend.jsonl", '{"at": "2026-11-17T07:00:00Z", "usd": "1.5"}\n'),
    ("ledger/spend.jsonl", "[]\n"),
    ("outbox/pending.jsonl", '{"at": 5, "text": "x"}\n'),
])
def test_a_file_of_the_wrong_shape_is_an_error_that_says_where(root, path, text):
    (root / "factories" / "a-consumer-apps" / path).write_text(text)
    with pytest.raises(ValueError, match="a-consumer-apps"):
        data.build(root, NOW)


def test_an_item_with_null_history_still_reads(root):
    item(root / "factories" / "a-consumer-apps", "bare", "discovered", [])
    path = root / "factories" / "a-consumer-apps" / "state" / "items" / "bare.json"
    path.write_text(json.dumps({"id": "bare", "stage": "discovered", "history": None, "blocked_by": None}))
    assert by_id(data.build(root, NOW)["factories"][0]["items"])["bare"]["stage"] == "mine"


def test_the_pages_escape_what_they_put_in_attributes():
    """Item files come from factory runs. An id holding HTML must not become script in the operator's page,
    where it could flip a switch. Every value a page writes into an attribute is escaped or is not file text."""
    import re
    plain = re.compile(r'''[\w.\s?:"'=!<>&|+*(),/-]*''')      # flags, counts and sizes: no text from a file
    from_files = re.compile(r"\.(id|name|short|title|detail|summary|text|file|why|category|platform|skill|expires|gate|kind|killed|blockedBy)\b|\[\d\]")
    for page in sorted((data.CONFIG.parent / "static").iterdir()):
        for value in re.findall(r'''="\$\{((?:[^{}]|\{[^{}]*\})*)\}''', page.read_text()):
            if value.startswith("esc("):
                continue
            assert plain.fullmatch(value), (page.name, value)
            assert not from_files.search(re.sub(r"[\w.]+ ?[=!]== ?[\w.]+", "", value)), (page.name, value)
    assert 'data-i="${esc(it.id)}"' in (data.CONFIG.parent / "static" / "live.html").read_text()
