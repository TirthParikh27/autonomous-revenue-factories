---
name: build
description: Stage 3 of Factory G. Use to implement one `specced` item (or fix one `live` or store-rejected item) as a Chrome extension or Shopify app with payment and licence gating in version 1, on a branch with a pull request and green CI. Not for deciding what to build or for store submission.
---

# Build

Goal: the smallest tool that meets the spec's acceptance criteria, takes payment in test mode and unlocks the paid feature. Nothing the spec does not ask for.

## Inputs

- One item, in this priority order: `live` with a recorded defect, `building` already in progress, `submitted` returned by an approved `G-REJ-1` packet, then `specced`.
- `state/specs/<id>.md`. This is the only description of the product you use.
- `products/<id>/` if it exists, and the open pull request for it.
- `budget.yaml` (`per_run.build`, `per_item`, `risk`).
- For a rejection fix: the approved `G-REJ-1` packet. Not the raw notice.

## Steps

1. Preconditions. Stop with a run report if `STOP` exists, a cap is reached, or an open packet blocks this item. Check `per_item.build_token_cap_usd` and `max_build_runs` against the item file. If either is exceeded without green CI, set the item to `killed` and exit.
2. Set the item to `building` if it was `specced`. Create or check out branch `claude/<id>`.
3. Start the `tool-builder` agent with the spec path and the product path. It writes code and tests only under `products/<id>/`.
4. Build order, so that the money path exists before features:
   a. Project skeleton, manifest or app config with exactly the spec's `permissions` and `hosts`.
   b. Licence check and checkout in test mode, with the locked state for unpaid users.
   c. The one paid feature from the acceptance criteria.
   d. The anonymous activation event, only if it is in `data_inventory`.
   e. Tests for each acceptance criterion.
5. Billing route comes from the spec. Use Stripe test mode, or the marketplace's own billing test facility if the spec says `marketplace_billing`. If the route's test facility is unknown, stop and raise `G-TOS-1`. Do not guess an API.
6. Run the test suite locally in the session. Fix failures. Do not delete, skip or weaken a test to make it pass. If a test is wrong, say so in the run report and leave it failing.
7. Commit, push the branch, open or update the pull request. Wait for CI on the pushed commit and read its real result.
8. If CI is green on the head commit, set the item to `built`. If not, leave it `building`, add 1 to `scores.build_runs`, and record the failing check names.
9. Record token spend against the item with the `ledger` skill. End with the `run-report` skill, quoting the CI run URL and its summary line for the head commit.

## Tools

- `tool-builder` agent: Read, Write, Edit, Bash, Grep, Glob.
- git and the GitHub connector for the branch and pull request.
- Node toolchain and a headless browser test runner in CI. Whether the runner can load an unpacked extension in CI is unverified, confirm at build time. If it cannot, stop and raise `GEN-1`. A Desktop task is not the fallback, because the operator's Mac has no Playwright and is work-managed (verified 2026-11-16).
- Stripe test-mode key in CI only. No live key. No store credentials.
- Shopify's developer CLI for Shopify items: official and verified (2026-11-16), but not installed on the operator's Mac. Confirm exact commands at build time before first use. Never use a deploy token.

## Deterministic check

GitHub Actions on the pull request, all required:

- Unit tests and the end-to-end test that loads the built tool.
- Checkout test: an unpaid user is locked, a test-mode payment completes, the paid feature unlocks.
- Manifest or app config `permissions` and `hosts` equal the spec lists exactly.
- Every host found in the built bundle is in the spec's `hosts`.
- No remote code loading or dynamic evaluation in the bundle.
- Secret scan clean. Lockfile present.
- Two builds of the same commit produce the same artifact hash.

`built` means these are green on the head commit. Your reading of the code is not the check.

## Outputs

`products/<id>/` on branch `claude/<id>`, a pull request, the updated item file, ledger lines, a run report.

## Stop conditions

- Per-run caps reached: commit work in progress to the branch, report honestly, exit.
- The spec is ambiguous or contradicts itself: do not improvise. Move the item back by raising `GEN-1` with the exact question.
- The feature cannot work with the spec's permissions: stop, raise `G-PERM-1` with the narrower design that failed.
- A needed account, key or policy answer is missing: raise `G-ACC-1`, `G-PAY-1` or `G-TOS-1`. Continue only the parts that do not need it.

## Never

- Never add a permission, host, dependency with network access, analytics call or data field that is not in the spec.
- Never ship a build without the payment path, "to add it later".
- Never push to `main`, merge the pull request, or deploy.
- Never use a live payment key, or create live products or prices.
- Never read `state/scout/` or any fetched page. The spec is the interface.
- Never copy an incumbent's code, assets, name or listing text.
- Never mark `built` on a local test run alone.
