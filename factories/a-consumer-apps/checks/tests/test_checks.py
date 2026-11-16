"""Tests for Factory A's gates. Thresholds come from the real budget.yaml, so a change there is felt here."""
import datetime as dt

import pytest

import ads_paused
import cadence
import copy_lint
import decide
import metadata_similarity
import portfolio_distinct
import screen_rank
from _common import load_budget

BUDGET = load_budget()
RULES = BUDGET["account_protection"]


# ---------- screen_rank ----------

def runs(*rankings):
    ids = sorted(rankings[0])
    orders = [ids[i:] + ids[:i] for i in range(len(rankings))]
    return [{"card_order": o, "ranking": list(r)} for o, r in zip(orders, rankings)]


def test_screen_kills_bottom_half_by_median_rank():
    r = screen_rank.evaluate(runs("abcdef", "abcdfe", "bacdef"), 3, 0.5)
    assert r["screened"] == ["a", "b", "c"] and r["killed"] == ["d", "e", "f"]


def test_screen_one_outlier_run_cannot_kill_a_good_idea():
    r = screen_rank.evaluate(runs("abcd", "abcd", "bcda"), 3, 0.5)
    assert "a" in r["screened"]


def test_screen_tie_at_cut_line_survives():
    tied = screen_rank.evaluate(
        [{"card_order": list("abcd"), "ranking": list("abcd")},
         {"card_order": list("bcda"), "ranking": list("acbd")}], 2, 0.5)
    assert tied["killed"] == ["d"]          # b and c tie on 2.5, so c is spared


@pytest.mark.parametrize("bad", [
    lambda: screen_rank.evaluate(runs("abc", "abc"), 3, 0.5),                       # too few runs
    lambda: screen_rank.evaluate(runs("abc", "abc", "abd"), 3, 0.5),                # an idea missing
    lambda: screen_rank.evaluate([{"card_order": list("abc"), "ranking": list("abc")}] * 3, 3, 0.5),  # same order
])
def test_screen_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        bad()


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


def test_copy_numeric_claim_allowed_when_listed():
    assert copy_lint.lint("Plan a week in 3 steps, 50% fewer taps.", claims=["50% fewer taps than the stock app"]) == []


def test_copy_brand_voice_we_is_allowed():
    assert copy_lint.lint("We use your calendar to find free time.") == []


def test_copy_pre_build_needs_marker_and_price_needs_no_charge_line():
    assert copy_lint.lint("A planner for busy weeks.", pre_build=True)
    assert copy_lint.lint("Early access at $6 a month.", pre_build=True, has_price=True)


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


def test_cadence_two_a_month_after_three_clean_approvals_but_ten_days_apart():
    subs = [sub("2026-12-01"), sub("2027-01-02"), sub("2027-02-02"), sub("2027-03-01")]
    assert cadence.blockers(subs, RULES, 4, day("2027-03-05"))            # under 10 days
    assert cadence.blockers(subs, RULES, 4, day("2027-03-11")) == []       # second of the month, 10 days on
    subs.append(sub("2027-03-11", outcome="pending"))
    assert cadence.blockers(subs, RULES, 4, day("2027-03-25"))            # third in a month


def test_cadence_any_submission_same_day_blocks():
    subs = [sub("2027-03-01", kind="update")]
    assert cadence.blockers(subs, RULES, 1, day("2027-03-01"))
    assert cadence.blockers(subs, RULES, 1, day("2027-03-02")) == []


def test_cadence_live_app_cap():
    assert cadence.blockers([], RULES, RULES["max_live_apps"], day("2027-03-01"))


def test_cadence_rolling_twelve_month_ceiling():
    subs = [sub(f"2026-{m:02d}-01") for m in range(1, 13)]
    assert any("12 months" in w for w in cadence.blockers(subs, RULES, 3, day("2026-12-20")))


@pytest.mark.parametrize("citation", ["Guideline 4.3(a) - Design - Spam", "DPLA 3.2(f)", "Fraud"])
def test_cadence_spam_or_fraud_citation_freezes_until_operator_lifts(citation):
    subs = [sub("2026-12-01", outcome="rejected", citation=citation)]
    assert cadence.frozen(subs, RULES)
    assert cadence.blockers(subs, RULES, 0, day("2027-06-01"))
    subs.append({"date": "2027-01-10", "kind": "freeze_lifted"})
    assert cadence.frozen(subs, RULES) is None


def test_cadence_ordinary_rejection_does_not_freeze():
    assert cadence.frozen([sub("2026-12-01", outcome="rejected", citation="Guideline 2.1 - App Completeness")], RULES) is None


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


def test_similarity_identical_name_fails():
    assert any("name" in f for f in metadata_similarity.problems(dict(B, name="weekthree"), {"a": A}, LIMIT))


# ---------- portfolio_distinct ----------

def item(i, name, cat, job):
    return {"id": i, "working_name": name, "category": cat, "core_job": job}


def test_distinct_ideas_pass_and_near_copies_fail():
    a = item("a", "Weekthree", "Productivity", "Choose three weekly priorities and protect time for them")
    b = item("b", "Potluck Pal", "Food", "Coordinate which guest brings which dish to a shared meal")
    c = item("c", "Trio", "Productivity", "Choose three weekly priorities and protect calendar time for them")
    assert portfolio_distinct.problems(b, [a]) == []
    assert portfolio_distinct.problems(c, [a, b])
    assert portfolio_distinct.problems(item("d", "weekthree", "Health", "Track water"), [a])


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


def test_ads_plan_respects_spend_already_recorded():
    assert ads_paused.check_plan(plan(), with_ads_cap(100), 50)


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


# ---------- decide ----------

def one(item):
    (d,) = decide.decide({"items": [item]}, BUDGET)
    return d


def t1(i, views, clicks=20, ended=True):
    return {"id": i, "stage": "demand_t1", "batch": "b1", "tranche_ended": ended, "spend_usd": 30,
            "impressions": 1000, "link_clicks": clicks, "landing_page_views": views}


def test_t1_keeps_top_third_with_enough_ctr():
    items = [t1("a", 60), t1("b", 50), t1("c", 40, clicks=5), t1("d", 30), t1("e", 20), t1("f", 0)]
    got = {d["id"]: d["to"] for d in decide.decide({"items": items}, BUDGET)}
    assert got == {"a": "demand_t2", "b": "demand_t2", "c": "killed", "d": "killed", "e": "killed", "f": "killed"}


def test_t1_waits_for_the_whole_batch():
    got = decide.decide({"items": [t1("a", 60), t1("b", 50, ended=False)]}, BUDGET)
    assert all(d["action"] == "insufficient data" and d["to"] is None for d in got)


def t2(visitors, signups, spend=200, top_ups=0, ended=True):
    return {"id": "x", "stage": "demand_t2", "tranche_ended": ended, "visitors": visitors,
            "committed_signups": signups, "spend_usd": spend, "top_ups_used": top_ups}


@pytest.mark.parametrize("item,action,to", [
    (t2(330, 8), "advance", "demand_validated"),          # 2.4%, $25 a signup
    (t2(330, 3), "kill", "killed"),                       # 0.9%
    (t2(330, 5), "top_up", "demand_t2"),                  # 1.5%, first time
    (t2(500, 8, spend=300, top_ups=1), "kill", "killed"), # 1.6% after the top-up
    (t2(300, 6, spend=200), "kill", "killed"),            # 2.0% but $33 a signup
    (t2(120, 6), "top_up", "demand_t2"),                  # too few visitors
    (t2(330, 8, ended=False), "insufficient data", None),
])
def test_t2_rules(item, action, to):
    d = one(item)
    assert (d["action"], d["to"]) == (action, to)


def test_threshold_is_not_rounded_up():
    assert one(t2(1000, 19, spend=100, top_ups=1))["action"] == "kill"     # 1.9% is not 2%


def test_missing_numbers_move_nothing():
    d = one({"id": "x", "stage": "demand_t2", "tranche_ended": True, "visitors": 330})
    assert d["action"] == "insufficient data" and d["to"] is None


def test_validated_idea_goes_stale():
    assert one({"id": "x", "stage": "demand_validated", "days_since_validated": 46})["to"] == "killed"
    assert decide.decide({"items": [{"id": "x", "stage": "demand_validated", "days_since_validated": 45}]}, BUDGET) == []


def p1(spend, trials, ended):
    return {"id": "x", "stage": "paid_t1", "tranche_ended": ended, "spend_usd": spend, "trials": trials}


@pytest.mark.parametrize("item,action,packet", [
    (p1(150, 0, False), "sunset", "A-SUN-1"),      # zero trials at $150, stop early
    (p1(100, 0, False), "insufficient data", None),
    (p1(300, 4, True), "sunset", "A-SUN-1"),       # $75 a trial
    (p1(300, 10, True), "advance", None),          # $30 a trial
])
def test_paid_t1_rules(item, action, packet):
    d = one(item)
    assert (d["action"], d["packet"]) == (action, packet)


def p2(matured, payers, revenue, spend=600, refunds=2, ended=True, **extra):
    return {"id": "x", "stage": "paid_t2", "tranche_ended": ended, "spend_usd": spend, "matured_trials": matured,
            "payers": payers, "d7_revenue_usd": revenue, "refund_rate_pct": refunds, **extra}


@pytest.mark.parametrize("item,action,packet", [
    (p2(30, 10, 380), "winner", "A-WIN-1"),                 # $60 a payer, 63% return, 10 payers
    (p2(30, 10, 380, refunds=12), "sunset", "A-SUN-1"),     # refunds too high for a winner
    (p2(30, 8, 380), "sunset", "A-SUN-1"),                  # passes kills, not a winner
    (p2(30, 4, 380), "sunset", "A-SUN-1"),                  # 13% trial to paid
    (p2(30, 10, 100), "sunset", "A-SUN-1"),                 # 17% return
    (p2(6, 3, 200), "insufficient data", None),             # trials not matured yet
    (p2(6, 3, 200, all_trials_matured=True), "sunset", "A-SUN-1"),
])
def test_paid_t2_rules(item, action, packet):
    d = one(item)
    assert (d["action"], d["packet"]) == (action, packet)


def test_winner_hold():
    w = {"id": "x", "stage": "winner", "refund_rate_pct": 3}
    assert decide.decide({"items": [dict(w, weekly_d7_roas_pct=[70, 35, 55])]}, BUDGET) == []
    assert one(dict(w, weekly_d7_roas_pct=[70, 35, 30]))["packet"] == "A-SUN-1"
    assert one(dict(w, weekly_d7_roas_pct=[70], refund_rate_pct=11))["packet"] == "A-SUN-1"


def test_the_paid_test_budget_can_actually_produce_a_winner():
    """Guards against a winner rule that the two tranches could never satisfy."""
    total = BUDGET["ads"]["paid_t1"]["lifetime_budget_usd"] + BUDGET["ads"]["paid_t2"]["lifetime_budget_usd"]
    assert total / BUDGET["winner"]["max_cost_per_payer_usd"] >= BUDGET["winner"]["min_payers"]
