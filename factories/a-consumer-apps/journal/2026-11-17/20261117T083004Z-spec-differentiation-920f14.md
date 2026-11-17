# Run report: spec-differentiation, 20261117T083004Z-920f14

Result: 3 items at `screened`; 1 moved to `specced`, 2 to `killed`. No escalation raised.

## Checks at start
- No `STOP` file in this directory or the repo root (Glob returned none for both).
- `budget.yaml` read: spec-differentiation cap $3.00 per run; `per_item_caps_usd.specced` 3. Run spend at report time about $1.1 across three items. Ledger entry left to the wrapper.
- Open escalations (A-AD-1, ACC-1, PII-1, BUD-1, SEC-1): none touch these items; no `approved/` or `rejected/` files existed.
- Excluded list read: none of scanner, photo restoration, captions matches.
- Earlier specs: lecture, journal, source-faithful study, spend, flashcards, pronunciation, watch, nutrient, bills. Core jobs and names do not collide with the three here. The scanner and journal both pitched "keep it safe locally"; jobs differ, listing text must be separate.

## Results
| Item | Platform | Outcome |
|---|---|---|
| old-photo-restoration-that-keeps-faces | web | `specced` (after one revision) |
| local-document-scanner-no-cloud-lock-in | ios | `killed` |
| caption-editing-with-stable-timing | web | `killed` |

## Verifier answers (release-verifier, spec and scout files only)
1. Photo restoration: distinguishable Borderline; capability Yes (face regions composited from original); stack fit Borderline (vendor, price, resolution unconfirmed).
2. Scanner: distinguishable No (Apple's free built-in scanner never scouted); capability Yes, weakly (mostly absences); stack fit Yes (custom native scan module in EAS build).
3. Captions: distinguishable No (web competitors never scouted); capability Yes, narrow; stack fit Borderline (speech vendor unnamed, ffmpeg.wasm size and Cloudflare file limit unconfirmed; the verifier's file-size figures were from memory).

## Reasoning
- Photo: verifier gaps were real and fixed in one revision: "faces exactly as original" conflicted with cleanup in face boxes; "face data never leaves the browser" was false as drafted (now faces are blanked before upload); seam risk added as a required test; vendor and price stated as unconfirmed; unsupported "buyers arrive from the web" reworded as an assumption. Q1 and Q3 stay borderline because they cannot be settled without web access. I moved it on because the differentiator is structural and the demand test is the real gate. This was a judgment call.
- Scanner: kill. Revising could not fix Q1, and an iOS item that cannot be told from a free native tool carries 4.3(b) account risk. Spec also contradicted itself (folder lost on app deletion vs "rebuilds on any install"; hard paywall vs the sourced complaint about export behind a subscription).
- Captions: kill. Evidence is two real apps (the InShot quote is about AI cut) and the lowest count of the batch; the nearest web rivals are unsourced.
- Quote spot-check: 8 of 8 sampled quotes found in `state/scout/reviews/` (scanner 3, photo 5 incl. captions). The InShot caption quote was not rechecked.
- LEGAL-1: photo spec involves photos of people, possibly minors, sent to a third-party model. I judged no LEGAL-1: nothing is shared publicly, face data stays in the browser, faces are not uploaded. Operator should confirm before launch.

## Evidence
- Glob `STOP` and `/home/user/autonomous-revenue-factories/STOP`: "No files found".
- Grep count of quotes in `state/scout/reviews`: "Found 3 total occurrences across 3 files" (scanner); "Found 5 total occurrences across 5 files" (photo and captions).
- Verifier hand-back received (agent a3090ae0f5d004e11); summary table above is its Q1/Q2/Q3.
- Files written: `state/specs/2026-11-17-old-photo-restoration-that-keeps-faces.md`, `...-local-document-scanner-no-cloud-lock-in.md` (marked KILLED), `...-caption-editing-with-stable-timing.md` (marked KILLED). Item JSONs updated with `platform`, verifier scores, history entries. Transitions used: screened to specced, screened to killed (FACTORY_SPEC 3.2 as the skill describes).
- Proposed prices are intentions only and unverified (competitor prices are not in the scout files).
- The North America payer-value note is in each spec marked as assumption; the verifier showed earlier that CLAUDE.md and the scout carry no such figure.

## Not done
- No hosted-AI vendor prices confirmed (no web tools in this stage); photo spec cost is an estimate to confirm before build.
- Verifier did not write `state/specs/verifier-20261117T083004Z.md`: its role limits it to a checklist file. Its findings are recorded above instead.
- No landing page, design or code. No escalation files touched.

## Denied or blocked
- None from the harness. Verifier declined to write the file path I gave it (role rule), quoted: "My role rules say the only file I write is a release checklist file."

## Proposed lesson (one)
A web spec needs web competitors sourced by the scout. Evidence: the captions spec was killed because the nearest web tools were never scouted, and the photo spec has the same gap. Suggest the gap-mining brief ask for web competitors when a candidate may be web.
