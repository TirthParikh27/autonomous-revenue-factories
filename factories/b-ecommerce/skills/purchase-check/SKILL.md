---
name: purchase-check
description: Run or triage the scripted end-to-end test purchase and fulfilment check for a product. Use after every build, when the scheduled check has failed, or when a product past test_passed has no passing check in the last 26 hours.
---

# Purchase check

Stage 4 of Factory B. The check itself is a script with no model in it, run by GitHub Actions. This skill covers two cases: gating a newly built item, and triaging a failure. It exists because a documented agent-run test had a dead payment path while the agent reported "all clear". Read `CLAUDE.md` and `budget.yaml` first.

## What the script does (`tools/purchase_check/`, to be built)

For one product, in test mode:

1. Open the page as a new visitor. Assert it loads and the price equals the offer spec.
2. Follow the buy link and complete checkout with the processor's test card. (`digital`: Stripe test mode. `pod`: Shopify's test payment provider, name and behaviour to confirm at build time.)
3. Assert the processor's test data shows a successful payment for that session.
4. Assert fulfilment. `digital`: the post-payment page serves the file, HTTP 200, hash equals `delivery.json`. `pod`: a draft order with the right variant reaches the provider's sandbox or draft queue.
5. Assert the delivery email reaches the test mailbox within the limit in `budget.yaml` and is in the inbox, not spam.
6. Assert refund, privacy and contact links return 200.
7. Call one read endpoint with every credential the factory uses. Assert each succeeds.
8. For products that are live: also assert the production page returns 200, the live buy link resolves to a checkout page that loads, and the processor account reports that it can take charges and pay out (exact fields to confirm at build time). No live payment is made.

It writes `state/checks/<id>/<timestamp>.json` with each assertion, pass or fail, and raw evidence, tags the test order as a test, and posts to Slack itself on failure.

Limits to state honestly: a test-mode pass does not prove a live card will be charged. The operator's real purchase at launch covers that once. Whether Stripe's hosted checkout accepts a scripted test purchase must be confirmed at build time. If it does not, the fallback is to create the test payment by API and check fulfilment from there, which is weaker because it skips the page, and the report must say which mode ran.

## Cadence

- On every build, before `built -> test_passed`.
- Daily for every product past `test_passed`.
- Hourly while a spend test is active.

## Case A: gate a built item

1. Run the start-of-run checks in `CLAUDE.md`.
2. Read the newest file in `state/checks/<id>/` for the item's current commit. If none exists, trigger the workflow and exit with the item unchanged.
3. All assertions pass: set `stage: test_passed`, record the check file in `checks`, then raise `F-LIVE-1` with the shared `escalate` skill, using the packet contents listed in `ESCALATION.md`.
4. Any assertion fails: leave the item in `built` and record which. Third consecutive failure on the item: kill it.

## Case B: triage a failure on a product past `test_passed`

1. Read the failing check file. Do not re-run more than once, and wait 30 minutes before that one re-run.
2. Raise `F-PAY-1` immediately. Do not wait for the re-run. If telemetry shows an active campaign, the packet's first line asks the operator to pause it.
3. Identify the failed assertion and the last passing check. Count orders taken since then from the processor (count only).
4. Propose the fix in the packet. Make the fix on a branch only if it is inside `products/<id>/` or a test-mode object. Live-mode changes are the operator's.
5. If a customer may have paid without receiving the product, say so in the packet in the first three lines.

## Tools

Read access to `state/checks/`, the GitHub Actions workflow trigger, the processor read-only key for the order count. Nothing else.

## Deterministic check

The check file is the check. Your job is to read it accurately. Paste the failing assertion lines verbatim in the run report.

## Outputs

- Item transition or `F-PAY-1` / `F-LIVE-1` packet
- Run report ending with the shared `run-report` skill

## Stop conditions

- No check file newer than 26 hours for a live product: treat as a failure of the scheduler and raise `F-PAY-1`.
- The check script itself errors (not an assertion failure): report it as a failed check, not as "unknown".
- Three consecutive failed runs: `FAIL-3`.

## Never

- Never mark a check as passed from your own browsing or reasoning.
- Never edit `tools/purchase_check/`, its thresholds or its workflow.
- Never make a live-mode purchase or use a real card.
- Never count the test order as an order.
- Never close or downgrade `F-PAY-1`. Only a passing check and the operator do.
