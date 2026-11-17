# Consumer app factory: how to run it

The factory is built end to end and needs no accounts to try. Each run does one stage and writes a report in `journal/`.

## Run a stage by hand

From the repo root, with Claude Code installed and `pip install -r requirements-dev.txt` done:

```
python3 tools/factory_run.py --factory a-consumer-apps --stage gap-mining
```

Stages, in order: `gap-mining`, `synthetic-screen`, `spec-differentiation`, `demand-test`, `mvp-build`, `release-readiness`, `paid-test`, `content-drafts`, `telemetry-winner-detection`, `weekly-review`. Run each by hand three times before scheduling it.

The wrapper refuses to start if a `STOP` file exists or the month's budget in `budget.yaml` is used up. It fails the run if the report has no evidence. Three failures in a row write `STOP`.

## What works without accounts

| Stage | Without accounts |
|---|---|
| Idea mining, screen, spec | Fully. Costs tokens only |
| Demand test | Writes landing pages, ads and the ad plan. `publish.py ads` runs dry: it writes `readback.json` and contacts nobody |
| Build | Writes the app and its tests. Store builds need an Expo token |
| Content | Writes drafts. `publish.py drafts` runs dry and writes `drafts.json` |
| Telemetry, paid test | Need real numbers, so they wait for accounts |

## To go live later

1. Approvals: the factory writes a packet to `escalations/open/`. You approve by moving it to `escalations/approved/` in a commit.
2. Ads: a Meta ad account with an account spending limit, then raise `monthly_caps_usd.ads` in `budget.yaml` from 0. Campaigns are always created paused. You activate them.
3. Content: a Postiz account. Posts are always drafts. You publish them.
4. Store: an Apple developer account. You submit every build yourself.

Live mode for `publish.py` is added when the first two exist.
