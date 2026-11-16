---
name: draft-outreach
description: Draft the first-touch message and call script for demo_verified leads, create Gmail drafts without sending, mirror the lead to HubSpot, and hand a send packet to the operator. Use for the Factory E drafting run. Never sends.
---

# Draft outreach

Stage 5 of `FACTORY_SPEC.md`. Output is a Gmail draft and a send packet. The operator sends, or does not.

## Inputs

- Lead items at `demo_verified`.
- `state/sender.json`: operator name, business name, ABN, contact details, opt-out wording. If any field is empty, stop.
- The offer file. `budget.yaml`: `messages`, `volume.max_open_drafts`, `volume.max_send_packet_size`.
- `state/suppression.jsonl`.

## Steps

1. Run the start-of-run checks in `CLAUDE.md`. Count leads at `draft_ready` and `awaiting_human` under `E-SEND-1`. Stop if at `max_open_drafts`.
2. Check each lead against the suppression list again. Check its `demo_url` still returns 200.
3. Write `state/drafts/<id>.json` with: subject, body, call script, the fact indexes each sentence relies on, and the consent record. Rules for the body:
   - At most `first_touch_max_words` words. Plain text.
   - One specific observation from the lead's facts, the demo link, what the offer is in one sentence, a low-pressure ask.
   - At most one link.
   - Sender name, business name and ABN. A plain opt-out line such as "Reply 'no' and I will not contact you again."
   - A subject that says what the message is. No "Re:", no fake familiarity, no urgency.
   - No claim that the page was made by hand. No claim about results for other clients unless the offer file lists a verified one.
4. Run `checks/draft_lint` on each file. One rewrite on failure, then kill.
5. Give `outreach-publisher` the validated draft files. For each it:
   - creates a Gmail draft. Recipient is empty for outbound leads. For inbound leads the recipient is the address on the HubSpot record.
   - reads the draft back by id and compares subject and body hash.
   - creates or updates the HubSpot company and a deal in the first pipeline stage, with the demo URL and item id, then reads the record back.
6. Move leads with a confirmed draft to `draft_ready`.
7. Write one send packet with the shared `escalate` skill, trigger `E-SEND-1`, covering up to `max_send_packet_size` leads, with the fields listed in `ESCALATION.md`. Put a plain warning beside every lead whose consent basis is unconfirmed. Move those leads to `awaiting_human`.
8. Write `state/funnel/<date>-draft-outreach.json`. Run `checks/funnel_invariants`, which compares draft ids on items with `list_drafts`.

## Tools

Gmail `create_draft`, `list_drafts`, `get_draft`. HubSpot `search_crm_objects`, `manage_crm_objects`. Slack and Linear only through `escalate`. Read, Write, Bash for checks.

## Deterministic check

- `checks/draft_lint` passed for the exact text placed in the draft.
- Draft exists when read back by id, with matching hash and, for outbound, no recipient.
- HubSpot record read back with the item id.
- Count of drafts equals count of leads moved.

## Outputs

Gmail drafts, `state/drafts/` files, HubSpot company and deal records, one send packet, items at `awaiting_human`.

## Stop conditions

- Open-draft cap reached. An earlier packet is still open and unexpired: add no second packet.
- `create_draft` unavailable or the read-back differs: stop, report, leave items at `demo_verified`.
- The operator left more than half of two consecutive packets unsent: stage paused per the spec.

## Never

- Never call a Gmail send, reply or forward tool.
- Never put a web-found address in a draft, an item, HubSpot or the packet.
- Never draft for a lead with no consent record.
- Never write follow-ups here. They belong to `handle-replies`.
- Never notify the operator per lead. One packet a run.

End by calling the shared `run-report` skill.
