---
name: offer-spec
description: Turn a discovered item into an offer spec with unit economics (price, COGS, fees, target CAC, break-even ROAS) and let the calculator pass or kill it. Use when items are waiting in the discovered stage, or when an item returns from iterating for a price change.
---

# Offer spec

Stage 2 of Factory B. Moves items from `discovered` (or `iterating`) to `specced` or `killed`. Read `CLAUDE.md` and `budget.yaml` first.

## Inputs

- Item files in `discovered`, or in `iterating` with an approved `F-PRICE-1` packet.
- The item's evidence array and `state/scout/` file.
- `budget.yaml`: `unit_economics_thresholds` and its `assumptions`.
- Observed fees and refund rate in `state/metrics/`, if any product has had orders. Observed values replace assumptions.

## Steps

1. Run the start-of-run checks in `CLAUDE.md`.
2. Take at most 3 items, oldest first.
3. For each, write `state/offers/<id>.yaml` with these fields:
   - `product`: what the buyer receives, in one paragraph. For `digital`: file types and how it is delivered. For `pod`: garment or object, print provider country, production and delivery time.
   - `buyer`: who buys and the problem it solves, tied to evidence in the item file.
   - `price` and `currency`. Justify against prices seen in the evidence. Do not invent a "was" price.
   - `cogs`: 0 for `digital` apart from per-order delivery cost. For `pod`: base cost plus domestic shipping from the provider's published price list, with URL and date. If the price list was not read in this run, mark `unverified` and stop on that item.
   - `fees`: payment and platform fees. Use observed figures, otherwise the assumptions in `budget.yaml`, and label which.
   - `refund_allowance`, `tax_handling` (state `unresolved` until `F-TAX-1` is decided).
   - `claims_allowed`: the specific factual statements the page and ads may make, each one checkable against the product.
   - `policies_needed`: refund, delivery, privacy, contact.
   - `distribution`: where buyers would come from at zero spend, stated honestly. If the answer is "nowhere without ads", write that.
4. Run `tools/unit_econ state/offers/<id>.yaml`. It writes `state/offers/<id>.econ.json` with: contribution margin before ads (amount and fraction), break-even CAC, break-even ROAS (price divided by contribution margin before ads), target CAC, and pass or fail against the thresholds.
5. Run `tools/claims_lint` on `claims_allowed` and the product description.
6. Pass: set `stage: specced`, set `offer` to the spec path. Fail: set `stage: killed` with the failing threshold as the reason. Do not escalate a numeric fail.
7. End with the shared `run-report` skill, pasting the calculator output line for each item.

## Tools

Repo files and the two deterministic tools only. No web access is needed. If a supplier price must be read, hand that to the `market-scout` sub-agent and use its structured output.

## Deterministic check

- `tools/unit_econ` exit code and its pass field decide the transition.
- `tools/claims_lint` must exit 0.
- The spec validates against `tools/schemas/offer.schema.json` (to be built).

You may not edit the `.econ.json` file. If you think the calculator is wrong, say so in the run report and leave the item where it is.

## Outputs

- `state/offers/<id>.yaml` and `state/offers/<id>.econ.json`
- Updated item files

## Stop conditions

- An input the calculator needs is unknown and cannot be read from a source in the repo: leave the item in `discovered` and list what is missing under "Not done".
- The offer only works with a claim the lint blocks: kill.
- The offer needs a new account or paid tool to price it: raise `F-ACCT-1`.
- Tax treatment would change the pass or fail result: note it and raise `F-TAX-1` if not already open.

## Never

- Never change an assumption, the refund allowance or the price to turn a fail into a pass.
- Never use a margin, conversion rate or CAC figure from a vendor blog as an input. The research found none with a traceable source.
- Never state projected revenue or profit. The spec contains per-order economics only.
- Never include reviews, ratings or testimonials in `claims_allowed`.
- Never spec a product whose value depends on a health, safety, income or guaranteed-result claim.
