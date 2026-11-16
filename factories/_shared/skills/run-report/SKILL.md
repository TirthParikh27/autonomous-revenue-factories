---
name: run-report
description: Write the mandatory evidence-first report at the end of every factory run. Use as the final step of any scheduled or headless run, including runs that failed or did nothing.
---

# Run report

Write `journal/<date>/<run id>.md` in the format in `factories/_shared/CONVENTIONS.md`. The run wrapper fails any run whose report is missing or has no evidence block.

## Rules

1. **Evidence means output you actually saw in this run.** Paste the command or check and its trimmed real output: a test summary line, an HTTP status and body excerpt, a row count, a file hash, a marketplace URL that you fetched and that returned the listing. "Tests pass" with no output is not evidence.
2. **Verify the outcome, not the request.** A 200 response to a publish call is a request result. The outcome is the listing being reachable, the payment link completing in test mode, the page being served, the order appearing in the paper account. Check the outcome.
3. **Say what did not happen.** List every planned step that was skipped, failed, or was blocked by permissions or network. Include permission denials verbatim.
4. **No rounding up.** Partial is partial. If 3 of 5 items progressed, say 3 of 5 and name the other two.
5. **Numbers carry their source.** Any metric quotes where it was read from and when.
6. **Keep it short.** Under 60 lines. Link to files instead of pasting them.
7. **One proposed lesson at most**, and only if this run produced direct evidence for it. Lessons are promoted to `journal/LESSONS.md` by the weekly review, not by individual runs.

## If the run did nothing

Still write the report. State why (blocked by budget, by `STOP`, by an open escalation, or nothing in the queue) and what would unblock it.
