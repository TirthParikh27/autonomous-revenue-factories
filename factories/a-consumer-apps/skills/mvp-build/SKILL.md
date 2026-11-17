---
name: mvp-build
description: Stage 5 of Factory A. Use when an item is at `demand_validated` or `building` and a build slot is free, to build the MVP with Expo and React Native, Supabase and RevenueCat on its own branch until CI is green. Never use for an item that has not passed its demand test.
---

# MVP build

Runs as a cloud scheduled task with GitHub Actions for CI. The operator's Mac has no Xcode and no Expo, EAS or Supabase CLI (verified 2026-11-16), so iOS binaries come from EAS cloud builds. Read `CLAUDE.md` and `budget.yaml` first. One item per run.

## Inputs

- One item at `demand_validated` or `building`.
- `state/specs/<id>.md` and `demand/<id>/claims.yaml`.
- `apps/_scaffold/`: the only shared code (auth, paywall, settings).
- `state/build/<id>/plan.md` and `progress.md` if a previous run started the work.
- `account_protection` and `build` sections of `budget.yaml`.

## Steps

1. Preconditions. Confirm the item's stage. Run `checks/cadence`. If submissions are frozen, or `max_concurrent_builds` or `max_live_apps` is reached, do not start. A build may start while the next submission date is still ahead, since a finished app can wait at `release_candidate`. Leave the item at `demand_validated` and report.
2. If the item is new to this stage: create branch `app/<id>`, move the item to `building`, record the start date, and write `state/build/<id>/plan.md` with one task per spec feature, each with its acceptance test.
3. Implement one task from the plan at a time, working in `apps/<id>/` only.
4. Stack rules:
   - Expo and React Native, TypeScript strict. Use the Expo CLI from the project's own dependencies. Build with EAS cloud builds. The official Expo MCP at `mcp.expo.dev/mcp` is verified (2026-11-16) and may be used once listed in `FACTORY_SPEC.md` section 6.
   - Supabase for data and auth through the Supabase CLI against the app's own project. Row level security on every table.
   - RevenueCat for subscriptions through the official RevenueCat MCP and SDK, in a sandbox project. Products, offerings and the paywall are created there. Store-side product creation is the operator's step.
   - Hard paywall with trial after onboarding. Onboarding must let the user see the core job working first. Trial length from the spec.
   - PostHog events for onboarding steps, paywall view, trial start and core action.
5. After each task: run typecheck, lint and tests in the session, commit, push, and update `progress.md` with what is done and what is next.
6. When all plan tasks are done and CI is green on the branch, capture simulator screenshots of each core feature from the CI macOS job into `apps/<id>/store/screenshots/` and record their hashes in `state/build/<id>/screenshots.json`. Update `claims.yaml` so every claim points to a test id or a screenshot hash.
7. Move the item to `release_candidate`.

## Tools

Bash (git, Expo CLI, Supabase CLI, npm, simulator tooling), Read, Write, Edit, RevenueCat official MCP with the sandbox key, GitHub connector to read CI status. No web research tools.

## Deterministic check

CI on GitHub Actions for branch `app/<id>` must be green on the head commit. It runs: typecheck, lint, unit tests with every spec feature covered, a scripted purchase and restore flow against the RevenueCat sandbox, and `checks/overlap`, which fails if feature code outside `account_protection.shared_scaffold_paths` overlaps any earlier app by more than `max_feature_code_overlap_pct`. The comparison tool is chosen at build time. Paste the CI run URL and its summary line. A local pass is not sufficient.

## Outputs

- `apps/<id>/` on branch `app/<id>`.
- `state/build/<id>/plan.md`, `progress.md`, `screenshots.json`.
- Item at `release_candidate`.

## Stop conditions

- Item spend above `per_item_caps_usd.build`, or clearly stalled in `building` (reference point: `build.max_days_in_building`). First time: raise `A-BLD-1`. Second time: kill.
- A feature cannot be built as specified: stop and raise `GEN-1`. Do not quietly cut the differentiator.
- A needed account, key or store product does not exist: raise `ACC-1`.
- `checks/overlap` fails: rewrite the feature code. If it fails again, report it. Do not rename identifiers to get under the limit.

## Never

- Never start without a passed demand test and a free slot.
- Never copy feature code from another app in `apps/`. Never fork a previous app as a starting point.
- Never push to `main`, edit `.github/` or `checks/`, skip or delete a failing test, or mark a test as expected to fail.
- Never create a production RevenueCat product, a store listing, or a build upload to a store.
- Never put a secret in the repo. Only publishable client keys go in app config.
- Never add analytics, advertising or tracking SDKs beyond PostHog and RevenueCat.
- Never install an MCP server or CLI not listed in `FACTORY_SPEC.md` section 6.

## Finish

End by calling the shared `run-report` skill. Include the CI run URL and summary line, the `checks/overlap` figure, and the list of plan tasks still open.
