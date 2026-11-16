# Factory D: Directories and Programmatic SEO

Status: blueprint for review. Nothing here has been built or run. Date: 16 November 2026.
Fits `ARCHITECTURE.md` and `factories/_shared/CONVENTIONS.md`. Shared skills `escalate`, `ledger` and `run-report` are referenced, not repeated.

## 1. Purpose and honest evidence summary

This factory builds a small number of local or transactional directory sites from verified business records, proves that Google indexes a small canary before adding pages, and only then attempts monetisation.

What the research found:

- No third-party verified case of a directory built with AI agents earning money was found. The best-documented cases (Frey Chu, John Rush) are self-reported by people who sell directory courses, communities or site builders. Chu's "$273/day" appears only in an episode title and is unexplained in the sources read. His own stated income is about $2,500 to $3,000 a month from 7 to 8 directories built over three years. The two TrustMRR leads are Stripe-verified but small: Directory Hunt has earned $80 in total, and Directorly, a tool sold to directory builders, has about $1,400 MRR (read 2026-11-16).
- The two fully documented 2026 build logs earned nothing. One submitted 8,653 URLs and had none indexed (about 89% near-duplicate pages on a new domain). The other found its LLM step had silently fallen back to templates, so every page carried the same text.
- Google's status dashboard (read 2026-11-16) shows four spam updates in 2026 (March, June, August, September) and core updates in March, May and November, the last still rolling out. Its spam policy names as scaled content abuse both scraping feeds to generate many low-value pages and creating multiple sites to hide the scaled nature of the content. The documented casualties were large programmatic sites with AI text (14K to 1.5M URLs). No evidence was found either way for small data-rich directories.
- AI Overviews appeared on about 15% of pure local-intent queries but 92% to 97% of informational and "cost of X in city" queries (Whitespark, May 2025, small sample, old). A later article title suggests local coverage has grown, so this must be measured per niche, not assumed.
- Self-reported revenue is a few hundred dollars a month per site on 5,000 to 20,000 monthly visits. Realistic time to first dollar is 4 to 9 months (researcher estimate). No base rate of success exists; the evidence pattern is consistent with most attempts earning nothing.

Consequence: the item in this factory is one site (one niche in one geography). The default outcome for a site is "killed early at low cost". At most two sites are live at once.

## 2. Item states

`discovered`, `niche_proposed`, `raw_acquired`, `verified`, `built`, `qa_passed`, `canary_live`, `index_confirmed`, `scaled`, `monetised`, `winner`, plus `awaiting_human`, `parked` and `killed`.

Item files live at `state/items/<id>.json`. This factory adds these fields to the shared format: `niche`, `geography`, `data_source`, `domain`, `pages_live`, `page_cap`, `canary_started`, `index_ratio`, `monetisation`.

## 3. State machine

One run does one stage for a bounded batch. Record-level work inside a site is chunked with a cursor file so a run can stop and a later run can resume.

| # | Stage (skill) | Input | Process | Tools | Deterministic check (outside the model) | Output artifact | Runs as | Scheduler and cadence |
|---|---|---|---|---|---|---|---|---|
| 1 | `niche-discovery` | Seed list in `state/seeds.md`, LESSONS | Pull keyword volume and live SERP features for candidate "service in place" query sets. Score. Draft niche packet with data-source options. | DataForSEO MCP (keyword and SERP modules only). No other web access needed. | `tools/check_niche` validates the brief against schema and recomputes every kill threshold from the saved raw API responses, not from the scout's summary. | `state/niches/<id>/brief.json`, raw API responses, escalation packet `D-NICHE-1` | `niche-scout` agent | Cloud scheduled task, weekly. Skips if two sites are already active. |
| 2 | `dataset-acquisition` | Approved `D-NICHE-1` packet naming one data source and a cost ceiling | Pull raw records from the approved source only. Strip disallowed fields at ingest. | The approved source's API or export (Outscraper, Apify, DataForSEO Maps endpoint, official Places API, or an open dataset). Exactly one, as approved. | `tools/check_raw`: row count, schema, no review text, photo or owner-name fields present, vendor invoice figure within ceiling. | `data/<id>/raw.jsonl.gz`, `data/<id>/acquisition.json` | Stage session, no sub-agent | Cloud task, on demand after approval. GitHub Actions job if the vendor host cannot be allowlisted in the cloud environment. Not run on the operator's work-managed Mac. |
| 3 | `clean-verify` | Raw rows | Deterministic de-duplication and filtering, then a crawl of each business's own website, then per-record verification from the crawl extracts. | Dedupe and filter scripts. Crawl4AI (self-run, plain script) or Firecrawl. `record-verifier` agent on extracts. | `tools/check_verified`: unique keys, every kept record has a live evidence URL on the business's own domain fetched within 30 days, required attributes present, personal-data filter, suppression list applied. Independent re-fetch of a random 30-record sample by script. | `data/<id>/verified.jsonl`, `data/<id>/verify_report.json` | Crawl: script with no model. Classification: `record-verifier` agent | Crawl: GitHub Actions, manual dispatch. Classification: headless run through the wrapper, on demand, chunked. |
| 4 | `site-build` | Verified records, approved `D-DOM-1` | Generate an Astro static site from verified records only. Listing pages and category or place pages that meet the minimum listing count. | Astro, Node, git. No network beyond package registries. | `tools/check_build`: build exits 0, page count at or under `page_cap`, every page maps to verified records, internal link check, required pages present (sources, removal request, disclosure where needed), no suppressed record present. | `sites/<id>/` source on a `claude/` branch, `sites/<id>/build_manifest.json` | `site-builder` agent | Cloud task, on demand. |
| 5 | `content-qa` | Built site | Near-duplicate analysis of rendered main content, template-fallback detection, fact spot-check against records. | `tools/check_duplicates`, `tools/check_fallback`, `tools/check_facts` in GitHub Actions. `content-verifier` agent for the sample review. | The scripts are the gate. Thresholds in `budget.yaml` under `content_qa`. Any failure blocks the pull request. The verifier's opinion cannot override a script failure. | `sites/<id>/qa_report.json` | CI scripts plus `content-verifier` agent | GitHub Actions on every pull request touching `sites/`. Verifier session on demand. |
| 6 | `canary-deploy` | `qa_passed` site | Select the canary set (at most `canary_pages`), restrict the sitemap to it, open the deploy pull request and packet `D-PUB-1`. Later tiers reuse this skill with `D-SCALE-1`. | git, GitHub. Cloudflare Pages deploys on merge to `main` (mechanism to be confirmed at build time). | After the operator merges: HTTP fetch of every canary URL returns 200 with the expected title, the sitemap lists exactly the canary set, robots file allows crawling, no page beyond the set is reachable from the sitemap. | Deploy pull request, `state/items/<id>.json` updated with `canary_started` | Stage session acting as publisher. It never deploys. The operator's merge deploys. | Cloud task, on demand. Outcome check runs in the next daily telemetry run. |
| 7 | `index-telemetry` | Live sites | Pull index status, impressions, clicks and sessions. Evaluate the canary gate and the scale gate from the stored series. | Search Console API through a read-only service account (route verified 2026-11-16, see the telemetry sources table), PostHog web analytics, operator-supplied earnings exports. | `tools/eval_gates` computes `index_ratio` and gate results from `state/metrics/` files. The model does not decide the gate. | `state/metrics/<id>/<date>.json`, gate result, revenue ledger lines | Stage session | Cloud scheduled task, daily. |
| 8 | `monetise` | Site at `index_confirmed` or `scaled` that meets an eligibility threshold | Rank monetisation options against real traffic, draft the application packet, and after approval place links or ad code with disclosure. | Repo only. Programme sign-up is done by the operator. | `tools/check_disclosure`: every page with an affiliate link carries the disclosure above the first link, and links carry the correct rel attributes. | Packet `D-MON-1`, then a pull request | Stage session plus `site-builder` for the change | Cloud task, monthly eligibility check, otherwise on demand. |
| 9 | `weekly-review` | Journal, ledger, metrics, rejected packets | Prune pages that fail to index, propose expansion where evidence supports it, and propose at most three process changes. | Repo only. | Every proposal cites metric files. Prune lists are produced by `tools/eval_gates`, not chosen by the model. | Pull requests, `journal/LESSONS.md` entries | Stage session on the Opus tier | Cloud scheduled task, weekly. |

Mapping to the required loop: Input is stages 1 and 2. Process is stages 3 and 4. QA is stage 5 and the canary gate in stage 7. Output is stage 6. Telemetry is stage 7. Self-improvement is stage 9. Stage 8 is the monetisation step.

## 4. Allowed transitions

```
discovered      -> niche_proposed          niche-discovery, all numeric criteria pass
discovered      -> killed                  any niche kill criterion
niche_proposed  -> awaiting_human          D-NICHE-1 (includes the data-source choice, D-DATA-1)
awaiting_human  -> raw_acquired            D-NICHE-1 approved, dataset-acquisition check passes
raw_acquired    -> verified                clean-verify check passes
raw_acquired    -> killed                  fewer verified records than the minimum, or cost per record too high
verified        -> awaiting_human          D-DOM-1 (domain purchase by the operator)
awaiting_human  -> built                   D-DOM-1 approved, site-build check passes
built           -> qa_passed               content-qa scripts all pass
built           -> built                   content-qa fails, returned to site-build (maximum 3 attempts)
built           -> killed                  third content-qa failure caused by thin data rather than a bug
qa_passed       -> awaiting_human          D-PUB-1 (canary deploy pull request)
awaiting_human  -> canary_live             D-PUB-1 approved and merged, outcome check confirms pages are served
canary_live     -> index_confirmed         canary gate passes
canary_live     -> canary_live             gate not yet decidable, or one remediation cycle in progress
canary_live     -> killed                  canary gate fails at the deadline
index_confirmed -> awaiting_human          D-SCALE-1 or D-MON-1
awaiting_human  -> scaled                  D-SCALE-1 approved and merged, outcome check passes
scaled          -> awaiting_human          next tier D-SCALE-1, D-CAP-1, or D-MON-1
scaled          -> index_confirmed         scale gate fails: new pages pruned back to the last passing tier
awaiting_human  -> monetised               D-MON-1 approved, operator has joined the programme, disclosure check passes
monetised       -> winner                  winner metrics met
monetised       -> awaiting_human          D-KILL-1 at the end of the validation window
any state       -> awaiting_human          any trigger in ESCALATION.md
awaiting_human  -> killed                  packet rejected and "If you say no" names kill
awaiting_human  -> <stage named in packet> packet rejected and "If you say no" names a stage
awaiting_human  -> parked                  packet expired
parked          -> <previous stage>        only by the operator's commit
any state       -> killed                  kill criteria, or the operator's decision
killed          -> (terminal)
```

## 5. Gates that precede any scale-up

These are proposed defaults. The research gave no sourced thresholds, so they are the factory's own conservative numbers and live in `budget.yaml`.

- **Canary size:** at most 40 pages, chosen as the records with the most verified attributes.
- **Canary gate:** not evaluated before day 28 after `canary_started`, because the documented failure showed a crawl burst and impressions for about a week followed by zero. Pass requires at least 60% of canary URLs indexed on two readings at least 7 days apart, and impressions above zero in the trailing 7 days.
- **Canary deadline:** day 56. Below 30% indexed at day 56 is a kill. Between 30% and 60% allows one remediation cycle of 28 days (remove the weakest pages, add data), then a kill.
- **Page tiers:** 40, then 150, then 500. Each tier needs `index_ratio` of at least 60% for the whole submitted set, held for 28 days, before the next `D-SCALE-1`.
- **Hard cap:** 500 pages per site. Raising it is `D-CAP-1` and needs an index ratio of at least 70% at 500 pages for 56 days.
- **Sitemap rule:** the sitemap never lists a page that has not passed content QA, and never grows by more than the approved tier.

## 6. Kill criteria

| Stage | Kill when (numeric, checked by script) |
|---|---|
| niche-discovery | Intent is informational or "cost of". AI Overview present on more than 25% of at least 20 sampled target queries. Combined monthly volume of the query set under 2,000. Niche is medical, legal or financial. Geography includes the EU or UK. Listings are mostly sole traders trading under a personal name. Fewer than 3 useful attributes that Google Maps does not show and that business websites publish. No named monetisation route. Spend on one candidate above USD 3. |
| dataset-acquisition | Source returns fewer than 500 raw rows. Quoted cost above the per-site data ceiling. Vendor terms changed since approval (this is `D-DATA-2`, not a silent retry). |
| clean-verify | Fewer than 150 verified records. Cost per verified record above USD 0.50. More than 10% of the 30-record re-fetch sample fails. |
| site-build | Three consecutive failed builds raises `FAIL-3`. |
| content-qa | Third failure where the cause is thin data. |
| canary | Rules in section 5. Also any Search Console manual action raises `D-SPAM-1` and freezes the site. |
| scaled | Index ratio under 40% for the site 28 days after a tier: prune to the previous tier. A second such failure kills the tier plan for that site (it stays at the smaller size). A site that pruning would reduce below 20 pages is killed. |
| monetised | No verified revenue 120 days after monetisation went live: kill or keep is decided in `D-KILL-1`. |

**Factory-level validation budget and window:** USD 900 in total recorded spend (tokens, data, domains, tools) and 270 days from the first `canary_live`. Checkpoints inside the window: day 56 canary gate; day 120 at least 300 Search Console clicks in the trailing 28 days on the best site; day 180 at least 1,000 sessions in the trailing 30 days on the best site (the Journey by Mediavine minimum, which counts sessions from Tier 1 countries, verified 2026-11-16) or an approved affiliate programme with at least 20 outbound affiliate clicks in 30 days; day 270 at least one dollar of verified revenue. Missing a checkpoint by more than half raises `D-KILL-1` early. Reaching either limit without verified revenue pauses the factory and raises `D-KILL-1`, as the portfolio rule requires. The window is long because domain-age rules alone delay ad income by four to six months.

## 7. Telemetry

Sources of truth:

| Metric | Source | Notes |
|---|---|---|
| Indexed URLs, impressions, clicks, positions | Google Search Console for the operator's own properties | The Search Console API accepts a service account with the read-only scope `webmasters.readonly` once the operator adds the account's `client_email` as a user on the property (verified 2026-11-16, official). There is no official Search Console MCP, only community servers, which are not used (secondary source). Fallback is a weekly export by the operator into `state/metrics_inbox/`. |
| Sessions, outbound clicks | PostHog web analytics (already connected) | Outbound affiliate clicks are a leading indicator only, never revenue. |
| Revenue | Affiliate network or ad network earnings and payout pages | No read-only API was verified for any network. Default is an operator export into `state/revenue_inbox/`. The run records revenue only from that file, with its reference. |
| Spend | Vendor invoices and the run wrapper's `total_cost_usd` | Through the `ledger` skill. |
| Served pages | Direct HTTP fetch of live URLs | Outcome check after every deploy. |

A site is a **winner** when all hold: net verified revenue of at least USD 100 a month for two consecutive months; trailing 90-day revenue above trailing 90-day attributed spend; index ratio at least 60%; no open compliance escalation. A winner earns the right to a `D-CAP-1` or a second site in an adjacent niche. Nothing else changes automatically.

## 8. Self-improvement loop

The weekly review examines:

- Index ratio by page type and by data richness (attribute count per page), to learn which pages Google keeps.
- Funnel yield: raw rows to verified records, and cost per verified record by source.
- Content QA failures by cause, and any template-fallback detections.
- Niche score against actual canary outcome, once at least three sites have a result.
- Rejected packets and the operator's one-line reasons.
- Spend against the validation budget and the next checkpoint.

It may propose, as pull requests, at most three changes a week and one per skill: niche scoring weights, extraction prompts for the verifier, page templates, the attribute list for a niche, prune lists, and tighter thresholds. It may not loosen any gate, change `budget.yaml`, `CLAUDE.md`, `ESCALATION.md`, the wrapper, hooks or settings. A wish to loosen a gate is an escalation with evidence.

## 9. Tools and accounts

| Tool or account | Role | Status |
|---|---|---|
| GitHub, GitHub Actions | Source control, CI gates, approval by merge | Already available (connector). Repo still to be created. |
| Slack, Linear | Notifications and escalation queue | Already available. |
| PostHog | Web analytics | Already available. |
| Claude Code cloud scheduled tasks | Scheduler | Already available. Research preview. |
| DataForSEO | Keyword volume, SERP features, optional Maps data | New account needed. Verified 2026-11-16 (official): pay as you go, USD 50 minimum top-up, balance never expires, USD 1 trial credit, SERP calls from USD 0.0006. Official MCP, hosted at `mcp.dataforseo.com/v3/mcp` or self-run from `dataforseo/mcp-server-typescript` (Apache-2.0). The older v2 server is deprecated. Dashboard spending limit is from a third-party comparison. Whether its SERP data flags AI Overview and local pack presence is unverified and is a precondition for stage 1. If self-run, pin a version; do not run `@latest`. |
| Outscraper | Maps-derived place data | New account needed. USD 3.00 per 1,000 records after the first 500 free, up to 100,000 (verified 2026-11-16, official). Usage beyond prepaid credits is invoiced, not stopped, so the pull size must be capped in the request. Use only if approved in `D-DATA-1`. |
| Apify | Maps-derived place data | New account needed. About USD 0.40 to 0.75 per 1,000 (indicative, from a competitor's comparison). Verified 2026-11-16: Free plan with USD 5 of usage a month, Starter USD 19 a month, official MCP at `mcp.apify.com`, and `maxTotalChargeUsd` caps a run. |
| Google Places API | Official place data | New Google Cloud billing account needed. Per 1,000 requests (verified 2026-11-16, official): Text Search Enterprise USD 35, Place Details Essentials USD 5 and Enterprise USD 20. Pro rows (Text Search USD 32, Place Details USD 17) are from secondary sources. Billing is per request, and asking for phone, website or rating moves a call to the Enterprise rate. 30-day storage restriction and 5-review cap as read from a secondary legal overview; the terms were revised several times in 2026 and must be re-read. |
| Crawl4AI | Self-run crawler for business websites | No account for the self-run package. Apache-2.0, and the README asks for attribution (verified 2026-11-16). A paid hosted Crawl4AI Cloud now exists and is not used. |
| Firecrawl | Alternative crawler | One-click connector. Free tier 1,000 credits a month, Hobby USD 16 a month on annual billing (verified 16 Nov 2026). |
| Astro | Static site generator | No account. |
| Cloudflare Pages | Hosting | New account needed. A Cloudflare connector exists in the directory but its listing shows Workers and KV tools; Pages deploy support is unverified. Free tier verified 2026-11-16 (official): 500 builds a month, 20,000 files per site, 100 custom domains per project, unlimited static requests, no commercial-use restriction found. The Wrangler CLI is not on the operator's Mac. |
| Domain registrar | One domain per site | Operator's own account. The agent holds no registrar credentials. Price unverified. |
| Google Search Console | Indexing source of truth | Operator's Google account. Property verification is done by the operator. Unattended route: a read-only service account added as a user on the property (verified 2026-11-16). |
| Affiliate and ad networks | Monetisation | Operator applies. Verified 2026-11-16 (official): Journey by Mediavine needs 1,000 sessions from Tier 1 countries in 30 days; Mediavine itself needs USD 5,000 of annual ad revenue; Raptive needs 25,000 monthly pageviews with 50% tier-1 traffic. Domain-history rules (four months for Journey, six for Raptive) are as read in January 2026. Secondary sources only: Ezoic has required 250,000 monthly active users since February 2026, and AdSense has no traffic minimum. All RPM figures unverified. |

## 10. Known failure modes and the design response

| Failure in the research | Design response |
|---|---|
| 8,653 URLs submitted, none indexed, about 89% near-duplicate | Canary of at most 40 pages, indexing gate before any scale-up, tiered page cap, near-duplicate check as a hard CI gate. |
| LLM step silently fell back to templates; identical text on every page | Pages are built from structured facts, not free prose. Any generated sentence carries a per-record `generation_source` flag. `tools/check_fallback` fails the build on any `template` value and on any non-template sentence that repeats across more than the allowed share of pages. |
| 71,000 raw rows reduced to 725 verified | The funnel expects about 99% discard. Budgets are per verified record. A site with fewer than 150 verified records is killed rather than padded. |
| Brief impressions then collapse to zero | The canary gate is not read before day 28 and needs two readings a week apart. |
| Site-wide algorithmic demotion of programmatic sites with AI text | No informational or "cost of" pages. No YMYL niches. Small sites. No appeal exists, so the response to a collapse is freeze, prune, and `D-SPAM-1`. |
| AI Overviews absorb informational clicks | Niche discovery measures AI Overview presence on live SERPs for the exact query set and kills above 25%. |
| The local pack sits above organic results on about 93% of local queries | A niche must offer at least 3 attributes that Maps lacks, collected from business websites. Without that there is no reason for a searcher to scroll past the pack. |
| Scraping Maps breaches Google's terms; Google v. SerpApi unresolved as of March 2026 | Data source is a human decision per site with the trade-off written out. Only facts are kept. Review text, photos and descriptions from Google are never stored or republished. |
| Ad networks screen for original content; domain-age rules | Monetisation is a human gate, attempted only after indexing is proven. The validation window is 270 days. |
| Agents report success that did not happen | Every gate is a script over saved files. Deploy success is judged by fetching the live pages. Revenue is recorded only from the operator's export of the network's own figures. |
| Revenue in this model comes from selling to businesses, which is not automatable | Paid listings and lead sales are out of scope in this version. Contacting businesses is disabled in `budget.yaml`. The spec is honest that this caps the upside. |
