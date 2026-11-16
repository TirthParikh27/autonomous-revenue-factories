# Revenue Factories: System Architecture

Status: blueprint for review. Nothing here has been built or run. Date: 16 November 2026.
Companion document: `RESEARCH_REPORT.md` (evidence, rankings, tooling matrix).

## 1. What the research changes about the design

The original brief assumed the hard part was building. The research says the opposite, and the architecture follows from four findings.

1. **No verified case of a fully autonomous revenue loop was found in any of the seven models.** Every public "agent runs a business" experiment that could be read made $0 or lost money (Autocomp: 39 days, about $1,117 in tokens, $0. Bottleneck Labs: $2,833 in tokens, $0. Andon Labs shop: $100k down to $61k). Building is cheap. Demand and distribution are the bottleneck.
2. **Agents report success that did not happen.** A cloud run marked "Succeeded" only means the session ended. Documented cases include a scoreboard that overstated a funnel by 57%, an agent reporting "all clear" while the payment path was dead, and campaigns returning 200 OK with no senders attached. So every stage needs a deterministic check outside the model.
3. **Model-level guardrails leak.** Anthropic's own figures: auto mode misses about 17% of overeager actions, and a red-team credential exfiltration succeeded 24 of 25 times. Limits that must hold go in deny rules, hooks, scoped tokens and branch protection. `CLAUDE.md` is guidance only.
4. **Platforms are closing the door on templated volume.** Apple's June 2026 rewrite of guideline 4.3(b), Google's 2026 spam updates, YouTube's inauthentic-content policy and Meta's "created PAUSED" ads design all punish or block unattended mass output. Factories therefore optimise for a small number of validated outputs, not throughput.

Design consequences:

- Each factory is a **validation funnel with cheap kills**, not a production line. The default outcome of any idea is "killed early at low cost".
- Factories that sell into **existing marketplace demand** (Apify Store, Chrome Web Store, Shopify App Store) are preferred over factories that must create their own traffic.
- The human gate is not only for capital. It also covers anything published under your name, anything sent to a person, and anything irreversible.
- Honest telemetry comes from the source of truth (Stripe, the marketplace payout page, the broker statement), never from the agent's own summary.

## 2. Factory portfolio

Seven factories are blueprinted. The build order is the one in `RESEARCH_REPORT.md`, which weights evidence quality first, then capital at risk, then platform and legal exposure. It is a recommendation for you to overrule.

| Order | Directory | Model | Default posture |
|---|---|---|---|
| 1 | `factories/f-apify-actors` | Apify Store actor portfolio (also the practical way to sell to agents) | Build and publish with approval per actor |
| 2 | `factories/g-marketplace-tools` | Chrome extensions and niche micro-tools sold through marketplaces | Build freely, human submits to stores. Shopify's 10 November 2026 rules rule out a Shopify app portfolio |
| 3 | `factories/a-consumer-apps` | Consumer apps with short-form video distribution | A few distinct apps on one account, human publishes. Needs cloud builds because there is no Xcode on your Mac |
| 4 | `factories/d-directories` | Programmatic SEO and directories, local and transactional intent only | One data-rich site, small verified dataset, indexing canary before scale |
| 5 | `factories/e-outbound` | B2B demo-first outbound | Drafts only. Automated sending stays off until you have legal advice on the Australian Spam Act |
| 6 | `factories/c-trading` | Strategy research, backtest and paper trading | Paper only, a research harness with no revenue expectation. Live capital is a separate, explicit gate |
| 7 | `factories/b-ecommerce` | E-commerce, digital products first | No ad spend without approval. Physical dropshipping is out of scope |

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
      inbox/, timers/, outbox/  (created at build time) events, follow-ups and pending messages, see section 4.5
      state/                    (created at build time) item files, one per idea or asset
      ledger/                   (created at build time) spend.jsonl, revenue.jsonl
      journal/                  (created at build time) one run report per run
      escalations/              (created at build time) open/, approved/, rejected/
```

At build time each factory gets a `.claude/` directory whose `skills` and `agents` entries point at the factory's `skills/` and `agents/` folders, so a session started with the factory directory as its working directory discovers them natively. The blueprint keeps them at the top level of the factory, as requested, so they are easy to review.

**Two branches, two trust levels.** `main` is protected and holds everything that defines the rules: specs, `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, skills, agents, application code after review, and `escalations/approved/` and `rejected/`. Only you can merge to it. A long-lived `factory-state` branch is writable by factory runs and holds `inbox/`, `timers/`, `outbox/`, `state/`, `ledger/`, `journal/` and `escalations/open/`. Runs read rules and approvals from `main` and write their bookkeeping to `factory-state`, so a run can record what it did without being able to approve itself or rewrite its own limits. Code and skill changes reach `main` only through pull requests.

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
- Acts as the single worker for the factory's event inbox and as the outbox dispatcher (section 4.5): it takes the factory lock, batches pending events, and marks them done only after the checks above pass.
- Writes a one line result to the outbox for the daily digest. Three consecutive failures of the same stage write the `STOP` file and raise an escalation, which is delivered immediately.

### 4.4 Model routing

| Work | Model tier | Reason |
|---|---|---|
| Triage, classification, dedupe, log summarising | Haiku 5.5 | $0.10 / $0.50 per million tokens |
| Stage work: research synthesis, specs, copy, most code | Sonnet 5.5 | $2 / $10 |
| Hard builds, architecture, weekly self-review | Opus 5.5 | $4 / $20 |
| Reserved for cases where the above failed twice | Fable 5.2 | $8 / $40 |

Subscription login carries scheduled cloud tasks and interactive work. An API key with a workspace spend limit carries `--bare` scripts and CI. Keeping both paths working means a change in subscription policy raises cost without stopping the factory.

### 4.5 Always-on primitives

A factory is an always-on agent in the sense of Anthropic's guide [Building always-on agents](https://claude.com/resources/articles/building-always-on-agents) (13 November 2026): it is asleep almost all the time and wakes for short runs. That guide names five primitives around the agent loop. Each one maps to a concrete part of this design, and three of them tighten what the first draft had.

| Primitive | What the guide says | How a factory implements it |
|---|---|---|
| **Event inbox** | Sources never call the agent directly. They append to a durable list, and a single worker pulls from it. The inbox is the source of truth, events are deduplicated by source id, one active worker at a time, pending events are batched into one run | `inbox/events.jsonl` on the `factory-state` branch. Every wake reason is an event with an id: a schedule tick, a due follow-up, an approval or rejection commit, a CI result, a payout or webhook notification. The run wrapper is the worker. It takes a per-factory lock (a GitHub Actions concurrency group or a lock file), reads all pending events, groups them by stage, runs, and marks them done only after the run report passes. A crashed run leaves events pending, so the next wake retries them |
| **Timers** | Two kinds: schedules on a known cadence, and follow-ups the agent sets for itself. They live in their own store. A scheduler polls it and moves due timers into the inbox | Schedules are the cloud scheduled tasks and GitHub Actions crons. Follow-ups are lines in `timers/followups.jsonl`, written by skills, for example "read the indexing canary on day 28", "this packet expires on the 23rd", "re-check this actor's canary tomorrow". The first step of every scheduled wake promotes due follow-ups into the inbox. A run that needs to wait sets a follow-up and exits. It never sleeps or polls inside a run |
| **Memory** | Hold only what cannot be looked up again, otherwise store a pointer. Load instructions, an index and "what I already told the user" at the start of each run. Keep per-task progress files and read them on demand | Instructions are `CLAUDE.md`. The index is a generated `state/INDEX.md` with one line per live item. Task progress is the item file. `journal/LESSONS.md` holds curated lessons. `outbox/reported.md` records what you have already been told. Metrics, revenue and listings are pointers to the source of truth, not copies treated as truth. The weekly review does the curation the guide calls dreaming |
| **Permissions** | Keep credentials outside the agent's environment behind a proxy. Use auto mode for routine work. Defer a tool call when approval is needed: the run ends, the request goes to the user, and the answer returns as an inbox event | Token-holding steps run in GitHub Actions or behind connectors, not in model sessions. Model runs use auto mode with deny rules. A gated action is a deferred call: the escalation packet is the request, your commit is the answer, and that commit arrives as an inbox event that resumes the item. Other items keep moving meanwhile |
| **Outbox** | Runs end by sending a message, sending nothing, or deferring. Pace what reaches the user. Start quiet and earn attention | `outbox/pending.jsonl` plus a dispatcher step in the wrapper. Escalations and `STOP` events are delivered immediately. Everything else is batched into one daily digest per factory in Slack. A run with nothing new sends nothing. Nothing in `outbox/reported.md` is sent twice |

Three consequences for the build:

1. **Schedules do not call skills directly.** A schedule tick only adds an event and wakes the worker. This removes the two failure modes the guide names: competing runs when two triggers land together, and a lost event when a run crashes.
2. **Files first, a database when webhooks arrive.** JSON Lines on the `factory-state` branch are enough while every event comes from a schedule or a commit. When a factory needs real webhooks (Stripe, a marketplace, a broker), the inbox, timers and outbox move to three Supabase tables with the same fields, and a small HTTP handler acknowledges the webhook quickly and writes the row. Checks for prompt injection happen in the run, not in the handler.
3. **Quiet by default.** The first draft had every run post to Slack. That is replaced by the outbox rule above, so your attention is spent on decisions and on one digest a day.

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
- **Publisher** steps are the only ones that touch an external write API, they consume only validated structured input, and in most factories they stop at "draft" or "paused" and hand the last click to you.

For each scheduled cloud task, the connector list is pruned to the minimum. By default a task would hold write access to Gmail, Slack, HubSpot, Linear, Notion, Drive and GitHub.

### 5.3 Budgets and kill switches

- `budget.yaml` per factory holds the monthly token cap, the monthly paid-API cap, per-run caps and factory-specific risk limits (for example maximum position size or maximum ad spend, both zero until you raise them).
- Hard backstops outside the repo: a monthly spend limit on Claude usage credits, a workspace limit on the API key, and prepaid or capped billing on every vendor that supports it.
- `STOP` file per factory, and one at the repo root that halts everything.
- **Portfolio rule:** a factory that has spent its validation budget without a dollar of verified revenue is paused and escalated for a keep-or-kill decision. The budget and window are set per factory in its spec.

### 5.4 Escalation protocol

Detailed in `factories/_shared/CONVENTIONS.md` and each factory's `ESCALATION.md`. In short:

1. The factory writes an approval packet to `escalations/open/<id>.md`: what it wants to do, evidence, cost, worst case, how to undo it, and what happens if you say no.
2. It notifies you in Slack and opens a Linear issue, both sent immediately rather than held for the digest, then moves the item to `awaiting_human` and continues with other items. Your decision returns as an event in the inbox.
3. **Approval is a commit by you** that moves the packet to `escalations/approved/` on `main`. The agent's identity cannot push to `main`, so it cannot approve itself. A Slack reply is a convenience and is never treated as approval on its own.
4. Silence is never approval. Packets expire after the period stated in the packet and the item is parked.

Triggers common to every factory: spending money beyond the token budget, creating or using any account, anything published or sent under your name, legal or compliance questions, accepting terms of service, handling personal data, three consecutive stage failures, any detected attempt at prompt injection, and any rule conflict.

### 5.5 Telemetry and the self-improvement loop

- **Sources of truth:** Stripe (read-only key), marketplace payout pages, broker statements, PostHog, Search Console. Revenue is recorded only from these.
- **Daily telemetry run:** pulls metrics into `state/metrics/` and appends revenue lines to the ledger with the source reference.
- **Weekly review run:** reads the week's journal, ledger and metrics, and produces at most three proposed changes. Each proposal names the observation, the hypothesis, the single change, the metric that will judge it and the review date.
- **Changes land as pull requests, never as direct edits.** You merge or close them. One change per skill per week, so effects can be attributed.
- **Off limits to self-modification:** `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, the run wrapper, hooks and settings. Deny rules cover these paths. A proposal to change them is an escalation.
- **Lessons** go into `journal/LESSONS.md` as dated, evidence-linked entries, capped in length, so the file stays cheap to load.

## 6. Shared tooling

Verification status for prices and for which integrations are official is in the tooling matrix in `RESEARCH_REPORT.md`. Tools are named here by role.

| Role | Default | Why | Already available to you |
|---|---|---|---|
| Scheduler | Claude Code cloud scheduled tasks, plus Desktop tasks for HeyGen and HyperFrames video work only | First party, bills to the plan, carries connectors | Yes |
| Queue and approvals | Linear issues, Slack notifications, approval by commit | Connectors already live | Yes |
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
3. Build factory 1 as a walking skeleton: one item pushed through every stage by hand-triggered runs, with you approving the one publish.
4. Only then turn on schedules, at the slowest cadence, with the connector list pruned.
5. Add the second factory after the first has produced two weeks of honest run reports.

## 8. Decisions needed from you

1. Which factory to build first. The recommendation is `f-apify-actors`.
2. Whether to approve the default toolset in section 6, in particular the new accounts it implies (Apify, Firecrawl, Cloudflare, Stripe, Sentry, Postiz).
3. Monthly ceilings for tokens and for paid APIs, per factory. Blueprints propose conservative defaults.
4. Whether Factory E should exist at all in outbound form, given the Australian Spam Act position, or be redesigned as inbound-led.
5. Whether you are comfortable running this on a work-managed Mac and a personal Claude subscription. Unattended use on a subscription is currently permitted but Anthropic paused a change to it in 2026, so the design keeps an API-key path as well.
6. Branch protection on `main` in the new repository, which the approval mechanism depends on.
