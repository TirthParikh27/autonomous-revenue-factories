---
name: release-readiness
description: Stage 6 of Factory A. Use when an item is at `release_candidate`, `submitted` or `rejected` to run the App Review guideline checklist with evidence, assemble the submission packet for the operator, and record outcomes. The operator submits to the store. This skill never does.
---

# Release readiness

The developer account is the scarcest asset in this factory. This stage exists to stop a weak submission. Read `CLAUDE.md` and `budget.yaml` first.

## Inputs

- One item at `release_candidate`, `submitted` or `rejected`.
- `apps/<id>/`, the CI run for the head commit, `state/build/<id>/screenshots.json`, `state/specs/<id>.md`, `demand/<id>/claims.yaml`.
- `data/review_checklist.yaml`: the checklist, maintained from the current guideline text.
- `state/submissions.jsonl`: every submission and outcome on the account.

## Steps for `release_candidate`

1. Run `checks/cadence`. It reads `state/submissions.jsonl` and `account_protection` in `budget.yaml`: submissions this month, days since the last new-app submission, new apps in the rolling 12 months, submissions today, live apps. If submissions are frozen by `A-ACCT-1`, stop and report. If the cadence says not yet, finish the checklist, leave the item at `release_candidate` with the earliest allowed date, set its `next_check` to that date, and stop.
1a. Run `checks/metadata_similarity` on the draft listing (name, subtitle, description, keywords, release notes, screenshot captions) against every other listing on the account. Over the limit in `budget.yaml`, rewrite the listing from the app's own spec and rerun once. A second fail goes back to `building`. Raise `A-CAP-1` only if the evidence is unusually strong.
2. Delegate the checklist to the `release-verifier` agent. For each row it records pass or fail and the evidence: a file path, a test id, or a screenshot hash. It writes `state/release/<id>/checklist.json`.
3. Checklist groups. Rows marked (unverified) come from background knowledge and must be confirmed against developer.apple.com before first use:
   - **Differentiation, 4.3(b):** not in a named saturated category. One-minute test against the 5 nearest competitors. `checks/overlap` under the cap. Store name, icon and screenshots do not resemble a competitor's.
   - **Substance:** the core job works end to end without placeholder content. Onboarding shows it before the paywall.
   - **Subscriptions (unverified):** price, period and trial terms visible before purchase. Restore purchases works. Links to terms and privacy policy.
   - **Privacy (unverified):** privacy answers match the SDKs actually present. Account deletion is available in the app if accounts are created.
   - **Review access (unverified):** a demo account or review notes that let a reviewer reach every feature.
   - **Content rules:** no user-generated content without moderation and a compliance plan (guideline 1.2). No Live Activities used for promotion (4.5.3).
   - **Listing honesty:** every listing claim is in `claims.yaml` with evidence. Screenshots are from this build.
4. Run `checks/review_checklist`.
5. On pass: write the store listing copy and privacy answers to `apps/<id>/store/`, open a pull request from `app/<id>` to `main`, and raise `A-SUB-1`. The operator merges, builds from that commit, submits, and appends the submission id and date to `state/submissions.jsonl`. When that line exists, move the item to `submitted`.
6. On fail: return the item to `building` with the failed rows listed, unless the failure is differentiation, in which case raise `GEN-1` with a kill recommendation.

## Steps for `submitted` and `rejected`

- `submitted`: do nothing here. The telemetry stage moves it to `live` when the public listing is reachable.
- When the operator records a rejection in `state/submissions.jsonl`: move the item to `rejected` and raise `A-REJ-1`. If the text cites 4.3, spam, 3.2(f) or fraud, or this is the second rejection on the account this quarter, also raise `A-ACCT-1`. Draft a factual reply for the operator to consider. Do not argue the guideline.

## Tools

Read, Write, Bash for check scripts and for reading CI simulator results (no local Xcode), GitHub connector to open the pull request. No store tools of any kind.

## Deterministic check

`checks/review_checklist` exits non-zero if any row lacks evidence that exists on disk or in CI, or any row is a fail. `checks/cadence` reads `state/submissions.jsonl` against every limit under `account_protection`. `checks/metadata_similarity` compares listing text across the account. All three run outside the model and their output goes in the packet.

## Outputs

- `state/release/<id>/checklist.json`, `apps/<id>/store/`.
- Pull request and packet `A-SUB-1`, or `A-REJ-1` and possibly `A-ACCT-1`.

## Stop conditions

- Cap reached or submissions frozen.
- The checklist file has unconfirmed (unverified) rows and this is the first submission: raise `GEN-1` asking the operator to confirm them.
- Any tax, banking, agreement or export-compliance form is needed: `TOS-1`.

## Never

- Never submit, upload a build to a store, or use a store credential or a community App Store Connect tool.
- Never mark a row as passed on reasoning alone.
- Never change app code in this stage.
- Never write to `state/submissions.jsonl`. Only the operator records submissions and outcomes.
- Never propose submitting two apps close together to catch up, or another account as a way around a freeze.
- Never propose resubmitting unchanged, or more than `max_resubmissions_per_app` times.

## Finish

End by calling the shared `run-report` skill. Include all three check outputs and the submission counts against each cadence limit.
