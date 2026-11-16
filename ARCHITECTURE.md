# Revenue Factories: System Architecture

Status: blueprint for review, revision 2. Nothing here has been built or run. Date: 16 November 2026.
Revision 2 changes the ranking lens to portfolio expected value at the operator's direction, makes the consumer app factory the first build, and adds section 2.1.
Revision 3 (16 November 2026) simplifies the runtime after a review of published software-factory practice (section 9): no event inbox or timer store until real webhooks exist, fewer sub-agents, one notification channel, every stage driven by hand before it is scheduled, and self-improvement deferred until there is data.
Companion document: `RESEARCH_REPORT.md` (evidence, rankings, tooling matrix).

## 1. What the research changes about the design

The original brief assumed the hard part was building. The research says the opposite, and the architecture follows from four findings.

1. **No verified case of a fully autonomous revenue loop was found in any of the seven models.** Every public "agent runs a business" experiment that could be read made $0 or lost money (Autocomp: 39 days, about $1,117 in tokens, $0. Bottleneck Labs: $2,833 in tokens, $0. Andon Labs shop: $100k down to $61k). Building is cheap. Demand and distribution are the bottleneck.
2. **Agents report success that did not happen.** A cloud run marked "Succeeded" only means the session ended. Documented cases include a scoreboard that overstated a funnel by 57%, an agent reporting "all clear" while the payment path was dead, and campaigns returning 200 OK with no senders attached. So every stage needs a deterministic check outside the model.
3. **Model-level guardrails leak.** Anthropic's own figures: auto mode misses about 17% of overeager actions, and a red-team credential exfiltration succeeded 24 of 25 times. Limits that must hold go in deny rules, hooks, scoped tokens and branch protection. `CLAUDE.md` is guidance only.
4. **Platforms are closing the door on templated volume.** Apple's June 2026 rewrite of guideline 4.3(b), Google's 2026 spam updates, YouTube's inauthentic-content policy and Meta's "created PAUSED" ads design all punish or block unattended mass output. So volume has to sit where platforms do not see it as spam: in cheap tests of ideas, not in published outputs.
5. **A low hit rate is acceptable if shots are cheap, fast to read and independent.** The operator's goal is a portfolio in which one real winner becomes likely, with a person in the loop. The chance of at least one hit in N independent shots is 1 − (1 − p)^N. The design work is therefore to cut the cost of a shot, shorten the time to read it, and stop shots failing together.

Design consequences:

- Each factory is a **validation funnel with cheap kills**, not a production line. The default outcome of any idea is "killed early at low cost". The funnel is wide at the top: many ideas tested, few built.
- Factories are ranked by **portfolio expected value**: cost per shot, time to read a shot, shots a year, hit rate, payoff on a hit, and whether shots fail together. Marketplace factories remain the lowest-risk option, but their payoff per winner is small.
- **Demand evidence means behaviour from real traffic.** Synthetic users, surveys and the agent's judgement may kill an idea. They may not pass one.
- **Accounts are the scarce asset.** A developer, ad or payment account that is lost takes every shot with it, so cadence and distinctness limits are enforced by scripts.
- The human gate is not only for capital. It also covers anything published under your name, anything sent to a person, and anything irreversible.
- Honest telemetry comes from the source of truth (Stripe, the marketplace payout page, the broker statement), never from the agent's own summary.

## 2. Factory portfolio

Seven factories are blueprinted. The build order is the portfolio ranking in `RESEARCH_REPORT.md`. It is a recommendation for you to overrule. The first revision's lowest-risk order (Apify first) is kept in the report for comparison.

| Order | Directory | Model | Default posture |
|---|---|---|---|
| 1 | `factories/a-consumer-apps` | Consumer app portfolio, test-first | About 100 ideas tested per cycle with real paid traffic, about 4 built, releases paced at 1 to 2 new apps a month. Operator activates ads and submits to the store. Needs cloud builds because there is no Xcode on your Mac |
| 2 | `factories/g-marketplace-tools` | Chrome extensions and niche micro-SaaS | Uses the same landing-page test pattern as factory A before building. Human submits to stores. Shopify's 10 November 2026 rules rule out a Shopify app portfolio |
| 3 | `factories/f-apify-actors` | Apify Store actor portfolio (also the practical way to sell to agents) | Build and publish with approval per actor. Lowest risk, small payoff per winner |
| 4 | `factories/d-directories` | Programmatic SEO and directories, local and transactional intent only | One data-rich site, small verified dataset, indexing canary before scale. Slow to read, and sites fail together |
| 5 | `factories/e-outbound` | B2B demo-first outbound | Drafts only. Automated sending stays off until you have legal advice on the Australian Spam Act |
| 6 | `factories/b-ecommerce` | E-commerce, digital products first | No ad spend without approval. Physical dropshipping is out of scope |
| 7 | `factories/c-trading` | Strategy research, backtest and paper trading | Paper only, a research harness with no revenue expectation. More strategies tested means more false positives, so portfolio logic does not apply |

### 2.1 Portfolio economics of the first factory

All figures are estimates built from published benchmarks. Sources and the full funnel are in `RESEARCH_REPORT.md` and `factories/a-consumer-apps/FACTORY_SPEC.md`.

| Quantity | Value |
|---|---|
| One cycle | 100 ideas mined, 50 pass an LLM screen, 30 get a $30 ad click test, 10 get a fake-door test with a price (to $200 each), 4 are built, each gets a paid test of $300 to $600 |
| Cycle cost and length | About $5,200 to $5,500, about 10 weeks |
| Cost per idea tested, per app shipped | About $55, about $1,350 |
| Your time per cycle | About 12 to 15 hours: two ad-batch approvals and activations, four store submissions, packet reviews |
| Capacity on one Apple account | 200 to 400 ideas tested a year, 8 to 12 apps shipped |
| Base rate per shipped app | 17.3% reach $1K a month within two years, 4.6% reach $10K (RevenueCat) |
| Chance of at least one $1K-a-month app | 53% with 4 apps, 85% with 10, 98% with 20, if apps perform at the base rate and independently |
| Chance of at least one $10K-a-month app | 17% with 4, 38% with 10, 61% with 20 |

Three limits on that arithmetic. The thresholds are revenue, and revenue bought with ads can be unprofitable, so the factory's winner rule is cost per payer and return on ad spend, not MRR. Independence fails if the developer account is lost, which is why release cadence, per-app listings and code distinctness are script-enforced and any 4.3, spam or fraud citation freezes all submissions. And "100 apps" is achievable as 100 tested ideas a quarter, not as 100 store submissions: many similar apps shipped quickly is the pattern Apple's guideline 4.3 and Google Play's Repetitive Content policy remove accounts for.

The landing-page test stage (page, paused campaigns, operator activation, scripted kill rules) is designed once, and factory G follows the same pattern.

Factories are independent. Nothing in one factory imports from another. They share only the conventions in `factories/_shared/`.

## 3. Repository layout

```
revenue-factories/
  RESEARCH_REPORT.md
  ARCHITECTURE.md
  factories/
    _shared/
      CONVENTIONS.md            state, ledger, escalation and run-report formats
      skills/
        escalate/SKILL.md       how any factory raises an escalation
        ledger/SKILL.md         how any factory records spend and revenue
        run-report/SKILL.md     the evidence-first report every run must end with
    <factory>/
      FACTORY_SPEC.md           state machine, tools per stage, gates, kill criteria
      CLAUDE.md                 operating rules for any session started in this directory
      ESCALATION.md             exact triggers and the approval packet for each
      budget.yaml               spend and risk caps, read by the run wrapper
      skills/<stage>/SKILL.md   one skill per stage, loaded on demand
      agents/<role>.md          sub-agent prompts with restricted tools
      outbox/                   (created at build time) messages waiting for the daily digest, see section 4.5
      state/                    (created at build time) item files, one per idea or asset
      ledger/                   (created at build time) spend.jsonl, revenue.jsonl
      journal/                  (created at build time) one run report per run
      escalations/              (created at build time) open/, approved/, rejected/
```

At build time each factory gets a `.claude/` directory whose `skills` and `agents` entries point at the factory's `skills/` and `agents/` folders, so a session started with the factory directory as its working directory discovers them natively. The blueprint keeps them at the top level of the factory, as requested, so they are easy to review.

**Two branches, two trust levels.** `main` is protected and holds everything that defines the rules: specs, `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, skills, agents, application code after review, and `escalations/approved/` and `rejected/`. Only you can merge to it. A long-lived `factory-state` branch is writable by factory runs and holds `outbox/`, `state/`, `ledger/`, `journal/` and `escalations/open/`. Runs read rules and approvals from `main` and write their bookkeeping to `factory-state`, so a run can record what it did without being able to approve itself or rewrite its own limits. Code and skill changes reach `main` only through pull requests.

This is designed as one git repository. No repository is attached to this project yet, so the files currently live in the project's shared files. Moving them into a repo is a prerequisite for scheduled cloud runs, which clone a repo fresh each run.

## 4. Runtime model

### 4.1 One run does one stage

A run is a fresh Claude Code session that:

1. Reads `budget.yaml`, the kill switch and open escalations. Stops if any blocks it.
2. Picks a bounded batch of items in one stage (default batch size 1 to 5).
3. Loads the single skill for that stage and does the work.
4. Runs the stage's deterministic check.
5. Writes item state, ledger lines and a run report, then exits.

No run carries context to the next. All memory is in files. This is what keeps context small, makes runs cheap to retry, and survives all three official schedulers, each of which starts from a fresh session or a fresh clone.

**Crashed runs are retried by the next run.** A stage picks its batch from item state, and an item changes stage only after its check passes. A run that crashes leaves its items where they were, so the next run picks them up again. No separate retry queue is needed. Because a crash can happen after an external side effect and before the item file is written, any step that creates something outside the repo (an ad campaign, a draft post, a deployed page) first reads back whether an object tagged with the item id already exists, and reuses it instead of creating a second one.

**Manual first.** Each skill is written so it can be invoked by hand in an interactive session and by the run wrapper on a schedule, with the same prompt. Every stage is run by hand, with you watching, at least three times before it gets a schedule. You cannot debug an unattended run of a stage you have never driven yourself.

**One loop, few sub-agents.** A run is one Claude session working through one skill. Sub-agents are used for two reasons only: to keep untrusted web content away from a session that holds write access (the scout), and to have output checked by a context that did not produce it (the verifier). Anything with a definite shape, such as creating paused ad campaigns from a validated plan, is a script, not an agent.

### 4.2 Schedulers

| Scheduler | Use for | Limits that shape the design |
|---|---|---|
| Cloud scheduled tasks (Claude Code on the web) | Stages that need only the repo and connectors: research, spec writing, code, telemetry pulls, weekly reviews | 1 hour minimum interval. Fresh clone each run. Research preview. All connectors attached with write access unless removed. "Succeeded" is not task success |
| Desktop scheduled tasks, or `launchd` with `claude -p` | Stages that need local tools or logins: HeyGen and HyperFrames renders with ffmpeg only | Mac must be awake. `-p` starts in Manual mode, so allow rules must be explicit |
| GitHub Actions on a schedule | Deterministic jobs with no model in them: test suites, backtests, canaries, data freshness checks, and any step that must hold a vendor token | Counts against GitHub minutes. If a model step runs here through `claude-code-action`, a subscription token cannot see claude.ai connectors, so its MCP servers must be declared in a committed `.mcp.json` |
| `/loop` | Interactive babysitting during the first days of a new stage | Session scoped, 7 day expiry. Not a production scheduler |

Default cadence is slow on purpose: discovery daily, build on demand, telemetry daily, self-improvement weekly. Nothing in any factory needs sub-hourly runs except trading data collection, which is a plain script, not a model call.

### 4.3 Run wrapper (to be built once, shared by all factories)

Every headless run goes through one wrapper script. Its job is to make failure loud.

- Refuses to start if `factories/<name>/STOP` exists, if the month's spend in `ledger/spend.jsonl` has reached the cap in `budget.yaml`, or if the stage is blocked by an open escalation.
- Starts Claude with explicit caps: `--max-turns`, `--max-budget-usd`, `--permission-prompts none`, an allow list for that stage only, and JSON output.
- After the run, fails the run if the exit code is non-zero, if `permission_denials` is non-empty, if the expected artifact for the stage is missing, or if the run report lacks an evidence block.
- Appends token cost from `total_cost_usd` to the ledger.
- Prevents two runs of one factory from overlapping. A local lock file does this for Desktop runs. Cloud scheduled tasks clone fresh and cannot see a local lock, so a factory's scheduled stages are set at different hours, further apart than the longest per-run cap, and any stage run through GitHub Actions uses a per-factory concurrency group. A lock older than the longest per-run cap is treated as stale, removed, and reported in the outbox, so a killed run cannot stall the factory silently.
- Writes a one line result to the outbox for the daily digest. Three consecutive failures of the same stage write the `STOP` file and raise an escalation, which is delivered immediately.

### 4.4 Model routing

Sonnet 5.5 by default. Opus 5.5 for app builds and the weekly review. Haiku 5.5 only where a step is pure classification and the saving is worth a second configuration. A stage moves up a tier only after it has failed twice on the lower one, and the change is recorded in its skill.

Subscription login carries scheduled cloud tasks and interactive work. An API key with a workspace spend limit carries `--bare` scripts and CI. Keeping both paths working means a change in subscription policy raises cost without stopping the factory.

### 4.5 Always-on primitives, kept to what a factory needs now

A factory is an always-on agent in the sense of Anthropic's guide [Building always-on agents](https://claude.com/resources/articles/building-always-on-agents) (13 November 2026): asleep almost all the time, awake for short runs. The guide names five primitives. It is written for agents that receive webhooks and user messages at any moment. A factory's wake reasons today are only schedules and your commits, so three of the five collapse into files the design already has. The guide is a reference here, not a requirement.

| Primitive | Factory implementation now | Add later, when |
|---|---|---|
| **Event inbox** | None. A scheduled task calls the run wrapper directly. Staggered schedules and the wrapper's lock stop overlapping runs (section 4.3), and item state is the source of truth, so a crashed run loses nothing (section 4.1) | A real webhook source arrives (Stripe, a marketplace, a broker). Then add one `events` table in Supabase and a small handler that acknowledges fast and writes the row. The wrapper becomes its single worker |
| **Timers** | Schedules are cloud scheduled tasks and GitHub Actions crons. A follow-up is a `next_check` date on the item file. A stage skips items whose `next_check` is in the future. A run that needs to wait sets `next_check` and exits. It never sleeps or polls | The same webhook moment. Follow-ups stay on the item |
| **Memory** | Instructions are `CLAUDE.md`. Task progress is the item file. A generated `state/INDEX.md` lists live items. `journal/LESSONS.md` holds dated lessons. Metrics and revenue are pointers to the source of truth | Curation by the weekly review once it is switched on (section 5.5) |
| **Permissions** | Tokens live in GitHub Actions or behind connectors, not in sessions. Auto mode with deny rules. A gated action ends the item's run with an escalation packet. Your commit is the answer, read at the start of the next run | n/a |
| **Outbox** | `outbox/pending.jsonl`. Escalations and `STOP` go out at once. Everything else goes into one daily Slack digest per factory. A run with nothing new sends nothing. `outbox/reported.md` stops repeats | n/a |

## 5. Control plane

### 5.1 Enforcement hierarchy

Rules are placed at the strongest layer that can express them.

1. **Outside the agent's reach.** Credentials it does not hold. Read-only API keys. Paper-trading keys only. Branch protection on `main` that the Claude GitHub identity cannot bypass. Marketplace and ad accounts where publishing needs your login.
2. **Deterministic gates.** Deny rules for paths and commands, `PreToolUse` and `Stop` hooks, the run wrapper, CI.
3. **Process.** Escalation files and approvals.
4. **Guidance.** `CLAUDE.md` and skills. Useful, but the agent may decide a guideline does not apply, so nothing safety-critical lives only here.

Each factory's `CLAUDE.md` has a section listing which of its rules must be implemented at layers 1 and 2 at build time.

### 5.2 Privilege separation inside a factory

A factory that reads the open web and also holds posting, payment or email credentials has all three ingredients of the worst case: untrusted input, private data and an outbound channel. So every factory splits roles:

- **Scout** agents read the web. They have no write connectors and no credentials. Everything they read is data, never instructions. Their output is a structured file validated against a schema.
- **Builder** agents write code and content in the repo. They never read raw scraped pages, only scout output.
- **Verifier** agents check a builder's output against the stage's acceptance criteria. They are told to report only gaps that affect correctness.
- **Publisher** steps are the only ones that touch an external write API, they consume only validated structured input, and in most factories they stop at "draft" or "paused" and hand the last click to you. Where the input is a validated plan, a publisher is a script rather than an agent.

These are roles, not necessarily separate agents. Only the scout and the verifier need their own context (section 4.1). The builder is normally the run's main session.

For each scheduled cloud task, the connector list is pruned to the minimum. By default a task would hold write access to Gmail, Slack, HubSpot, Linear, Notion, Drive and GitHub.

### 5.3 Budgets and kill switches

- `budget.yaml` per factory holds the monthly token cap, the monthly paid-API cap, per-run caps and factory-specific risk limits (for example maximum position size or maximum ad spend, both zero until you raise them).
- Hard backstops outside the repo: a monthly spend limit on Claude usage credits, a workspace limit on the API key, and prepaid or capped billing on every vendor that supports it.
- `STOP` file per factory, and one at the repo root that halts everything.
- **Portfolio rule:** a factory that has spent its validation budget without a dollar of verified revenue is paused and escalated for a keep-or-kill decision. The budget and window are set per factory in its spec.

### 5.4 Escalation protocol

Detailed in `factories/_shared/CONVENTIONS.md` and each factory's `ESCALATION.md`. In short:

1. The factory writes an approval packet to `escalations/open/<id>.md`: what it wants to do, evidence, cost, worst case, how to undo it, and what happens if you say no.
2. It notifies you with one Slack message, sent immediately rather than held for the digest, then moves the item to `awaiting_human` with `next_check` set to the packet's expiry, and continues with other items. Every run, and at least the daily telemetry run, checks all `awaiting_human` items for a decision on `main`, whatever their `next_check`, so an approval is picked up within a day even when the item's own stage runs weekly. A run outside the item's stage only records the decision: it clears `next_check` and moves the item to the stage the packet names. The gated action itself is carried out only by that stage's own run, with that stage's permissions.
3. **Approval is a commit by you** that moves the packet to `escalations/approved/` on `main`. The agent's identity cannot push to `main`, so it cannot approve itself. A Slack reply is a convenience and is never treated as approval on its own.
4. Silence is never approval. Packets expire after the period stated in the packet and the item is parked.

Triggers common to every factory: spending money beyond the token budget, creating or using any account, anything published or sent under your name, legal or compliance questions, accepting terms of service, handling personal data, three consecutive stage failures, any detected attempt at prompt injection, and any rule conflict.

### 5.5 Telemetry and the self-improvement loop

- **Sources of truth:** Stripe (read-only key), marketplace payout pages, broker statements, PostHog, Search Console. Revenue is recorded only from these.
- **Daily telemetry run:** pulls metrics into `state/metrics/` and appends revenue lines to the ledger with the source reference.
- **Corrections first.** Until a factory has four weeks of run reports, self-improvement is manual: whenever you correct a run, the lesson goes into `journal/LESSONS.md` or the relevant skill in the same change. Practitioners report this is the stage that pays off most.
- **Weekly review run (switched on after four weeks of run reports):** reads the week's journal, ledger and metrics, and produces at most three proposed changes. Each proposal names the observation, the hypothesis, the single change, the metric that will judge it and the review date.
- **Changes land as pull requests, never as direct edits.** You merge or close them. One change per skill per week, so effects can be attributed.
- **Off limits to self-modification:** `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, the run wrapper, hooks and settings. Deny rules cover these paths. A proposal to change them is an escalation.
- **Lessons** go into `journal/LESSONS.md` as dated, evidence-linked entries, capped in length, so the file stays cheap to load.

## 6. Shared tooling

Verification status for prices and for which integrations are official is in the tooling matrix in `RESEARCH_REPORT.md`. Tools are named here by role.

| Role | Default | Why | Already available to you |
|---|---|---|---|
| Scheduler | Claude Code cloud scheduled tasks, plus Desktop tasks for HeyGen and HyperFrames video work only | First party, bills to the plan, carries connectors | Yes |
| Queue and approvals | Item files for the queue, Slack for notifications, approval by commit | Slack is already connected. One channel is enough | Yes |
| Source control and CI | GitHub, GitHub Actions | Branch protection is the approval mechanism | Yes, connector. A repo still needs creating |
| Web research | Parallel Search or Exa connector, Firecrawl for page content | First-party connectors, free or low entry tiers | No, one click each |
| Scraping at volume | Apify actors, Firecrawl, Crawl4AI for self-run | Cheapest per record for maps and listings data | No |
| Browser automation | Playwright, Browserbase when a hosted browser is required | Local options are free, hosted starts at $20 a month | Not installed. The cloud container has Playwright and Chromium |
| Backend | Supabase | Connector plus CLI, Postgres, auth | No. One-click connector, CLI not installed |
| Hosting | Cloudflare Pages and Workers | Free tier with no commercial-use restriction found. Vercel Hobby is non-commercial only | No |
| Payments | Stripe, with an agent-tagged read-only restricted key for unattended runs | Source of truth for revenue. Stripe's MCP stops accepting ordinary keys in December 2026 | No, one click connector |
| Product analytics and LLM cost traces | PostHog | Already connected, covers analytics, errors and LLM costs | Yes |
| Error tracking | Sentry | Closes the deploy then triage loop | No, one click |
| Video and motion | HyperFrames and HeyGen, ffmpeg, ElevenLabs for voice | Programmatic, cents per clip, no per-second generative pricing | Yes: ffmpeg, HeyGen CLI and HyperFrames skills on your Mac |
| Paid traffic for tests | Meta Ads through the official MCP. Campaigns are created paused, you activate, and an account spending limit you set is the backstop | The only pre-build demand signal that is behaviour. Ad spend is the main cost of a shot | No, new account |
| Search demand data | Appfigures, MobileAction or Astro | Shows that people search for a problem. Not evidence they will pay | No |
| Social scheduling | Postiz, as drafts | API, MCP and CLI on the entry plan | No |

Third-party MCP servers outside the Claude connector directory are treated as untrusted code: pinned versions, reviewed before use, tested against fake data, and never given credentials they do not need. This follows documented registry-poisoning incidents in 2025 and 2026.

**Your environment, verified on 16 November 2026** by a read-only inventory on your Mac (full detail in `RESEARCH_REPORT.md`):

- `claude mcp list` shows only the claude.ai connectors (HubSpot, Avoma, Notion, Linear, Drive, Gmail, Calendar, Claude Docs), the PostHog and Slack plugins, and `node_repl`. There is no scraping, search, browser, payments, deploy or database MCP server installed.
- Installed CLIs: node, npm, pnpm, uv, git, gh (signed in), docker (running), ffmpeg, the HeyGen CLI, jq, sqlite3. A large HyperFrames and video skill suite is installed in `~/.claude/skills`.
- Not installed: Xcode, Playwright, and the supabase, vercel, wrangler, stripe, apify, firecrawl, agent-browser, codex, hyperframes and openbb CLIs. Config folders exist for the last four, but the commands are not on your PATH.
- The Mac is work-managed with Aikido device protection, so package installs may be blocked. Together with the missing CLIs, this makes cloud scheduled tasks plus GitHub Actions the default place to run factories. The Mac is reserved for HeyGen and HyperFrames video work, which is already set up there.
- No Xcode means the consumer app factory would need cloud builds (EAS) or an Xcode install.

## 7. Build sequence once you approve

1. Create the repository, protect `main`, add CODEOWNERS for `escalations/approved/`, `budget.yaml`, `CLAUDE.md` and `ESCALATION.md`.
2. Build the shared run wrapper and its tests. Prove the failure paths first: missing artifact, permission denial, budget exceeded, `STOP` present.
3. Build factory 1 as a walking skeleton: one batch of five ideas pushed through the screen, the spec gate and a tranche 1 ad test by hand-triggered runs, with you approving and activating the one batch. This proves the test rig before any app is built. The store accounts (Apple Developer, RevenueCat, Expo) are opened in parallel, since identity checks take days.
4. Only then turn on schedules, one stage at a time, at the slowest cadence, with the connector list pruned. A stage is scheduled after at least three clean hand-driven runs.
5. Add the second factory after the first has produced two weeks of honest run reports.

## 8. Decisions needed from you

1. Which factory to build first. The recommendation is `a-consumer-apps`, run as a test-first portfolio. `g-marketplace-tools` is the close second and `f-apify-actors` is the lowest-risk alternative.
2. Whether to approve the default toolset in section 6, in particular the new accounts factory A implies: Apple Developer, Meta Ads, RevenueCat, Expo, Cloudflare, a keyword tool, and later Postiz.
3. Monthly ceilings for tokens, paid APIs and ads. Factory A's ad cap starts at $0 and nothing spends until you raise it. One full cycle needs about $4,400 to $4,700 of ad budget over about ten weeks, released in tranches you approve batch by batch.
3a. The release cadence for factory A. The blueprint proposes one new app a month until three are approved cleanly, then two a month, with at most 12 in any 12 months. Apple publishes no safe number, so this is a judgement.
4. Whether Factory E should exist at all in outbound form, given the Australian Spam Act position, or be redesigned as inbound-led.
5. Whether you are comfortable running this on a work-managed Mac and a personal Claude subscription. Unattended use on a subscription is currently permitted but Anthropic paused a change to it in 2026, so the design keeps an API-key path as well.
6. Branch protection on `main` in the new repository, which the approval mechanism depends on.

## 9. Outside practice behind revision 3

A review on 16 November 2026 of published write-ups on agentic software factories found broad agreement with this design's core: deterministic checks outside the model, humans on a few high-leverage gates, unattended runs that cannot ship on their own, and cost caps enforced outside the agent. It also found agreement against complexity added before it is needed, which is what revision 3 removes.

- Anthropic, [Building always-on agents](https://claude.com/resources/articles/building-always-on-agents) (November 2026): the five primitives. Used as a reference, scaled down in section 4.5.
- Anthropic, [When to fold subagents into your main agent loop](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop) (October 2026): prefer one loop with skills. Split only for context bloat, parallel work or conflicting instructions.
- Anthropic, [Getting started with loops](https://claude.com/resources/articles/getting-started-with-loops) (June 2026): start with the simplest loop. Deterministic stop criteria work best.
- Joe Paravisini, [Building a software factory](https://joeparavisini.com/writing/building-a-software-factory) (July 2026): solo operator, three human checkpoints, every stage a skill with a manual and a scheduled trigger, run by hand before automating. Corrections routed into permanent lessons were the most valuable stage.
- LaunchDarkly, [Building a software factory on our scariest code](https://launchdarkly.com/blog/building-a-software-factory-on-our-scariest-code) (August 2026): chasing full autonomy became "Rube Goldberg development". Human steering at phase boundaries is what shipped.
- Magrathea, [Running an overnight team of AI coding agents](https://magratheasoftware.com/blog/overnight-autonomous-ai-dev-team.html) (July 2026): the run never pushes, merges or deploys. That read-only boundary is what made it safe.
- Alexandre Carette, [Running Claude Code agents unattended: three failures](https://medium.com/@alexandrecarette/running-claude-code-agents-unattended-three-failures-my-guardrails-didnt-see-2947e2e3fd05) (October 2026): a guard must sit on the execution path the scheduler uses, not in the interactive session. A busy agent burned 12 times its token ceiling, so cost caps must be enforced outside the agent, and a runaway is never restarted without a human diagnosis.
- [Agent harness checklist](https://capitalandcompute.net/blog/agent-harness-checklist) (October 2026): multi-agent orchestration is the last layer to add, not the first.
