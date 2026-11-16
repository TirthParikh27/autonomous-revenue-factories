---
name: build-demo
description: Build the per-lead audit or demo page data for qualified leads using the single approved template. Use for the Factory E demo generation run, or when a qualified lead needs its demo data file written.
---

# Build demo

Stage 3 of `FACTORY_SPEC.md`. The demo is one approved template plus one data file per lead. You write data, never per-lead code. The `demo-builder` agent does the writing.

## Inputs

- Lead items at `qualified` (batch from `budget.yaml` `per_run.build-demo`).
- The offer's `demo_template` id and the template's data schema in `demos/schema.json`.
- The lead's `signals[]` and `facts[]` only. Not the raw pages.
- `budget.yaml`: `per_lead.max_token_usd_demo`, `volume.max_live_demo_pages`.

## Steps

1. Run the start-of-run checks in `CLAUDE.md`. Confirm an approved `E-PUB-1` packet exists for the current template version. If not, you may still write data files but nothing will deploy. Say so in the report.
2. Stop if live pages plus this batch would pass `max_live_demo_pages`.
3. For each lead, have `demo-builder` write `demos/data/<slug>.json` where `<slug>` is a random unguessable token stored on the item, not the business name.
4. Every statement about the lead in the data file is an entry that references a `facts[]` index. Free text fields may describe the offer and what the audit checked. They may not describe the lead.
5. Findings are stated as observations with their source, for example "Your booking page returned this message on 14 Nov" with the quote. No scores presented as measurements, no money figures, no comparisons with named competitors.
6. Include the fixed blocks the template requires: who made the page, the removal link, the date the facts were checked.
7. Run `checks/demo_data_schema` on each file. On failure, one rebuild. On second failure, kill the lead.
8. Record token cost per lead. Above the cap, kill the lead with reason `demo_cost`.
9. Move passing leads to `demo_built`. Write `state/funnel/<date>-build-demo.json`. Run `checks/funnel_invariants`.

## Tools

`demo-builder` agent. Read, Write, Edit, Bash for checks. No web tools, no connectors, no deploy command.

## Deterministic check

- `checks/demo_data_schema` passes.
- Every lead-specific field resolves to a fact index that exists.
- No field contains an email address, phone number, image URL on the lead's domain, or more than 25 consecutive words copied from a fact quote.
- Per-lead cost at or under the cap.

## Outputs

`demos/data/<slug>.json` on the run branch, items at `demo_built` with the slug.

## Stop conditions

- Template or schema missing.
- Live page cap reached.
- Two leads in one batch killed for cost: stop and report, the template is too heavy.

## Never

- Never fetch the lead's site here. If a fact is missing, the lead goes back through QA failure or is killed.
- Never use the lead's logo, photos, brand colours as assets, or copied marketing text.
- Never write a claim with no fact behind it, including flattering ones.
- Never generate a separate app, repo or codebase for a lead.
- Never deploy. Deployment belongs to the CI job after QA.
- Never change the template. That is `E-PUB-1`.

End by calling the shared `run-report` skill.
