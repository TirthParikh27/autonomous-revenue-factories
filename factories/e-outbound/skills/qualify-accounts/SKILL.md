---
name: qualify-accounts
description: Score signal_found leads against the approved offer's rules using the qualification script, and move each to qualified or killed with a reason. Use for the weekly qualification run of Factory E.
---

# Qualify accounts

Stage 2 of `FACTORY_SPEC.md`. The scoring is done by code. You run it, read its output and file the result. You do not overrule it.

## Inputs

- Lead items at `signal_found` (batch from `budget.yaml` `per_run.qualify-accounts`).
- The approved offer's rules: niche, signal types, exclusions.
- `budget.yaml`: `per_lead.min_sourced_facts`, `per_lead.max_signal_age_days`, `funnel_bands`.
- `state/suppression.jsonl`.

## Steps

1. Run the start-of-run checks in `CLAUDE.md`.
2. Run `checks/qualify_rules` over the batch. It applies, in order, and prints kept and removed counts per rule:
   - on suppression list
   - niche match
   - signal age within limit
   - at least the minimum number of facts with source, quote and date
   - consent basis is not `none` and has evidence
   - a contact route exists (`contact_page_url` for outbound, HubSpot record for inbound)
3. Run `checks/consent_record_lint`. An `express_inbound` record must name who, when and how. An `existing_relationship` record must point at HubSpot activity. An unconfirmed basis must carry the contact page URL, fetch date, a page snapshot path, a note that no statement refusing commercial messages appears, the named person or role, and one sentence on why the offer fits that role (Spam Act Schedule 2 clause 4(2); the sender bears the burden of proof).
4. Read the per-rule counts. If one rule removed more than the share in `funnel_bands` on a batch of 10 or more, stop. Do not transition anything. Raise `E-FUNNEL-1` with 5 example records.
5. Otherwise apply transitions: `qualified`, or `killed` with the rule name as the reason. Store the script's score in `scores`.
6. Write `state/funnel/<date>-qualify-accounts.json`.
7. Run `checks/funnel_invariants`.

## Tools

Read, Write, Bash for the check scripts. No web tools, no connectors.

## Deterministic check

- Every transition matches the output of `checks/qualify_rules`. The run fails if an item's new stage differs from the script's verdict.
- `checks/consent_record_lint` passes on every `qualified` item.
- `checks/funnel_invariants` passes: conservation, pass rate inside `qualify_pass_rate`, single-rule share under its limit.

## Outputs

Items at `qualified` or `killed`, the funnel file with per-rule counts.

## Stop conditions

- A funnel invariant fails.
- The rules script errors or is missing. Do not score by judgement instead.
- Pass rate under 10% for a second week: report it, the stage is paused per the spec.

## Never

- Never qualify a lead the script rejected, or kill one it passed.
- Never edit `checks/qualify_rules` or its thresholds. Propose a change through the weekly review.
- Never fetch anything from the web in this stage to "fill in" a missing fact.
- Never upgrade a consent basis. Only new evidence in HubSpot changes it.

End by calling the shared `run-report` skill.
