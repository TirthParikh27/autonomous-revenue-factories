# Factory E: B2B demo-first outbound (drafts only)

Status: blueprint. Nothing here has been built or run. Date: 16 November 2026.
Fits `ARCHITECTURE.md` and `factories/_shared/CONVENTIONS.md`. Research: `factory_e_b2b_outbound.md`.

## 1. Purpose and honest evidence summary

The factory finds businesses showing a buying signal, builds each one a small audit or demo page from sourced public facts, and prepares a draft message for the operator to send by hand. It sells one productised, fixed-scope offer at a time.

- No independently verifiable revenue case was found for per-lead demo outreach at solo scale. Every source gives process without a full denominator (sends, replies, closes, revenue).
- The only large-sample number is a vendor benchmark: about 3.43% of cold emails get any reply (Instantly, 2025 data). Meetings are quoted secondhand at 0.5 to 2.5% of emails. No source measures lift from a per-lead page.
- The operator is in Australia. ACMA's guidance (read) says commercial messages need consent, consent cannot be requested by email, bought lists carry no consent, and harvested lists and harvesting software are prohibited. Verified 2026-11-16 (Spam Act Schedule 2 clause 4 and sections 7 and 16, read on AustLII): consent can be inferred from conspicuous publication only when the address belongs to a particular person, office or role, was published with their agreement, carries no statement refusing commercial messages, and the message is relevant to that person's work role. The sender bears the evidential burden. The Act also applies when an Australian sender emails only overseas recipients. ACMA's public guidance does not mention the exception, and "conspicuously" is not defined.
- Documented failures in this model are silent: a regex removed 80% of a pool, campaigns returned 200 OK with no sender attached, and a proxy priced at 2x cost over $1,400.
- Closing needs a call, and delivery can turn each sale into a job. No source quantifies delivery hours.

Consequence: this factory is a small validation funnel. Its default result is "killed cheaply, with honest numbers".

## 2. Modes

| Mode | Status | What it does |
|---|---|---|
| 1. Drafts only | Enabled, default | Prepares demo page, draft message and consent-basis record per lead. The operator reviews and sends from his own mailbox, one at a time. Also serves inbound leads (people who asked). |
| 2. Automated sending | Disabled. Needs `E-LEGAL-1` then `E-MODE2-1` approved | Sending platform with warm-up, volume caps, suppression list, unsubscribe honoured within 5 working days, sender identification, complaint and bounce monitoring with auto-pause. Requirements are in section 10. No skill for it exists in this blueprint on purpose. |

Out of scope in every mode: LinkedIn automation, LinkedIn data in any form, address-harvesting tools, bought or rented contact lists.

## 3. Item types

- **Offer** (`state/offers/<slug>.json`): the productised offer. Fixed scope checklist, fixed price, delivery hour cap, target niche, signal definitions, demo template id. Created and changed only through `E-OFFER-1`. No lead work runs without one approved offer. At most one active offer during validation.
- **Lead** (`state/items/<id>.json`): one business. Standard item format plus `offer`, `mode_origin` (`outbound` or `inbound`), `signals[]`, `facts[]`, `consent`, `contact_page_url`, `hubspot_company_id`, `demo_url`, `gmail_draft_id`, `touches[]`.

`facts[]` entries are `{claim, source_url, quote, checked}`. `quote` is a verbatim excerpt that the fact check can find again at `source_url`.

`consent` is `{basis, evidence, recorded}` where `basis` is one of:

| basis | Meaning | Usable in Mode 1 |
|---|---|---|
| `express_inbound` | The person asked. Evidence is the HubSpot record id, form or thread, and timestamp (who, when, how). | Yes |
| `existing_relationship` | A provable ongoing relationship in HubSpot. | Yes, flagged for operator judgement |
| `published_business_contact_unconfirmed` | A work contact route is publicly listed on the business's own site. Inferred consent under Schedule 2 clause 4(2) is narrow and the sender must prove every limb (verified 2026-11-16). The record must hold the source URL, a snapshot of the page, a note that no statement refusing commercial messages appears, the named person or role, and why the offer fits that role. Whether a lead meets the test is not decided by the agent. | Draft is prepared with a visible warning. The operator decides whether and how to make contact. |
| `none` | Nothing documented. | No. Lead is killed. |

The factory never extracts or stores an email address or phone number from the web. For outbound leads it stores `contact_page_url` only, and the Gmail draft has an empty recipient. Addresses enter only from HubSpot records where the person supplied them. Relaxing this is part of `E-LEGAL-1`.

## 4. State machine

All model stages run through the shared run wrapper. "Check" is a script or query whose result decides the transition. Check scripts live in `checks/` and are to be built. Tool names for Gmail, HubSpot and Calendar are as seen in the operator's connector list on 16 Nov 2026 and must be confirmed at build time.

| # | Stage (skill) | Input | Process | Tools | Deterministic check | Output | Runs as | Scheduler and cadence |
|---|---|---|---|---|---|---|---|---|
| 1 | Signal sourcing (`source-signals`) | Approved offer, its signal definitions; HubSpot inbound records | Search for businesses showing a defined signal. Record the signal with source and quote. Pull inbound requests from HubSpot. | Parallel Search connector (in directory, listed as free, authless), Firecrawl connector free tier (1,000 credits a month, verified) for page content, HubSpot `search_crm_objects`. HubSpot `search_intent_signals` exists in the tool list; plan requirements unverified. | `checks/lead_schema`, `checks/no_addresses_lint` (no email or phone pattern in outbound items), dedupe against all items and `state/suppression.jsonl`, `checks/funnel_invariants` | Items at `signal_found`, `state/funnel/<date>.json` | `lead-scout` agent | Cloud scheduled task, weekly (Monday) |
| 2 | Account qualification (`qualify-accounts`) | `signal_found` items | Score against the offer's rules: niche match, signal age, at least 3 sourced facts, documented consent basis, contact route exists. | Read, Write, Bash for check scripts. No web tools. | Rule scoring is done by `checks/qualify_rules` (code, not the model). `checks/consent_record_lint`. Funnel invariants including the per-rule rejection share. | `qualified` or `killed` with reason | Main session, Haiku tier | Cloud scheduled task, weekly (Tuesday) |
| 3 | Demo generation (`build-demo`) | `qualified` items | Write `demos/data/<slug>.json` for the single approved template. One page per lead at an unguessable URL. No per-lead code. | Read, Write, Edit, Bash. Reads scout output only. | `checks/demo_data_schema`. Token cost per lead against the cap in `budget.yaml`. | `demo_built`, data file on the run branch | `demo-builder` agent | Cloud scheduled task, twice weekly |
| 4 | Demo QA (`qa-demo`) | `demo_built` items | Re-fetch every fact source and confirm the quote is still present. Render the page. Lint claims. Then deploy to a preview and confirm it is served. | GitHub Actions job (no model) with a headless browser such as Playwright (Microsoft's Playwright CLI and MCP are free and Apache-2.0, verified 2026-11-16; not installed on the operator's Mac). Hosting deploy token held by Actions only. | `checks/fact_source_check`, `checks/render_check` (HTTP 200, no console errors, no unfilled placeholders, `noindex`, sender footer, removal link), `checks/claims_lint`. After deploy: fetch the live URL and match the lead marker. | `demo_verified` with `demo_url`, or back to `demo_built` once, then `killed` | CI job, plus `demo-verifier` agent as a second reader | GitHub Actions on push of demo data; verifier in the next cloud run |
| 5 | Message drafting (`draft-outreach`) | `demo_verified` items | Draft first-touch message and a short call script from the lead's facts. Create a Gmail draft. Mirror company and deal to HubSpot. Write the weekly send packet. | Gmail `create_draft`, `list_drafts`, `get_draft`; HubSpot `manage_crm_objects`, `search_crm_objects`; Slack and Linear through the `escalate` skill | `checks/draft_lint` (word cap, sender identification, opt-out line, at most one link, every claim maps to a fact, empty recipient for outbound). Outcome check: read the draft back by id and compare body hash. Read the HubSpot record back. | `draft_ready`, then `awaiting_human` under send packet `E-SEND-1` | `outreach-publisher` agent | Cloud scheduled task, twice weekly |
| 6 | Human send | Send packet | Operator reviews, edits, adds the recipient, sends from his own mailbox, applies the Gmail label `factory-e`. | None for the agent | Next `handle-replies` run finds the sent message in Gmail by the demo URL slug. Only that moves the item. | `sent` | Operator | Manual |
| 7 | Reply handling to proposal (`handle-replies`) | `sent`, `replied`, `call_booked` items; labelled Gmail threads | Detect sends and replies. Classify replies into a fixed set. Apply suppression the same run. Draft replies, at most 2 follow-ups, and after a call a proposal draft from the offer template. | Gmail `search_threads`, `get_thread`, `create_draft`; Google Calendar `list_events` (connector observed, confirm); HubSpot as above | Classification file validated against schema. Suppression check before every draft. Booked call counts only if a calendar event exists. Draft outcome check as in stage 5. | `replied`, `call_booked`, `proposal_drafted` then `awaiting_human` (`E-CLIENT-1`), `closed_no_reply`, `suppressed` | Main session reads mail; `outreach-publisher` drafts from the structured file | Cloud scheduled task, daily on weekdays |
| 8 | Delivery (`deliver-offer`) | `won` items with approved `E-CLIENT-1` and a verified Stripe payment | Work through the offer's fixed checklist only. | Read, Write, Edit, Bash; Stripe read-only | Every checklist line has an evidence entry. Operator hours logged against the cap. | `delivering`, then `delivered` after operator hand-off | `demo-builder` agent, operator hands over | Hand-triggered run only |
| 9 | Telemetry and review (`telemetry-review`) | Ledger, journal, funnel files, Gmail, Calendar, Stripe, PostHog, HubSpot | Daily: pull counts from sources of truth, expire demo pages, enforce kill criteria. Weekly: review and at most three proposals as pull requests. | Gmail search, Calendar, Stripe connector with a read-only key (one-click connector, not yet added), PostHog `exec`, HubSpot read | `checks/funnel_invariants` over the whole funnel. Revenue only from Stripe. | `state/metrics/<date>.json`, revenue ledger lines, `journal/reviews/<week>.md`, PRs | Main session; Sonnet daily, Opus weekly | Cloud scheduled task daily and weekly; invariants also as a daily GitHub Actions job |

Mapping to the required loop: Input (1, 2), Process (3, 5), QA (4, plus the checks in every stage), Output (5, 6, 7, 8), Telemetry (9 daily), Self-improvement (9 weekly).

## 5. Transitions

```
(new)            -> signal_found
signal_found     -> qualified | killed
qualified        -> demo_built | killed
demo_built       -> demo_verified | demo_built (one retry) | killed
demo_verified    -> draft_ready | killed
draft_ready      -> awaiting_human            (send packet E-SEND-1)
awaiting_human   -> sent                      (sent message found in Gmail)
awaiting_human   -> killed                    (packet rejected, or expired after 14 days)
sent             -> replied | closed_no_reply | suppressed
replied          -> call_booked | closed_no_reply | suppressed
call_booked      -> proposal_drafted | closed_no_reply | suppressed
proposal_drafted -> awaiting_human            (E-CLIENT-1)
awaiting_human   -> won                       (E-CLIENT-1 approved and Stripe payment verified)
awaiting_human   -> closed_no_reply           (E-CLIENT-1 rejected or expired)
won              -> delivering
delivering       -> awaiting_human            (E-SCOPE-1, any request outside the fixed checklist)
awaiting_human   -> delivering | killed       (per the E-SCOPE-1 decision)
delivering       -> delivered
any non-terminal -> awaiting_human            (any other trigger in ESCALATION.md)
awaiting_human   -> the stage named in the packet, or killed
any non-terminal -> suppressed                (opt-out, complaint, removal request)
any non-terminal -> killed
```

Terminal: `killed`, `suppressed`, `closed_no_reply`, `delivered`. `suppressed` also writes the business name and domain to `state/suppression.jsonl` and unpublishes the demo page. A suppressed business is never contacted or re-sourced.

## 6. Funnel invariants (the answer to silent drops)

Each stage run writes `state/funnel/<date>-<stage>.json` with `in`, `out`, `held`, `killed_by_reason{}`. `checks/funnel_invariants` fails the run and raises `E-FUNNEL-1` when:

- Conservation breaks: `in != out + held + killed`.
- A non-empty input produces zero output.
- One rule or filter removes more than 50% of a batch of 10 or more.
- A stage's pass rate leaves its band in `budget.yaml` (first guesses, to be tuned by review, never by the stage itself).
- A count read from a source of truth (Gmail drafts, HubSpot deals, live pages) differs from the item files.

## 7. Kill criteria

Per lead (cheap, automatic, no escalation):

| Stage | Kill when |
|---|---|
| Signal | Signal older than 60 days, duplicate, on suppression list, or business not in the offer's niche |
| Qualification | Fewer than 3 facts that pass the source check, consent basis `none`, or no public contact route |
| Demo | Token cost for the lead above $3.00, or data schema fails twice |
| Demo QA | Any fact fails the source check and cannot be replaced, or the second render attempt fails |
| Draft | Lint fails twice |
| Send | Packet rejected or 14 days old |
| Sent | No reply 10 days after the last allowed touch (first touch plus at most 2 follow-ups) |

Per stage (pause the stage and escalate):

- Sourcing: fewer than 5 `signal_found` per week for 2 weeks, or more than $0.50 of tokens per `signal_found` lead.
- Qualification: pass rate under 10% for 2 weeks (the signal definition is wrong).
- Demo QA: first-pass failure above 40% over 20 leads.
- Drafts: the operator rejects or leaves unsent more than 50% of a packet twice in a row.
- Replies: 2 or more complaints, hostile replies or removal demands within any 50 sent. Pause all drafting and raise `E-COMPLAINT-1`.

Factory-level validation:

- **Unit:** conversations booked per 100 qualified leads sent. A conversation counts only with a calendar event and a matching Gmail thread.
- **Budget:** $200 total recorded spend (tokens plus anything else), $0 paid data. **Window:** 12 weeks from the first scheduled run, or 100 leads sent, whichever comes first.
- **Checkpoint at 50 sent:** zero replies of any kind pauses the factory for a keep-or-kill decision. This is weak evidence: at the 3.43% benchmark the chance of zero replies in 50 is about 17%.
- **At 100 sent:** 4 or more booked conversations continues. 2 or 3 allows one more batch of 100 with exactly one change. 0 or 1 ends the outbound form; inbound use may continue.
- **Honesty note:** 100 leads cannot separate a 1% from a 3% meeting rate with confidence. The thresholds are decision rules for a small budget, not statistical proof.
- **Portfolio rule:** budget or window spent with no verified Stripe revenue raises `E-KILL-1`.
- **Operator time:** more than 10 minutes of operator time per sent lead on average, or more than 3 hours a week, raises `E-KILL-1`. The factory must not become a job before it has revenue.

## 8. Telemetry

| Metric | Source of truth |
|---|---|
| Leads sent | Gmail sent mail carrying the label and the demo slug |
| Replies and their class | Labelled Gmail threads |
| Conversations booked | Google Calendar event plus thread |
| Demo page views | PostHog events from the demo template (already connected) |
| Pipeline and stage mirror | HubSpot deals (CRM of record for companies, contacts, deals) |
| Revenue | Stripe only, read-only key |
| Spend | `ledger/spend.jsonl`, token cost from the wrapper |
| Operator minutes | Operator's one-line note in each send packet when he closes it |

A winner is an offer and signal pair with: at least 4 booked conversations per 100 sent, at least one Stripe payment, verified revenue above all recorded spend for that offer, delivery within the offer's hour cap, and no complaint.

## 9. Self-improvement loop

Weekly review (Opus tier) examines:

- Funnel counts by stage and every kill reason's share, looking for a rule that quietly removes most leads.
- Replies and bookings by signal type and niche.
- Demo QA failure reasons and which fact sources go stale.
- The difference between each Gmail draft and what the operator actually sent. Repeated edits are the best available signal about the drafts.
- Rejected packets and their one-line reasons. Demo views against replies.

It may propose, as pull requests, at most three changes, one per skill per week: a signal definition, a qualification threshold, template copy, a draft instruction, a check's band. Each proposal names observation, hypothesis, single change, judging metric and review date.

It may not propose by PR: more volume, a new channel, Mode 2, a new data vendor, a new offer, or any change to `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, checks' pass or fail logic, hooks or settings. Those are escalations.

## 10. Mode 2 requirements (disabled, for the record)

Only after a lawyer's written answer under `E-LEGAL-1` and a separate `E-MODE2-1` approval:

- A sending platform called through its REST API from the operator's own code. Verified 2026-11-16: Instantly has an official hosted MCP (`mcp.instantly.ai`) with the full V2 API at no extra fee, and its Growth plan is $47 a month. Smartlead Base is $39 a month and lemlist's Email plan is $69 a month. A Google Workspace Business Starter mailbox is A$11.80 a month on flexible billing. Domain prices were not obtained.
- A dedicated sending domain separate from the main brand. SPF, DKIM and DMARC. Warm-up from 5 to 10 a day over 4 to 6 weeks (Instantly benchmark).
- Hard daily caps in code. Suppression check before every send. Sender name, business name and ABN in every message. Unsubscribe that works for at least 30 days, needs no login, and is applied within 5 working days (design target: same day).
- Outcome checks after every action: sender accounts attached, campaign state active, sent count above zero within 24 hours.
- Auto-pause at bounce rate above 2%, complaint rate at or above 0.1%, or 2 complaints in 7 days.

## 11. Tools and accounts

| Tool | Role | Status |
|---|---|---|
| HubSpot connector | CRM of record, inbound source | Already available. Plan limits for intent signals unverified |
| Gmail connector | Drafts, reading labelled threads | Already available. Send tools must be denied |
| Slack, Linear connectors | Notifications, escalation queue | Already available |
| Google Calendar connector | Proof of booked calls | Connected (verified in the operator's connector list, 2026-11-16) |
| PostHog | Demo page views | Already available |
| GitHub and Actions | State, CI checks, deploy job | Connector available. Repository still to be created |
| Parallel Search connector | Signal search | In the directory, not installed. Free MCP needs no account but rate-limits after roughly 8 to 10 quick calls. Search API $1 to $5 per 1,000 requests (verified 2026-11-16) |
| Firecrawl connector | Page content for facts | One-click connector, new account. Free tier 1,000 credits a month, verified |
| Static hosting (Cloudflare Pages per `ARCHITECTURE.md`, or GitHub Pages) | Demo pages | New account for Cloudflare. Cloudflare Pages free tier: 500 builds a month, unlimited static requests, no commercial-use restriction found (verified 2026-11-16). Vercel Hobby is non-commercial only and is not used. GitHub Pages reported as free by one practitioner. Confirm whether pages can stay unlisted |
| Stripe connector | Revenue source of truth | In the directory, not installed. New account. Verified 2026-11-16: Australian fees are 1.65% + A$0.30 on domestic cards and 3.5% + A$0.30 on international cards, and from December 2026 the Stripe MCP accepts only OAuth or an agent-tagged restricted key. GST registration is required at $75,000 of turnover across all the operator's businesses (ATO). Invoicing rules not researched |
| Clay (MCP or plugin) | Optional enrichment | New account. Launch from $185 a month, free plan with 500 actions a month (verified 2026-11-16, official). Not used in validation |
| Google Places API | Optional local-business data | Paid and metered per request, for example Text Search Enterprise at $35 per 1,000, and no SKU returns an email address (verified 2026-11-16). Confirm terms before any use |
| Sending platform, mailboxes, domains | Mode 2 only | New accounts. Platform and mailbox prices are in section 10 (verified 2026-11-16). Domain prices not obtained |
| Apollo, Apify, Exa, Explorium MCP servers | Not used | Official MCP servers exist for all four (verified 2026-11-16). Explorium's AgentSource is being discontinued on 2 December 2026. ACMA states that a list created with address-harvesting software may not be used or supplied, so list scraping stays out of scope |

## 12. Known failure modes and design responses

| Failure (source) | Response |
|---|---|
| Regex zeroed out 80% of a pool (Wolfe) | Funnel invariants, per-rule rejection share, qualification rules in tested code |
| 200 OK with no sender attached (Wolfe) | Outcome checks: read back the draft, the HubSpot record, the live page, the sent mail |
| $1,400 lost to a 2x proxy, pagination burning credits (Wolfe) | Paid data cap is $0. `E-SPEND-1` needs a price quote read from the vendor this run, direct against proxy price, and a row cap |
| Agent skips steps, ignores rate limits (Wolfe) | One stage per run, wrapper fails on missing artifact, checks outside the model |
| Vendor endpoint or vendor shutdown (Apollo 404s, Proxycurl) | No LinkedIn data. Validation uses search and the lead's own site only |
| Spam Act exposure (ACMA) | Mode 1 only, consent record per lead, no stored addresses, human sends, `E-LEGAL-1` |
| Complaints and reputation ("I rebuilt your site" reads as presumptuous) | Low volume, facts only, removal link on every page, suppression in the same run, pause at 2 complaints in 50 |
| Fabricated claims about the lead | Every claim has a quote re-found at its source by script. No estimates of the lead's revenue or losses |
| Branding and copyright exposure of spec pages (no source found) | Pages use no logos, photos or copied copy from the lead. Text facts with citations. `noindex`, unguessable URL, 45 day expiry |
| Recipients discount AI pitches; one source advises hiding AI use | Do not hide it and do not claim hand work. Answer truthfully if asked |
| Delivery becomes a job | One fixed-scope offer, hour cap, `E-CLIENT-1` before any client, `E-SCOPE-1` for anything outside the checklist |
| Prompt injection through lead sites or replies | Scout and reply reading have no outbound tool. Drafting consumes structured files only. `SEC-1` |
