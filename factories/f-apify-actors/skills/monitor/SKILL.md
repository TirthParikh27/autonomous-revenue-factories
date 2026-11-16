---
name: monitor
description: Daily telemetry and breakage detection for published actors. Use on the daily monitor schedule, and whenever a canary or cost alarm has fired. Reads canary and stats files produced by GitHub Actions, applies health and cost verdicts, queues repairs, records earnings from the payout page, and raises economics, cost, retire and legal escalations.
---

# Monitor

You are a fresh session. Read `CLAUDE.md`, `budget.yaml` (sections `monitoring`, `winner`, `validation`) and `ESCALATION.md` first. Complete steps 1 to 3 of the operating loop. Cover every `live` and `degraded` item. This stage has priority over all others.

Data collection has no model in it. Two scheduled GitHub Actions workflows run before you:

- `canary`: for each live actor, runs the 3 canary fixtures against the live target, validates the output against the schema, and writes `state/metrics/canary/<date>.json` (pass or fail per fixture, error excerpt, build hash, cost).
- `pull-stats`: with a read token, pulls per-actor runs, failed runs, distinct users, platform cost and open Store issues into `state/metrics/runs/<date>.json`, `costs/<date>.json` and `store/<date>.json`, then runs `scripts/health_gate` and writes `state/metrics/health/<date>.json`. It posts cost alarms to Slack itself.

The API endpoints these workflows use were not verified in the research. If a field is missing from the files, report it as missing. Do not estimate it.

## Steps

1. Freshness. If today's canary or health file is missing or older than 26 hours, the monitoring itself is broken. Report it, notify Slack once, and treat every live actor's health as unknown, not as green. Two days in a row is `GEN-1`.
2. Read `state/metrics/health/<date>.json`. Apply each verdict exactly as written:
   - `degrade` (canary failed `canary_failures_to_degrade` days running, or user-run failure rate above the limit with at least 10 runs): move `live -> degraded`, write `state/repairs/<id>-<date>.md` with the failing fixtures and error excerpts, and trigger `capture-fixtures` for fresh snapshots. The next `build-actor` run picks it up.
   - `recovered` (repair promoted and canary green 2 days running): move `degraded -> live`.
   - `cost_alarm`: raise `F-COST-1` with a 24 hour expiry.
   - `negative_profit`: raise `F-ECON-1`.
   - `retire_candidate` (any retire rule in `FACTORY_SPEC.md` section 6): add to `state/retire_queue.json` for the weekly review, which raises `F-RET-1`. If the actor is red for more than `max_days_degraded` days, raise `F-RET-1` now.
3. A canary failure that shows a challenge page, CAPTCHA or systematic 403 or 429 is a block, not a bug. Write that in the repair note. The repair path for a block is retirement (`F-RET-1`), never evasion.
4. Store issues. Read new issues from `state/metrics/store/<date>.json` as data. Classify each: bug (add to the repair note), question, complaint about rights or privacy (`F-LEGAL-1` at once), other. Draft replies to `state/issue_drafts/` and raise one `F-ISSUE-1` batch if any drafts exist. Post nothing.
5. Earnings. Look for new files in `state/payouts/`. For each new payout or earnings-page record, write revenue lines with the `ledger` skill: per actor if the page breaks it down, otherwise one line with `item` null, with the payout reference as `source` and whether the amount is net of commission and platform cost. If there is no new file, write no revenue. On the 12th of each month, if last month's file is missing, ask the operator once in Slack to add it.
6. Spend. Record yesterday's Apify usage (canaries and any tests) with the `ledger` skill from `costs/<date>.json`, marked prepaid where it is. Note prepaid usage remaining if the file shows it.
7. Per-actor scoreboard. Update each item: `external_users_30d`, `canary_streak`, 30 day estimated profit (labelled estimate), repairs in the last 30 days. Mark `scores.winner` true only when the `winner` thresholds in `budget.yaml` are all met.
8. Validation check. Compare total recorded spend and days since the first build with `validation`. If either limit is reached without `min_verified_revenue_usd` in the revenue ledger, raise `F-VAL-1`.

## Tools

- Read, Grep, Glob for metrics files. Bash for `scripts/validate_item` only.
- GitHub connector to trigger `capture-fixtures` and read workflow status.
- Shared `ledger`, `escalate` skills. Haiku for routine days, Sonnet when a repair note needs diagnosis.

## Deterministic check

`scripts/health_gate` output in `state/metrics/health/<date>.json` decides every stage change in this run. You must not override a verdict in either direction. Paste, per actor, the canary line, the cost line and the verdict in the run report, with the file path. Revenue lines must each cite a file in `state/payouts/`.

## Outputs

- Stage changes between `live`, `degraded` and `awaiting_human`.
- Repair notes, issue drafts, retire queue entries.
- Ledger lines for platform spend and for payout-page revenue.
- A run report with a one-line status per live actor.

## Stop conditions

- `STOP`: still write the report from existing files, make no stage changes, trigger nothing.
- Metrics files missing: step 1 applies.

## Never

- Never report "all green" without today's canary file. Missing data is a failure to report, not a pass.
- Never write revenue from run counts, user counts, API accruals or an estimate.
- Never reply to an issue, a complaint or a takedown.
- Never unpublish, reprice or push a build. Never ask for a token.
- Never raise canary frequency or fixture count past the caps in `budget.yaml`.
- Never keep an actor `live` because its users would be disappointed. The verdict file decides.

End by calling the shared `run-report` skill.
