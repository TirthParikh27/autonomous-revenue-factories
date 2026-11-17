# Review rules

Every pull request is reviewed against this file before it is merged. The author reads it before opening a pull request. The reviewer follows it. The merge steps are in [`CLAUDE.md`](CLAUDE.md).

## What the author provides

Stress testing counts only when someone else can check it.

1. **Stress cases are tests in the repository.** Every edge case, bad input and failure path the author tried is a checked-in test, so CI reruns it on every pull request. A case that was only tried by hand does not count.
2. **Evidence in the pull request.** An `Evidence` section lists the exact commands that were run (the tests, and an end-to-end run where the change has one) with a one-line result for each. Long output goes in a pull request comment. The commands work from a clean checkout. A step that needs money, keys or a live account is shown in dry-run mode.
3. **CI is green.**

## What CI enforces

The `checks` workflow fails a pull request when:

- any test fails;
- code changed but no test did, or the change adds `pragma: no cover` (`tools/pr_gate.py`);
- fewer than 80% of the changed Python lines are run by the tests (`diff-cover`). A new file that no test imports counts as uncovered.

The trading factory's tests need its own requirements, so the `c-trading` workflow measures `factories/c-trading/` with the same 80% rule. Any other factory that needs its own requirements gets the same: its own test job, and only then its folder left out of the root `.coveragerc`.

Python under `factories/c-trading/design/` holds one-off trials and is not measured.

These rules are easy to satisfy on paper: any test file anywhere counts as "a test changed", code placed under a `tests/` folder or in a `conftest.py` is not measured, and only Python lines are measured. The reviewer checks that the tests really exercise the change.

## What the reviewer checks

| | Question | What to look for | Blocks the merge |
|---|---|---|---|
| 1 | Does it work? | Bugs, untested paths, tests that cannot fail or do not touch the change, evidence that does not reproduce. | Yes |
| 2 | Does it do what was asked? | Nothing missing, nothing extra. | No |
| 3 | Is it simple? | A library where one fits, plain code where it does not, no needless layers. | No |
| 4 | Is it safe? | No keys in code, logs or test data. Paid, live and publishing actions stay in dry run unless turned on deliberately. Spending caps and guard checks are not weakened. | Yes |
| 5 | Is it honest about results? | Trading: no use of future or held-back data, and costs are counted. Apps: the numbers behind every claim are real and can be traced to a source. | Yes |
| 6 | Can the next agent pick it up? | Docs and config are updated. The pull request description is short. | No |

Questions 2, 3 and 6 come back as suggestions. The author decides whether to take them.

## How to review

The reviewer is a fresh agent that did not write the code: `pr-reviewer` (`.claude/agents/pr-reviewer.md`), which runs on Opus 5.5 at high effort. It is given the pull request number and nothing else.

1. Read the diff, the description and the evidence.
2. **Rerun the evidence.** Run each command from a clean checkout of the branch. A result that does not match the claim blocks the merge.
3. **Attack it.** Try cases the author did not cover, chosen for this change: empty and malformed input, very large input, repeated runs, a failing external call, a missing file. Any case that breaks blocks the merge, and is reported with the command that shows it.
4. **Decide who merges.** See the next section.
5. Reply with the verdict.

The reviewer never changes the pull request, never merges, and never spends money or uses live keys.

## Pull requests that wait for Tirth

The author's session merges its own pull request once CI is green and the verdict is PASS, except when the pull request:

- spends real money or raises a spending cap;
- places or enables live trades;
- publishes, launches or submits anything outside the repository (ads, store releases, posts, emails);
- adds, reads or changes how keys and credentials are handled;
- was opened by a factory run;
- removes a stop or freeze file, or otherwise restarts something Tirth stopped;
- changes a file listed in [`.github/CODEOWNERS`](.github/CODEOWNERS) or on a factory's own deny list (`factories/<name>/.claude/settings.json`), on the base branch or in the pull request. These are each factory's rules and budgets, guard checks, publishers, CI and these review rules. `python tools/pr_gate.py` names them.

When in doubt, it waits.

## Verdict format

```
Review: PASS | BLOCK
Merge: author's session | waits for Tirth (reason)

Blocking
- file:line, what is wrong, and the command that shows it

Suggestions
- ...

Checked
- evidence commands rerun, and whether each matched
- the reviewer's own cases, and the result of each
```
