"""Essential tests for the hard gates only: money, the store account and legal copy."""
import datetime as dt

import pytest

import ads_paused
import cadence
import copy_lint
import metadata_similarity
import overlap
from _common import load_budget

BUDGET = load_budget()
RULES = BUDGET["account_protection"]


# ---------- copy_lint ----------

CLEAN = "In development. A planner that turns your week into three priorities. Get early access at $6 a month. Nothing is charged today."


def test_copy_clean_pre_build_page_passes():
    assert copy_lint.lint(CLEAN, pre_build=True, has_price=True) == []


@pytest.mark.parametrize("text", [
    "Users love how simple it is.",
    "I lost 10 pounds with this app.",
    "Rated 4.8 out of 5",
    "★★★★★",
    "Join 10,000+ users",
    "The #1 habit tracker",
    "Download now on the App Store",
    "Cut your planning time by 50%",
])
def test_copy_banned_patterns_fail(text):
    assert copy_lint.lint(text + " In development. Nothing is charged today.", pre_build=True, has_price=True)


# ---------- cadence ----------

def sub(date, kind="new_app", outcome="approved", **extra):
    return {"date": date, "app": extra.pop("app", "x"), "kind": kind, "outcome": outcome, **extra}


def day(s):
    return dt.date.fromisoformat(s)


def test_cadence_first_submission_allowed():
    assert cadence.blockers([], RULES, 0, day("2026-12-01")) == []


def test_cadence_one_new_app_a_month_before_ramp():
    subs = [sub("2026-12-01")]
    assert cadence.blockers(subs, RULES, 1, day("2026-12-20"))
    assert cadence.earliest(subs, RULES, 1, day("2026-12-02")) == day("2027-01-01")


def test_cadence_live_app_cap():
    assert cadence.blockers([], RULES, RULES["max_live_apps"], day("2027-03-01"))


@pytest.mark.parametrize("citation", ["Guideline 4.3(a) - Design - Spam", "DPLA 3.2(f)", "Fraud"])
def test_cadence_spam_or_fraud_citation_freezes_until_operator_lifts(citation):
    subs = [sub("2026-12-01", outcome="rejected", citation=citation)]
    assert cadence.frozen(subs, RULES)
    assert cadence.blockers(subs, RULES, 0, day("2027-06-01"))
    subs.append({"date": "2027-01-10", "kind": "freeze_lifted"})
    assert cadence.frozen(subs, RULES) is None


# ---------- metadata_similarity ----------

A = {"name": "Weekthree", "subtitle": "Three priorities a week",
     "description": "Weekthree turns a crowded calendar into three priorities. Pick them on Sunday, protect time for each, and review on Friday.",
     "keywords": "planner,priorities,weekly review", "release_notes": "First release with weekly planning and Friday review.",
     "screenshot_captions": ["Pick three priorities", "Protect the time", "Review on Friday"]}
B = {"name": "Potluck Pal", "subtitle": "Who brings what",
     "description": "Potluck Pal lets a host list dishes and guests claim one, so nobody arrives with a fourth pasta salad.",
     "keywords": "potluck,party,dishes", "release_notes": "Launch version with dish lists and guest claims.",
     "screenshot_captions": ["List the dishes", "Guests claim one"]}
LIMIT = float(RULES["max_listing_text_similarity_pct"])


def test_similarity_distinct_listings_pass():
    assert metadata_similarity.problems(A, {"b": B}, LIMIT) == []


def test_similarity_templated_listing_fails():
    reskin = dict(A, name="Daythree", description=A["description"].replace("Weekthree", "Daythree"))
    found = metadata_similarity.problems(reskin, {"a": A}, LIMIT)
    assert any("description" in f for f in found) and any("release_notes" in f for f in found)


# ---------- ads_paused ----------

def plan(n=2, budget=30, tranche="demand_t1"):
    return {"tranche": tranche, "campaigns": [{"ref": f"i{k}", "lifetime_budget_usd": budget, "days": 3, "country": "US"} for k in range(n)]}


def with_ads_cap(cap):
    return {**BUDGET, "monthly_caps_usd": {**BUDGET["monthly_caps_usd"], "ads": cap}}


def test_ads_default_cap_of_zero_blocks_every_plan():
    assert BUDGET["monthly_caps_usd"]["ads"] == 0
    assert any("monthly ads cap" in p for p in ads_paused.check_plan(plan(), BUDGET, 0))


def test_ads_plan_within_limits_passes():
    assert ads_paused.check_plan(plan(), with_ads_cap(2000), 0) == []


@pytest.mark.parametrize("bad", [plan(budget=31), plan(n=16), plan(tranche="scale"), {"tranche": "demand_t1", "campaigns": []}])
def test_ads_plan_over_limits_fails(bad):
    assert ads_paused.check_plan(bad, with_ads_cap(2000), 0)


def test_ads_readback_must_be_paused_planned_and_complete():
    p = plan()
    ok = {"campaigns": [{"ref": "i0", "id": "1", "status": "PAUSED", "lifetime_budget_usd": 30},
                        {"ref": "i1", "id": "2", "status": "PAUSED", "lifetime_budget_usd": 30}]}
    assert ads_paused.check_readback(p, ok) == []
    active = {"campaigns": [dict(ok["campaigns"][0], status="ACTIVE"), ok["campaigns"][1]]}
    assert any("PAUSED" in x for x in ads_paused.check_readback(p, active))
    raised = {"campaigns": [dict(ok["campaigns"][0], lifetime_budget_usd=300), ok["campaigns"][1]]}
    assert any("differs" in x for x in ads_paused.check_readback(p, raised))
    extra = {"campaigns": ok["campaigns"] + [{"ref": "ghost", "id": "9", "status": "PAUSED", "lifetime_budget_usd": 30}]}
    assert any("not in the plan" in x for x in ads_paused.check_readback(p, extra))
    assert any("not read back" in x for x in ads_paused.check_readback(p, {"campaigns": ok["campaigns"][:1]}))


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


# ---------- publish (dry run) ----------

import json

import publish


def test_publish_ads_needs_an_approved_packet_and_writes_paused_campaigns_once(tmp_path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan()))
    budget = with_ads_cap(2000)
    assert publish.publish_ads(plan_path, "A-AD-1", tmp_path, budget, "2026-12")       # no packet yet
    assert not (tmp_path / "readback.json").exists()
    (tmp_path / "escalations" / "approved").mkdir(parents=True)
    (tmp_path / "escalations" / "approved" / "2026-12-01-A-AD-1-batch1.md").write_text("ok")
    assert publish.publish_ads(plan_path, "A-AD-1", tmp_path, budget, "2026-12") == []
    assert publish.publish_ads(plan_path, "A-AD-1", tmp_path, budget, "2026-12") == []  # retry
    campaigns = json.loads((tmp_path / "readback.json").read_text())["campaigns"]
    assert [c["status"] for c in campaigns] == ["PAUSED", "PAUSED"]


def test_publish_ads_refuses_a_plan_over_budget(tmp_path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan()))
    (tmp_path / "escalations" / "approved").mkdir(parents=True)
    (tmp_path / "escalations" / "approved" / "A-AD-1.md").write_text("ok")
    assert publish.publish_ads(plan_path, "A-AD-1", tmp_path, BUDGET, "2026-12")       # ads cap is 0
    assert not (tmp_path / "readback.json").exists()


def test_publish_drafts_writes_drafts_and_refuses_bad_copy(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"posts": [{"caption": "Three priorities, one week.", "hashtags": ["#planning"]}]}))
    assert publish.publish_drafts(manifest, []) == []
    assert json.loads((tmp_path / "drafts.json").read_text())["drafts"] == [{"post": 1, "id": "dry-1", "state": "draft"}]
    manifest.write_text(json.dumps({"posts": [{"caption": "Users love it. Rated 4.8 out of 5"}]}))
    assert publish.publish_drafts(manifest, [])


# ---- page_check.js: walks a test page's funnel in a real browser. Skipped where Node or Playwright is missing.

PAGE = """<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><body>
<button id="p" data-walk="1">Get early access</button>
<form id="f" hidden><input type="email" id="e" data-walk="2"><button data-walk="3">Join</button></form>
<script>
var C = window.LAUNCH || {};
function track(n){ if (C.eventEndpoint && navigator.sendBeacon) navigator.sendBeacon(C.eventEndpoint, JSON.stringify({event:n})); }
track("page_view");
p.onclick=function(){track("price_click");%s};
f.onsubmit=function(ev){ev.preventDefault();fetch(C.signupEndpoint,{method:"POST",body:"{}"}).then(function(){track("committed_signup");});};
</script>"""


def run_page_check(tmp_path, page):
    import shutil, subprocess
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    if not shutil.which("node"):
        pytest.skip("node not installed")
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text(page)
    proc = subprocess.run(["node", str(root / "page_check.js"), str(site), str(tmp_path / "check")], capture_output=True, text=True, timeout=120)
    if "Cannot find module 'playwright'" in proc.stderr or "Executable doesn't exist" in proc.stderr:
        pytest.skip("playwright not installed")
    return proc


def test_page_check_walks_a_working_funnel(tmp_path):
    proc = run_page_check(tmp_path, PAGE % "f.hidden=false")
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["events"] == ["page_view", "price_click", "committed_signup"]
    assert report["signup_posted"] and not report["external_requests"]
    assert all(__import__("os").path.exists(s) for s in report["screenshots"])


def test_page_check_fails_when_a_step_cannot_be_used(tmp_path):
    proc = run_page_check(tmp_path, PAGE % "")   # the button never opens the form
    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert "committed_signup" not in report["events"] and not report["signup_posted"]


def test_page_check_fails_a_page_that_clicks_fine_but_sends_nothing(tmp_path):
    silent = '<!doctype html><body><button data-walk="1">Get early access</button>'
    proc = run_page_check(tmp_path, silent)
    assert proc.returncode == 1
    assert "no sign-up was posted" in json.loads(proc.stdout)["problems"]


def test_page_check_follows_a_step_that_appears_after_a_click(tmp_path):
    late = PAGE.replace('<form id="f" hidden><input type="email" id="e" data-walk="2"><button data-walk="3">Join</button></form>', '<div id="slot"></div>') % (
        "slot.innerHTML='<form id=f><input type=email id=e data-walk=2><button data-walk=3>Join</button></form>';"
        "f.onsubmit=function(ev){ev.preventDefault();fetch(C.signupEndpoint,{method:'POST',body:'{}'}).then(function(){track('committed_signup');});}")
    late = late.replace("f.onsubmit=function(ev){ev.preventDefault();fetch(C.signupEndpoint,{method:\"POST\",body:\"{}\"}).then(function(){track(\"committed_signup\");});};", "")
    proc = run_page_check(tmp_path, late)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(proc.stdout)["events"][-1] == "committed_signup"


def test_copy_lint_reads_html_as_a_person_would():
    html = "<style>.a{width:100%}</style><p>In development. Early access.</p><script>var x = 50 % 3;</script>"
    assert copy_lint.lint(copy_lint.visible_text(html), pre_build=True) == []
    assert copy_lint.lint(copy_lint.visible_text("<p>In development. Users love it.</p>"), pre_build=True)
    assert copy_lint.lint(copy_lint.visible_text("<p>In development. Users&nbsp;love it. &#9733;&#9733;</p>"), pre_build=True)


def test_page_check_fails_a_page_wider_than_the_phone(tmp_path):
    proc = run_page_check(tmp_path, (PAGE % "f.hidden=false") + '<div style="width:900px;height:10px"></div>')
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["sideways_scroll"]


def test_voice_never_prints_or_crashes_on_a_strange_credentials_file(tmp_path, capsys, monkeypatch):
    voice = _voice()
    cred = tmp_path / ".heygen" / "credentials"
    cred.parent.mkdir()
    for content in ["api_key: SECRETKEY123\nother: x", '{"oauth": "x"}', '{"oauth": {"access_token": "SECRETKEY123", "expires_at": 5}}', "[1]"]:
        cred.write_text(content)
        assert voice.heygen_headers({}, tmp_path)[0] is None
    cred.write_text(json.dumps({"oauth": {"access_token": "t", "expires_at": "2999-01-01T00:00:00.123456789Z"}}))
    assert voice.heygen_headers({}, tmp_path)[0] is not None                     # long fractions still parse on Python 3.9

    def boom(*a, **k):
        raise ValueError("Invalid header value b'SECRETKEY123'")
    monkeypatch.setattr(voice, "heygen_headers", lambda: ({"X-Api-Key": "SECRETKEY123"}, "HeyGen API key"))
    monkeypatch.setattr(voice, "speak_heygen", boom)
    monkeypatch.setattr(voice, "speak_local", boom)
    assert voice.main(["hello", "-o", str(tmp_path / "vo")]) == 1
    assert "SECRETKEY123" not in capsys.readouterr().out


# ---- voice.py: which voice is used, and that a dead login falls back instead of failing or leaking

def _voice():
    import importlib
    return importlib.import_module("voice")


def test_voice_prefers_key_then_valid_login_and_refuses_an_expired_one(tmp_path):
    voice = _voice()
    assert voice.heygen_headers({"HEYGEN_API_KEY": "k"}, tmp_path)[0] == {"X-Api-Key": "k"}
    assert voice.heygen_headers({}, tmp_path)[0] is None                       # no login at all
    cred = tmp_path / ".heygen" / "credentials"
    cred.parent.mkdir()
    cred.write_text(json.dumps({"oauth": {"access_token": "t", "expires_at": "2999-01-01T00:00:00Z"}}))
    assert voice.heygen_headers({}, tmp_path)[0]["Authorization"] == "Bearer t"
    cred.write_text(json.dumps({"oauth": {"access_token": "t", "expires_at": "2020-01-01T00:00:00Z"}}))
    headers, note = voice.heygen_headers({}, tmp_path)
    assert headers is None and "expired" in note and "t" not in note.split()   # says why, never the token
    assert cred.read_text().count("2020-01-01")                                # the login file is never rewritten


def test_voice_heygen_writes_audio_and_reports_length(tmp_path):
    voice = _voice()

    class Resp:
        def __init__(self, body): self.body = body
        def read(self): return self.body
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def opener(req, timeout=0):
        if req.full_url == voice.HEYGEN_SPEECH_URL:
            assert json.loads(req.data)["text"] == "hello"
            return Resp(json.dumps({"data": {"audio_url": "https://cdn.example/a.mp3", "word_timestamps": [{"word": "hello", "start": 0, "end": 0.6}]}}).encode())
        assert "Authorization" not in req.headers and "X-api-key" not in req.headers   # no credential sent to the file host
        return Resp(b"mp3-bytes")

    result = voice.speak_heygen("hello", tmp_path / "audio" / "vo-1", "v", {"X-Api-Key": "k"}, opener)
    assert result["provider"] == "heygen" and result["durationSeconds"] == 0.75
    assert (tmp_path / "audio" / "vo-1.mp3").read_bytes() == b"mp3-bytes"
    with pytest.raises(RuntimeError):
        voice.speak_heygen("hello", tmp_path / "x", "v", {}, lambda req, timeout=0: Resp(b'{"data": {"audio_url": "http://insecure/a.mp3"}}'))
