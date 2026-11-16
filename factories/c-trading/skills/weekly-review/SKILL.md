---
name: weekly-review
description: Run the weekly self-improvement review for Factory C. Use once a week to verify the trial registry, report the honest funnel, detect idea collapse, and propose at most three changes to skills or agent prompts as pull requests. Never use it to change thresholds, budgets or the engine.
---

# Weekly review

No item changes stage in this run. Model: Opus.

## Inputs

- `budget.yaml`, `STOP` files, `escalations/` (open, approved, rejected with the operator's reasons).
- `journal/` for the last 7 days, `journal/LESSONS.md`.
- `registry/trials.jsonl`, `results/`, `paper/journal/`, `state/items/`, `state/metrics/`.
- `ledger/spend.jsonl`. Open PRs from earlier reviews and their review dates.

## Steps

1. **Integrity first.** Run `engine/registry_verify`. Then count trial requests in `trials/requests/` against registry lines. Any break or mismatch: raise `F-INT-1` and end the review there.
2. **Budget position.** Report spend, trials and holdout evaluations used against `validation` in `budget.yaml`, and days left in the window. If any is used up, raise `F-VAL-1`.
3. **Funnel, in counts.** Cards written, killed at card stage, implemented, trials run, killed by each gate (name the gate), validated, on paper, paper-passed, killed on paper. Lifetime and this week. Verified revenue from `ledger/revenue.jsonl` (expected 0).
4. **Idea collapse.** Cards per mechanism. Number of distinct return-correlation clusters among all trials. Share of trials in the largest cluster. If the largest cluster holds more than half of trials, say so in the first line of the report.
5. **Where the factory is wrong.** For each kill reason this week, is the cause the idea, the implementation, or a factory defect (ambiguous card template, flaky CI, look-ahead bug class)? Only factory defects lead to proposals.
6. **Paper versus backtest.** For each strategy on paper: measured cost against assumed cost, divergence, heartbeat gaps. Flag `F-DIV-1` if its condition holds and no packet exists.
7. **Run health.** Failed runs, permission denials, runs whose report listed "Not done" items for two weeks running.
8. **Earlier proposals.** For each merged proposal past its review date, read the metric it named and state whether it moved. Propose reverting changes that did not help.
9. **Proposals.** At most 3, each a separate PR touching one skill or agent file, each with: observation and file evidence, hypothesis, the single change, the metric that will judge it, the review date. One change per skill per week.
10. **Lessons.** Promote at most 3 run-level lessons to `journal/LESSONS.md` as dated, evidence-linked entries. Remove the oldest if the file exceeds 60 lines.
11. Write `journal/<date>/weekly-review.md`, post a Slack summary under 80 words, and update the factory's standing Linear issue.

## Tools

Read, Write (`journal/` only, plus proposal branches), `git`, `gh`, Slack and Linear connectors, shared `escalate` and `ledger` skills.

## Deterministic check

- `engine/registry_verify` output, pasted.
- The request-count versus registry-count command and output, pasted.
- Each funnel count shown with the command that produced it.
- `gh pr list` output showing no more than 3 new proposal PRs and no touched protected path.

## Outputs

Weekly report, up to 3 PRs, `LESSONS.md` entries, Slack message, Linear update, run report.

## May propose

Changes to skill steps, agent prompts, the card template, the mechanism taxonomy, batch sizes below the caps in `budget.yaml`.

## Must escalate instead (`F-ENG-1` or `F-VENUE-1`)

Any change to thresholds, trial or holdout budgets, the cost model, the trial-counting rule (including counting by cluster instead of by trial), the import allowlist, the universe, the benchmark, the venue list, or anything under `engine/`.

## Stop conditions

- Integrity failure at step 1.
- Fewer than 3 runs in the week: report run health only, make no proposals.

## Never

- Never propose making a gate easier because nothing passes. Nothing passing is the expected state and is reported as a finding.
- Never summarise the week as progress when the funnel shows only kills. Say "no strategy passed this week" in those words.
- Never edit `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, the engine, workflows, hooks or settings.
- Never merge your own PR.

End by calling the shared skill `factories/_shared/skills/run-report`.
