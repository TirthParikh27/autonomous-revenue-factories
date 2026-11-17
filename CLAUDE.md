# Changing this repository

This file is for a session merging a pull request it wrote itself. A factory run follows `factories/<name>/CLAUDE.md`, and any pull request a factory run opens is merged by Tirth, never by the run.

## From pull request to merge

1. **Before opening.** Read [`REVIEW.md`](REVIEW.md), including how code is written here. Turn every stress case you tried into a test. Tests call the code in-process, because lines run only in a subprocess are not measured. Run `python -m pytest -q --cov --cov-report=xml`, `ruff check .`, `python tools/pr_gate.py` and `diff-cover coverage.xml --compare-branch origin/main --fail-under 80`, and `zizmor --offline .github` when workflows changed. If the `simplify` skill is available, run it on your diff and keep what makes the change smaller. For trading changes, also run the `c-trading` workflow's test command with that factory's requirements installed.
2. **Open the pull request.** Keep the description to a few short lines: what changed, why, what needs Tirth's attention, and `Evidence` (the commands you ran, one-line result each).
3. **Wait for CI to be green.** Fix failures in the code. Never skip, delete or weaken a test to pass.
4. **Get an independent review.** Spawn a fresh `pr-reviewer` agent with only the pull request number. If that agent type is not available, spawn a fresh general agent on Opus 5.5 at high effort and tell it to follow `.claude/agents/pr-reviewer.md`. Post its verdict on the pull request word for word.
5. **On BLOCK,** fix every `[blocker]`, rerun the evidence, update the description, push, and ask a new reviewer. Repeat until a round has no blocker. If you believe a blocker is wrong, or the same blocker comes back after you fixed it, stop and ask Tirth.
6. **On PASS with "Merge: author's session",** fix the suggestions and nits that are high value and low effort, push, and get one more review round, since every commit must be reviewed. Suggestions from that round do not start another one: once it has no blocker, squash-merge the pull request yourself and tell Tirth in one or two lines what was merged.
7. **On "waits for Tirth",** do not merge. Tell Tirth it is ready and why it needs them.

You never review your own pull request, and you never merge one whose latest commit has not been reviewed.
