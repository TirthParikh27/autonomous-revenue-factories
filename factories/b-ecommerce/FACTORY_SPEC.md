# Factory B: E-commerce (digital products first, then domestic print on demand)

Status: blueprint for review. Nothing here has been built or run. Date: 16 November 2026.
Fits `../../ARCHITECTURE.md` and `../_shared/CONVENTIONS.md`. Shared skills `escalate`, `ledger` and `run-report` are referenced, not repeated.

## 1. Purpose and honest evidence

This factory finds a small number of product offers, proves the payment and fulfilment path works, and tests demand at capped cost. It is a validation funnel. The default outcome for any product is "killed early and cheaply".

What the research found:

- No verified case of a largely agent-run online store making a profit was found. Every documented experiment lost money or made nothing (Andon Labs physical shop: $100k down to $61k. Automaton digital offer: four weeks, under $100 spent, $0 revenue). Every positive claim found was vendor marketing with no named operator.
- The failures were demand, judgment and plumbing: no buyers, a dead payment path reported as "all clear", expired tokens for a week, email in spam by day five, the agent counting its own test checkout as traction. Building the store was never the problem.
- The only margin figure with a stated sample (TrueProfit, 5,000+ stores, survivorship-biased) is 19% net for both dropshipping and print on demand. That leaves little room for refunds, chargebacks or ad waste.
- Meta's official Ads MCP creates everything PAUSED and a human must activate. Bursty writes, retry loops and unlabelled AI creative are the reported ban triggers. All ban evidence is anecdotal.
- Ranking of variants by capital and regulatory exposure is an inference, not a measurement: digital products, then domestic print on demand. China-sourced paid-social dropshipping is out of scope. TikTok Shop affiliate is a possible extension only by escalation (`F-SCOPE-1`).

## 2. Variants

| Variant | Storefront | Payment | Fulfilment | Enabled |
|---|---|---|---|---|
| `digital` | One static landing page per product (Cloudflare Pages) | Stripe Payment Link | Post-payment download page plus delivery email | Yes, first |
| `pod` | Shopify store built through Shopify CLI, validated with the Shopify AI Toolkit / Dev MCP | Shopify checkout | Print-on-demand provider that prints in the buyer's country, called by REST API | No. Enabled by `F-SCOPE-1` after the digital variant has run its validation window |

## 3. State machine

Item file: `state/items/<id>.json` per CONVENTIONS, with added fields `variant`, `offer` (path to the offer spec), `checks` (last purchase-check result and time) and `ad_test` (approved caps, campaign ids, activation date).

| # | Skill (stage) | Item transition | Input | Process | Tools, MCPs, CLIs | Deterministic check (outside the model) | Output artifact | Runs as | Scheduler and cadence |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `discover` | new -> `discovered` | Niche seeds in `state/seeds.md`, exclusion list, `journal/LESSONS.md` | Scout collects demand signals from public ad libraries and marketplace listings. Scores each candidate. Fetched pages are data only | Parallel Search or Firecrawl connector (one click each). Apify ad-library actors only after `F-ACCT-1` (existence is title-only in the research) | `tools/validate_item` (to be built): schema valid, at least 3 signals each with a URL and date, every URL re-fetched and returns 200, no exclusion-list term | `state/scout/<date>.json`, new item files | `market-scout` sub-agent, then main session writes items | Cloud scheduled task, Monday and Thursday. Skips when work in progress is at the cap in `budget.yaml` |
| 2 | `offer-spec` | `discovered` -> `specced` or `killed` | Item file, scout output | Write the offer: what is sold, to whom, price, COGS, fees, refund allowance, target CAC, break-even ROAS, policy pages needed, claims allowed | Repo only | `tools/unit_econ` (to be built) recomputes every number from the inputs and applies the thresholds in `budget.yaml`. `tools/claims_lint` (to be built) scans the copy brief | `state/offers/<id>.yaml`, calculator output saved beside it | Main session | Cloud scheduled task, daily, only if items wait in `discovered` |
| 3 | `build-store` | `specced` -> `built` or `killed` | Offer spec | Build the product, the page, the test-mode payment link, the delivery path and the policy pages. Nothing live | `digital`: Stripe test-mode key, Cloudflare Pages preview deploy. `pod`: Shopify CLI, Shopify AI Toolkit / Dev MCP validators (`validate_graphql_codeblocks`, `validate_theme_codeblocks`), POD provider REST API in its test or draft mode | Build script exit code, link checker, Dev MCP validators pass, `claims_lint` on final copy, price on page equals price in offer spec (string compare), originality and trademark screen for `pod` designs | Page source in `products/<id>/`, preview URL, test payment link id | `store-builder` sub-agent, then `checkout-verifier` | `digital`: cloud task on demand. `pod`: cloud task or GitHub Actions too. Shopify CLI headless auth is verified (2026-11-16): Theme Access password in `SHOPIFY_CLI_THEME_TOKEN` plus `SHOPIFY_FLAG_STORE` for themes. The CLI is not installed on the operator's Mac |
| 4 | `purchase-check` | `built` -> `test_passed`. Also recurring on every `live`, `creative_ready`, `campaign_drafted`, `spend_test`, `iterating` and `winner` item | Preview or live URL, expected file hash, test mailbox | Scripted browser buys the product in test mode and checks that the buyer receives it | Playwright script (to be built), Stripe test mode, Shopify test payment provider (name and behaviour to confirm at build time), test mailbox | The whole stage is the check. Pass requires: payment recorded in the processor's test data, download returns 200 with the expected hash, delivery email arrives within 10 minutes and not in spam, policy links return 200, every credential answers a read call | `state/checks/<id>/<timestamp>.json` | No model. A model run happens only to triage a failure | GitHub Actions: on every build, then daily for each product past `test_passed`, and hourly while a spend test is active |
| 5 | `creative` | `live` -> `creative_ready` | Offer spec, live page, product files | Generate 3 to 5 ad creatives: product demo, screen recording or clearly scripted spokesperson. No testimonial formats | HyperFrames skills (run with `npx hyperframes`), HeyGen CLI and ffmpeg on the operator's Mac (verified 2026-11-16). Image and avatar generation tools are not chosen. The Sora API was shut down on 24 Sep 2026 and Veo left the Gemini API on 22 Oct 2026, so neither is an option | `claims_lint` on scripts and captions, file format and size check, AI-label flag present in the manifest for every asset with a synthetic person or voice, `checkout-verifier` review | `products/<id>/creatives/` plus `manifest.json` | `store-builder`, then `checkout-verifier` | Desktop task, on demand |
| 6 | `campaign-draft` | `creative_ready` -> `awaiting_human` (`F-ADS-1`) -> `campaign_drafted` | Approved `F-ADS-1` packet with caps, creative manifest | Create one campaign, one ad set and up to three ads, all PAUSED, with the approved daily budget. Read back and compare. Hand over to the operator to activate | Official Meta Ads MCP (`https://mcp.facebook.com/ads`, beta) or the `meta` CLI: `ads_create_campaign`, `ads_create_ad_set`, `ads_create_ad`, read tools. `ads_activate_entity` and `ads_update_entity` are denied | `tools/verify_campaign` (to be built) reads the entities back: status is PAUSED, daily budget equals the packet, destination URL equals the live page, entity count matches, write count for the day is within the limit | `state/campaigns/<id>.json` with entity ids and read-back | `ads-drafter` sub-agent, then `checkout-verifier` | Hand-triggered cloud session using the hosted MCP (the Mac is work-managed, so Desktop tasks are kept for video work). Never on a recurring schedule |
| 7 | `telemetry` | `campaign_drafted` -> `spend_test` when the operator has activated. `spend_test` -> `winner`, `iterating` or `killed`. `live` -> `killed` on window expiry | Processor, store, ad and analytics data | Pull orders, refunds, disputes, fees, payouts, ad spend, visits. Compute contribution margin. Apply kill and risk thresholds. Raise escalations | Stripe read-only restricted key, Shopify read scope, Meta read-only consent tier, PostHog connector | `tools/reconcile` (to be built): order count in metrics equals the processor's count, test orders excluded by tag, PostHog purchase events within 10% of processor charges, revenue lines each carry a processor reference | `state/metrics/<date>.json`, ledger lines | Main session | Cloud scheduled task, daily |
| 8 | `weekly-review` | No item transition. May open pull requests | Week of journal, ledger, metrics, checks, rejected packets | Find the largest waste or failure, propose at most three changes | Repo, GitHub | Each proposal has observation, hypothesis, single change, metric and review date, and touches no protected path (CI check) | `journal/reviews/<week>.md`, pull requests | Main session on Opus | Cloud scheduled task, weekly |

How this maps to the required loop: Input (1), Process (2, 3, 5, 6), QA (the deterministic check in every row, and stage 4 as a standing QA job), Output (the live page and the paused campaign), Telemetry (7), Self-improvement (8).

## 4. Transitions

```
(new)             -> discovered
discovered        -> specced | killed
specced           -> built | killed | awaiting_human
built             -> test_passed | built (retry, max 3) | killed
test_passed       -> awaiting_human [F-LIVE-1]
awaiting_human    -> live                 (F-LIVE-1 approved and operator's live purchase recorded)
live              -> creative_ready | killed | awaiting_human
creative_ready    -> awaiting_human [F-ADS-1]
awaiting_human    -> campaign_drafted     (F-ADS-1 approved, paused draft verified)
awaiting_human    -> live                 (F-ADS-1 rejected: product stays organic until its window ends)
campaign_drafted  -> spend_test           (telemetry reads the campaign as active: the operator switched it on)
campaign_drafted  -> live                 (not activated within 14 days)
spend_test        -> winner | iterating | killed | awaiting_human
iterating         -> specced              (price change: full rebuild and purchase check)
iterating         -> creative_ready       (creative change)
winner            -> awaiting_human [F-ADS-3] | killed
any non-terminal  -> awaiting_human       (any trigger in ESCALATION.md)
awaiting_human    -> the stage named in the packet | killed | parked
parked            -> the stage named in a newly approved packet | killed
any non-terminal  -> killed               (terminal, reason recorded)
```

No other transition is allowed. `iterating` may be entered at most twice per item. The third time the item is killed.

## 5. Kill criteria

All numbers are proposed defaults held in `budget.yaml`. None comes from a verified benchmark, because the research found none.

| Stage | Kill when |
|---|---|
| `discover` | Fewer than 3 independent demand signals with live sources. Category on the exclusion list (health, supplements, safety or children's safety products, anything needing a safety or efficacy claim, licensed characters or brands, regulated goods, physical goods shipped across a border). More than $1.50 of tokens and API per candidate |
| `offer-spec` | `digital`: price under $9, or contribution margin before ads under 70% of price. `pod`: contribution margin before ads under 40% of price or under $8 per order (break-even ROAS above 2.5). Any required claim fails `claims_lint` |
| `build-store` | Three failed builds, or more than $15 of tokens on one item's build |
| `purchase-check` | Not a kill stage. Three consecutive failures of the check on a pre-live item kill it. Any failure on a live item raises `F-PAY-1` |
| `live` (organic, zero spend) | 30 days with no verified order and no approved `F-ADS-1`. Item spend above $40 before its first verified order |
| `spend_test` | Ad spend reaches 2 times break-even CAC with zero orders. Total test cap reached with contribution margin after ad spend at or below zero. Refund rate at or above 10% with at least 10 orders. Any chargeback. The agent cannot pause a campaign, so each of these raises `F-ADS-2` asking the operator to pause, and the daily cap and account spending limit bound the loss meanwhile |
| `iterating` | Second iteration still fails the winner test |

Factory-level validation budget: **$400 all-in (tokens, APIs, infrastructure, fees) over 90 days from the first scheduled run**, excluding operator-approved ad tests, which have their own caps. If it is spent, or the window ends, with no verified revenue, the factory pauses and raises `BUD-2` for a keep-or-kill decision.

## 6. Telemetry

Sources of truth, in order:

1. Stripe balance transactions and payouts (`digital`), Shopify orders and payouts (`pod`). Read-only credentials.
2. The ad platform's billed spend. Insights figures are used for daily monitoring, the billing figure for the ledger.
3. POD provider invoices for COGS.
4. PostHog for visits and funnel steps. Never used for revenue.
5. `state/checks/` for payment-path health.

Revenue is payouts net of refunds, disputes and fees. Orders tagged as tests (the scheduled check and the operator's launch purchase) are excluded from every metric. Amounts are recorded in USD at the processor's settlement rate, with the original currency kept in the ledger line's `source`.

Metrics per product: verified orders, net revenue, refund rate, dispute count, COGS, ad spend, contribution margin per order and in total (before and after ad spend), CAC against target CAC, ROAS against break-even ROAS, purchase-check pass rate, tokens and API spend.

A **winner** is a product that, over its approved spend test, has all of: at least 10 verified non-test orders, total contribution margin after ad spend above zero, CAC at or below target CAC, refund rate under 10%, zero chargebacks, and purchase-check pass rate of 100% during the test. Revenue without positive contribution margin is not a win. The factory-level report also shows the result after tokens and tooling, and that is the number that decides whether the factory continues.

## 7. Self-improvement loop

The weekly review reads the week's run reports, ledger, metrics, check results and rejected escalation packets. It specifically examines:

- Which discovery signals preceded killed items and which preceded any item that got an order. The research found no evidence that tool-surfaced "winning products" beat chance, so this is the factory's own test of that.
- Gap between spec-stage unit economics and observed fees, refund rate and COGS.
- Every purchase-check failure and how long the path was dead before detection.
- Tokens per stage against `budget.yaml`, and any run where the report and the deterministic check disagreed.
- Reasons the operator rejected packets.

It may propose, as pull requests, at most three changes a week and one per skill: discovery scoring weights, exclusion-list additions, calculator assumptions (replacing assumed fees with observed ones), copy and creative templates, check coverage, seeds. It may not change `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, hooks, settings, the run wrapper or the purchase-check thresholds. Proposals for those are `GEN-2` escalations. Lessons go to `journal/LESSONS.md`, dated and evidence-linked, capped at 60 lines.

## 8. Tools and accounts

| Tool or account | Used for | Status |
|---|---|---|
| Claude Code cloud scheduled tasks, Desktop tasks, GitHub, GitHub Actions, Slack, Linear | Scheduling, approvals, CI | Already available (a repository still needs creating) |
| PostHog connector | Page analytics | Already available |
| Parallel Search connector | Discovery | Connector in the directory, not installed. Free MCP needs no account but rate-limits after roughly 8 to 10 quick calls. Search API $1 to $5 per 1,000 requests (verified 2026-11-16) |
| Firecrawl connector | Page content for discovery | One-click connector. Free tier 1,000 credits a month (verified 16 Nov 2026) |
| Stripe connector and account | Payment links, revenue truth | Connector is one click. A Stripe account under the operator's name is a new account (`F-ACCT-1`). Whether the connector can create Payment Links was not read: confirm at build time. Verified 2026-11-16: from December 2026 the Stripe MCP accepts only OAuth or a restricted key with the Agent tag (migrate by 30 Nov 2026). A read-only key is an agent-tagged restricted key with only Read permissions. Australian fees are 1.65% + A$0.30 on domestic cards and 3.5% + A$0.30 on international cards (2.8% from 1 April 2027), plus 2% if currency conversion is needed. The Stripe CLI is not installed on the operator's Mac |
| Cloudflare Pages | Landing pages | Connector in the directory, new account. Free tier: 500 builds a month, unlimited static requests, no commercial-use restriction found (verified 2026-11-16). Vercel Hobby is not a substitute: it is non-commercial only |
| Playwright | Purchase check | Microsoft's Playwright CLI and MCP are free and Apache-2.0 (verified 2026-11-16). Playwright is not on the operator's Mac. It is preinstalled with Chromium in the cloud session container, and the check itself runs in GitHub Actions. Whether Stripe's hosted checkout accepts scripted test purchases must be confirmed at build time |
| Test mailbox and transactional email sender | Delivery email and spam check | New account needed. No vendor researched. Sending domain setup (SPF, DKIM, DMARC) is a build task |
| Shopify store, Shopify CLI, Shopify AI Toolkit / Dev MCP | `pod` storefront | Verified 2026-11-16 on shopify.dev: the AI Toolkit and Dev MCP (`npx -y @shopify/dev-mcp@latest`) are official and free. The Dev MCP covers docs, schemas and validation only, and there is no Admin MCP. Store changes go through `shopify store execute`, which is read-only unless `--allow-mutations` is passed. Store is a new account: 3-day trial, then Basic at $39 a month ($29 billed yearly). Headless CLI auth is available (see stage 3) |
| POD provider (Printful, Printify, Gelato or other) | `pod` fulfilment | New account. Printful and Printify both have official APIs with scoped or personal tokens and no official MCP (verified 2026-11-16, MCP absence from a secondary source). Gelato was not re-checked. Community Printify MCP servers are not used |
| Meta Ads MCP and `meta` CLI | Paused campaign drafts, spend reads | Verified 2026-11-16 on Meta's developer docs: official, hosted at `mcp.facebook.com/ads`, open beta since 29 Apr 2026, free, no developer app needed. Campaigns are created paused, `ads_activate_entity` starts spend, and there is no delete. Needs the operator's Meta Business account (whether one exists is unknown). Post-beta pricing unannounced |
| Apify ad-library actors | Deeper discovery | New account. Actors seen by title only. Verified 2026-11-16: Free plan has $5 of usage a month, Starter is $19 a month, and there is an official MCP at `mcp.apify.com`. Cap each run with `maxTotalChargeUsd` |
| HyperFrames, HeyGen, ffmpeg | Creative | Verified 2026-11-16 on the operator's Mac: ffmpeg, HeyGen CLI v0.8.1 with credentials, and the HyperFrames skill suite (no `hyperframes` binary on PATH, use `npx hyperframes`) |
| Arcads, Creatify, MakeUGC and similar | Avatar video | Not used by default. Arcads puts its API on Pro and above only and does not publish dollar prices. Creatify API pricing and MakeUGC API access by plan are still unverified |
| Tax tooling (GST, sales tax, VAT) | Compliance | Escalation `F-TAX-1`. Verified 2026-11-16 (ATO): GST registration is required at $75,000 of GST turnover across all of the operator's businesses combined, and sales not connected with Australia are excluded. Stripe Managed Payments is a merchant-of-record option open to Australian businesses for digital products at 3.5% on top of processing, with Checkout and Payment Links only and an eligibility review |

## 9. Known failure modes and design response

| Failure in the research | Design response |
|---|---|
| Agent reported "all clear" while the payment path was dead | Stage 4 is a script with no model in it. It runs daily on every live product and hourly during a spend test. A test-mode pass does not prove the live path, so the operator makes one real purchase at launch and after any payment-path change |
| Expired tokens for about a week | The check calls a read endpoint with every credential daily and fails loudly. Expiry dates are tracked in `state/credentials.md` (names and dates only, no secrets) and escalated 14 days ahead |
| Delivery email in spam by day five | The check asserts the email reached the inbox, not spam. Delivery never depends on email alone: the post-payment page gives the download |
| Agent counted its own test checkout as traction | Test orders carry a tag and are excluded by `tools/reconcile`. Revenue lines need a processor reference |
| Agent over-read tiny samples | Winner needs at least 10 verified orders. Below that the report says "insufficient data" |
| Scheduled runs that did not fire | The telemetry run records the last run time of every stage. A stage more than two intervals late is reported and escalated after the second miss |
| Paid test never approved, loop stalled | The product has a 30-day organic window, then is killed. The factory does not wait indefinitely |
| Ad account banned after agent writes (anecdotal) | Official MCP only. One hand-triggered write session per account per day, at most 5 writes, no retries, no edits after creation. Activation and budget changes are the operator's |
| Frequent edits reset the learning phase | No edits by the agent at all during a test. Changes go through `iterating` as a new approved draft |
| Unlabelled AI creative, health claims | `claims_lint`, AI-label flag in the manifest, verifier review, exclusion list |
| Fake testimonials (FTC rule 16 CFR Part 465, up to $53,088 per violation, verified on FTC pages 2026-11-16; the ACCC treats fake or misleading reviews as unlawful too) | No reviews, ratings or first-person customer statements are generated, ever. Lint blocks the patterns |
| Payout holds at low chargeback rates (forum headlines only) | Any dispute escalates. Refund and dispute thresholds freeze launches. Ad spend is never funded from expected receipts |
| Memory loss across runs | All state in files. One run does one stage |
| Etsy's 22 Oct 2026 policy prohibits bot-generated or mass-automated listings, and requires an original design and a disclosed production partner for print on demand (verified 2026-11-16) | No marketplace listings in scope. Adding one is `F-SCOPE-1`, and agent-created Etsy listings are not available even then. The only Etsy option is one where the operator prompts, curates and publishes every listing (see the Etsy and Fiverr section of `RESEARCH_REPORT.md`) |
| Copied or trademarked designs | `pod` designs are original, screened, and seen by the operator in the `F-LIVE-1` packet before going live |
