# Factory A: Consumer App and Web Product Portfolio

Status: blueprint, revision 2. Nothing here has been built or run. Date: 16 November 2026.
Fits `ARCHITECTURE.md` and `factories/_shared/CONVENTIONS.md`. Numbers marked "proposed" are operator-tunable defaults, not sourced benchmarks. Numbers marked (E) are estimates.

Revision 2 replaces the first design, which capped the factory at one new app a quarter. The operator's goal is a portfolio: many cheap shots, so that one profitable app becomes likely. This revision keeps the account protections and moves the volume to where volume is safe.

Revision 3 (17 November 2026, operator decision): the factory builds web products as well as iOS apps. Each idea picks one platform at the spec stage. The planned Factory G (micro-SaaS and browser extensions) is folded into this one. Section 1a describes what differs for web.

## 1. Purpose and honest evidence

Test a large number of app ideas cheaply with real paid traffic, build only the survivors, release them at a pace the store accounts can bear, and put more money only behind an app whose paid funnel has shown it can pay back.

**The rule that shapes everything: volume happens before the store, never in it.** A hundred ideas can be tested on landing pages in a quarter. Only the few that pass are built and submitted.

- No verified case exists of a solo developer running a Claude Code-built app portfolio at meaningful revenue. Every revenue figure found was self-reported or came from an aggregator blog.
- Base rates per shipped app (RevenueCat, 115,000+ apps): median about $72 a month one year after launch. 17.3% reach $1K a month within two years and 4.6% reach $10K. Both fell from the prior year. That dataset includes funded teams, so a solo portfolio should not assume it does better.
- Paid funnel benchmarks (Adapty, Meta ads for about 5,000 subscription apps, Q3 2026): cost per trial about $20, cost per paying subscriber $43 to $82 depending on the optimisation event, day-7 return on ad spend 34% to 75%. The median paid cohort has not paid back after a week.
- Store rules (wording verified on developer.apple.com, 16 November 2026): guideline 4.3(a) forbids multiple Bundle IDs of the same app. 4.3(b) rejects apps "indistinguishable from what's already widely available" and says repeated low-effort submissions may lead to removal from the Developer Program. Google Play's Repetitive Content policy bars multiple apps with highly similar functionality, and a Play termination removes every app and extends to related and future accounts (linked by payment details, device, address and network, per a secondary guide).
- How enforcement reads volume: in an Apple developer forum case (August 2026), twelve updates submitted within 90 minutes from one API key were all rejected under 4.3(a), with release notes 46% similar. In June 2026 a developer who mass-created AI prototype apps received a Pending Termination Notice under DPLA 3.2(f), reversed on appeal after about six weeks (self-reported). Apple's 2025 transparency report lists 418 app removals citing 4.3 Spam and 90,608 citing 3.2(f) Fraud. Viktor Seraleev lost a 6-app account at a self-reported $33,680 MRR when Apple linked it to an older terminated account.
- Consequence: cadence and similarity are what the stores see. The factory controls both with deterministic gates, and never opens a second account to get around a limit.

## 1a. Two platforms, one pipeline

Mining, the screen, the spec gate, the demand test and telemetry are the same for both. The platform is chosen in the spec and stored on the item as `platform: ios` or `platform: web`.

| | iOS app | Web product |
|---|---|---|
| Choose it when | The job needs the phone: camera, microphone, notifications, offline use, something done on the move | The job is done at a desk or in a browser, buyers look for it by searching the web, or a small business pays for it |
| Stack | Expo, Supabase, RevenueCat | TypeScript web app on Cloudflare Pages, Supabase, Stripe Checkout and customer portal |
| Release | Operator submits to the store. Cadence limits in section 4 apply | Operator merges the launch pull request and switches Stripe to live. No store review and no cadence limit |
| Payments | Apple in-app purchase, 15% to 30% commission | Stripe, about 3% fees. The agent holds test-mode keys only |
| Traffic | Meta ads to the store listing | Meta ads to the site, plus a few honest search pages for the terms named in the spec |
| Main risk | Losing the developer account | Building things nobody finds. Stripe account restrictions for misleading billing |
| Revenue source of truth | App Store Connect proceeds | Stripe balance transactions, net of fees and refunds |

A web build is cheaper and faster to ship, so more validated ideas can be built in a year than the 8 to 12 one Apple account allows. The demand test is still the gate: cheap to build is not a reason to skip it. A browser extension adds a store account (Chrome Web Store), so it is allowed only as a companion to a web product and only through `ACC-1`. The distinctness rules (no reskins, no shared core job) apply to web products too, because near-copies split the same demand.

Base rates for web are weaker evidence than for apps: an analysis of TrustMRR data put median verified MRR near $136 with a top decile above $30K, and that set is self-selected (see `RESEARCH_REPORT.md`).

## 2. Portfolio economics (all proposed or estimated)

One cycle is 100 mined ideas. Costs are ad spend plus tokens.

| Step | Ideas in | Ideas out | Cost per idea in | Cycle cost | Reads in | Evidence quality |
|---|---|---|---|---|---|---|
| Gap mining and synthetic screen | 100 | 50 | about $3 tokens | $300 | Same day | Weak. Ranking only |
| Spec and distinctness review | 50 | 30 | about $2 tokens | $100 | Same day | Judgment |
| Demand test, tranche 1 (ad click test) | 30 | 10 | $30 ads | $900 | 3 days | Real behaviour, weak signal |
| Demand test, tranche 2 (fake door with price) | 10 | 4 | $170 more ads | $1,700 | 5 to 7 days | Real behaviour, medium signal |
| Build and release | 4 | 4 | about $100 tokens and build | $400 | 2 to 3 weeks | n/a |
| Paid test, tranche 1 | 4 | 2 to 3 | $300 ads | $1,200 | 3 to 4 days | Real trials |
| Paid test, tranche 2 | 2 to 3 | 0 to 2 | $300 more ads | $600 to $900 | 7 to 14 days | Real payers |
| **Cycle total** | | | | **about $5,200 to $5,500** | about 10 weeks | |

- **Cost per idea tested:** about $55 (E). **Cost per app shipped:** about $1,350 (E).
- **Operator time per cycle:** about 12 to 15 hours (E): two ad-batch approvals and activations, four store submissions, packet reviews.
- **Odds, if each shipped app performs like the average RevenueCat app and outcomes are independent:** the chance that at least one of N shipped apps reaches the threshold is 1 − (1 − p)^N.

| Apps shipped | At least one at $1K a month | At least one at $10K a month |
|---|---|---|
| 4 (one cycle) | 53% | 17% |
| 10 | 85% | 38% |
| 20 | 98% | 61% |
| 50 | about 100% | 90% |

Read this table with four cautions. The thresholds are revenue, not profit, and an app whose revenue is bought with ads can reach $1K a month at a loss. The two-year window is long. The independence assumption fails if one account ban takes every app. And nothing found shows that pre-testing raises the per-app hit rate, although it is the reason for the design.

**Capacity.** Ideas tested: 200 to 400 a year. Apps shipped on one Apple account: 8 to 12 a year under the cadence rules in section 4. A hundred shipped apps on one account in a year is not a safe target. A hundred tested ideas a quarter is.

## 3. State machine

One run does one stage on a batch. All memory is in files under `state/`.

### 3.1 Stages

| # | Skill | Input | Process | Hard check, or what the run judges | Output | Scheduler |
|---|---|---|---|---|---|---|
| 1 | `gap-mining` | Seed categories, exclusion list | Scout mines store reviews, complaints about web products, competitor prices and rating counts, verified revenue on TrustMRR, free substitutes, keyword popularity and trend signals for unmet jobs. Batch of up to 25 | Judged on the whole evidence file: the complaint is a common pattern, at least one competitor shows signs of earning, no free or built-in substitute does the job, category not excluded | `state/scout/<id>.json`, item at `discovered` | Cloud task, twice weekly |
| 2 | `synthetic-screen` | Items at `discovered` | An LLM ranker scores the batch several times with no personas. The run drops the weakest ideas by median rank | Judged. The screen can kill but never pass | `state/screen/<batch>.json`, items at `screened` or `killed` | Cloud task, after stage 1 |
| 3 | `spec-differentiation` | Items at `screened` | One-page spec with a platform choice (iOS or web), a differentiation statement and a proposed price. Verifier scores it, then the `idea-critic` agent reads the market itself and tries to break the idea | Judged: the critic's verdict is not `kill`, competitors and complaints come from the scout file, and core job, category and name are not shared with any earlier item at `specced` or later | `state/specs/<id>.md`, item at `specced` | Cloud task, weekly |
| 4 | `demand-test` | Items at `specced` | First shows the operator each idea's evidence on one page and raises `A-IDEA-1`. Only for ideas he approves: builds a landing page with a visible price and a no-payment commitment funnel (price tap, plan choice, email, one question), plus a character, three demo video ads and a still per idea (`skills/ad-creative`). Pages live under `demand/sites/`, the only folder deployed. `page_check.js` walks each page and the `creative-reviewer` agent looks at pages and ads as images. One `preview.html` shows the operator the whole batch. Pages deploy from CI when the operator merges the batch. Publisher creates paused campaigns. Operator activates the batch. Tranche 1 then tranche 2 | `checks/copy_lint` on page and ads. `checks/ads_paused`: every campaign read back as paused with the lifetime budget in `budget.yaml` | `demand/<id>/`, packets `A-IDEA-1` and `A-AD-1` per batch, items at `demand_t1`, `demand_t2`, `demand_validated` or `killed` | Cloud task, weekly batch |
| 5 | `mvp-build` | Item at `demand_validated`, a free build slot | Builds the MVP on branch `app/<id>`. iOS: Expo, Supabase, RevenueCat. Web: Cloudflare Pages, Supabase, Stripe in test mode. Paywall with trial | CI: typecheck, lint, tests, scripted sandbox or test-mode purchase, `checks/overlap` | `apps/<id>/`, item at `release_candidate` | Cloud task, on demand |
| 6 | `release-readiness` | Item at `release_candidate` | iOS: App Review checklist, similarity checks, cadence check, submission packet. Operator submits. Web: launch checklist and launch packet. Operator merges and switches Stripe to live | Checklist judged with evidence per row. iOS only: `checks/cadence`, `checks/metadata_similarity` | Packet `A-SUB-1`. iOS item at `submitted`, then `live` or `rejected`. Web item at `live` | Cloud task, on demand |
| 7 | `paid-test` | Item at `live` | Paused campaigns optimised for trial start (to the store listing for iOS, to the site for web). Operator activates. Tranche 1 then tranche 2 | `checks/ads_paused`. Telemetry judges spend, trials and payers | Packet `A-AD-2`, item at `paid_t1`, `paid_t2`, `winner` or sunset | Cloud task, on demand |
| 8 | `content-drafts` | Item at `winner` (organic content is for winners only) | Slideshows and demos from real screenshots, as drafts | `checks/copy_lint`, draft read-back | Postiz drafts | Desktop task, weekly per winner |
| 9 | `telemetry-winner-detection` | Items in any test or live stage | Pulls ad, analytics, store, RevenueCat and Stripe numbers. Makes kill, advance and winner calls | Judged, with the numbers in the run report | `state/metrics/<date>.json`, ledger lines, transitions | Cloud task, daily |
| 10 | `weekly-review` | Week of journal, ledger, metrics | At most 3 proposals as pull requests | Protected paths untouched | PRs, `journal/LESSONS.md` | Cloud task, weekly, switched on after four weeks of run reports |

### 3.2 Allowed transitions

```
(new)              -> discovered
discovered         -> screened | killed
screened           -> specced | killed
specced            -> awaiting_human            [A-IDEA-1, the operator's go on each idea before any page or ad is made]
awaiting_human     -> specced | killed          [A-IDEA-1 approved: ideas left in the packet return with idea_approved, ideas removed are killed]
specced            -> awaiting_human            [A-AD-1, one packet per batch of up to 15 approved ideas]
awaiting_human     -> demand_t1                 [A-AD-1 approved and operator has activated the batch]
demand_t1          -> demand_t2 | killed
demand_t2          -> demand_validated | killed
demand_validated   -> building | killed         [killed if stale]
building           -> release_candidate | awaiting_human [A-BLD-1] | killed
release_candidate  -> awaiting_human            [A-SUB-1; waits here if checks/cadence says not yet]
awaiting_human     -> submitted                 [iOS: A-SUB-1 approved and operator records the submission id]
awaiting_human     -> live                      [web: A-SUB-1 approved and operator records the launch in state/launches.jsonl]
submitted          -> live | rejected
rejected           -> awaiting_human            [A-REJ-1; A-ACCT-1 if the reason is 4.3, spam or fraud]
live               -> awaiting_human            [A-AD-2]
awaiting_human     -> paid_t1                   [A-AD-2 approved and operator has activated]
paid_t1            -> paid_t2 | awaiting_human [A-SUN-1]
paid_t2            -> winner | awaiting_human [A-SUN-1]
winner             -> awaiting_human            [A-WIN-1 for any scale budget]
awaiting_human     -> <stage named in the packet> | killed | parked
parked             -> killed                    [after 30 days]
any stage          -> awaiting_human            [any trigger in ESCALATION.md]
any non-live stage -> killed
killed             -> (terminal)
```

A live app or web product is never moved to `killed` without `A-SUN-1`, because subscribers are involved.

### 3.3 Copy lint (pages, ads, content)

A script that fails any ad, caption or page containing: first-person customer statements, "users say" or similar, star ratings or review counts, download counts, numeric outcome claims not in the item's `claims.yaml`, or a mock-up presented as a shipping app. Pre-build pages and ads must carry "in development" or "early access". A page that shows a price must also say that nothing is charged today.

## 4. Store account protection

This section applies to iOS items. Web products have no store account, and their equivalent asset is the Stripe account: honest billing, a visible cancel path and a refund policy are checklist rows in `skills/release-readiness`.

The developer account is the single point of failure for the iOS portfolio. Most of these rules are checked by scripts, not by the model.

| Risk | Rule | Check |
|---|---|---|
| Submission cadence reads as a farm | New-app submissions: 1 a month for the first three approvals, then 2 a month. At least 10 days between new-app submissions. At most 12 new apps in any rolling 12 months. Never two submissions of any kind on the same day (proposed. Apple publishes no number) | `checks/cadence` reads `state/submissions.jsonl` |
| Near-identical apps (4.3(a), Repetitive Content) | Each app has its own core job and category. Shared code is limited to auth, paywall and settings. Feature code overlap at most 30% | Spec review, `checks/overlap` |
| Templated listings | Name, subtitle, description, keywords, screenshots and release notes are written per app. Text similarity to any other listing on the account at most 30% (proposed. The forum case was rejected at 46%) | `checks/metadata_similarity` |
| Saturated categories (4.3(b)) | Exclusion list killed at stage 1 | Gap mining, against `data/excluded_categories.yaml` |
| Thin apps behind a paywall | Onboarding shows the core job working before the paywall | Checklist row with a test id |
| One rejection becomes a pattern | Any rejection or notice citing 4.3, spam, 3.2(f) or fraud freezes every submission until `A-ACCT-1` is approved | Wrapper refuses `release-readiness` |
| Dead apps pile up | An app that fails its paid test goes to `A-SUN-1`. The default recommendation is removal from sale, since 4.3(b) lets Apple remove apps that do not attract customers. At most 6 live apps (proposed) | `checks/cadence` |
| Batch automation fingerprints | The agent holds no store credential. The operator submits by hand from their own login | Credential absence |
| A ban tempts a second account | Never create, borrow or buy another developer account to continue after a limit, freeze or termination. An organisation account for a registered company is a legitimate operator decision through `ACC-1`, not a workaround | Listed under "never" |
| Google Play linkage | Play stays off by default. A new personal account needs 12 testers for 14 days first. If enabled, the same cadence and similarity rules apply, counted separately | `budget.yaml` |

A winning iOS app can also be offered on the web with Stripe billing, and a winning web product as an app. Either is an `A-WIN-1` option, not a default.

## 5. Kill criteria

The run makes kill, advance and winner calls with judgment and states its evidence. The figures here and in `budget.yaml` are proposed reference points, weighed against the niche, price point and sample size. They are not pass marks. Anything that spends money or cannot be undone still goes to the operator through its packet.

| Stage | Kill when |
|---|---|
| Gap mining | Excluded category. Too little recent, sourced complaint evidence to show the problem is real and common. No keyword popularity signal recorded |
| Synthetic screen | Clearly among the weakest of the batch by median rank (reference point: bottom half). The screen can kill. It can never pass an idea to a build |
| Spec | Still not distinct from earlier items or competitors after one revision. Differentiator is only visual or only price |
| Demand test, tranche 1 ($30, 3 days) | Clearly weak against the batch on cost per landing-page view or link click-through (reference points: top third of the batch, 1.0% click-through) |
| Demand test, tranche 2 (to $200 total, 7 days) | Too few visitors click the price and leave an email, or each signup costs too much for the price point. One top-up of $100 for a close call. Reference points: about 300 visitors, under 1% committing is a clear fail, 2% is a pass, $30 per committed signup (anchor: fake-door guides put the bar at 1% to 2%) |
| Validated but idle | No build slot for a long time (reference point: 45 days) |
| Build | Over the build cap, or stalled in `building` (reference point: 21 days). First overrun raises `A-BLD-1`. Second kills |
| Review | Second rejection of the same app. Any 4.3, spam or fraud citation also freezes the account |
| Paid test, tranche 1 ($300, 4 days) | No trials, or trials too costly for the price to pay back. Reference points: zero trials at $150, $60 per trial at $300 (anchor: Adapty median about $20, healthy $20 to $40) |
| Paid test, tranche 2 ($300 more, 14 days) | Too few trials convert, or payers cost too much to pay back. Reference points: 15% trial-to-paid over about 10 matured trials (anchor: 27.8%), $120 per payer (anchor: $43 to $82), 25% day-7 return on ad spend (anchor: 34% to 75%) |
| Winner hold | After `winner`: return or refunds stay clearly below what a winner needs (reference points: day-7 return under 40% two weeks running, refunds over 10%) |

Small numbers warning: 300 visitors and 6 signups can tell 0.5% from 3%. They cannot tell 2% from 3%. The reference points catch clear failures cheaply. They do not rank close calls.

**Winner:** payers cheap enough and early return strong enough that scale spend should pay back, with enough payers to trust it, low refunds and no open review or account warning. Reference points: $60 per payer, 60% day-7 return, 10 payers, refunds under 10%. A winner raises `A-WIN-1`, which asks for a scale budget in tranches. Scale spend is never automatic.

**Factory validation budget (proposed):** $6,000 total recorded spend or 150 days from the first scheduled run, whichever comes first. That is one full cycle. If no app has reached `winner`, the factory raises `BUD-2` and pauses everything except telemetry for a keep-or-kill decision.

## 6. Telemetry

- **Ad spend and ad results:** Meta Ads reporting through a read-only token. Spend goes to the ledger from the ad platform's own figure.
- **Landing pages:** PostHog events `page_view`, `price_click`, `plan_selected`, `committed_signup`, `question_answered`. Supabase row count as a cross-check.
- **Subscriptions:** RevenueCat for iOS, Stripe for web (trials, trial to paid, MRR, refunds).
- **Revenue for the ledger:** iOS: App Store Connect proceeds, net of commission. RevenueCat gross is used only until the store figure exists. Web: Stripe balance transactions, net of fees and refunds.
- Never a source: the agent's own summary, a synthetic panel, third-party download estimators, or view counts.

Factory-level numbers tracked weekly: ideas killed per stage and cost per kill, cost per validated idea, cost per shipped app, submissions used against the cadence, rejections, verified revenue minus recorded spend, and the hit rate of the synthetic screen against tranche 1 results (so the screen can be dropped if it predicts nothing).

## 7. Tools and accounts

| Tool or account | Role | Status |
|---|---|---|
| Meta Ads account and Meta Ads MCP | Paid traffic for demand tests and paid tests | New account needed. Official MCP in open beta. Campaigns are created paused and a person must activate them (verified 16 November 2026). An account spending limit set by the operator in Meta is the hard backstop |
| In-house LLM ranker | Synthetic screen | No vendor. Runs on the Claude subscription. See `skills/synthetic-screen` for why no persona service is used |
| ASO keyword data | Search demand signal for stage 1 | Appfigures (free Starter, keyword tracking from $44.99 a month, hosted MCP and CLI) or MobileAction Lite ($15 a month). Astro ($108 a year, Apple Search Ads popularity, local MCP in beta) is Mac-only and the operator's Mac is work-managed, so it needs an install the device policy may block. AppTweak ($99 a month) says its MCP is included in all plans. Third-party comparisons say it needs an API plan from $199. Unverified |
| Cloudflare Pages | One landing page per tested idea, and hosting for web products, deployed from CI | New account. Free tier, 500 builds a month |
| Stripe | Payments for web products: Checkout, customer portal, webhooks | New account, operator-owned. No monthly fee, about 3% per charge (price unverified, confirm on stripe.com before first use). The agent holds a restricted test-mode key only. Live products, prices and payouts are the operator's. Telemetry reads with a read-only restricted key |
| PostHog | Page and in-app analytics | Already available |
| TrustMRR | Verified revenue of products whose founders opted in, as a sanity check on a niche | Official MCP, declared in `.mcp.json` (approved 17 November 2026). Read-only. The discovery snapshot needs no account. Filtering by category and revenue needs the operator's free API key, stored as a network secret on the environment (host `trustmrr.com`, header `Authorization`) so it never appears in the repo or in a run. Limit 10 requests a minute; no republishing under their acceptable use policy |
| Supabase | App backend, early-access table | Connector in the directory, not installed. Free projects pause after a week idle. Official MCP supports `read_only=true` |
| RevenueCat | Subscriptions and paywall | New account. Official MCP at `https://mcp.revenuecat.ai/mcp`, declared in a committed `.mcp.json`. Free up to $2,500 monthly tracked revenue, then 1%. It can change store prices, so no agent key carries that permission |
| Expo and EAS | Cloud builds | New account. Required because the operator's Mac has no Xcode. Free plan has 15 iOS builds a month. Official Expo MCP at `mcp.expo.dev/mcp` |
| Apple Developer Program | Store account | $99 a year. 30% commission, or 15% in the Small Business Program, which needs enrolment |
| App Store Connect data | Downloads and proceeds | No official Apple MCP. Sales and finance reports through the API with a reports-only Team key, or an operator export into `state/metrics/inbox/` |
| Google Play | Second platform | Off by default. $25 one-time. New personal accounts need 12 testers for 14 days |
| HyperFrames (`npx hyperframes`, pinned version) | Demo video ads for demand tests, paid tests and content | Open source, free, no account. Renders HTML to MP4 with its own headless browser. `snapshot` and `render` were run by hand in a cloud container on 17 November 2026, not yet inside a stage run. Needs Node 22, ffmpeg, and network access to the npm registry and `cdn.jsdelivr.net` |
| Playwright | `page_check.js`: phone-sized screenshots and a funnel walk of each test page | Open source, free, no account |
| GetAppNiche (optional) | Estimated revenue and downloads for competitors, read by the scout | Not connected. $39 a month, official MCP at `api.getappniche.com/mcp`. Estimates are rough bands. Setup in `README.md`. The factory works without it |
| PickFu (optional) | Consumer panel poll on ad hooks before ad money is spent. Can kill, never pass | Not connected. Pay as you go from about $1 a response, official MCP at `mcp.pickfu.com/mcp`. Setup in `README.md`. The factory works without it |
| HeyGen voice (`voice.py`) | Ad narration, made only after the operator approves an idea | Operator decision 17 November 2026. Uses the HeyGen login on the operator's machine (10 free minutes a month) or `HEYGEN_API_KEY`. Falls back to the free local voice. The live HeyGen call is not yet verified: the login had expired when this was built |
| Postiz, ElevenLabs, ffmpeg | Organic content for winners | Postiz $29 a month, drafts only. A realistic presenter is `ACC-1` |
| GitHub, GitHub Actions, Slack | Source control, CI and page deploys, notifications | Already available |
| Prelaunch.com | Reservation-deposit tests | Not used by default. Plans from $279 a month (secondary source), built mainly for physical products. An `A-MCP-1` escalation if wanted |
| Apple pre-orders, Play pre-registration | Launch warm-up | Not a pre-build test. Apple pre-orders need the app submitted and reviewed first, and Play pre-registration needs an uploaded app bundle (both read on the vendors' pages) |
| Hosted AI model API | In-app AI features, called from a Supabase edge function | Allowed by the operator on 2026-11-17. Needs an API key with a spend limit before the first build that uses it |

## 8. Known failure modes and design responses

| Failure mode | Design response |
|---|---|
| Account termination takes every app and unpaid proceeds | Section 4: cadence, similarity and distinctness checks, freeze on any spam or fraud citation, hand submission, no second account |
| A web product ships and nobody finds it | The spec names the search terms and the paid channel before the build. The paid test is the same gate as for apps |
| Misleading billing gets the Stripe account restricted | Price, period and trial terms shown before payment, a cancel path in the product, a refund policy. Test-mode keys only for the agent |
| Building things nobody wants | Two tranches of real paid traffic before any code. Build slots only for validated ideas |
| Synthetic demand signals overstate interest | The LLM screen may only kill. Price and pass decisions use real traffic. Screen accuracy is tracked against tranche 1 |
| Signups that do not become payers | The fake door shows the price. The paid test measures trials and payers, and the winner call rests on payers |
| Ad spend runs away | Campaigns are created paused with lifetime budgets. The operator activates. Meta account spending limit. Monthly ads cap in `budget.yaml`. Telemetry calls kills with evidence |
| Ad account ban | Copy lint on every ad. No fake testimonials, no invented customers, no "available now" wording before launch. One ad account, operator-owned |
| Revenue bought at a loss | The winner call is on cost per payer and return on ad spend, not on MRR |
| Fake testimonials breach 16 CFR Part 465 and Australian Consumer Law | Copy lint, no AI "customers", brand-voice product claims only |
| Agents report success that did not happen | Every call is written with its evidence. Money, accounts and copy have script checks. Outcomes are read back |
| Scout reads untrusted reviews and pages | Scout has no credentials and no write connectors |
| Operator overload | Batch approvals: one packet per 15 ideas, not per idea. At most 6 live apps |
