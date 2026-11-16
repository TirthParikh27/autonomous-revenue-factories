---
name: publish
description: Take tested actors to the Apify Store through the approval gate. Use when items are in `tested`, or when an `F-PUB-1`, `F-PUB-2` or `F-REP-1` packet has been approved and the listing must be verified. Prepares packets, never publishes by itself.
---

# Publish

You are a fresh session. Read `CLAUDE.md`, `budget.yaml` (section `portfolio`) and `ESCALATION.md` rows `F-PUB-1`, `F-PUB-2`, `F-CAP-1` first. Complete steps 1 to 3 of the operating loop.

The operator makes an actor public and sets its price in the Apify Console. You prepare the decision and then verify the outcome. `auto_actions.auto_publish` is false. If it is ever true, the publish action is still a token-holding workflow that checks for the approved packet, never a call from this session.

## Inputs

- Items in `tested` with a complete `unit_econ` block and a live-test result file.
- Items in `awaiting_human` whose publish or repair packet is in `escalations/approved/` or `rejected/`.
- Count of actors ever published (items that have ever been `live`), and all `live` and `degraded` items.

## Part A: new packets

1. Run `scripts/portfolio_gate`. It reports: live count against `max_live_actors`, 7 day green ratio against `min_green_ratio_7d`, any actor `degraded` longer than `max_days_degraded`, and duplicate or target-family conflicts for each `tested` item.
2. If the gate fails on cap or health: write no publish packet. Items stay in `tested`. Raise `F-CAP-1` only if the weekly review has asked for a cap change. Otherwise report "publish blocked by portfolio gate" and exit.
3. If an item fails on duplicate or `max_actors_per_target_family`: kill it.
4. Check staleness. If the live-test result is older than 7 days, send the item back through `live-test` first (it stays `tested`, note the reason). Prices and site behaviour move.
5. Choose the trigger. Fewer than `per_actor_approval_count` actors ever published: one `F-PUB-1` packet per actor. Otherwise: one `F-PUB-2` packet for up to `max_batch_size` actors.
6. Have the `publisher` sub-agent assemble each packet from files only, with every item `ESCALATION.md` lists for that trigger. In particular:
   - build hash and pull request link,
   - the approved `F-TGT-1` packet path for each target domain,
   - the gate lines copied from the live-test result file, with its path,
   - price per result and the event definition,
   - daily canary cost and the total daily canary cost of the portfolio after this publish,
   - predictions labelled as estimates,
   - the exact Console steps, as confirmed from Apify's docs in the spec's platform notes, and how to unpublish,
   - "If you say no": the item is killed and its spend is written off.
7. Use the shared `escalate` skill: write the packet, set `awaiting_human`, notify once.

## Part B: after a decision

8. Rejected packet: move the item to `killed` (never published) with the operator's reason, or back to `degraded` for a rejected repair.
9. Approved packet: check whether the operator has published. Have `publisher` fetch the public Store URL of the actor.
   - Listing not reachable yet: leave the item in `awaiting_human`, note it, and look again next run. Remind the operator once after 3 days. Paid pricing is reported to need a review of about 48 hours (unverified), so a delay is normal.
   - Listing reachable: verify the outcome with the deterministic check below, then move the item to `live`, set `published_at`, and hand it to `monitor`.
10. If anything on the listing differs from the approved packet (price, title, build), do not move to `live`. Report the difference and raise `GEN-1`.
11. For an approved `F-REP-1`: confirm the promoted build hash through the next canary result, then leave the stage change to `monitor`.

## Tools

- `publisher` sub-agent: Read, Write (packets and `state/publish/` only), WebFetch (public Store pages only).
- Bash: `scripts/portfolio_gate`, `scripts/validate_item`.
- GitHub connector to trigger a `canary` run for a newly listed actor.
- Shared `escalate` skill.

## Deterministic check

- Before a packet: `scripts/portfolio_gate` exit 0 for the items in the packet. Paste its output.
- Before `live`: (a) the Store URL was fetched in this run and returned the actor's listing, (b) the displayed price equals the approved price, (c) a `canary` workflow run triggered after publication is green and its build hash equals the approved hash. Paste the fetch status with a short body excerpt and the canary result line.

## Outputs

- Packets in `escalations/open/`, items in `awaiting_human`.
- After approval and verification: items in `live` with `apify_actor_id`, `published_at`, approved price.

## Stop conditions

- `STOP`, budget cap, portfolio gate failure.
- Any item in the batch missing an approved target packet or a passing `unit_econ` block: remove it from the batch and report it.

## Never

- Never make an actor public, set or change pricing, or accept platform terms. Never ask for a token to do so.
- Never treat a Slack reply or Linear comment as approval. Only the packet's location on `main` counts.
- Never include in a packet a build other than the one that passed live test.
- Never split a batch or re-raise a rejected packet to get around a decision.
- Never write a packet while the portfolio gate fails.
- Never present accrued or predicted revenue as fact in a packet.
- Never announce or promote the actor anywhere.

End by calling the shared `run-report` skill.
