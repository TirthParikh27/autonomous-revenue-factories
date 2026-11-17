# Factory G: Marketplace-distributed micro-tools

Status: folded into Factory A on 17 November 2026 (operator decision). Web products and micro-SaaS are built there. This blueprint is kept for reference and will not be built separately. Date written: 16 November 2026.
Fits `ARCHITECTURE.md` and `factories/_shared/CONVENTIONS.md`. Shared skills (`escalate`, `ledger`, `run-report`) are referenced, not copied.

## 1. Purpose and honest evidence

Build a small number of differentiated paid micro-tools (Chrome extensions, Shopify apps, small add-ons to an established platform) where a marketplace already supplies the demand, and prove each one with verified revenue or kill it cheaply.

What the research found:

- No verified case exists of an agent-built or agent-run extension or Shopify app portfolio with processor-verified revenue. The category evidence is real, the autonomous evidence is absent. The nearest processor-checked portfolio result is one solo developer's 38 Chrome extensions at $31.03 MRR and $165.47 lifetime net revenue (his own Stripe figures, August 2026).
- Verified base rate (TrustMRR data via a vendor analysis with internal inconsistencies): median verified MRR about $136, AI-tagged median about $7, top decile above $30K. The sample is self-selected, so a random launched tool likely does worse.
- Installs are not revenue: a 3-year-old extension with about 60,000 users shows zero subscriptions (verified zero; the seller's $2,000 MRR figure is a projection).
- Every readable "autonomous company" run earned $0 while spending $1,100 to $2,800 on tokens. The repeated lessons: sell before building, verify with a fresh context, and check the money path with synthetic tests because agents reported "all clear" over a dead payment path.
- Researcher estimates, not observations: 55 to 70% of the loop is automatable, capital under $300, first dollar in 1 to 3 months.

Design consequence: this factory is a validation funnel. Willingness-to-pay (WTP) evidence is a hard gate before any build, payment ships in version 1, and the default outcome of an idea is `killed` at the gap or spec stage.

## 2. State machine

Item = one tool. File: `state/items/<id>.json` (shared format). Factory-added directories at build time: `state/scout/`, `state/specs/`, `state/packets/`, `state/metrics/`, `state/support/drafts/`, `products/<id>/` (source code), `policy/` (store policy snapshots and checklists committed by the operator only).

| # | Stage (item `stage` after success) | Input | Process | Tools | Deterministic check (outside the model) | Output artifact | Runs as | Scheduler and cadence |
|---|---|---|---|---|---|---|---|---|
| 1 Input | Gap mining (`discovered`) | Target marketplaces and categories in `state/targets.yaml` | Scout reads 1 to 3 star reviews of paid incumbents, abandoned listings that still show users, breakage after platform or manifest changes, Shopify merchant complaints. Records each complaint with the incumbent's price | Parallel Search connector, Firecrawl connector (search and scrape). Connector tool ids to be confirmed at build time | Schema validation of scout output by a plain script; every evidence URL re-fetched for a 200 status by the script; duplicate check against all existing items | `state/scout/<run id>.json`, new item files | skill `gap-mine`, agent `market-scout` | Cloud scheduled task, weekly |
| 2 Process | WTP spec (`specced`) | One `discovered` item | Write a one-page spec: named paying user, price, WTP evidence, differentiation, permissions and data inventory, billing route, kill numbers | Read and Write only. No web access. Uses scout output | `spec-lint` script: all required fields present, WTP score at or above threshold in `budget.yaml`, price numeric, permissions list present, no banned category, not a clone of a portfolio item | `state/specs/<id>.md` | skill `wtp-spec` (main session) | Cloud scheduled task, daily, exits if queue empty |
| 3 Process | Build (`building` then `built`) | One `specced` item, or one `live` item with a recorded defect or approved change | Implement from the spec with payment and licence gating in version 1. Work on a `claude/` branch, open a pull request | git, Node toolchain, GitHub connector, Stripe in test mode only. Shopify's official CLI if the item is a Shopify app (verified 2026-11-16; not installed on the operator's Mac, and its deploy tokens are store credentials that no run holds) | GitHub Actions on the pull request: unit tests, end-to-end test of the extension or app in a headless browser, test-mode checkout completes and unlocks the paid feature, unpaid user stays locked, manifest permissions equal the spec's list, secret scan | `products/<id>/`, open pull request with green CI | skill `build`, agent `tool-builder` | Cloud scheduled task, daily, exits if queue empty. The cloud session container has Chromium with Playwright preinstalled and the operator's Mac has neither (verified 2026-11-16), so there is no Desktop fallback |
| 4 QA | Verify (`verified`) | One `built` item | Fresh-context verifier checks the build against the spec acceptance criteria. Policy checklist run against `policy/<store>.yaml` | Read, Grep, Glob, Bash for the test and checklist commands | `policy-check` script (permissions, declared hosts versus hosts in code, no remotely loaded code, data fields in code equal the data inventory, bundle builds reproducibly to the same hash twice). CI must be green on the exact commit | `state/packets/<id>/verify.json` | skill `verify`, agent `release-verifier` | Cloud scheduled task, daily, exits if queue empty |
| 5 Output | Store handoff (`packaged`, then `awaiting_human`, then `submitted`, then `live`) | One `verified` item | Assemble the submission packet: build artifact and hash, listing copy, screenshots list, permission justifications, draft privacy disclosure, pricing, test evidence. Raise `G-SUB-1`. The operator submits under their own developer account | Read, Write, Bash for hashing. No store credentials exist in any run | `packet-lint` script: every packet file present, artifact hash equals the CI artifact hash, permission list equals manifest. Later: public listing URL fetched and returns the listing | `state/packets/<id>/`, escalation packet | skill `store-handoff`, agent `listing-packager` | Cloud scheduled task, daily, exits if queue empty |
| 6 Telemetry | Telemetry (stays `live`) | All `live` and `submitted` items | Pull installs, activation, paid conversion, revenue, refunds. Draft review replies. Apply kill rules | Stripe connector with a read-only restricted key, PostHog connector (already connected), marketplace payout report committed by the operator, public listing fetch | Reconciliation script: sum of new ledger revenue lines equals the Stripe or payout total for the same period. Synthetic money-path check (test-mode checkout) runs daily in GitHub Actions with no model | `state/metrics/<id>/<date>.json`, ledger lines | skill `telemetry` | Cloud scheduled task, daily. GitHub Actions cron, daily, for the synthetic check |
| 7 Self-improvement | Weekly review | Week of journal, ledger, metrics, rejected packets | At most three proposals, each as a pull request | Read, Grep, GitHub connector | CI path check: the pull request touches only `skills/`, `agents/`, `state/targets.yaml`, `journal/LESSONS.md`. Every proposal cites a journal or ledger line | Pull requests, `journal/LESSONS.md` entries | skill `weekly-review` (main session, Opus) | Cloud scheduled task, weekly |

Each cloud task has its connector list pruned to the tools in its row. Gmail, HubSpot, Notion, Drive and Calendar are removed from every task in this factory. Slack and Linear are kept only for escalation notices.

The default cloud network allowlist returns 403 for most hosts. Scout reading therefore goes through connectors. Whether store listing and review pages are reachable that way, and whether each store's terms permit automated reading of them, is unverified and must be confirmed at build time (trigger `G-TOS-1`).

## 3. Allowed transitions

```
(new)          -> discovered
discovered     -> specced | killed
specced        -> building | awaiting_human | killed
building       -> built | awaiting_human | killed
built          -> verified | building (verifier gaps, at most 2 returns) | killed
verified       -> packaged
packaged       -> awaiting_human            (always, trigger G-SUB-1)
awaiting_human -> submitted                 (G-SUB-1 packet in approved/)
awaiting_human -> <stage named in packet>   (other trigger approved)
awaiting_human -> killed | <stage named in "If you say no">   (packet in rejected/)
awaiting_human -> awaiting_human            (packet expired: parked, scores.parked = true, no further notices)
submitted      -> live | building (store rejection, once per rejection reason) | killed
live           -> building (defect fix or approved change) | awaiting_human | killed
killed         -> (terminal)
```

No other transition is valid. Every store upload, including updates to a live tool, passes through `packaged -> awaiting_human`. "Winner" is a flag (`scores.winner`), not a stage.

## 4. Kill criteria

Numbers are proposed design defaults, not research results. They live in `budget.yaml` and only the operator changes them.

| Stage | Kill when |
|---|---|
| discovered | WTP score below 6 after at most 2 scout runs or $3 of spend on the idea. No incumbent charges money and no user states a price. The idea is a generic AI wrapper. It duplicates a portfolio item or is a near-copy of one incumbent. It needs login-walled or personal data it cannot get with narrow permissions |
| specced | `spec-lint` fails twice. No named paying user. Price below $3 per month or $15 one-off. Billing route unknown for the target store |
| building | Item token spend passes $40 without green CI. More than 3 build runs without green CI. Payment cannot be made to work in test mode |
| built / verified | Verifier returns the item twice and gaps remain. A policy-check failure cannot be fixed without widening permissions beyond the spec |
| submitted | Second store rejection for the same reason. Any store warning that mentions the developer account (also raises `G-REJ-1`) |
| live | 30 days live and fewer than 25 installs. 60 days live and zero paid conversions. 90 days live and verified net MRR below $25. Refund rate above 20% of payments in any 30 days |

A `live` item with at least one active paying customer is not killed directly. It raises `G-SUNSET-1`, because customers and refunds are involved.

Factory-level validation budget: $400 all-in (tokens, paid APIs, fees) or 120 days from the first build run, whichever comes first. If no revenue line exists in `ledger/revenue.jsonl` by then, the factory pauses and raises `G-BUD-2` for a keep-or-kill decision. Portfolio limits: at most 2 items in `building` to `packaged`, at most 3 `live`, at most 2 new specs per month.

## 5. Telemetry and the definition of a winner

Sources of truth, in order:

1. Revenue: Stripe via a read-only restricted key, or the marketplace payout report (Shopify Partner payouts, merchant-of-record payout statement) exported and committed by the operator.
2. Installs and uninstalls: the store's developer dashboard. No verified API for this is in the research notes. Until one is confirmed, the operator exports the figures weekly into `state/metrics/inbox/`.
3. Activation: an anonymous first-core-action event in PostHog. This only ships if it is listed in the privacy disclosure the operator approved.
4. Listing health: the public listing URL fetched by the run.

Metrics per item: installs, activation rate (first core action within 7 days, divided by installs), paid conversion (active paying customers divided by installs), net MRR, refund rate, monthly churn, token spend to date, net profit (revenue minus recorded spend).

Winner: verified net MRR of at least $136 (the median in the verified dataset) for two consecutive calendar months, refund rate under 10%, and cumulative revenue above the item's recorded spend. A winner earns a larger iteration budget through `G-BUD-1`. Nothing is a winner on installs alone.

## 6. Self-improvement loop

The weekly review reads the week's run reports, both ledgers, `state/metrics/` and `escalations/rejected/`. It examines:

- Funnel counts by stage and the kill reason at each stage.
- Calibration: WTP score at spec time against actual paid conversion for live items. This is the main question this factory must learn to answer.
- Which gap source (review mining, abandoned listing, platform breakage, merchant complaint) produced items that reached a paid customer.
- Store rejections and policy-check failures by cause.
- Token cost per item per stage, and runs that failed the wrapper.
- Any day the synthetic money-path check failed, and how long before it was noticed.

It may propose at most three changes, one per skill per week, as pull requests limited to `skills/`, `agents/`, `state/targets.yaml` and `journal/LESSONS.md`. Each names the observation, hypothesis, single change, judging metric and review date. Changes to `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, `policy/`, kill numbers, the WTP threshold, the wrapper, hooks or settings are escalations (`G-SELF-1`), never pull requests from the factory.

## 7. Tools and accounts

| Tool or account | Used for | Status |
|---|---|---|
| Claude Code cloud scheduled tasks | All model stages | Already available |
| GitHub connector and GitHub Actions | Source, CI, synthetic checks | Connector already available. Repository must be created |
| Slack, Linear connectors | Escalation notices | Already available |
| PostHog connector | Activation events | Already available |
| Parallel Search connector | Scout search | In the directory, not installed. Free MCP needs no account but rate-limits after roughly 8 to 10 quick calls. Search API $1 to $5 per 1,000 requests (verified 2026-11-16) |
| Firecrawl connector | Scout page content | One-click connector plus new account. Free tier 1,000 credits a month, verified 16 Nov 2026 |
| Stripe connector | Revenue truth, test-mode checkout | In the directory, not installed. Account status unknown. Australian fees: 1.65% + A$0.30 domestic cards, 3.5% + A$0.30 international, plus 2% for currency conversion (verified 2026-11-16). Unattended runs get a read-only restricted key, which must carry the Agent tag for the Stripe MCP from December 2026 |
| Chrome Web Store developer account | Human submission | New account needed (operator only). $5 one-time registration. The store has no built-in payments, so billing is always off-store (verified 2026-11-16) |
| Shopify Partner account | Human submission, marketplace billing | New account needed (operator only). Verified 2026-11-16: 0% revenue share on the first $1M of lifetime gross app revenue, 15% above it, 2.9% processing, $19 one-time registration. Shopify App Store rules from 10 Nov 2026 (verified 2026-11-16): one new app in review at a time, each published app needs 10 or more paid installs before another can be submitted, cooldowns escalate after a rejection, and an app with zero installs after six months is removed. Whether Shopify mandates its own billing for App Store apps is stated in the notes as an inference, confirm at build time |
| Merchant of record (Lemon Squeezy, Polar, Dodo Payments, ExtensionPay) | Alternative to Stripe for tax handling | Fees verified 2026-11-16: Lemon Squeezy 5% + 50c and being wound toward Stripe Managed Payments; Polar 5% + 50c on the free plan for new organisations; Paddle 5% + 50c with an official MCP; Stripe Managed Payments 3.5% on top of processing, open to Australian businesses, digital products through Checkout and Payment Links only. Dodo Payments and ExtensionPay were not checked |
| Cloudflare Developer Platform connector | Licence-check endpoint, privacy policy page | In the directory, not installed. New account. Workers free tier is 100,000 requests a day, Workers Paid is $5 a month, and no commercial-use restriction was found (verified 2026-11-16) |
| Headless browser test runner (Playwright is the default named in the architecture) | End-to-end tests | Microsoft's Playwright CLI and MCP are free and Apache-2.0, and Playwright with Chromium is preinstalled in the cloud container (verified 2026-11-16). Whether it can load an extension under test in CI must be confirmed |
| Shopify developer CLI | Shopify app scaffolding and tests | Official and free. Headless auth uses `SHOPIFY_SERVICE_ACCOUNT_TOKEN` or `SHOPIFY_APP_AUTOMATION_TOKEN` (verified 2026-11-16). Those tokens are store credentials, so deploys stay with the operator |
| TrustMRR | Base-rate data, optional verified listing or sale | Public pages. Database listing is free, marketplace listings start at $29, and there is a 3% closing fee, split (verified 2026-11-16). Listing needs a new account |
| Sentry connector | Error tracking for live tools | One-click, optional |

## 8. Known failure modes and the design response

| Failure mode (source) | Response |
|---|---|
| Installs without revenue (60,000-user extension, zero subscriptions) | Payment and licence gating are acceptance criteria of version 1. Winner and kill rules use paid conversion and verified MRR |
| Median outcome near zero, AI wrappers lowest (AI-tagged median about $7) | WTP gate before build. Generic AI wrappers are killed at discovery. Preference for add-ons to an established platform |
| Loop keeps building instead of selling (Autocomp) | Portfolio caps. No new spec while 2 items are in build. Validation budget ends in a keep-or-kill escalation |
| "All clear" over a dead payment path (Automaton) | Daily synthetic checkout in GitHub Actions with no model. Revenue only from Stripe or payout reports |
| Scoreboard overstated the funnel by 57% (Autocomp) | Reconciliation script compares ledger to source totals. Metrics carry their source and date |
| Store rejection and developer-account risk from templated volume | No clones, no templated variants, human submits every upload, second same-reason rejection kills the item |
| Broad permissions or user data handling | Narrowest permissions in the spec, CI diff of manifest against spec, `G-PERM-1` escalation before build |
| Platform API or manifest change breaks a live tool | Daily listing and synthetic checks, defect fix path `live -> building`. The same events are also a gap-mining source |
| Support load grows with each product | At most 3 live items. Review replies are drafts for the operator |
| Unsafe drift toward spam (Bottleneck Labs) | The factory holds no email, posting or store credentials. Outreach and promotion are out of scope without `GEN-1` |
| Prompt injection through reviews and listings | Scout has no credentials and writes one schema-validated file. Builders never read raw fetched pages. `SEC-1` on any embedded instruction |
