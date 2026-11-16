---
name: telemetry
description: Pull orders, refunds, disputes, payouts, ad spend and visits from the sources of truth, compute contribution margin, apply kill and risk thresholds, and record ledger lines. Use for the daily telemetry run.
---

# Telemetry

Stage 7 of Factory B. Read-only against every external system. It applies thresholds and moves items between `campaign_drafted`, `spend_test`, `winner`, `iterating`, `live` and `killed`. Read `CLAUDE.md`, `ESCALATION.md` and `budget.yaml` first.

## Inputs

- Item files past `test_passed`, `state/offers/<id>.econ.json`, `state/campaigns/<id>.json`.
- `state/checks/` (latest result per product), `state/credentials.md` (names and expiry dates only).
- Yesterday's `state/metrics/<date>.json`.

## Steps

1. Run the start-of-run checks in `CLAUDE.md`.
2. Health first. For each product past `test_passed`: is the newest check passing and under 26 hours old? If not, raise `F-PAY-1` (see the `purchase-check` skill, case B). Check each scheduled stage's last run time in `journal/`. A stage more than two intervals late is reported, and escalated under `F-PAY-1` on the second miss. Any credential within 14 days of expiry: `F-CRED-1`.
3. Pull from the processor (read-only key): charges, refunds, disputes, fees, payouts and any hold or review notice, since the last pull. Exclude orders tagged as test. Keep reference ids, amounts, currency, country. Do not copy names, emails or addresses.
4. `pod` only: pull provider invoices for COGS.
5. Ads: read campaign status and spend for each item with `state/campaigns/<id>.json` (read-only consent tier). Use billed spend for the ledger where available and insights for the daily view, and label which. If a `campaign_drafted` item now reads as active, set `stage: spend_test` and record the activation date. If any active campaign has no approved packet, raise `F-ADS-2`.
6. Pull page visits and funnel events from PostHog.
7. Write `state/metrics/<date>.json`, then run `tools/reconcile` (check below).
8. Write ledger lines with the shared `ledger` skill: revenue net of fees with the processor reference, refunds and disputes as negative lines, ad spend under category `ads`.
9. Compute per product, using `tools/unit_econ --observed`: verified orders, net revenue, refund rate, contribution margin before and after ads, CAC against target, ROAS against break-even ROAS. Fewer than 10 orders: report the raw counts and "insufficient data". No rates, no trend language.
10. Apply thresholds from `budget.yaml`, in this order:
    - Risk (`F-RISK-1`): any dispute, refund thresholds, any hold notice. Freeze launches and drafts.
    - Spend-test kill rules and cap overrun: raise `F-ADS-2`, first line "Pause campaign <id> now". Set the item to `awaiting_human`. It becomes `killed` once telemetry reads the campaign as paused.
    - Winner test at the end of the approved test: all conditions hold, set `winner`. Some fail and iterations remain: set `iterating` and name the single change to test. Otherwise kill (via `F-ADS-2` if still spending).
    - Organic window: a `live` item past `organic_window_days` with no verified order and no approved `F-ADS-1` is killed. Note in the report that the operator should retire the live payment link.
    - Tax re-trigger points: `F-TAX-1`.
    - Customer contact or refund request visible in processor data: `F-CUST-1`.
11. Check the factory validation budget and window: `BUD-2` if exhausted without verified revenue.
12. Post one Slack line: verified orders, net revenue, ad spend, contribution margin after ads, open escalations. End with the shared `run-report` skill.

## Tools

- Stripe connector read tools (`stripe_api_read`, `get_balance_summary`) with a read-only restricted key that carries the Agent tag (required by the Stripe MCP from December 2026). Shopify read scope for orders and payouts.
- Meta Ads MCP insights and read tools on the read-only consent tier.
- PostHog connector.
- Slack and Linear for escalations only.

## Deterministic check

`tools/reconcile` (to be built) must exit 0:

- Order count and net amount in the metrics file equal a fresh count from the processor for the same period.
- No test-tagged order is included.
- Every revenue ledger line written in this run has a processor reference that exists.
- PostHog purchase events are within 10% of processor charges. A larger gap is reported as a tracking fault and the processor figure is used.
- Ad spend recorded is at or below the approved caps, otherwise the tool prints the overrun for `F-ADS-2`.

## Outputs

- `state/metrics/<date>.json`, ledger lines, item transitions, escalation packets, Slack line

## Stop conditions

- A source of truth cannot be read: do not estimate. Record the failure, raise `F-PAY-1` (credential read failure), and write no revenue lines for that source.
- A credential allows writes: report it under `SEC-1` and use read calls only.

## Never

- Never write to the processor, the store or the ad account. No refunds, no pauses, no edits.
- Never record revenue from PostHog, from an order notification email or from memory.
- Never report revenue without ad spend and contribution margin beside it.
- Never call a product a winner on fewer than 10 verified orders.
- Never store customer personal data.
