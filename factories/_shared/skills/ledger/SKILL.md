---
name: ledger
description: Record spend and revenue for a factory, and check remaining budget. Use before any paid call, after any run, and whenever revenue is pulled from a payment processor, marketplace or broker.
---

# Ledger

Formats are defined in `factories/_shared/CONVENTIONS.md`. Files are `ledger/spend.jsonl` and `ledger/revenue.jsonl`. Both are append-only.

## Before a paid action

1. Sum this month's `usd` in `ledger/spend.jsonl` by category.
2. Compare against `budget.yaml`. If the action would take any category or the monthly total past its cap, do not do it. Raise the factory's budget trigger with the `escalate` skill.
3. If the price of the action is unknown, find out before acting. Do not guess low.

## Recording spend

- One line per paid event, written when the cost is known, with the vendor's own figure as `source`.
- Token cost comes from the run's reported cost. The wrapper normally writes this. Do not double count.
- Subscriptions are recorded on the day they bill, with the item set to null.
- Attribute to an item when the spend was for that item, and add the amount to the item's `spend_usd`.

## Recording revenue

- Only from a source of truth: a payment processor record, a marketplace payout or earnings page, a broker statement. Include the reference.
- Record net of platform and processing fees and set `net_of_fees` accordingly. If only gross is known, record gross and say so.
- Refunds and chargebacks are negative revenue lines that reference the original.
- Paper-trading results, projected revenue, pipeline value and "verbal yes" are never revenue.

## Never

- Never edit or delete a ledger line. Add a correcting line.
- Never record revenue you did not read from the source during this run.
- Never report a profit figure without subtracting recorded spend.
