---
name: deliver-offer
description: Deliver the fixed-scope productised offer for a won client by working through the offer's checklist only. Use only in a hand-triggered Factory E run after E-CLIENT-1 is approved and the Stripe payment has been verified.
---

# Deliver offer

Stage 8 of `FACTORY_SPEC.md`. Delivery is the place this factory can turn into a job. The checklist in the offer file is the whole scope.

## Inputs

- One lead item at `won` or `delivering`.
- The approved `E-CLIENT-1` packet for that lead in `escalations/approved/` on `main`.
- The offer file: `scope_checklist[]`, `exclusions[]`, `delivery_hour_cap`.
- `budget.yaml`: `delivery`.
- Client inputs the operator has placed in `state/clients/<id>/inputs/`. You do not collect inputs from the client yourself.

## Steps

1. Run the start-of-run checks in `CLAUDE.md`. Confirm `delivery.client_work_enabled` is true and active clients are within `max_active_clients`. If not, stop.
2. Confirm payment: read the Stripe payment for this client with the read-only key. Record the reference. No payment, no work. Record the revenue line with the shared `ledger` skill if it is not already recorded.
3. Create or open `state/clients/<id>/delivery.json`: one entry per checklist line with `status`, `evidence`, `operator_minutes`.
4. Work the next unfinished checklist lines through the `demo-builder` agent. It works from the operator-provided inputs and the lead's facts only.
5. For each finished line, record evidence that a check produced: a test output, a rendered page status, a file hash. A line with no evidence is not finished.
6. Sum operator minutes from the operator's notes. At 80% of the hour cap raise `E-SCOPE-1`.
7. Anything the client asked for that is not a checklist line: do not do it, do not partly do it. Raise `E-SCOPE-1` with the request described in your own words.
8. When every line has evidence, write `state/clients/<id>/handover.md` for the operator: what was delivered, where it is, what the client must do, what is excluded. Leave the item at `delivering`. The operator hands over and the next telemetry run moves it to `delivered` when his hand-off note exists in HubSpot.

## Tools

`demo-builder` agent. Read, Write, Edit, Bash. Stripe connector, read only. HubSpot read. No Gmail.

## Deterministic check

- Stripe payment reference present and read in this run.
- Every checklist line has an evidence entry before the handover file is written.
- No file changed outside `state/clients/<id>/` and the delivery workspace named in the offer.
- Logged hours under the cap.

## Outputs

Delivery record, deliverables in the workspace named by the offer, handover note.

## Stop conditions

- No approved `E-CLIENT-1`, or no verified payment.
- Missing client inputs: report which, and stop. The operator asks the client.
- Hour cap reached. Any out-of-scope request.

## Never

- Never contact the client.
- Never accept access to a client's accounts or credentials. If delivery needs them, that is `E-ACCT-1`.
- Never deploy to anything the client owns. The operator does the hand-off.
- Never add "small extras". Extras are how this becomes a job.
- Never start a second client while one is in `delivering` unless `budget.yaml` allows it.

End by calling the shared `run-report` skill.
