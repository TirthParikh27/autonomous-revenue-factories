---
name: synthetic-screen
description: Stage 2 of Factory A. Use when items sit at `discovered` to rank a batch of app ideas with an LLM and kill the bottom half before any money is spent on ads. This screen can only kill. It never passes an idea to a build and never sets a price.
---

# Synthetic screen

A free, same-day filter that decides which ideas are worth $30 of real traffic. Read `CLAUDE.md` and `budget.yaml` first.

## What the evidence says, and what this skill does about it

- LLM panels can rank concepts roughly the way human survey panels do. One study with a consumer goods company reached 90% of human test-retest reliability on concept ranking across 57 surveys (arXiv 2510.08338). That measures agreement with what people say in a survey, in a well-documented product category. It does not measure what people buy.
- They are bad at price. A 2026 benchmark against real incentive-compatible willingness to pay found synthetic respondents overstating it by 86% and 37% for two products and understating it by 27% for another, with no consistent direction (Journal of Marketing Analytics, September 2026).
- They are over-positive and compress variation, and subgroup results can be far off even when the average looks right (NIM review 2026, arXiv 2609.13148).
- Personas made things worse in the one test against real click behaviour that was found: a plain "how likely is a typical reader to click" ranker beat a ten-persona panel at predicting real A/B winners (Kendall tau 0.36 against 0.08, arXiv 2609.25010).

So: rank, do not rate. Use no personas. Never ask about price. Use the result only to drop the weakest half. Track how well the ranking predicted tranche 1, and stop using it if it does not.

Paid persona services are not used. The self-serve ones cost from about $20 a month to $12,500 a year and their accuracy claims are their own. Requesting one is `A-MCP-1`.

## Inputs

- Items at `discovered`, in batches of 10 to 25. If fewer than 10 are waiting, exit.
- Each item's `state/scout/<id>.json`: the unmet job, sourced complaints, competitor list, keyword popularity.
- `pipeline.screen_runs` and `pipeline.screen_kill_fraction` in `budget.yaml`.

## Steps

1. Build one neutral card per idea from the scout file: the job in one sentence, who has it, the three strongest sourced complaints, the keyword popularity figure and its source, the number of established competitors. No name, no branding, no price.
2. Run the ranking `screen_runs` times, each in a fresh context with the cards in a different shuffled order. The prompt asks one question: order these by how likely a typical person with this problem is to tap an ad for an app that solves it, and give one sentence of reasoning per idea. No personas, no 1 to 5 scores.
3. Write each run to `state/screen/<batch>/run-<n>.json` exactly as returned.
4. Run `checks/screen_rank state/screen/<batch>/`. It computes the median rank per idea and marks the bottom `screen_kill_fraction` as killed. Ties at the cut line survive.
5. Apply exactly the transitions the script prints: `discovered` to `screened`, or to `killed` with the reason "synthetic screen, rank N of M".
6. Copy the one-line reasons for surviving ideas into the item file as `screen_notes`. The spec stage may use them as copy ideas, not as evidence.

## Deterministic check

`checks/screen_rank` exits non-zero unless there are exactly `screen_runs` run files, each ranks every idea in the batch once, and the card order differs between runs. It, not you, decides who is cut. When telemetry later has tranche 1 results for a batch, it records the rank correlation between this screen and the real cost per landing-page view in `state/screen/accuracy.jsonl`.

## Outputs

- `state/screen/<batch>/` run files and `result.json`.
- Items at `screened` or `killed`.

## Never

- Never promote an idea past the demand test because it ranked first.
- Never use a screen result as evidence in an escalation packet, a spec's demand section or a price decision.
- Never add personas, demographic role-play or numeric purchase-intent scores.
- Never rerun a batch to rescue an idea you like.

## Finish

End by calling the shared `run-report` skill. Include the `checks/screen_rank` output.
