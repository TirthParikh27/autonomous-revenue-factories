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
- fewer than 80% of the changed Python lines are run by the tests (`diff-cover`). A new file that no test imports counts as uncovered;
- `ruff check .` finds a fault: an undefined name, an unused import or variable, or a likely bug. The rules are in [`ruff.toml`](ruff.toml) and cover faults only, not style;
- `zizmor` finds a security fault in a workflow or the Dependabot file.

CI runs the base branch's copy of `tools/pr_gate.py`, so a pull request cannot change the gate script that judges it. It can change the workflows, which is why they are protected files. A `.py` edit that only changes comments or layout needs no test, but a protected file is named however small the edit. The gate also names the Python test functions a pull request removes or moves, and the skip markers it adds. That does not fail CI, because a test can go with the code it tested, but the reviewer checks each one.

The trading factory's tests need its own requirements, so the `c-trading` workflow measures `factories/c-trading/` with the same 80% rule. Any other factory that needs its own requirements gets the same: its own test job, and only then its folder left out of the root `.coveragerc`.

Python under `factories/c-trading/design/` holds one-off trials and is not measured.

These rules are easy to satisfy on paper: any test file anywhere counts as "a test changed", code placed under a `tests/` folder or in a `conftest.py` is not measured, and only Python lines are measured. The reviewer checks that the tests really exercise the change.

## How code is written here

Agents write all the code, so the code has to stay small enough for the next agent to read whole. Think from the problem, not from patterns: what is the least code that does what was asked, safely?

- **Do what was asked, nothing more.** No options, settings, layers or extension points for needs nobody has yet. Add an abstraction when a second real caller needs it, not before.
- **Reuse before writing.** Look for an existing function, module or established library first. Never paste a second copy of logic that exists; move it somewhere both can use.
- **One job per unit.** A function or file does one thing, and the parts that change for different reasons live apart. When a function is hard to name, it is doing too much.
- **Extend by adding.** A new factory, check, stage or strategy should be a new file or folder that existing code picks up, not an edit to shared code with a new special case. Change shared code only when every caller needs the change.
- **Depend on plain data and small interfaces.** Pass dicts, dataclasses and paths between parts, not objects that reach into each other. Keep side effects (network, files, money) at the edges, where they are easy to fake in a test.
- **Fail loudly.** No blanket `except` that hides an error, no silent fallback that turns a failure into a wrong number.
- **Leave it smaller.** Delete code, files and docs the change makes dead. Update the docs the change makes wrong.
- **Clear over clever.** Names say what a thing is or does. Comments say why, not what.

These are judgement, not counts. The reviewer asks of each new piece: would the change be worse without it?

## What the reviewer checks

| | Question | What to look for | Blocks the merge |
|---|---|---|---|
| 1 | Does it work? | Bugs, untested paths, tests that cannot fail or do not touch the change, evidence that does not reproduce. Tests gamed to pass: a test removed, skipped or loosened, an expected value changed to match the code, code that special-cases test inputs or compares equal to anything. | Yes |
| 2 | Does it do what was asked? | Nothing missing, nothing extra. | No |
| 3 | Is it simple? | The section above: no speculative layers, no copied logic, shared code not bent for one caller, dead code removed. | No |
| 4 | Is it safe? | No keys in code, logs or test data. Paid, live and publishing actions stay in dry run unless turned on deliberately. Spending caps and guard checks are not weakened. A new dependency is real, maintained and worth its weight: models invent package names, so check the name on the registry. | Yes |
| 5 | Is it honest about results? | Trading: no use of future or held-back data, and costs are counted. Apps: the numbers behind every claim are real and can be traced to a source. | Yes |
| 6 | Can the next agent pick it up? | Docs and config are updated. The pull request description is short. | No |

Every finding carries one marker:

- `[blocker]`: a real fault under question 1, 4 or 5 that would do harm if merged. Wrong results, something unsafe, a dishonest number, evidence that fails when rerun.
- `[suggestion]`: worth doing, but safe to merge without. Everything under questions 2, 3 and 6, and limits of the checks that this file already states.
- `[nit]`: small and cosmetic. Wording, naming, a count in the description that is slightly out of date while the command still succeeds.

Only a `[blocker]` stops the merge. Before merging, the author fixes the suggestions and nits that are high value and low effort, and leaves the rest. A fix makes a new commit, and every commit is reviewed before merge, so it goes to a new review round.

## How to review

The reviewer is a fresh agent that did not write the code: `pr-reviewer` (`.claude/agents/pr-reviewer.md`), which runs on Opus 5.5 at high effort. It is given the pull request number and nothing else.

1. Read the diff, the description and the evidence.
2. **Rerun the evidence.** Run each command from a clean checkout of the branch. A command that fails, or a result that changes what the claim means, is a blocker.
3. **Attack it.** Try cases the author did not cover, chosen for this change: empty and malformed input, very large input, repeated runs, a failing external call, a missing file. A case that breaks is a blocker, and is reported with the command that shows it.
4. **Decide who merges.** See the next section.
5. Reply with the verdict.

The verdict is PASS when there is no blocker, however many suggestions and nits there are. After a BLOCK the author fixes every blocker and a new reviewer looks again. This repeats until a round has no blocker.

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

Findings
- [blocker] file:line, what is wrong, and the command that shows it
- [suggestion] ...
- [nit] ...

Checked
- evidence commands rerun, and whether each matched
- the reviewer's own cases, and the result of each
```
