---
name: wtp-spec
description: Stage 2 of Factory G. Use to turn one `discovered` item into a one-page spec with a named paying user, a price and scored willingness-to-pay evidence, or to kill it. This is the gate before any build. Not for research or code.
---

# WTP spec

Goal: decide, on evidence already collected, whether this tool deserves a build. Most items should be killed here.

## Inputs

- One item in `discovered`, oldest first, and its evidence array.
- The scout file it came from in `state/scout/`.
- `budget.yaml` (`wtp_gate`, `portfolio`, `risk`).
- `policy/<store>.yaml` if it exists for the target store.
- Existing specs in `state/specs/`, for the differentiation check.

## Steps

1. Preconditions. Stop with a run report if `STOP` exists, a cap is reached, `portfolio.max_items_in_build` is full, or `portfolio.max_new_specs_per_month` is reached.
2. Apply the kill list first. Kill the item, with the reason in `history`, if any of these hold: `wtp_prelim` below `wtp_gate.min_score`; fewer than `min_independent_sources`; no type A evidence; a generic AI wrapper; a clone or a cheaper copy of one incumbent; it depends on login-walled or personal data, an incumbent's private API, or getting around a platform restriction.
3. If the item is one scout run short of the threshold and `per_item.max_scout_runs` is not used up, leave it `discovered` with a note asking `gap-mine` for one more pass. Do this once only.
4. Write `state/specs/<id>.md`, at most one page, with this front matter and three short body sections (Problem, What it does, What it will not do):

```yaml
id: <item id>
store: chrome_web_store | shopify_app_store | other
paying_user: "<role> at <business type> who currently pays <incumbent> <price> for <job>"
price: {amount_usd: 0, model: monthly | one_off, trial_days: 0}
price_basis: "<which incumbent prices and which evidence lines justify it>"
wtp_evidence: [<copied evidence entries with type, source, author_key>]
wtp_score: 0
differentiator: "<one sentence: what this does that the named incumbent does not>"
billing_route: stripe | marketplace_billing | merchant_of_record | unknown
permissions: [<exact list>]
hosts: [<exact host patterns the tool touches>]
data_inventory: [{field: "", purpose: "", leaves_device: false, stored_where: "", retention: ""}]
acceptance_criteria: [<5 to 8 testable statements, including the paid unlock and the locked unpaid state>]
kill_numbers: {day_30_installs: 0, day_60_paid: 0, day_90_net_mrr_usd: 0}
open_questions: [<anything needing G-TOS-1, G-ACC-1, G-PAY-1 or G-LEGAL-1>]
```

5. Rules for the fields:
   - `paying_user` describes a role and business type backed by type A evidence. It is never a real person's name.
   - `price` sits at or below what the evidence shows people paying, and at or above the `wtp_gate` minimums.
   - `permissions` and `hosts` are the narrowest that deliver the paid feature. Prefer access the user grants per site or per action.
   - `kill_numbers` may be stricter than `budget.yaml`, never looser.
6. Run `spec-lint` (below). If it fails, fix the spec once. If it fails again, kill the item.
7. Raise escalations the spec implies, using the `escalate` skill, before the item can be built:
   - `G-PERM-1` if any host pattern is broader than named sites, or `data_inventory` contains anything other than the anonymous activation event.
   - `G-TOS-1` if `policy/` does not answer a store question the design depends on, or `billing_route` is `unknown`.
   - `G-ACC-1` and `G-PAY-1` if the accounts or live payment objects do not exist yet. Build may proceed in test mode while these wait.
   - `G-LEGAL-1` if the working name or listing would use an incumbent's or platform's name.
8. If nothing blocks, set the item to `specced`. If a blocking packet was raised, the `escalate` skill has set `awaiting_human`.
9. End with the `run-report` skill. Quote the `spec-lint` output.

## WTP score

Computed by the script from the typed evidence, not by you: A = 3 points (at most 2 counted), B = 2 points (at most 2 counted), C = 1 point (at most 2 counted), D = 4 points. D is a real payment or pre-order visible in Stripe, which can only exist after the operator approved a pre-sale under `GEN-1`. Pass needs the score at or above `wtp_gate.min_score`, at least `min_independent_sources`, and at least one A or D.

## Tools

Read, Write, Grep, Glob. Bash only to run `spec-lint`. No web tools. If the evidence is not enough, the answer is kill or one more scout pass, not your own browsing.

## Deterministic check

`spec-lint` (plain script, written at build time) exits 0 only if: every front-matter field is present and typed; `wtp_score` equals the recomputed score and passes the gate; every evidence source is a URL present in the scout file; `price` meets the minimums; `permissions` and `hosts` are non-empty lists; any wildcard host has an approved `G-PERM-1` packet id beside it; `differentiator` is present and the incumbent set does not match another spec; the body is under 400 words.

## Outputs

`state/specs/<id>.md`, the updated item file, any escalation packets, a run report.

## Stop conditions

- One item per run. Exit after it is specced, killed or escalated.
- Per-run caps reached: write the report with the item left `discovered`.

## Never

- Never raise the score by rewording evidence, or count two entries from the same author.
- Never invent a price, a user count or a quote. If the scout file does not contain it, it does not exist.
- Never state a store fee, revenue share or policy as fact. Write "unverified" and list it in `open_questions`.
- Never spec a tool with no payment in version 1.
- Never lower the gate. A proposal to change it is `G-SELF-1`.
