# Run 20261117T075047Z-spec-differentiation-3e521d
Stage: spec-differentiation   Items: 2 at `screened`; 1 specced, 1 killed   Model: sonnet   Cost: about $0.80 (budget counter, includes verifier)

## Did
- No STOP in the factory dir or repo root (Glob). Read CLAUDE.md, the skill, budget.yaml, the two items, the Lifestyle and Finance scout files and the earlier LectureSafe spec. SEC-1 (Business scout) is open and does not touch these items; not acted on.
- Wrote specs for both items, spot-checked 6 quotes (Grep over state/scout/reviews/, all found), ran the release-verifier once on both (checklist: state/specs/verifier-20261117T075047Z.md), revised the journal spec once, moved items.

## Evidence and decisions
- **private-journal-that-never-loses-entries -> specced.** Verifier: distinguishable borderline; capability yes, partly (verified backup and restore check; "no AI" and "local" are omissions); stack gap no. Fixes applied: backup key comes from a user passphrase (otherwise it will not open on a new phone); lost-entry complaints cover 4 apps, not 5 (none for DailyBean); AI/cloud complaints are 7, not 8; unsourced lines (trial length, regional payer value, Apple Journal restore) now marked as such. Open risk: Apple Journal's own lock and backup were never checked; demand-test must settle it.
- **private-spend-tracking-without-bank-login -> killed.** Verifier: borderline leaning no; capability yes; stack no gap. Nearest real competitors are manual and CSV-import trackers the scout never read, and no review asks for statement import. Spendee was wrongly in the competitor set (not in fin-c4). Not revised: no revision adds distinctness without browsing, which this stage may not do. Spec kept with a kill note.
- Job reuse check: the spend job differs from the killed bill-list job; the journal job matches no earlier item.
- LEGAL-1 judgement: I did not raise it. The journal avoids mood and mental-health claims; the spend tracker was manual import only, no advice, no linking. Raise if you read the rule more strictly (journal scout notes mention mental-health framing).

## Not done
- No landing page, design, code or web access. No ledger call (no paid API). checks/metadata_similarity and checks/overlap not run (no listing text yet).
- Verifier did not re-check the quotes; I did.
- Competitor prices and the "higher payer value in North America" line are not in any scout file or CLAUDE.md; the journal spec says so. The proposed $3.99 price is an unverified intention.
- Item files got an extra `scores_spec` key rather than overwriting `scores`; tell me if the schema wants otherwise.

## Denied or blocked
- Bash: `python3 -I -c "import json;d=json.load(open('state/scout/2026-11-17-lifestyle.json'));print(json.dumps(d,indent=1)[:14000])"` — "Permission for this tool use was denied. It requires approval, and this session has no approval surface". Same for the finance file. I read both with Read instead.

## Findings
- Scout competitor sets can include apps with no matching complaint (Spendee in fin-c4 per the verifier). Spec writers should cross-check each named app against the complaints.
- Journal and LectureSafe both use a "never lose it" hook; keep listing text distinct (metadata_similarity before release).
- Pipeline: 3 specced items (LectureSafe, Verbatim, InkSafe) await demand-test; no `screened` items remain.

## Proposed lesson
- Check each competitor's complaint coverage in the scout file before writing the differentiation statement; two verifier corrections this run were overclaims of that kind. Evidence: this run's verifier checklist.
