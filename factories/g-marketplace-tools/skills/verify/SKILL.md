---
name: verify
description: Stage 4 of Factory G. Use to check one `built` item with a fresh-context verifier and the store-policy checklist before any submission packet is made. Produces `verify.json` and moves the item to `verified` or back to `building`. Not for fixing code.
---

# Verify

Goal: an independent yes or no on whether the build does what the spec says, takes money correctly, and matches what will be declared to the store. The verifier did not write the code and does not fix it.

## Inputs

- One item in `built`, oldest first.
- `state/specs/<id>.md`.
- The pull request for `claude/<id>` and its CI run on the head commit.
- `policy/<store>.yaml`: the store checklist the operator committed, with the date the policy text was read.
- `budget.yaml` (`per_run.verify`, `per_item.max_verifier_returns`).

## Steps

1. Preconditions. Stop with a run report if `STOP` exists or a cap is reached.
2. If `policy/<store>.yaml` does not exist, or its `read_on` date is more than 90 days old, raise `G-TOS-1` asking the operator to commit or refresh it. Leave the item `built`. Do not write a checklist from memory.
3. Confirm CI is green on the exact head commit of the pull request. If the head moved since the `built` transition and CI has not finished, exit and try on the next run.
4. Check out the head commit. Run the test suite and the `policy-check` script yourself and keep the output.
5. Start the `release-verifier` agent with only: the spec path, the product path, the test output and the `policy-check` output. Do not give it the build run reports or the builder's notes. Ask it for a verdict per acceptance criterion and per checklist line, with the file and line or the test name as evidence, and to report only gaps that affect correctness, payment, permissions, data handling or policy.
6. Write `state/packets/<id>/verify.json`:

```json
{
  "item": "<id>", "commit": "<sha>", "ci_run": "<url>", "artifact_sha256": "<hash>",
  "acceptance": [{"criterion": "...", "pass": true, "evidence": "test name or file:line"}],
  "policy": [{"check": "...", "pass": true, "evidence": "script output line"}],
  "gaps": [{"severity": "blocker | note", "what": "...", "where": "..."}],
  "verdict": "pass | return"
}
```

7. Decide by rule, not by feel:
   - `pass` only if every acceptance criterion passes, every `policy-check` line passes, and there is no blocker gap.
   - Otherwise `return`. Set the item to `building`, add 1 to `scores.verifier_returns`, and copy the blocker gaps into the item's `history` note for the builder.
   - If `scores.verifier_returns` would exceed `per_item.max_verifier_returns`, set the item to `killed`.
8. On `pass`, set the item to `verified`.
9. End with the `run-report` skill. Quote the test summary line, the `policy-check` summary line and the artifact hash.

## Tools

- `release-verifier` agent: Read, Grep, Glob, Bash.
- Bash in the main session for checkout, tests, `policy-check` and hashing.
- GitHub connector, read only, for the CI status.
- No web tools, no Stripe live access, no write access to `products/`.

## Deterministic check

`policy-check` (plain script, written at build time) exits 0 only if:

- The manifest or app config permissions and hosts equal the spec lists.
- No host pattern is a wildcard unless the spec carries an approved `G-PERM-1` packet id.
- Every outbound host in the bundle is in the spec's `hosts`.
- Every data field sent off the device in code appears in `data_inventory`, and every `data_inventory` field appears in the draft privacy disclosure if one exists.
- No remotely loaded code, no dynamic evaluation, no obfuscation beyond the bundler default.
- Two clean builds of the commit give the same hash.
- Each line in `policy/<store>.yaml` that is marked `automated: true` passes its own check. Lines marked `automated: false` are listed for the operator in the submission packet, not judged here.

The verdict in `verify.json` must agree with the script's exit code and the CI status. If the verifier says pass and the script says fail, the result is `return`.

## Outputs

`state/packets/<id>/verify.json`, the updated item file, a run report.

## Stop conditions

- One item per run.
- The verifier and the scripts disagree in a way you cannot explain: verdict is `return`, describe the disagreement in "Not done".
- Tests cannot be run in this environment: do not pass on CI alone. Report the blocker and leave the item `built`.

## Never

- Never edit code, tests, the spec or the policy checklist in this stage.
- Never pass an item whose paid unlock or locked unpaid state was not exercised by a test in this run.
- Never accept "works as designed" for a mismatch between code behaviour and the data inventory.
- Never ask the verifier to find as many problems as possible. Style, naming and refactoring comments are discarded.
- Never state that a build complies with store policy. State which checklist lines passed and which are left for the operator.
