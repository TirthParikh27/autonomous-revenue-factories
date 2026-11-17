# Spec: Verbatim (working name) — 2026-11-17-source-faithful-ai-study-material

**Job:** Turns a university student's own uploaded notes or text PDFs into flashcards and quizzes that use only the sentences in that material, with every card pointing back to its source passage.

**Differentiation statement:** Unlike Turbolearn, StudyFetch, Studley, Noji, Quizlet and Knowt, this app builds cards and quizzes only from text found in the uploaded file, shows the source passage for each, and builds answer keys from that same text, which matters because reviewers of Turbolearn, StudyFetch, Studley and Quizlet report outside content added, definitions reworded, errors and wrong answer keys, while Noji and Knowt reviewers report upload and card-generation failures (13 dated complaints Feb to Nov 2026 in the scout file, e.g. StudyFetch 2026-09-01 "pull outside resources in to supplement your material", StudyFetch 2026-09-16 "changing words up to sound more complex", Turbolearn 2026-10-20 "wrong answers marked as correct"). Source: state/scout/2026-11-17-education-b.json, edu-b2.

**Design choice that keeps it inside what the factory has:** no hosted language model. Cards are cloze and term-definition cards extracted from the user's own sentences by deterministic rules on-device; quiz distractors come from other answers in the same document. This avoids any LLM credential or per-use cost. It is a weaker "AI" story than the competitors tell, and the demand test must show whether faithfulness alone sells. No page, ad or listing may call it AI. The scout cannot tell whether competitor errors come from the model or from upload parsing, so "deterministic extraction fixes it" is an assumption the demand test tests. Reading PDFs needs a PDF parser (native module or WebView pdf.js); no credential.

**Competitor table** (URLs from the scout file)
| App | URL | Lacks (per reviews) |
|---|---|---|
| Turbolearn | https://apps.apple.com/us/app/turbolearn-learn-faster/id6502794561 | wrong keys, outside info |
| StudyFetch | https://apps.apple.com/us/app/studyfetch-ai-tutor/id6663574866 | outside content, rewording, wrong subject |
| Studley | https://apps.apple.com/us/app/studley-ai-study-tutor/id6744783834 | added information, misses document |
| Noji | https://apps.apple.com/us/app/noji-flashcards-study-app/id1573585542 | ignores formatting, PDF makes no cards |
| Quizlet | https://apps.apple.com/us/app/quizlet-more-than-flashcards/id546473125 | AI misreads upload |
| Knowt | https://apps.apple.com/us/app/knowt-ai-flashcards-notes/id6463744184 | wrongly rejects file |
Substitute pressure from NotebookLM and ChatGPT is named by reviewers (scout trend_signals); not in the table, as the scout did not source their URLs.

**Core features**
1. Import text-based PDFs and pasted notes; extract sentences with page reference.
2. Generate cloze and term-definition cards from those sentences only; every card shows its source passage.
3. Quiz mode whose answer key is the source text, with distractors from the same document.

**Not building:** summaries, free-form AI answers, chat tutor, scanned-PDF OCR, images, video, sharing or user-generated public decks, minors' accounts (university and adult learners only).

**Monetisation:** hard paywall after onboarding shows a sample PDF turned into cards with sources. 7-day trial. Proposed price $5.99/month, an intention only; competitor prices not in the scout file and must be confirmed by the demand-test stage. Nothing charged at concept stage.

**Target market:** US first (higher median payer value in North America per RevenueCat data in the research notes; not in the scout file).

**Demand test plan**
- Page promise: "Study cards made only from your own notes. Every card shows its source." Concept page, early access, nothing charged.
- 6 angles: (1) the AI added things your professor never said; (2) wrong answer key on exam night; (3) your definitions, not reworded ones; (4) tap a card, see the page it came from; (5) uploaded nursing slides, got engineering; (6) why this does not hallucinate: it only copies.

**Review risk:** 4.3(b) crowded AI-study space; 5.1.1 file access; copyright on uploaded material (keep it private on-device); 1.2 user-generated content avoided by no sharing; COPPA avoided by 18+ target.

**Claims** (build evidence needed)
- "Every card links to the passage it came from." — test: all cards have a source span that matches the text.
- "Never adds information that is not in your file." — test by construction plus string-match check.
- "Works offline." — airplane-mode test.
Not claimed: "better grades", "accurate" in a general sense.
