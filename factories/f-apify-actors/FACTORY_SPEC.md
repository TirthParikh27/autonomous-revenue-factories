# Factory F: Apify Store actor portfolio

Status: blueprint for review. Nothing here has been built or run. Date: 16 November 2026.
Fits `ARCHITECTURE.md` and `factories/_shared/CONVENTIONS.md`. Shared skills (`escalate`, `ledger`, `run-report`) are referenced, not copied.

## 1. Purpose and evidence

Publish a small portfolio of Apify Store actors (scrapers and data tools) priced pay-per-event, in niches where the Store already has search demand and weak or broken incumbents, and keep them working. The same actors are the factory's route to selling to AI agents.

What the research supports, and how strongly:

- Platform terms, read from Apify's docs (V1): Apify keeps a 20% commission. For pay-per-event actors, platform usage cost is deducted from the creator's payout and can produce negative profit. The Creator plan includes $500 of prepaid usage for the first 6 months and test runs draw on it. AI agents can pay for an actor with a prepaid token without an Apify account.
- One small-operator ledger (V2, self-reported, not verified by a payout screenshot): 13 Korean-site scrapers, 2,186 runs, $20.11 revenue, $5.99 platform cost, $14.12 profit in the first three days of paid pricing, settling at $1 to $2 a day. Users per actor were 2 to 12. The post does not say the actors were built by an agent.
- Distribution is a steep long tail (V3, interested author): most published actors have 0 to 5 users. A reported 3,329 actors were added to a roughly 6,000 actor catalogue in eight weeks (V3/V4), so commodity categories are saturated.
- **No verified case of an autonomous or agent-run actor portfolio earning money was found.** Apify itself publishes only aggregates (read 2026-11-16): "$1.7M paid out last month" across about 5,600 community developers, top independent creators above $10,000 a month, and no named revenue or distribution. The expectation of "tens to low hundreds of dollars a month" is an extrapolation from the single V2 data point.
- Payouts, verified 2026-11-16 in Apify's Store publishing terms: the creator gets 80% of fees minus platform usage costs, invoiced monthly. Minimum payout is $20 by PayPal and $100 by other methods, and a balance under the minimum is forfeited after 12 months. Identity verification is required. Free-plan users generate no creator revenue. The 11th-of-the-month date and the roughly 48-hour pricing review come from the V2 post only. Unverified, confirm at build time.

Design stance: the default outcome for any candidate is "killed early at low cost". The expensive part is maintenance, so the factory limits how many actors are live and spends first on keeping them green.

### Agent-buyer rail and the optional side bet

Every published actor is already purchasable by agents through Apify's prepaid-token route (V1). No extra stage is needed. A standalone paid MCP server or x402 endpoint is **not part of the state machine**. The only evidence for it is an interested party's estimate that 95% or more of MCP servers earn nothing. It may be proposed once by the weekly review under trigger `F-SIDE-1`, only for an actor that already shows repeat usage, with a cap in `budget.yaml` (default 0, disabled).

## 2. Layout added by this factory (created at build time)

```
actors/<item-id>/        actor source, one directory per actor
fixtures/<item-id>/      inputs.json, expected.schema.json, snapshots/ (raw captures, data only)
compliance/deny_list.yaml    targets that are never built (operator-owned)
compliance/allow_list.yaml   target domains the operator has approved (operator-owned)
state/metrics/           canary/, runs/, costs/, store/ daily JSON files
state/payouts/           one file per payout period, from the Apify payout or earnings page
scripts/                 deterministic checks named below (no model inside)
```

Deny list seed, to be extended by the operator before the first scan: LinkedIn (named by the architect); Reddit and X (verified 2026-11-16: X's terms effective 9 Oct 2026 prohibit crawling or scraping "in any form, for any purpose" without prior written consent, and Reddit's Data API terms require explicit approval and bar commercial mining or scraping without written approval, while its public Data API is being shut down); and four categories checked per target: login-walled data, personal-data-heavy targets, sites known to have sued scrapers, and anything needing circumvention of a technical protection. The research notes contain no legal analysis by jurisdiction, so the lists are the operator's decisions and the factory only enforces them.

Item files follow CONVENTIONS and add: `target_domains`, `apify_actor_id`, `price_per_result_usd`, `unit_econ`, `fixture_set_hash`, `repair_attempts`, `canary_streak`, `external_users_30d`.

## 3. State machine

One run does one stage on 1 to 3 items. Model sessions never hold an Apify token. Every call to the Apify platform that needs the token (private build push, fixture runs, canaries, stat pulls) is a deterministic GitHub Actions job using a repository secret. This is the main privilege boundary in the factory.

| Stage (skill) | Input | Process | Tools | Deterministic check (outside the model) | Output artifact | Runs as | Scheduler, cadence |
|---|---|---|---|---|---|---|---|
| **Input 1: gap scan** (`gap-scan`) | Apify Store category and search pages, issue tabs of incumbent actors, `journal/LESSONS.md`, list of live and killed items | Find queries with demand and weak, stale or broken incumbents. Favour regional and newly growing platforms. Score and dedupe. | `store-scout` sub-agent with WebFetch and WebSearch. Parallel Search or Firecrawl connector if the operator adds one. An Apify Store listing API may exist: unverified, confirm at build time. | `scripts/validate_item` (schema, evidence has source URLs, no duplicate target and output type). `scripts/deny_check` on every target domain. | `state/items/<id>.json` in `discovered`, max 5 new per run | Main session (Sonnet) plus `store-scout` (Haiku) | Cloud scheduled task, weekly |
| **Input 2: spec and compliance** (`spec-compliance`) | Items in `discovered`; approved `F-TGT-1` or `F-PII-1` packets | Compliance screen first (deny list, login wall, personal data, robots, circumvention). Then write the actor spec, fixture set and price hypothesis. | `store-scout` for the target's terms and robots.txt. `scripts/capture_fixtures` (GitHub Actions, at most 10 polite requests) for snapshots. | `scripts/deny_check`; `scripts/validate_spec` (required sections present, fixture count 5 to 10 including one zero-result input, egress host list equals `target_domains`, runtime and item caps set). New domain not on `allow_list.yaml` forces `F-TGT-1`. | `actors/<id>/SPEC.md`, `fixtures/<id>/`, item in `specified` | Main session (Sonnet) plus `store-scout` | Cloud scheduled task, daily, max 2 items |
| **Process: build** (`build-actor`) | Items in `specified`, or `degraded` items with a repair note | Implement the actor from an Apify template (Crawlee, Playwright or plain HTTP), input schema with zero-config defaults, README, Store title and description. Offline tests against snapshots. | `actor-builder` sub-agent: Read, Write, Edit, Bash, Grep, Glob. Node and Crawlee from the package registry. No Apify token, no web tools. | CI on the pull request (GitHub Actions): unit tests on snapshots, output schema validation, lint, `scripts/egress_check` (no hosts outside `target_domains`), no secrets. Then `actor-verifier` in a fresh context. | Pull request on a `claude/` branch, item in `built` when CI is green and the verifier reports no correctness gap | Main session (Sonnet, Opus after one failed attempt) plus `actor-builder`, `actor-verifier` | Cloud scheduled task, daily check, max 1 item |
| **QA and backtest: live test** (`live-test`) | Items in `built` | Private build pushed to Apify, fixture set run 3 times against the live target, cost and block rate measured, unit economics computed. | GitHub Actions `fixture-run` workflow (Apify CLI or API with the build-and-run token). Model session only triggers it through the GitHub connector and reads the result file. | `scripts/fixture_run` result: pass rate, schema validity, block rate. `scripts/unit_econ`: hard gate, see section 5. | `state/metrics/runs/<id>-livetest.json`, `unit_econ` written to item, item in `tested` | Main session (Haiku or Sonnet) | Cloud scheduled task, daily, max 2 items |
| **Output: publish** (`publish`) | Items in `tested` | Portfolio gate, then approval packet. After approval the operator makes the actor public and sets pricing in the Apify Console. The run then verifies the outcome. | `publisher` sub-agent: Read, Write, WebFetch. `escalate` skill. Whether the Apify API can set visibility and pricing is unverified, so the default is the operator's click. | `scripts/portfolio_gate` (cap, green ratio, duplicates). After approval: Store URL fetched and returns the listing, displayed price equals approved price, first canary green. | Packet in `escalations/open/`, item `awaiting_human`, then `live` | Main session (Sonnet) plus `publisher` | Cloud scheduled task, daily |
| **Telemetry: monitor** (`monitor`) | Items in `live` or `degraded` | Daily canary on the fixed fixture subset, pull of runs, failures, users, platform cost and Store issues. Health and cost verdicts. Repair notes. Earnings recorded from the payout page only. | GitHub Actions `canary` and `pull-stats` workflows (no model). Model session reads their output, drafts repair notes and issue replies, calls `ledger`. | `scripts/health_gate` (canary, failure rate, daily cost alarm, trailing profit). Revenue lines only from `state/payouts/`. | `state/metrics/**/<date>.json`, stage changes, ledger lines | GitHub Actions for data, main session (Haiku) for triage | GitHub Actions daily, cloud scheduled task daily about one hour later |
| **Self-improvement: weekly review** (`weekly-review`) | Week of journal, ledger, metrics, rejected packets, `LESSONS.md` | Compare predictions to outcomes, find the costliest failure, propose at most three changes, propose retirements and double-downs, check validation budget. | Read, Grep, Glob, Bash (read-only scripts), GitHub connector for pull requests | `scripts/review_inputs` builds the numbers table from files so the model does not compute totals. Each proposal must carry the five fields in ARCHITECTURE 5.5. | `journal/<date>/weekly-review.md`, up to 3 pull requests, `LESSONS.md` update by pull request | Main session (Opus) | Cloud scheduled task, weekly |

Cloud runs clone fresh and the Claude identity cannot push to `main`. Per ARCHITECTURE.md section 3, runs write `state/`, `ledger/`, `journal/` and `escalations/open/` to the `factory-state` branch and read rules and approvals from `main`. The wrapper must implement this before any schedule is turned on.

## 4. Transitions

Only these are allowed. `scripts/validate_item` rejects any other.

```
(new)          -> discovered        gap-scan, schema and deny check pass
discovered     -> specified         spec-compliance, all target domains on allow list
discovered     -> awaiting_human    F-TGT-1 (new target domain) or F-PII-1 (personal data)
discovered     -> killed            deny list hit, login wall, robots disallow, circumvention needed, score below threshold, duplicate
specified      -> built             CI green and verifier pass
specified      -> killed            2 failed build attempts or build spend cap reached
built          -> tested            fixture pass and unit economics gate pass
built          -> specified         live test failed, first time only, with a defect note
built          -> killed            second live test failure, unit economics fail, block rate over limit
tested         -> awaiting_human    F-PUB-1 or F-PUB-2
tested         -> killed            portfolio gate fails on duplicate or monoculture rule
live           -> degraded          health gate fails
degraded       -> live              repair promoted and canary green 2 days running
live|degraded  -> awaiting_human    F-ECON-1, F-COST-1, F-REP-1, F-RET-1, F-LEGAL-1, F-PRICE-1
any stage      -> awaiting_human    GEN-1, SEC-1, BUD-1, RUN-3
awaiting_human -> specified         F-TGT-1 or F-PII-1 approved (spec written in the same run)
awaiting_human -> live              F-PUB-* approved and listing verified, or a live-actor packet resolved with "keep"
awaiting_human -> degraded          F-REP-1 approved or rejected with "keep repairing"
awaiting_human -> retired           F-RET-1, F-ECON-1, F-COST-1 or F-LEGAL-1 approved and the operator has unpublished
awaiting_human -> killed            packet rejected for an item that was never published
awaiting_human -> parked            packet expired
parked         -> awaiting_human    re-raised once, only with materially changed evidence
parked         -> killed            weekly review, after 30 days parked
killed, retired                     terminal
```

A repair of a `degraded` actor runs `build-actor` and `live-test` on a branch without changing the item's stage. The item stays `degraded` until the health gate passes. Putting a repair build in front of users is an external write to a published product, so by default it needs `F-REP-1` approval. Automatic promotion of schema-preserving repairs is a `budget.yaml` switch that stays off until a staged build mechanism on Apify (for example a separate build tag) is confirmed at build time.

## 5. Unit economics gate (hard, per actor)

Computed by `scripts/unit_econ` from the live-test runs, never by the model.

- `cost_p90` = 90th percentile across the 3 fixture runs of (total platform cost of the run, including failed and zero-result inputs) divided by (results returned).
- `net_per_result` = `price_per_result_usd` x 0.80 minus `cost_p90`. The 0.80 is the V1 commission figure and is read from `budget.yaml`.
- Pass requires all of: `price >= price_multiple_of_cost x cost_p90` (default 5), `price <= max_price_per_result_usd` (default 0.01; the read examples cluster at 0.002 to 0.005), the zero-result fixture costs no more than `max_zero_result_run_usd`, and the actor enforces a maximum runtime and maximum items per run so a user cannot create unbounded cost.
- Which events are chargeable under pay-per-event, and whether a per-run start event is allowed, was not in the research notes. Unverified, confirm at build time. Until confirmed the gate assumes revenue only per result.

After publish the same formula runs daily on real usage, plus a daily compute cost alarm per actor (`daily_cost_alarm_usd`) and a trailing 14 day profit check.

## 6. Kill criteria

| Stage | Kill when |
|---|---|
| gap-scan | No demand signal with a source URL. Or 3 or more maintained incumbents each with over 500 users. Or target already covered by a live or killed item. Run-level: 3 scans in a row with zero candidates passing means the scan prompt is escalated, not retried. |
| spec-compliance | Deny list hit. Data only behind login. robots.txt disallows the needed paths. Any CAPTCHA, fingerprint evasion or other circumvention needed. Scout cost for one item over $1. |
| build-actor | 2 failed attempts (CI red or verifier gap). Token spend on the item over `max_build_usd_per_item` (default $15). |
| live-test | Fixture pass rate under 90% twice. Block rate (403, 429, challenge pages) over 10%. Unit economics gate fails at the price ceiling. |
| publish | Packet rejected. Duplicate of a live actor. More than `max_actors_per_target_family` on one site. |
| live | 0 external users 30 days after publish. Under $1 trailing 60 day profit. Trailing 14 day profit negative. 2 failed repairs, or red for more than 7 days. More than 3 repairs in 30 days. Each of these raises a retire proposal, since unpublishing is the operator's action. |

**Factory-level validation budget and window:** $350 total recorded spend (tokens plus any cash beyond the Creator prepaid usage) or 120 days from the first build run, whichever comes first. If neither a payout nor payout-page earnings of at least $20 exists by then, the factory pauses and raises `F-VAL-1`. Checkpoint at day 45 after the first publish: if no actor has 3 or more external users, the weekly review must propose a change of niche or a stop.

## 7. Telemetry and what a winner is

| Metric | Source of truth | Used for |
|---|---|---|
| Revenue | Apify payout or earnings page only, saved as `state/payouts/<period>.*`. How the page is read unattended is unverified (an earnings API may or may not exist), so the default is that the operator drops the monthly export or screenshot in that folder. | `ledger/revenue.jsonl`, winner test, validation gate |
| Runs, failures, distinct users, platform cost per actor | Apify API through the `pull-stats` workflow with a read token. Exact endpoints unverified, confirm at build time. | Leading indicators and alarms only. Never written as revenue. |
| Canary result | `canary` workflow output | Breakage detection |
| Store issues and rating | Actor page | Repair queue, retire decisions |
| Token cost | Wrapper, `total_cost_usd` | Ledger, per-item spend |

A **winner** is an actor that over a 30 day window has 10 or more distinct external users, positive profit after commission, platform cost and its own maintenance tokens, and canary green on at least 90% of days. A factory-level success is a payout actually received. Daily accrued figures from the API are estimates and are labelled as such in every report.

## 8. Self-improvement specifics

The weekly review examines: predicted versus actual users and cost per result for each published actor, which gap-scan signals preceded winners and zeros, repair count and repair tokens per actor, canary false alarms and misses, rejected packets and their reasons, prepaid usage remaining and its runway, share of spend going to maintenance versus new builds.

It may propose (as pull requests, one change per skill per week, three in total): scoring weights and thresholds in `gap-scan`, the spec template, fixture design rules, canary subset size, README and title wording, adjacent actors around a winner, retirements, a price change (`F-PRICE-1`), and one side-bet experiment (`F-SIDE-1`). It may not touch `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, `compliance/`, `scripts/`, workflows, hooks or settings. A wish to change those is `F-SELF-1`.

## 9. Tools and accounts

| Tool or account | Role | Status |
|---|---|---|
| Claude Code cloud scheduled tasks | All model stages | Already available |
| GitHub, GitHub Actions, repository secrets | Source control, CI, token-holding jobs | Connector available. Repository must be created |
| Slack, Linear | Notifications, escalation queue | Already available |
| Apify account on the Creator plan, payout method, tax and identity details | Platform, Store, billing | New account needed. Operator only (`F-ACCT-1`) |
| Apify API tokens: one read-only for stats, one for build and run | Used only inside GitHub Actions | New. Verified 2026-11-16 (Apify docs): tokens can be scoped at account level or to specific resources, but a scoped token cannot create or modify Actors, and scheduled runs get an unscoped token. So the stats token is scoped and the build token is not, which is why it lives only in Actions secrets |
| Apify CLI, Apify SDK, Crawlee, Playwright | Build and test | The official `apify-cli` exists (verified 2026-11-16). Neither it nor Playwright is on the operator's Mac, so both run in GitHub Actions or the cloud container. Exact commands and versions unverified, confirm at build time |
| Apify MCP server | Possible agent channel | Official, hosted at `mcp.apify.com` and published as `@apify/actors-mcp-server` (verified 2026-11-16). Connecting is free and runs bill to the account. Not in the Claude connector directory. Not used by default |
| Parallel Search or Firecrawl connector | Store and terms research | One-click connector. Optional. WebFetch is the default |
| PostHog | LLM cost traces | Already available. Optional |
| PayPal or bank account for payouts | Payout | Operator's own. Minimum $20 by PayPal, $100 by other methods, monthly invoice (verified 2026-11-16). Payout date unverified |

## 10. Known failure modes and the design response

| Failure mode from the research | Response |
|---|---|
| Most actors get 0 to 5 users | Small batches, demand evidence required before spec, 30 day zero-user retire rule, validation budget |
| Under-pricing produces negative payout | Unit economics gate before publish, daily cost alarm, trailing profit check, bounded runtime per run |
| Target site changes break actors silently | Daily canary on fixed fixtures run by a script, not by agent self-report |
| Catalogue saturation after the 2025 to 2026 challenge | Scan favours regional and new platforms, kills commodity categories with strong incumbents |
| Early revenue spikes fade | Winner test uses 30 day windows, not launch week |
| Near-duplicate monoculture invites delisting | Duplicate check, cap per target family, portfolio cap |
| Legal, terms and privacy exposure lands on the publisher | Operator-owned deny and allow lists, operator sign-off for every new target domain, personal data is always an escalation |
| Agents report "all clear" while the money path is dead | Revenue only from the payout page, wrapper checks artifacts, verification by a fresh-context verifier |
| Token burn with $0 revenue ($1,117 and $2,833 in the read experiments) | Monthly token cap, per-run caps, validation budget of $350 |
| Agents drift to spam when asked to make money | No outbound channel at all. No marketing, no email, issue replies are drafts |
| Credential theft through injected content | No Apify token in any model session. Scouts have no credentials. Builder has no network tools |
| Single-platform dependency, pricing model changes | Accepted risk. Weekly review reads the monetisation doc date and flags changes as `GEN-1` |
