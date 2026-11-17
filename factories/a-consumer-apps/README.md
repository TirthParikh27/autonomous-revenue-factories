# Consumer app and web product factory: how to run it

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
| Demand test | Writes landing pages, demo video ads, a batch preview and the ad plan. `publish.py ads` runs dry: it writes `readback.json` and contacts nobody |
| Build | Writes the app or web product and its tests. Store builds need an Expo token. Web payments need a Stripe test key |
| Content | Writes drafts. `publish.py drafts` runs dry and writes `drafts.json` |
| Telemetry, paid test | Need real numbers, so they wait for accounts |

## Network

Idea mining reads Apple's search and review feeds, so the machine running it must be able to reach `itunes.apple.com` and `apps.apple.com`. The scout can also read verified revenue from TrustMRR (`trustmrr.com`), declared in `.mcp.json`. It works without an account. To unlock filtering, store a free API key as a network secret on the environment (host `trustmrr.com`, header `Authorization`, value `Bearer <key>`), never in the repo.

## Set up once, then say go

The factory prepares everything and never spends or launches by itself. Your part is connecting accounts once, then approving each batch.

Once:

1. Tools on the machine that runs stages: Node 20 or later, then at the repo root `npm install playwright` and `npx playwright install chromium`. Demo videos render with `npx hyperframes`, which downloads itself.
2. A Meta ad account with an account spending limit. Raise `monthly_caps_usd.ads` in `budget.yaml` from 0.
3. A Cloudflare Pages project that serves the `demand/` folder, and a Supabase table for the early-access list.
4. Fill in `demand/config.js` (pixel id, sign-up endpoint and its publishable key, event endpoint). Every test page reads this one file.
5. Later, when something ships: Apple developer account, Stripe, Postiz.

Each batch:

1. Open `demand/batches/<batch>/preview.html`. It shows every idea's videos, page screenshots, price and the critic's and reviewer's verdicts.
2. If you like it, approve by moving the `A-AD-1` packet from `escalations/open/` to `escalations/approved/` in a commit, and merge the batch pull request. CI deploys the pages.
3. Run the `demand-test` stage again. It creates the campaigns paused.
4. Activate them in Ads Manager and record the date. Telemetry takes it from there.

You submit store builds, publish posts and switch web payments to live yourself. Live mode for `publish.py` is added when the Meta account exists; until then it runs dry.

## Optional integrations

The factory works without these. Each one makes its evidence stronger. Both are paid, so the factory uses them only when you connect them.

| Tool | What it adds | Cost |
|---|---|---|
| GetAppNiche | Estimated revenue and downloads for competing apps, so the scout can tell a market that pays from one that only complains. Estimates are rough bands | $39 a month |
| PickFu | A poll of real people in the target audience on an idea's ad hooks before ad money is spent. Can kill an idea or pick the lead hook; never passes one | Pay as you go, about $1 a response |

To connect one:

1. Create the account and an API key.
2. Store the key as a network secret on the environment, never in the repo. GetAppNiche: host `api.getappniche.com`, header `Authorization`, value `Bearer <key>`. PickFu: host `mcp.pickfu.com`, same header.
3. Add the server to `.mcp.json`:

```
"getappniche": {"type": "http", "url": "https://api.getappniche.com/mcp"},
"pickfu": {"type": "http", "url": "https://mcp.pickfu.com/mcp"}
```

4. GetAppNiche's read tools are already on the allow list in `.claude/settings.json`. For PickFu, add its tool names there after you have looked at what the server offers, because creating a poll spends money.

Research behind these picks (2026-11-17): they are the cheapest options an agent can call directly. The larger names (Sensor Tower, Appfigures estimates, UserTesting) cost far more, and the free tiers elsewhere have no API.

## Known limit

Mining web categories directly is weak: search results give complaints without dates and review sites are not reachable, so the first test run kept none. Web products still appear, because the spec stage picks the platform for jobs found in app reviews.

## Not built yet, on purpose

These are in the architecture and wait until they are needed:

- Schedules. Every stage is run by hand first.
- The daily Slack digest. Runs write to `outbox/pending.jsonl`; nothing sends it yet.
- Tool hooks on ad and Postiz calls. They matter once live mode exists.
- Branch protection on `main` and a `factory-state` branch rule. These are GitHub settings only you can change.
