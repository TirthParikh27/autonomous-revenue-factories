# Run 20261117T073740Z-spec-differentiation-c1e9cc
Stage: spec-differentiation   Items: 5 at `screened`; 2 specced, 3 killed   Model: sonnet   Cost: about $1.12 (budget counter at last read, includes the verifier)

## Did
- No STOP in the factory dir or repo root (Glob). Read CLAUDE.md, the skill and budget.yaml. One open escalation (SEC-1, Business scout), not affecting these items; not acted on.
- Wrote state/specs/ for all 5 items; spot-checked 8 quotes against state/scout/reviews/ (all found); ran the release-verifier once on 4 specs (checklist: state/specs/verifier-20261117T073740Z.md); revised once; moved items.

## Evidence
- Item stages before: Grep of state/items showed 5 `screened`, 1 `killed` (nutrient tracking, by the screen).
- Quote spot-check (Grep count over state/scout/reviews): 6 phrases from edu-b1/b2/b7/c1 matched 5 files; "jumps to the next exercise" and "outside resources" matched 2 more.
- No earlier specs existed (Glob state/specs, empty), so no Job reuse or name collision with a specced item.
- Decisions:
  - **lecture-recording-never-lost -> specced.** Verifier: distinguishable borderline, capability yes, stack: custom native module, no credential. Corrected two unsupported lines.
  - **source-faithful-ai-study-material -> specced.** First draft would have needed a hosted LLM (a credential the factory lacks), so the spec was rewritten as deterministic extraction from the user's own text. Verifier: yes, yes, needs a PDF parser. Corrected complaint count (13 not 12) and who said what.
  - **watch-strength-logging-that-syncs -> killed.** Verifier: no / yes / stack cannot (watchOS is native Swift, operator has no Xcode); Strong, Fitbod and Hevy already have Watch apps. I did not revise: no revision removes the watch dependency.
  - **portable-flashcard-decks -> killed.** Verifier: no / borderline / yes. Also contradicted itself (free export vs hard paywall) and the scout evidence is 3 apps, mostly Noji. Revising leaves only price positioning.
  - **fair-pronunciation-checking -> killed** at step 2, not sent to the verifier: needs a speech-assessment service; complaints contradict; one revision (on-device only) adds no capability. Its stub spec records why. The "same job as the language-gamification candidate" check is moot.
- Overlap: no two specced jobs share a core job (verifier). Both are Education apps for students; metadata similarity not yet checked.

## Not done
- No landing page, design or code. No web access used. No ledger call (no paid API; the wrapper records token cost).
- Did not run checks/metadata_similarity or checks/overlap (they run in CI and there is no listing text yet).
- Did not verify the RevenueCat "higher payer value in North America" line; it is not in the scout files, and the specs now say so.
- Competitor prices are not in the scout files, so each proposed price ($4.99, $5.99) is an unverified intention; demand-test must read the store pages first.
- Spec data/spec_template.md: never looked for it. The prior run reported it missing; the skill does not name it, so I used the skill's section list.

## Denied or blocked
- None. No permission denials this run.

## Findings
- The stack list has no hosted-LLM or speech-scoring service, which makes "AI" capability ideas hard to spec honestly. Worth an operator decision on whether one is ever allowed (escalation before build), since many AI-app gaps will hit this.
- Native-module work (chunked recording, PDF parsing) is in the two surviving specs; mvp-build will need native modules in an Expo dev build. Operator's Mac has no Xcode; EAS build-only is allowed.
- Both survivors are Education apps naming Quizlet and Knowt; keep listings distinct. LectureSafe's "never lose it" hook is similar to DeckKeep's, which is now killed.
- Verifier flagged one wording trap: Verbatim must not be described as AI anywhere.
- Pipeline: 2 specced items awaiting demand-test, which wants a batch of ideas (max_ideas_per_batch up to 15); more gap-mining is needed.

## Proposed lesson
- Spec the differentiator against what the stack can actually run before writing the full spec: two of five items died on a stack gap or on an LLM credential, which costs a page of work each. Evidence: this run.
