# Factory A: Consumer Apps with Short-Form Distribution

Status: blueprint. Nothing here has been built or run. Date: 16 November 2026.
Fits `ARCHITECTURE.md` and `factories/_shared/CONVENTIONS.md`. Numbers marked "proposed" are operator-tunable defaults, not sourced benchmarks.

## 1. Purpose and honest evidence

Find a small number of differentiated subscription app ideas, prove demand before building, ship at most one new app per quarter, and feed it with honest short-form content that the operator publishes.

- No verified case exists of a solo developer running a Claude Code-built app portfolio at meaningful revenue. Every revenue figure found was self-reported or came from an aggregator blog.
- The only neutral dataset (RevenueCat, 115,000+ apps) puts the median subscription app at about $72 a month one year after launch. 17.3% reach $1K a month within two years and 4.6% reach $10K. Both figures fell from the prior year.
- The best-documented automated TikTok pipeline that could be read reported 100+ downloads and no revenue. Views to revenue is the unproven link.
- Apple's guideline 4.3(b) (wording verified on developer.apple.com, 2026-11-16; the 8 June 2026 change touched both 4.3(a) and 4.3(b)) rejects apps "indistinguishable from what's already widely available", says repeated low-effort submissions may lead to removal from the Developer Program, and says Apple may remove apps that do not attract customers. 4.3(a) forbids multiple Bundle IDs of the same app. No Apple rule names AI-built apps (secondary sources). One operator, Viktor Seraleev, lost a 6-app account at a self-reported $33,680 MRR in September 2023 when Apple linked it to an older terminated account of his (his own account, sequence corroborated by Communications Daily and PocketGamer.biz).
- Consequence: the developer account is the scarcest asset, the default outcome of an idea is "killed before build", and volume is capped by design.

## 2. State machine

One run does one stage on a batch of 1 to 3 items. All memory is in files under `state/`.

### 2.1 Stages

| # | Skill | Input | Process | Tools | Deterministic check (outside the model) | Output artifact | Runs as | Scheduler and cadence |
|---|---|---|---|---|---|---|---|---|
| 1 | `gap-mining` | Seed categories in `data/seeds.yaml`, exclusion list in `data/excluded_categories.yaml` | Scout mines store reviews, ASO keyword data and trend signals for unmet jobs in existing apps | Parallel Search or Firecrawl connector, WebFetch. Store review feeds and ASO tools as confirmed at build time | `checks/gap_schema`: scout file validates against schema, every complaint has a fetched source URL, category not on the exclusion list, at least 15 sourced complaints across at least 3 competitor apps | `state/scout/<id>.json`, item at `discovered` | `market-scout` agent | Cloud scheduled task, weekly. Skips when 5 or more items sit in `discovered` or `specced` |
| 2 | `spec-differentiation` | Item at `discovered` and its scout file | Builder writes a one-page spec with a differentiation statement. Verifier scores it | Repo only | `checks/spec_gate`: required fields present, at least 5 named competitors with store URLs from the scout file, differentiator maps to at least 3 sourced complaints from at least 3 competitors, core job not shared with any earlier item, word count under 600 | `state/specs/<id>.md`, item at `specced` | `app-builder` writes, `release-verifier` checks | Cloud scheduled task, weekly, day after stage 1 |
| 3 | `demand-test` | Item at `specced` | Builds a waitlist landing page and 6 concept posts as files. Operator deploys and publishes after approval | Repo, PostHog connector, Supabase connector, `content-drafts` skill in concept mode, Postiz for drafts | `checks/demand_assets`: page builds, PostHog snippet present, privacy notice link present, copy lint passes (section 2.3), every post marked `concept: true` | `demand/<id>/` site and post manifest, packet `A-DEM-1`, item at `demand_test_ready` then `awaiting_human` | `app-builder`, `draft-publisher` | Cloud scheduled task, on demand, checked weekly |
| 4 | `mvp-build` | Item at `demand_validated`, a free submission slot this quarter | Builds the MVP on branch `app/<id>`: Expo and React Native, Supabase, RevenueCat, hard paywall with trial | Expo and EAS cloud builds, Supabase, RevenueCat official MCP (sandbox project), git, GitHub Actions. The Expo, EAS and Supabase CLIs are not on the operator's Mac (verified 2026-11-16) and are installed in the cloud or CI environment | CI on the branch: typecheck, lint, unit tests, a scripted purchase flow against the RevenueCat sandbox, `checks/overlap` (feature code overlap with any earlier app under the cap in `budget.yaml`) | App source in `apps/<id>/`, CI run URL, item at `release_candidate` | `app-builder` | Cloud scheduled task, on demand. The operator's Mac has no Xcode and is work-managed (verified 2026-11-16), so iOS builds go through EAS cloud builds. CI on GitHub Actions per push |
| 5 | `release-readiness` | Item at `release_candidate` | Verifier runs the App Review checklist and assembles the submission packet. Operator submits | Repo, simulator run in CI on a macOS runner (proposed; no local Xcode), CI results, read-only fetch of the public listing after release | `checks/review_checklist`: every checklist row has evidence (file path, screenshot hash or test id). `checks/quota`: submissions this quarter under the cap. After submission, the public store URL returns the listing | `state/release/<id>/checklist.json`, packet `A-SUB-1`, item at `awaiting_human`, then `submitted`, then `live` or `rejected` | `release-verifier` | Cloud scheduled task, on demand. Listing check daily in stage 7 |
| 6 | `content-drafts` | Item at `live` or `winner` (or concept mode from stage 3) | Renders slideshows and screen-recording demos from real screenshots, then schedules them as drafts | Screenshots from the CI build, HyperFrames or HeyGen, ffmpeg, ElevenLabs API, Postiz (drafts only) | `checks/content_lint`: claims allowlist, no testimonial patterns, every frame traces to a screenshot hash from the shipped build, at most 5 hashtags, AI-label flag set where required. Postiz read-back shows each post as a draft | `content/<id>/<batch>/manifest.json`, Postiz draft ids | `app-builder` renders, `draft-publisher` schedules | Desktop scheduled task, weekly per live app. This is the only stage that runs locally, because the HeyGen CLI and HyperFrames skills are on the operator's Mac |
| 7 | `telemetry-winner-detection` | Items at `demand_testing`, `submitted`, `live`, `winner` | Pulls metrics, appends revenue to the ledger, applies kill and winner rules | RevenueCat official MCP (read), PostHog connector, App Store Connect reports (API verified, no official Apple MCP, see section 6), Supabase connector | `checks/decide`: a script, not the model, compares metrics to the thresholds in `budget.yaml` and emits the transition. Revenue lines carry a store or RevenueCat reference | `state/metrics/<date>.json`, ledger lines, transitions | Stage session, no sub-agent | Cloud scheduled task, daily |
| 8 | `weekly-review` | Week of journal, ledger, metrics, rejected packets | Produces at most 3 proposals as pull requests, and promotes lessons | Repo, GitHub connector | PR touches only `skills/`, `agents/`, `checks/` thresholds docs or `data/`. CI denies changes to protected paths | `journal/reviews/<week>.md`, up to 3 PRs, `journal/LESSONS.md` entries | Stage session on Opus | Cloud scheduled task, weekly |

Coverage of the required chain: Input (1, 2), Process (3, 4), QA or backtest (deterministic checks in every row, 5 as the main gate), Output (5, 6), Telemetry (7), Self-improvement (8).

### 2.2 Allowed transitions

```
(new)               -> discovered
discovered          -> specced | killed
specced             -> demand_test_ready | killed
demand_test_ready   -> awaiting_human            [A-DEM-1]
awaiting_human      -> demand_testing            [A-DEM-1 approved and operator has published]
demand_testing      -> demand_validated | killed
demand_validated    -> building | killed         [building only if a submission slot is free; killed if stale after 60 days]
building            -> release_candidate | awaiting_human [A-BLD-1] | killed
release_candidate   -> awaiting_human            [A-SUB-1]
awaiting_human      -> submitted                 [A-SUB-1 approved and operator records the submission id]
submitted           -> live | rejected
rejected            -> awaiting_human            [A-REJ-1]
awaiting_human      -> release_candidate | killed [A-REJ-1 outcome]
live                -> winner | awaiting_human [A-SUN-1] | killed
winner              -> awaiting_human            [A-WIN-1, A-SUN-1]
awaiting_human      -> <stage named in the packet> | killed | parked
parked              -> killed                    [after 30 days] | <stage named in a new approved packet>
any stage           -> awaiting_human            [any trigger in ESCALATION.md]
any non-live stage  -> killed
killed              -> (terminal)
```

A live app is never moved to `killed` without `A-SUN-1`, because paying subscribers and the store listing are involved. `killed` for a live app means the factory stops all work on it. Whether it stays on sale is the operator's decision in the packet.

### 2.3 Copy lint (used by stages 3 and 6)

A script, built at build time, that fails any caption, overlay or page copy containing: first-person customer statements, the phrases "users say", "customers love" or similar, star ratings or review counts, numeric outcome claims not in the item's `claims.yaml`, or screenshots of an app that does not exist presented as shipping. Concept content must carry the words "in development" or "join the waitlist".

## 3. Kill criteria and validation budget

Thresholds live in `budget.yaml`. All are proposed defaults anchored where possible on RevenueCat figures.

| Stage | Kill when |
|---|---|
| Gap mining | Category is on the exclusion list (dating, flashlight, sound effect, wallpaper, simple timer, fortune telling, drinking game, fart and burp, and similar). Fewer than 15 sourced complaints across 3 competitors. Item spend over $2 |
| Spec | Fails `checks/spec_gate` twice. Differentiator is a visual or pricing change only. Item spend over $3 |
| Demand test | 14 days after the operator's first publish: fewer than 30 waitlist signups, or fewer than 200 unique visitors with at least 6 posts published (no reach), or visitor to signup under 8% with 200 or more visitors. No extension. Item spend over $15 |
| Validated but idle | No free submission slot within 60 days of validation. The signal is stale |
| Build | 21 days in `building`, or item token spend over the build cap. First overrun raises `A-BLD-1`. Second kills |
| Review | Second rejection of the same app, or any rejection citing 4.3 or spam. This also freezes all submissions (`A-ACCT-1`) |
| Live, day 14 | Fewer than 100 first-time downloads with at least 10 posts published |
| Live, day 35 | Download to paid under 2% with 200 or more downloads. Reference: 10.7% by day 35 for hard paywalls in the RevenueCat data |
| Live, day 60 | MRR under $100. Reference: survivors reach $1K in a median of 58 days |
| Live, day 90 | MRR under $300 and month-on-month growth under 20% |

Live kills go through `A-SUN-1`. All others are immediate and need no approval.

Factory validation budget (proposed): **$900 total recorded spend or 180 days from the first scheduled run, whichever comes first**. If no verified revenue line exists at that point, the factory raises `BUD-2` and pauses every stage except telemetry for a keep-or-kill decision. This budget tests whether the funnel can produce one demand-validated app with first verified dollars. It does not test profitability, and at the base rates above, profitability should not be expected inside it.

## 4. Telemetry and the definition of a winner

Sources of truth:

- **Revenue for the ledger:** App Store Connect proceeds and payment reports (net of commission). RevenueCat is used when the store figure is not yet available, recorded as gross with `net_of_fees: false`.
- **Subscription behaviour:** RevenueCat (trials started, trial to paid, MRR, churn, refunds), through the official RevenueCat MCP at `https://mcp.revenuecat.ai/mcp`.
- **Downloads and store conversion:** App Store Connect analytics.
- **Demand test and in-app funnels:** PostHog. Waitlist rows in Supabase.
- **Content reach:** read by the operator from TikTok or from Postiz analytics if available (unverified). Views are never a success metric on their own.

Never a source: the agent's own summary, third-party estimators such as Sensor Tower (reported to undercount by about half), or view counts.

Winner (all must hold, proposed): MRR of $1,000 or more in RevenueCat within 90 days of `live`, matching proceeds visible in App Store Connect, refund rate under 10% of transactions, and no open review or account warning. Early winner signal that raises `A-WIN-1` sooner: day 35 download to paid of 8% or more with 300 or more downloads.

Factory-level metrics tracked weekly: ideas killed per stage and cost per kill, cost per demand-validated idea, submissions used against the quarterly cap, rejections, verified revenue minus recorded spend.

## 5. Self-improvement loop

The weekly review reads: run reports, `permission_denials`, ledger totals by stage, the funnel counts, kill reasons, rejected escalation packets and their one-line reasons, App Review feedback text recorded by the operator, and per-post reach figures the operator recorded.

It may propose (at most 3, one change per skill per week, each as a PR with observation, hypothesis, single change, judging metric and review date):

- Seed categories and scoring weights in `data/seeds.yaml`.
- Wording and steps in a skill or agent prompt.
- New rows in the App Review checklist drawn from actual rejection text.
- Content hook and format templates, judged by signups or downloads per published post, never by views alone.
- Additions to the exclusion list. Removals are an escalation.

It may not touch `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, thresholds in `checks/`, hooks, settings or the run wrapper. A wish to change those is raised as `GEN-1`.

## 6. Tools and accounts

| Tool or account | Role | Status |
|---|---|---|
| Claude Code cloud and Desktop scheduled tasks | Schedulers | Already available |
| GitHub and GitHub Actions | Source control, CI, approval by commit | Connector available. A repository must be created |
| Slack, Linear | Notifications, escalation queue | Already available |
| PostHog | Landing page and in-app analytics | Already available |
| ffmpeg | Video assembly | Already available |
| HyperFrames and HeyGen | Programmatic motion graphics | Verified 2026-11-16: HeyGen CLI v0.8.1 with credentials and the HyperFrames skill suite are on the operator's Mac. The `hyperframes` CLI is not on PATH, so use `npx hyperframes`. HyperFrames is Apache 2.0 with no render fees. HeyGen API use is pay-as-you-go from a $5 top-up, in a wallet separate from plan credits. A HyperFrames connector is listed in the directory but not installed |
| Supabase | App backend, waitlist table | Connector is in the directory but not installed. The CLI is not on the operator's Mac (verified 2026-11-16). Free: 2 active projects, paused after 1 week of inactivity. Pro from $25 a month (verified 2026-11-16). Official MCP supports `read_only=true` |
| Parallel Search, Firecrawl | Scout research | Connectors are in the directory but not installed (verified 2026-11-16). Firecrawl free tier is 1,000 credits a month (verified). The free Parallel MCP rate-limits after roughly 8 to 10 quick calls |
| RevenueCat | Subscriptions, paywall, revenue signal | New account needed. Official MCP verified. Not found in the Claude connector directory search, so cloud runs need it declared in a committed `.mcp.json`. Pricing verified 2026-11-16: free up to $2,500 monthly tracked revenue, then 1%. The MCP can now change product prices and availability in App Store Connect and Google Play, so no agent key may carry those permissions. Whether a read-only API key exists is unverified |
| Expo and EAS | Build toolchain | New account needed. Official Expo MCP verified 2026-11-16: hosted at `mcp.expo.dev/mcp` (OAuth), on the Free plan since May 2026 with fair-use limits. Community servers with similar names exist and must not be used. EAS Free: 15 iOS builds a month in a low-priority queue. Starter $19 a month plus usage (verified 2026-11-16). No Xcode on the operator's Mac, so EAS cloud builds are required |
| Apple Developer Program | Store account | New account needed unless the operator holds one. Operator's legal identity, banking and tax forms. Fee US$99 a year. Commission 30%, or 15% in the Small Business Program, which needs enrolment (verified 2026-11-16) |
| App Store Connect data | Downloads and proceeds | No official Apple MCP exists (verified 2026-11-16, secondary: OpenASO), so none is used. The App Store Connect API serves sales and finance reports (`GET /v1/salesReports`, `GET /v1/financeReports`) with a Team key holding the Sales and Reports or Finance role (verified 2026-11-16, official). Default stays an operator export into `state/metrics/inbox/` until the operator issues such a key |
| Google Play | Second platform | Disabled by default. Verified 2026-11-16: US$25 one-time fee, new personal accounts need a closed test with 12 testers for 14 continuous days, and the Repetitive Content policy bars multiple apps with highly similar functionality |
| Postiz | Scheduling as drafts | New account needed. $29 a month Standard with API, MCP and CLI (verified). For TikTok, `content_posting_method: UPLOAD` sends the post to the TikTok inbox as a draft that the owner publishes within 24 hours. `DIRECT_POST` publishes and is never used (verified 2026-11-16, Postiz docs) |
| ElevenLabs API | Voiceover | New account needed. Starter $6 a month, $0.04 to $0.08 per 1,000 characters (verified) |
| TikTok account | Distribution | Operator creates and warms it by hand. Verified 2026-11-16 on TikTok's developer pages: unaudited API clients can post only privately (`SELF_ONLY`) for up to 5 users per 24 hours, TikTok names a tool that uploads to your own accounts as not acceptable, and each creator account is limited to about 15 API posts a day. Realistic AI people or scenes must be labelled |
| ASO keyword tool (Astro, AppFigures or similar) | Keyword gap data | New account needed, optional. Astro: $9 a month billed annually, App Store only. Appfigures: free Starter plan, Connect $9.99 a month, official MCP at `mcp.appfigures.com/mcp` (verified 2026-11-16) |
| Apple public review feed and search API | Review mining | Unverified recollection that these are free and unauthenticated. Confirm at build time |
| Cloudflare Pages or similar | Landing page hosting | New account needed. Cloudflare Pages free tier: 500 builds a month, no commercial-use restriction found (verified 2026-11-16). Vercel Hobby is not an alternative because it is non-commercial only |
| Image generation APIs | Not in the default stack | Unverified. Real screenshots are preferred |

## 7. Known failure modes and design responses

| Failure mode from the research | Design response |
|---|---|
| Account termination takes every app and unpaid proceeds | Quarterly submission cap, differentiation gate, overlap check, every submission an escalation, freeze on any 4.3 rejection |
| Templated near-identical apps are the exact pattern 4.3(b) targets | Shared scaffold is limited to auth, paywall and settings. Feature code overlap is capped and checked in CI. Excluded categories are killed at stage 1 |
| Harsh base rates and worsening odds | Demand test precedes any build. Numeric kills at days 14, 35, 60 and 90. Validation budget with a hard pause |
| Views do not convert to revenue | Winner rules use RevenueCat and store data only. Content is judged on signups and downloads per post |
| Hard paywall on a thin app attracts review scrutiny | Onboarding must demonstrate the core job before the paywall. Checklist row requires it. Longer trials convert better in the data, so trial length is a spec decision, default 7 days (proposed) |
| Fake testimonials breach 16 CFR Part 465, up to $53,088 per violation | Copy lint, no AI "customers", brand-voice product claims only, claims allowlist per app |
| Undisclosed realistic AI content leads to labels, removal, strikes | Realistic AI people and scenes are disabled in `budget.yaml`. Real screenshots are the default. AI-label flag in every manifest |
| Unaudited TikTok API clients can post only privately (verified 2026-11-16). Direct API posting and unwarmed accounts are also reported to suppress reach (vendor claim) | Drafts only. Operator warms the account, picks audio and publishes |
| Phone automation over ADB is a grey-area workaround | Not used. Listed under "never" |
| Community App Store Connect MCP servers are a supply-chain and credential risk | Not used. The agent holds no store write credential |
| Agents report success that did not happen | Every stage has a script-level check and an outcome check, such as reading back the Postiz draft state or fetching the public listing |
| Scout reads untrusted reviews and web pages | Scout has no connectors with write access and no credentials. Builders read only the validated scout file |
| Operator burnout from running many apps | Hard cap on live apps in `budget.yaml`. Sunset escalation for under-performers |
