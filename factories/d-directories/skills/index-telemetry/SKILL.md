---
name: index-telemetry
description: Pull indexing, search, traffic and revenue figures for every live site from their sources of truth, store them, and evaluate the canary and scale gates by script. Use for the daily telemetry run.
---

# Index telemetry

You are running stage 7 of Factory D. Assume no prior context. Read `CLAUDE.md` and `budget.yaml` (sections `indexing`, `validation`, `winner`, `per_run.index_telemetry`) first.

Indexing is outside your control and has no appeal. Your job is to measure it honestly and let the gate script decide.

## Inputs

- Items at `canary_live`, `index_confirmed`, `scaled`, `monetised` or `winner`.
- `state/metrics/<id>/`: earlier daily files.
- `state/metrics_inbox/` and `state/revenue_inbox/`: exports placed by the operator.
- The live URL list for each site from `build_manifest.json` or `canary_set.json`.

## Steps

1. **Served check.** Fetch a random 10 live URLs per site plus the sitemap. Record statuses. If any fail, report it first in the run report.
2. **Search Console.** For each site read, for the site's own property: per-URL index status for every submitted URL (or for the canary set while at `canary_live`), and impressions, clicks and average position by page for the trailing 28 days. The verified route (2026-11-16) is the Search Console API with a read-only service account that the operator has added to the property. If that is not set up, read the operator's latest export in `state/metrics_inbox/` and record its date. If there is no data newer than 10 days, say so and do not evaluate any gate.
3. **Traffic.** Read sessions and outbound clicks for the trailing 30 days from PostHog web analytics for each site.
4. **Revenue.** Read any new file in `state/revenue_inbox/`. For each payout or earnings line that carries a network reference, append a revenue line with the `ledger` skill. If there is no file, record no revenue. Outbound clicks and estimates are never revenue.
5. Write `state/metrics/<id>/<date>.json` with every number, its source and the time it was read.
6. Run `tools/eval_gates state/metrics/<id>/ budget.yaml`. It computes `index_ratio` (indexed submitted URLs divided by submitted URLs), and returns one of: `not_decidable`, `canary_pass`, `canary_fail`, `canary_remediate`, `scale_pass`, `scale_fail`, `hold`.
7. Apply the result:
   - `not_decidable` or `hold`: no transition.
   - `canary_pass`: move `canary_live` to `index_confirmed` and store the script's output hash in the history entry.
   - `canary_remediate`: stay at `canary_live`, set `scores.remediation_started` to today, and note that the weekly review must produce the remediation pull request. Only one cycle is allowed.
   - `canary_fail`: move to `killed` with the reading series as the reason.
   - `scale_pass`: no transition. Note that `canary-deploy` Mode C may prepare the next tier.
   - `scale_fail`: note that the weekly review must prune to the previous tier. A site at `scaled` moves to `index_confirmed` once the prune is merged.
8. **Alarms.** Raise `D-SPAM-1` if: a manual action is reported; indexed pages fell more than 50% within 14 days; or impressions have been zero for 7 consecutive days after being above zero.
9. **Checkpoints.** Compare against `validation.checkpoints` and the validation budget from the ledger. Raise `D-KILL-1` when its condition in `ESCALATION.md` is met.
10. **Winner.** If `tools/eval_gates` reports the winner metrics met from ledger and metric files, move `monetised` to `winner`.
11. End with the `run-report` skill. Give the index ratio as a fraction with its counts, for example "23 of 40".

## Tools

- Search Console data access for the operator's own properties (Search Console API, read-only service account, scope `webmasters.readonly`; no official MCP exists and community servers are not used).
- PostHog connector, read only.
- HTTP fetch of the sites' own URLs.
- `tools/eval_gates`.
- Shared skills: `escalate`, `ledger`, `run-report`.

## Deterministic check

`tools/eval_gates` is the check. It enforces: no canary result before `gate_min_days`; a pass needs `min_index_ratio_to_pass` on two readings at least 7 days apart and impressions above zero in the trailing 7 days; the deadline, kill ratio and single remediation cycle from `budget.yaml`; scale results need `scale_hold_days` at the current tier. The wrapper also requires today's metrics file to exist for every live site.

## Outputs

- `state/metrics/<id>/<date>.json` per live site.
- Revenue ledger lines with source references.
- Gate transitions, alarms and checkpoint escalations.

## Stop conditions

- Search Console data unavailable or stale: record, evaluate nothing, exit normally.
- A metrics source returns values that contradict the previous day by an impossible amount (for example more indexed URLs than submitted): record both, evaluate nothing, report.

## Never

- Never evaluate the canary gate yourself or before day 28. An early burst of impressions is the documented prelude to zero.
- Never count a URL as indexed because a search for it returned a result, or because the sitemap was read. Only the Search Console status counts.
- Never query Google Search to check rankings or indexing. That is automated querying of Google.
- Never record revenue without a network reference read in this run.
- Never request indexing, resubmit sitemaps or change the site from this stage.
- Never round an index ratio up to the threshold.
