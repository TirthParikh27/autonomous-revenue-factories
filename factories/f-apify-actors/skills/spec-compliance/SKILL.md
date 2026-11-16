---
name: spec-compliance
description: Compliance screen and actor specification for candidates. Use when items are in `discovered`, or when an `F-TGT-1` or `F-PII-1` packet has been approved. Either kills the item, escalates it, or writes the spec, fixture set and price hypothesis.
---

# Spec and compliance

You are a fresh session. Read `CLAUDE.md` (the compliance rules matter most here), `budget.yaml` and `ESCALATION.md` first. Complete steps 1 to 3 of the operating loop. Work on at most 2 items, highest score first.

## Inputs

- Items in `discovered`, and items in `awaiting_human` whose `F-TGT-1` or `F-PII-1` packet is now in `escalations/approved/`.
- `compliance/deny_list.yaml`, `compliance/allow_list.yaml`.
- The target's terms page and robots.txt, read through `store-scout`.

## Part A: compliance screen (always first, in this order)

1. Run `scripts/deny_check` on `target_domains`. Hit: move the item to `killed` with the matching entry as the reason. Stop work on it.
2. Personal data. If `scores.pii_flag` is true, or the wanted fields include anything about identifiable private individuals, raise `F-PII-1` and stop work on the item. Do not weigh it up yourself.
3. Ask `store-scout` for `state/scout/<item>-target.json`: the robots.txt rules for the needed paths (quoted), the lines of the terms that mention automated access, scraping or reuse (quoted, with URL and date), whether the data shows without login, and any challenge page, CAPTCHA or block seen on a plain fetch of one public page.
4. Kill without escalating when: the data needs a login or account, robots.txt disallows the needed paths, or a challenge or CAPTCHA appears on a plain request.
5. If any target domain is not on the allow list, raise `F-TGT-1` with the packet contents listed in `ESCALATION.md` and stop work on the item. You report what the terms say. You do not conclude that scraping is permitted.
6. Only items whose domains are all on the allow list (or have an approved packet naming them) continue to Part B.

## Part B: spec

7. Write `actors/<item-id>/SPEC.md` with exactly these sections:
   - **Purpose and user**: the Store query it answers, in one sentence.
   - **Input schema**: fields with defaults that give a small useful run with zero configuration.
   - **Output schema**: reference to `fixtures/<item-id>/expected.schema.json`, with required fields marked.
   - **Method**: plain HTTP or browser, and why. Request rate, concurrency, retry policy.
   - **Bounds**: maximum runtime, maximum items, early exit on no results.
   - **Egress**: the host list, identical to `target_domains`.
   - **Pricing**: pay-per-event, price per result, the event definition, and the doc URL and date where the event rules were confirmed.
   - **Platform notes**: the template to start from, the pay-per-event charging call and the build procedure, each with the official Apify doc URL and date, read through `store-scout` from docs.apify.com. The builder has no web tools, so anything left "unconfirmed" here blocks the build. If the docs cannot settle a point, keep the item in `discovered` and raise `GEN-1`.
   - **Predictions**: users at 30 days, cost per result, both labelled as estimates.
   - **Acceptance criteria**: numbered and testable, used by the verifier.
8. Write `fixtures/<item-id>/inputs.json`: 5 to 10 fixed inputs. Include one that returns zero results, one with pagination, and one edge case with unusual characters. Mark 3 as the canary subset.
9. Write `fixtures/<item-id>/expected.schema.json` and, per input, the minimum result count and the fields that must not be null.
10. Request snapshots: trigger the `capture-fixtures` GitHub Actions workflow for the item (through the GitHub connector). It makes at most 10 polite requests and commits raw responses to `fixtures/<item-id>/snapshots/`. Do not fetch raw pages yourself.
11. Record `fixture_set_hash` in the item (hash of `inputs.json` and the schema). The fixture set is fixed from here on. Changing it later needs a note in the run report and a new hash.
12. Run the deterministic check, then move the item to `specified`.

## Tools

- `store-scout` sub-agent for all web reads.
- Bash for `scripts/deny_check`, `scripts/validate_spec`, `scripts/validate_item`.
- GitHub connector to trigger `capture-fixtures` and read its result.
- Shared `escalate` skill.

## Deterministic check

`scripts/validate_spec <item-id>` must exit 0: all sections present, 5 to 10 fixtures with a zero-result case and 3 canary inputs, egress hosts equal `target_domains`, bounds set, price within `unit_economics.max_price_per_result_usd`, every domain on the allow list, snapshots present for each fixture. Paste the output in the run report.

## Outputs

- `killed`, `awaiting_human` (packet in `escalations/open/`), or `specified` with `SPEC.md` and `fixtures/<item-id>/`.

## Stop conditions

- `STOP`, budget cap, or scout cost for the item above `per_item.max_scout_usd`: kill the item with that reason.
- The terms page or robots.txt cannot be fetched: do not assume. Report it and leave the item in `discovered` for one retry. On the second failure raise `F-TGT-1` with "could not read terms" stated.
- `capture-fixtures` returns block or challenge responses: kill the item.

## Never

- Never write a spec for a domain that is not on the allow list.
- Never add or remove entries in `compliance/`.
- Never describe a target as "legal" or "allowed to scrape". Quote and stop.
- Never design around a block: no proxies, no header spoofing to imitate a logged-in user, no CAPTCHA services.
- Never include a personal-data field without an approved `F-PII-1` packet that names it.
- Never set a price above the ceiling or leave bounds unset to make the spec simpler.

End by calling the shared `run-report` skill.
