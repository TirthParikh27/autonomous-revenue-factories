"""Tests for the second set of Factory A gates. Thresholds come from the real budget.yaml and data/."""
import copy
import datetime as dt
import json

import pytest
import yaml

import content_lint
import demand_assets
import gap_schema
import overlap
import review_checklist
import spec_gate
from _common import load_budget

BUDGET = load_budget()
RULES = BUDGET["account_protection"]
TODAY = dt.date(2026, 11, 16)
EXCLUDED = gap_schema.load_excluded()


def write_json(path, data):
    path.write_text(json.dumps(data))
    return path


# ---------- gap_schema ----------

APPS = ["Alpha Planner", "Beta Tasks", "Gamma Focus", "Delta Notes", "Epsilon Lists"]


def scout():
    return {
        "id": "2026-11-16-week-planner",
        "category": "Productivity",
        "unmet_job": "Turn a messy week into three priorities without manual sorting.",
        "competitors": [{"name": a, "store_url": f"https://apps.apple.com/app/id{100 + i}"} for i, a in enumerate(APPS)],
        "complaints": [{"id": f"c{i}", "quote": f"cannot reorder tasks by priority ({i})", "app": APPS[i % 3],
                        "source_url": f"https://apps.apple.com/app/id{100 + i % 3}?see-all=reviews",
                        "date": "2026-09-01"} for i in range(15)],
        "keyword_popularity": [{"term": "weekly planner", "figure": 41, "source": "Astro", "date": "2026-11-16"}],
        "trend_signals": [{"signal": "rising", "source": "https://trends.example/x", "date": "2026-11-01"}],
        "revenue_guess": {"usd_month": 9000, "estimate": True, "source": "https://estimator.example/app"},
    }


def test_gap_valid_scout_passes():
    assert gap_schema.problems(scout(), TODAY, EXCLUDED) == []


def test_gap_excluded_list_has_the_spec_categories():
    for name in ("dating", "flashlight", "sound effect", "wallpaper", "simple timer", "fortune telling",
                 "drinking game", "fart", "burp"):
        assert name in EXCLUDED
    assert gap_schema.excluded_match("Utilities: updating apps", EXCLUDED) is None   # word boundary


def broken(edit):
    s = scout()
    edit(s)
    return s


@pytest.mark.parametrize("edit, expect", [
    (lambda s: s.pop("unmet_job"), "missing unmet_job"),
    (lambda s: s.pop("keyword_popularity"), "missing keyword_popularity"),
    (lambda s: s.__setitem__("keyword_popularity", []), "missing keyword_popularity"),
    (lambda s: s.__setitem__("category", "Dating"), "excluded"),
    (lambda s: s.__setitem__("category", "Simple timer apps"), "excluded"),
    (lambda s: s.__setitem__("complaints", s["complaints"][:14]), "14 complaint(s)"),
    (lambda s: [c.__setitem__("app", APPS[i % 2]) for i, c in enumerate(s["complaints"])], "cover 2 app(s)"),
    (lambda s: s["complaints"][3].__setitem__("source_url", "apps.apple.com/review"), "no http(s) source_url"),
    (lambda s: s["complaints"][3].pop("source_url"), "no http(s) source_url"),
    (lambda s: s["complaints"][4].__setitem__("date", "2025-11-15"), "older than 12 months"),
    (lambda s: s["complaints"][4].__setitem__("date", "2026-12-01"), "after"),
    (lambda s: s["complaints"][4].__setitem__("date", "last spring"), "no valid date"),
    (lambda s: s["complaints"][5].pop("quote"), "no quote"),
    (lambda s: s.__setitem__("competitors", s["competitors"][:2]), "2 competitor(s)"),
    (lambda s: s["competitors"][1].__setitem__("store_url", s["competitors"][0]["store_url"]), "repeated"),
    (lambda s: s["competitors"][1].pop("name"), "has no name"),
    (lambda s: s["keyword_popularity"][0].pop("source"), "keyword_popularity 0 has no source"),
    (lambda s: s["revenue_guess"].pop("source"), "estimate without a source"),
    (lambda s: s["trend_signals"][0].update(estimate=True, source=""), "estimate without a source"),
])
def test_gap_failures(edit, expect):
    found = gap_schema.problems(broken(edit), TODAY, EXCLUDED)
    assert any(expect in p for p in found), found


def test_gap_complaint_exactly_twelve_months_old_passes():
    s = broken(lambda s: s["complaints"][0].__setitem__("date", "2025-11-16"))
    assert gap_schema.problems(s, TODAY, EXCLUDED) == []


def test_gap_main_exit_codes(tmp_path, capsys):
    good = write_json(tmp_path / "good.json", scout())
    bad = write_json(tmp_path / "bad.json", broken(lambda s: s.__setitem__("category", "Wallpaper")))
    assert gap_schema.main([str(good), "--today", "2026-11-16"]) == 0
    assert "OK gap_schema" in capsys.readouterr().out
    assert gap_schema.main([str(bad), "--today", "2026-11-16"]) == 1
    assert "FAIL gap_schema" in capsys.readouterr().out
    (tmp_path / "junk.json").write_text("{not json")
    assert gap_schema.main([str(tmp_path / "junk.json")]) == 1


# ---------- spec_gate ----------

BODY = "\n\n".join(f"## {s.title()}\nShort text for {s}." for s in spec_gate.SECTIONS)


def front():
    s = scout()
    return {
        "id": s["id"], "working_name": "Three Things", "category": "Productivity",
        "core_job": "Turn a messy week into three priorities.", "proposed_price_usd_month": 6,
        "differentiator": "Ranks tasks from calendar load automatically.", "differentiator_type": "capability",
        "competitors": [dict(c) for c in s["competitors"]],
        "complaint_refs": ["c0", "c1", 2],
    }


def spec_text(fm=None, body=BODY):
    return "---\n" + yaml.safe_dump(fm or front(), sort_keys=False) + "---\n" + body


def spec_problems(text, earlier=None):
    return spec_gate.problems(text, scout(), RULES["min_named_competitors_in_spec"], EXCLUDED, earlier)


def test_spec_valid_passes():
    assert spec_problems(spec_text()) == []


def edited_front(edit):
    fm = front()
    edit(fm)
    return spec_text(fm)


@pytest.mark.parametrize("edit, expect", [
    (lambda f: f.pop("working_name"), "missing working_name"),
    (lambda f: f.pop("differentiator"), "missing differentiator"),
    (lambda f: f.__setitem__("category", "Fortune telling"), "excluded"),
    (lambda f: f.__setitem__("proposed_price_usd_month", 0), "positive number"),
    (lambda f: f.__setitem__("proposed_price_usd_month", "$6"), "positive number"),
    (lambda f: f.__setitem__("proposed_price_usd_month", -3), "positive number"),
    (lambda f: f.__setitem__("differentiator_type", "visual"), "not a capability"),
    (lambda f: f.__setitem__("differentiator_type", "Price"), "not a capability"),
    (lambda f: f.__setitem__("competitors", f["competitors"][:4]), "4 named competitor(s)"),
    (lambda f: f["competitors"][2].__setitem__("store_url", "https://apps.apple.com/app/id999"), "not in scout file"),
    (lambda f: f["competitors"][2].pop("name"), "has no name"),
    (lambda f: f.__setitem__("complaint_refs", ["c0", "c1"]), "cites 2 complaint(s)"),
    (lambda f: f.__setitem__("complaint_refs", ["c0", "c3", "c6"]), "from 1 app(s)"),   # all Alpha Planner
    (lambda f: f.__setitem__("complaint_refs", ["c0", "c1", "c99"]), "'c99' is not in the scout file"),
])
def test_spec_front_matter_failures(edit, expect):
    found = spec_problems(edited_front(edit))
    assert any(expect in p for p in found), found


def test_spec_needs_front_matter_sections_and_word_limit():
    assert spec_problems(BODY) == ["no YAML front matter"]
    assert any("missing section 'review risk'" in p
               for p in spec_problems(spec_text(body=BODY.replace("## Review Risk", "## Risks"))))
    long_body = BODY + "\n\n" + "word " * 600
    assert any("must be under 600" in p for p in spec_problems(spec_text(body=long_body)))


def test_spec_reused_core_job_fails():
    found = spec_problems(spec_text(), {"old.md": "turn a MESSY week into three priorities"})
    assert any("core_job matches old.md" in p for p in found)


def test_spec_main_exit_codes(tmp_path, capsys):
    scout_path = write_json(tmp_path / "scout.json", scout())
    specs = tmp_path / "specs"
    specs.mkdir()
    new = specs / "new.md"
    new.write_text(spec_text())
    assert spec_gate.main([str(new), str(scout_path), "--earlier", str(specs)]) == 0
    assert "OK spec_gate" in capsys.readouterr().out
    (specs / "old.md").write_text(spec_text())
    assert spec_gate.main([str(new), str(scout_path), "--earlier", str(specs)]) == 1
    assert "FAIL spec_gate: core_job matches old.md" in capsys.readouterr().out


# ---------- demand_assets ----------

PAGE = """<!doctype html><html><head><title>Three Things</title>
<style>.x{color:red}</style>
<script>track('page_view'); function go(){ track('price_click'); }</script></head>
<body><h1>Three Things is in development</h1>
<p>A planner that turns your week into three priorities.</p>
<button onclick="go()">Get early access at $6 a month</button>
<form onsubmit="track('committed_signup')">
<p>The app is not available yet. Nothing is charged today.</p>
<input type="email" name="email" required>
<label><input type="checkbox" required> I consent to being emailed when it launches.</label>
</form>
<a href="privacy.html">Privacy</a></body></html>"""
AD = "In development: a planner that turns your week into three priorities. Join early access."


def make_site(tmp_path, page=PAGE, ads=(AD,), privacy=True):
    site = tmp_path / "demo" / "site"
    site.mkdir(parents=True)
    (site / "index.html").write_text(page)
    if privacy:
        (site / "privacy.html").write_text("notice")
    ads_dir = tmp_path / "demo" / "ads"
    ads_dir.mkdir()
    for i, text in enumerate(ads):
        (ads_dir / f"ad{i}.txt").write_text(text)
    return site


def assets(site, price=6):
    return demand_assets.problems(site, price, BUDGET["ads"]["max_creatives_per_idea"])


def test_demand_valid_page_passes(tmp_path):
    assert assets(make_site(tmp_path, ads=(AD, AD, AD))) == []


def test_demand_events_may_live_in_a_js_file(tmp_path):
    site = make_site(tmp_path, page=PAGE.replace("track('committed_signup')", "submit()"))
    assert any("committed_signup" in p for p in assets(site))
    (site / "app.js").write_text("function submit(){ track('committed_signup'); }")
    assert assets(site) == []


@pytest.mark.parametrize("old, new, expect", [
    ("track('price_click')", "track('click')", "event 'price_click'"),
    ("track('page_view');", "", "event 'page_view'"),
    ("$6 a month", "$9 a month", "page shows $9"),
    ("$6 a month", "early access", "no price shown"),
    ('href="privacy.html"', 'href="about.html"', "no privacy link"),
    ('href="privacy.html"', 'href="privacy-notice.html"', "does not resolve"),
    ('type="email"', 'type="text"', "no email input"),
    ("I consent to being emailed when it launches.", "Email me at launch.", "no consent line"),
    ('<input type="email"', '<input name="card-number"><input type="email"', "card input"),
    ('<input type="email"', '<input type="password"><input type="email"', "password input"),
    ("</head>", '<script src="https://js.stripe.com/v3/"></script></head>', "stripe"),
    ("Nothing is charged today.", "", "nothing is charged today"),
    ("A planner that", "Users love this planner that", "speaks for customers"),
])
def test_demand_page_failures(tmp_path, old, new, expect):
    assert old in PAGE
    found = assets(make_site(tmp_path, page=PAGE.replace(old, new)))
    assert any(expect in p for p in found), found


def test_demand_page_without_pre_build_marker_fails(tmp_path):
    page = PAGE.replace("Three Things is in development", "Three Things").replace("Get early access at", "Join at")
    found = assets(make_site(tmp_path, page=page))
    assert any("in development" in p for p in found), found


def test_demand_hidden_text_in_scripts_is_not_linted_as_copy(tmp_path):
    page = PAGE.replace("track('page_view');", "track('page_view'); var s='Download now';")
    assert assets(make_site(tmp_path, page=page)) == []


def test_demand_absolute_privacy_link_is_accepted(tmp_path):
    page = PAGE.replace('href="privacy.html"', 'href="https://example.org/privacy"')
    assert assets(make_site(tmp_path, page=page, privacy=False)) == []


@pytest.mark.parametrize("ads, expect", [
    ((), "0 ad file(s)"),
    ((AD, AD, AD, AD), "4 ad file(s)"),
    (("A planner for your week.",), "in development"),
    (("In development. Download now!",), "implies the app is available"),
    (("In development. Rated 4.9 out of 5.",), "star rating"),
])
def test_demand_ad_failures(tmp_path, ads, expect):
    found = assets(make_site(tmp_path, ads=ads))
    assert any(expect in p for p in found), found


def test_demand_main_exit_codes_and_claims(tmp_path, capsys):
    page = PAGE.replace("three priorities.</p>", "three priorities in 2x less time.</p>")
    site = make_site(tmp_path, page=page)
    assert demand_assets.main([str(site), "--price", "6"]) == 1
    assert "numeric claim" in capsys.readouterr().out
    (site.parent / "claims.yaml").write_text("claims:\n  - claim: plans a week in 2x less time\n")
    assert demand_assets.main([str(site), "--price", "6"]) == 0
    assert "OK demand_assets" in capsys.readouterr().out
    assert demand_assets.main([str(tmp_path / "missing"), "--price", "6"]) == 1


# ---------- overlap ----------

FEATURE_A = """import { useState } from 'react';
// rank tasks by load
export function rankTasks(tasks, calendar) {
  const weighted = tasks.map(t => ({ ...t, w: calendar.loadFor(t.day) * t.effort }));
  return weighted.sort((a, b) => b.w - a.w).slice(0, 3);
}
"""
FEATURE_B = """export function scoreHabits(entries) {
  const streaks = entries.filter(e => e.done).map(e => e.streakLength);
  return streaks.reduce((sum, s) => sum + Math.log1p(s), 0);
}
"""
SCAFFOLD = """export function PaywallScreen({ offering, onPurchase }) {
  const pkg = offering.availablePackages.find(p => p.identifier === '$rc_monthly');
  return renderPaywall(pkg, onPurchase, offering.serverDescription);
}
"""


def app(root, feature, extras=None):
    files = {"src/features/main.ts": feature, "src/paywall/Paywall.tsx": SCAFFOLD, "auth/session.ts": SCAFFOLD}
    files.update(extras or {})
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


def run_overlap(new, *others):
    return overlap.evaluate(new, list(others), RULES["shared_scaffold_paths"], RULES["max_feature_code_overlap_pct"])


def test_overlap_distinct_apps_pass_even_with_shared_scaffold(tmp_path):
    scores, fails = run_overlap(app(tmp_path / "a", FEATURE_A), app(tmp_path / "b", FEATURE_B))
    assert fails == [] and list(scores.values()) == [0.0]


def test_overlap_copied_feature_code_fails(tmp_path):
    a = app(tmp_path / "a", FEATURE_A)
    b = app(tmp_path / "b", FEATURE_B + "\n" + FEATURE_A.replace("  ", "    "))   # reindented copy
    c = app(tmp_path / "c", FEATURE_B)
    scores, fails = run_overlap(a, b, c)
    assert scores[str(b)] == 100.0 and scores[str(c)] == 0.0
    assert len(fails) == 1 and str(b) in fails[0]


def test_overlap_ignores_tests_config_lockfiles_node_modules_and_noise(tmp_path):
    copied = {"src/features/main.test.ts": FEATURE_B, "tests/x.ts": FEATURE_B, "babel.config.js": FEATURE_B,
              "node_modules/lib/index.js": FEATURE_B, "package-lock.json": FEATURE_B, ".expo/x.js": FEATURE_B,
              "README.md": FEATURE_B}
    a = app(tmp_path / "a", FEATURE_A, copied)
    scores, fails = run_overlap(a, app(tmp_path / "b", FEATURE_B))
    assert fails == [] and list(scores.values()) == [0.0]


def test_overlap_normalisation_rules():
    assert overlap.normalise("   ") is None
    assert overlap.normalise("// a long comment line here") is None
    assert overlap.normalise(" * continued block comment text") is None
    assert overlap.normalise("import { thing } from './somewhere/far';") is None
    assert overlap.normalise("const x = require('some-long-module');") is None
    assert overlap.normalise("return a;") is None                      # under 12 characters
    assert overlap.normalise("  return  weighted.sort( ) ;") == "returnweighted.sort();"


def test_overlap_just_over_the_limit_fails(tmp_path):
    unique = [f"const uniqueValueNumber{i} = compute({i});" for i in range(7)]
    shared = [f"const sharedValueNumber{i} = compute({i});" for i in range(3)]   # 3 of 10 = 30%, at limit
    a = app(tmp_path / "a", "\n".join(unique + shared))
    b = app(tmp_path / "b", "\n".join(shared))
    assert run_overlap(a, b)[1] == []
    a2 = app(tmp_path / "a2", "\n".join(unique[:6] + shared + ["const sharedValueNumber0b = compute(0);"]))
    b2 = app(tmp_path / "b2", "\n".join(shared + ["const sharedValueNumber0b = compute(0);"]))
    scores, fails = run_overlap(a2, b2)
    assert scores[str(b2)] == 40.0 and fails


def test_overlap_main_exit_codes(tmp_path, capsys):
    a = app(tmp_path / "a", FEATURE_A)
    b = app(tmp_path / "b", FEATURE_B)
    copy_app = app(tmp_path / "copy", FEATURE_A)
    assert overlap.main(["overlap.py", str(a), str(b)]) == 0
    assert "OK overlap: 0.0%" in capsys.readouterr().out
    assert overlap.main(["overlap.py", str(a), str(b), str(copy_app)]) == 1
    out = capsys.readouterr().out
    assert "FAIL overlap: 100.0%" in out and "OK overlap: 0.0%" in out


# ---------- review_checklist ----------

TEMPLATE = yaml.safe_load((review_checklist.TEMPLATE).read_text())


def test_review_template_covers_the_skill_groups_and_marks_unverified():
    groups = {r["group"] for r in TEMPLATE["rows"]}
    assert groups == {"differentiation_4_3b", "substance", "subscriptions", "privacy", "review_access",
                      "content_rules", "listing_honesty"}
    for row in TEMPLATE["rows"]:
        assert row["id"] and row["requirement"]
        assert row["unverified"] is (row["group"] in {"subscriptions", "privacy", "review_access"})
    ids = [r["id"] for r in TEMPLATE["rows"]]
    assert len(ids) == len(set(ids))


def filled(root):
    (root / "store").mkdir(parents=True, exist_ok=True)
    (root / "store" / "shot1.png").write_bytes(b"png")
    (root / "src.ts").write_text("x")
    rows = []
    for i, r in enumerate(TEMPLATE["rows"]):
        kind = ["file", "test", "screenshot"][i % 3]
        ref = {"file": "src.ts", "test": "e2e::restore", "screenshot": "store/shot1.png"}[kind]
        rows.append({"id": r["id"], "group": r["group"], "result": "pass",
                     "evidence": {"type": kind, "ref": ref}, "unverified": False})
    return {"rows": rows}


def required():
    return review_checklist.template_ids()


def test_review_complete_checklist_passes(tmp_path):
    assert review_checklist.problems(filled(tmp_path), tmp_path, required()) == []


@pytest.mark.parametrize("edit, expect", [
    (lambda rows: rows[0].__setitem__("result", "fail"), "result is 'fail'"),
    (lambda rows: rows[0].pop("result"), "result is None"),
    (lambda rows: rows[1].pop("evidence"), "no evidence"),
    (lambda rows: rows[1]["evidence"].__setitem__("ref", " "), "no evidence"),
    (lambda rows: rows[1]["evidence"].__setitem__("type", "reasoning"), "no evidence"),
    (lambda rows: rows[0]["evidence"].__setitem__("ref", "missing.ts"), "does not exist"),
    (lambda rows: rows[2]["evidence"].__setitem__("ref", "store/none.png"), "does not exist"),
    (lambda rows: rows[0]["evidence"].__setitem__("ref", "../outside.ts"), "does not exist"),
    (lambda rows: rows[0]["evidence"].__setitem__("ref", "store"), "does not exist"),       # a folder
    (lambda rows: rows[6].__setitem__("unverified", True), "still marked unverified"),
    (lambda rows: rows.pop(), "required by the checklist template but absent"),
    (lambda rows: rows.append(copy.deepcopy(rows[0])), "duplicate id"),
])
def test_review_failures(tmp_path, edit, expect):
    (tmp_path.parent / "outside.ts").write_text("x")
    checklist = filled(tmp_path)
    edit(checklist["rows"])
    found = review_checklist.problems(checklist, tmp_path, required())
    assert any(expect in p for p in found), found


def test_review_main_exit_codes(tmp_path, capsys):
    root = tmp_path / "root"
    good = write_json(tmp_path / "good.json", filled(root))
    assert review_checklist.main([str(good), "--root", str(root)]) == 0
    assert "OK review_checklist" in capsys.readouterr().out
    bad = filled(root)
    bad["rows"][0]["result"] = "fail"
    assert review_checklist.main([str(write_json(tmp_path / "bad.json", bad)), "--root", str(root)]) == 1
    assert "FAIL review_checklist" in capsys.readouterr().out


# ---------- content_lint ----------

CONTENT = BUDGET["content"]


def post(**over):
    p = {"id": "p1", "format": "slideshow", "caption": "Three priorities for your week, picked from your calendar.",
         "hashtags": ["planner", "productivity"], "concept": False, "ai_generated_elements": [],
         "ai_label_required": False}
    p.update(over)
    return p


def test_content_clean_manifest_passes():
    assert content_lint.problems({"posts": [post(), post(id="p2", format="demo")]}, CONTENT) == []


@pytest.mark.parametrize("p, expect", [
    (post(caption="I lost hours every week until this."), "first-person customer statement"),
    (post(caption="Rated 5 stars by students."), "star rating"),
    (post(caption="Plan 3x faster."), "numeric claim"),
    (post(caption=""), "missing caption"),
    (post(hashtags=["a", "b", "c", "d", "e", "f"]), "6 hashtags"),
    (post(caption="Plan your week #a #b #c #d", hashtags=["e", "f"]), "6 hashtags"),
    (post(concept=True), "in development"),
    (post(ai_label_required=True), "realistic AI people or scenes are disabled"),
])
def test_content_failures(p, expect):
    found = content_lint.problems({"posts": [p]}, CONTENT)
    assert any(expect in f for f in found), found


@pytest.mark.parametrize("field", content_lint.LABEL_FIELDS)
def test_content_missing_label_field_fails(field):
    p = post()
    p.pop(field)
    assert any(f"missing {field}" in f for f in content_lint.problems({"posts": [p]}, CONTENT))


def test_content_rules_follow_budget():
    assert content_lint.problems({"posts": [post(ai_label_required=True)]},
                                 dict(CONTENT, allow_realistic_ai_people_or_scenes=True)) == []
    assert content_lint.problems({"posts": [post(hashtags=list("abcde"))]}, CONTENT) == []
    assert content_lint.problems({"posts": []}, CONTENT) == ["manifest has no posts"]


def test_content_main_exit_codes_and_directory_argument(tmp_path, capsys):
    write_json(tmp_path / "manifest.json", {"posts": [post(caption="Plan in 3x fewer taps.")]})
    assert content_lint.main([str(tmp_path)]) == 1
    assert "FAIL content_lint" in capsys.readouterr().out
    claims = tmp_path / "claims.yaml"
    claims.write_text("claims:\n  - claim: plan in 3x fewer taps than before\n")
    assert content_lint.main([str(tmp_path / "manifest.json"), "--claims", str(claims)]) == 0
    assert "OK content_lint" in capsys.readouterr().out
