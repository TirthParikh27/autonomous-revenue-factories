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
