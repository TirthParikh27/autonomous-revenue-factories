---
name: monetise
description: Check whether an indexed site meets a monetisation programme's entry requirements, draft the application packet for the operator, and after approval add affiliate links or ad code with mandatory disclosure. Use for the monthly eligibility check, or when a D-MON-1 packet has been approved.
---

# Monetise

You are running stage 8 of Factory D. Assume no prior context. Read `CLAUDE.md` and `budget.yaml` (sections `monetisation`, `disabled_until_raised`, `per_run.monetise`) first.

Be honest in every packet: the research found no verified revenue figure for an agent-built directory. Display ads at the one average seen (about USD 11 per 1,000 sessions on Journey, anecdotal) need roughly 27,000 monthly sessions to earn USD 300 a month. The self-reported affiliate figure (about USD 600 a month on 5,000 to 20,000 visits) comes from someone who sells a site builder. Paid listings and lead sales need outreach to businesses, which is disabled.

## Inputs

- Items at `index_confirmed` or `scaled`.
- Latest `state/metrics/<id>/` files: sessions, clicks, index ratio.
- The item's `canary_started` date and domain registration date, for domain-age rules.
- The monetisation route named in the niche brief.

## Mode A: eligibility check and packet

1. For each item, compute from metric files: trailing 30-day sessions, domain age in days, index ratio, share of traffic by country if available.
2. Compare with the programme named in the brief. Entry requirements as read in the research, all to be re-read on the programme's own page before the packet is written:
   - Affiliate programme in the niche: requirements are programme specific and were not researched.
   - Journey by Mediavine: 1,000 sessions from Tier 1 countries in 30 days (verified 2026-11-16). At least four months of domain history, Grow installed for 30 days, "original and helpful content" (read January 2026).
   - Mediavine: USD 5,000 of annual ad revenue. The old 50,000-sessions test is gone (verified 2026-11-16).
   - Raptive: 25,000 monthly pageviews with 50% tier-1 traffic (verified 2026-11-16). Domain at least six months old (read January 2026).
   - Ezoic: 250,000 monthly active users since February 2026. AdSense: no traffic minimum. Both from secondary sources only.
3. If the item meets no programme's requirements, write the gap in the run report and exit. Do not raise a packet to ask whether to apply early.
4. If it meets one, re-read that programme's requirements and terms on the programme's own pages. Record the URL and date. Note any term that affects a directory: original content rules, restrictions on link placement, prohibited content.
5. Draft the `D-MON-1` packet with the `escalate` skill, one programme per packet, with everything `ESCALATION.md` requires. Label every revenue number as an estimate and give its basis. State the worst case, including rejection for templated content and the effect of ad code on page quality.
6. Prepare, on a `claude/` branch but without opening a pull request, the exact change that would be made: disclosure wording, placement, the link or ad-slot component with placeholder ids.
7. The item moves to `awaiting_human`. End with the `run-report` skill.

## Mode B: after approval

1. Confirm the packet is in `escalations/approved/` and that the operator has recorded, in the packet or a commit, that they joined the programme and supplied the publisher or affiliate id through the agreed secret route. If not, exit. You never apply, sign up or accept terms.
2. Have the `site-builder` agent apply the prepared change:
   - Affiliate links only on pages where the linked offer is relevant to the listing or category.
   - A clear disclosure in plain words above the first affiliate link on every such page, and on the disclosure page. Not in a footer only, not behind a tooltip.
   - Affiliate links carry the sponsored rel attribute.
   - Ad code only in the slots named in the packet.
3. Run `tools/check_disclosure sites/<id>/`, `tools/check_build` and the three content QA scripts. All must pass.
4. Open a pull request. The operator's merge deploys it. This merge is covered by the approved `D-MON-1` packet only if the change matches the packet exactly; otherwise raise a new packet.
5. After the merge, fetch five monetised pages and confirm the disclosure text is present in the served HTML above the first affiliate link. Then set the item's `monetisation` field, set `scores.monetised_on` to today, and move the item to `monetised`.
6. End with the `run-report` skill.

## Tools

- Repo and git. HTTP fetch of the programme's public requirement pages and of the site's own URLs.
- `site-builder` agent.
- `tools/check_disclosure`, `tools/check_build`, content QA scripts.
- Shared skills: `escalate`, `ledger`, `run-report`.

## Deterministic check

`tools/check_disclosure` exits 0 only if: every built page containing a link to a domain in the affiliate domain list has the disclosure block earlier in the document than the first such link; every such link has the sponsored rel attribute; the disclosure page exists and names the programme type; no affiliate link appears on a page type the packet did not list. Paste its output line. Mode B also requires the post-merge served-HTML check.

## Outputs

- `D-MON-1` packet, prepared branch, later a pull request.
- Item at `awaiting_human`, then `monetised`.

## Stop conditions

- The programme's current requirements differ from the research notes: use the current ones, and say so in the packet.
- The programme's terms prohibit sites built from third-party or scraped data, or the approved data source conflicts with them: stop and say so in the packet. Do not apply anyway.
- A `D-SPAM-1`, `D-LEGAL-1` or `D-PII-1` packet is open for the site.

## Never

- Never create an account, submit an application, accept terms or enter payment or tax details.
- Never add an affiliate link or ad code before the packet is approved and the operator has joined.
- Never publish an affiliate link without disclosure, or style the disclosure to be missed.
- Never write comparison, review or "best of" content to carry affiliate links.
- Never contact a listed business to sell a listing, a lead or placement.
- Never record expected, pending or estimated earnings as revenue.
