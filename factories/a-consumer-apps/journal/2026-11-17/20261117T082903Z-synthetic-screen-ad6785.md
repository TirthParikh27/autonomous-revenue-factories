# Run 20261117T082903Z-synthetic-screen-ad6785 (synthetic-screen)

Result: 3 of 3 items at `discovered` screened; 0 killed. No spend beyond tokens (wrapper records).

## What I did
- No `STOP` file in this directory or repo root (Glob returned none).
- Read `budget.yaml`: `screen_runs` 3, `screen_kill_fraction` 0.5 (reference points only). Ledger not consulted for a paid call; none made.
- Open escalations (A-AD-1, ACC-1, PII-1, BUD-1, SEC-1) concern other stages; none blocks this one. No approved/rejected files to apply.
- Built neutral cards (job, who, complaint count, keyword data absent, competitor note) from the item files, not the scout file quotes.
- Ran 3 rankings with fresh haiku subagents, no tools, shuffled order and letters. Files: `state/screen/2026-11-17-c/run-{1,2,3}.json`, `result.json`.

## Median ranks
| item | ranks | median |
|---|---|---|
| old-photo-restoration-that-keeps-faces | 1,1,1 | 1 |
| local-document-scanner-no-cloud-lock-in | 2,3,2 | 2 |
| caption-editing-with-stable-timing | 3,2,3 | 3 |

## Cut decision
No cut. With three ideas, only a clear gap justifies a kill. Captions ranked last twice but above the scanner once, so it is a close call and survives. Reference fraction 0.5 not applied as a gate. All three moved `discovered` to `screened` with `screen_notes`.

## Evidence
- `Glob STOP` and `Glob ../../STOP`: "No files found".
- `Glob state/items/*.json`: 12 items; `grep` of stage showed exactly 3 at `discovered` (caption-editing, local-document-scanner, old-photo-restoration).
- Three subagent replies returned valid ranking JSON, written verbatim to run files.
- Item files edited with stage `screened` and appended history (Edit calls succeeded).

## Not done
- Did not read the scout file for the top three quotes per card; used item-file summaries. Cards are therefore thinner than the skill asks.
- No keyword popularity (none configured). Accuracy tracking in `state/screen/accuracy.jsonl` is telemetry's job, not done here.
- No ledger line written (wrapper records token cost). Did not verify the item JSON by re-reading it.

## Denied or blocked
None.

## Notes
- Screen is a weak proxy: it favours emotional hooks over utility. Nothing here is demand evidence.
- Photo restoration risk note stands: depends on model quality; the spec must show a verifiable capability.
