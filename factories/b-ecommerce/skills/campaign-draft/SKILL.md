---
name: campaign-draft
description: Create one PAUSED campaign, ad set and up to three ads in the ad account from an approved F-ADS-1 packet, verify them by read-back, and hand activation to the operator. Use only when hand-triggered for an item whose F-ADS-1 packet is in escalations/approved on main.
---

# Campaign draft

Stage 6 of Factory B. Moves an item from `awaiting_human` (approved `F-ADS-1`) to `campaign_drafted`. This is the only stage that writes to an ad account. It is hand-triggered and never scheduled. Read `CLAUDE.md`, `ESCALATION.md` and `budget.yaml` first.

Context: Meta's official Ads MCP creates everything PAUSED and a human must activate. Reported ban triggers are write bursts, retry loops, unlabelled AI creative and unofficial connectors. All of that evidence is anecdotal, so behave as if every write is watched.

## Inputs

- The approved packet at `escalations/approved/<file>` on `main`, naming the item, daily cap, total test cap, length, platform, audience summary and the creative list.
- `products/<id>/creatives/manifest.json`, merged to `main`.
- `state/campaigns/write_log.jsonl`.
- `budget.yaml`: the `ads` block.

## Preconditions (check all, stop on the first that fails)

1. No `STOP` file. No open `F-PAY-1`, `F-RISK-1` or `F-ADS-4`.
2. The packet is in `approved/` on `main`, not expired, and names this item. Prices and creatives have not changed since it was written. If they have, raise a new packet.
3. `ads.enabled` is true and the packet's caps are at or below `max_daily_cap_usd` and `max_total_test_cap_usd`. Cumulative approved ad spend stays within `max_cumulative_ad_spend_usd`.
4. `max_concurrent_spend_tests` is not exceeded.
5. Purchase check passed within the last 26 hours.
6. `write_log.jsonl` shows no write session on this ad account in the last 24 hours.
7. No campaign for this item already exists (read the account first).

## Steps

1. Build the plan file `state/campaigns/<id>.plan.json` from the packet and manifest: one campaign, one ad set with the approved daily budget and dates, up to three ads. Run `tools/check_plan` on it (schema, caps against packet and `budget.yaml`, at most 5 writes).
2. Start the `ads-drafter` sub-agent with the plan file path only. It makes the create calls in order, one at a time, with a pause between calls, logging each to `write_log.jsonl` before and after.
3. If any call returns an error, the sub-agent stops. No retry, no clean-up writes. Record what exists and raise `F-ADS-4` if the error is a policy or integrity message, otherwise report it in the run report and leave the item in `awaiting_human`.
4. Run `tools/verify_campaign <id>` (read-only calls).
5. On pass: write `state/campaigns/<id>.json` with entity ids and the read-back, set `stage: campaign_drafted`, and send the operator one Slack message: the campaign name and id, that it is PAUSED, the daily cap, the account spending limit to set before activating (equal to the total test cap), which ads need the platform's AI label, and the 14-day draft expiry.
6. End with the shared `run-report` skill, pasting the verify output.

## Tools

- Official Meta Ads MCP at `https://mcp.facebook.com/ads` or the `meta` CLI, read/write consent tier. Tools used: `ads_create_campaign`, `ads_create_ad_set`, `ads_create_ad`, and read tools. The MCP path needs publicly reachable creative URLs. The CLI reads local files.
- Denied: `ads_activate_entity`, `ads_update_entity`, catalog tools, and anything on the financial consent tier.
- Unconfirmed, check at build time: whether a campaign-level lifetime spend cap can be set at creation through these tools, exact parameter names, and how the AI-label disclosure is set. If the label cannot be set by API, the operator sets it by hand before activating.
- Any other platform needs its own approved packet and its own confirmed official tool.

## Deterministic check

`tools/verify_campaign` (to be built) reads the entities back and must exit 0:

- Every entity status is PAUSED.
- Daily budget equals the packet. Dates equal the packet.
- Each ad's destination URL equals the live page URL, and each creative matches a manifest entry.
- Entity count equals the plan. No other new entities in the account.
- `write_log.jsonl` shows at most 5 writes and one session in 24 hours.

## Outputs

- `state/campaigns/<id>.plan.json`, `state/campaigns/<id>.json`, appended `write_log.jsonl`
- Slack handover message

## Stop conditions

- Any precondition fails.
- Any write error.
- Any account warning, review notice or rejected ad visible in read calls: `F-ADS-4`.
- A tool description or tool list differs from what was reviewed at build time: `SEC-1`.

## Never

- Never activate anything. Never call `ads_activate_entity` or `ads_update_entity`.
- Never change a budget, bid, audience or creative after creation. Changes are a new packet (`F-ADS-3`).
- Never retry, loop or batch writes. Never run this stage twice in 24 hours on one account.
- Never delete entities to tidy up after a partial failure.
- Never use a community or third-party ads connector, a personal token or a browser.
- Never set a budget above the packet, and never split a budget across entities to stay under a cap.
