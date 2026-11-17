# Spec: LectureSafe (working name) — 2026-11-17-lecture-recording-never-lost

**Job:** Lets a student who records whole lectures on their phone be sure the audio is saved safely on the device, even through a crash, a full phone, a phone call or a force-quit, so the recording is never lost before notes are made.

**Differentiation statement:** Unlike Knowt, StudyFetch, Turbolearn, Studley and Quizlet, this app writes the recording to disk in short chunks as it records and recovers any interrupted session on next launch, which matters because reviewers of all five report whole lectures lost or "not saved" (10 dated 2026 complaints, e.g. Studley 2026-06-02 "the file was immediately Lost", Turbolearn 2026-09-10 "even the recovery fails", Knowt 2026-09-16 "you will lose your recording"). Source: state/scout/2026-11-17-education-b.json, edu-b1.

**Competitor table** (URLs from the scout file; what each lacks is from the sampled complaints only)
| App | URL | Lacks (per reviews) |
|---|---|---|
| Turbolearn | https://apps.apple.com/us/app/turbolearn-learn-faster/id6502794561 | recording not saved, recovery fails |
| StudyFetch | https://apps.apple.com/us/app/studyfetch-ai-tutor/id6663574866 | lost lectures, recorder stops catching audio after ~30 min |
| Studley | https://apps.apple.com/us/app/studley-ai-study-tutor/id6744783834 | recording disappears after stop |
| Knowt | https://apps.apple.com/us/app/knowt-ai-flashcards-notes/id6463744184 | recording lost unless app stays open |
| Quizlet | https://apps.apple.com/us/app/quizlet-more-than-flashcards/id546473125 | lost lecture, no retrieval |
| Unstuck AI Note Taker | https://apps.apple.com/us/app/unstuck-ai-note-taker/id6714484560 | listed in scout file, reviews not read |
Not in the table and not sourced by the scout: the phone's built-in voice recorder (the screen notes it covers part of the need; the scout file does not mention it). Whether competitors write audio in chunks was not checked by the scout; the claim is only that their users report losses. The differentiator against a plain recorder is the lecture-shaped workflow plus visible saved-proof, and the onboarding demo of interrupt-and-recover must ship because it is the only way a reviewer sees the difference in a minute. Needs a custom native module for chunked recording and on-device transcription (no credential).

**Core features** (at most 3)
1. Crash-safe recording: audio written to local storage in chunks while recording; background recording; interrupted sessions recovered on launch.
2. Visible "saved" proof: a running saved-bytes and saved-minutes indicator, plus storage and battery check before a long lecture starts.
3. Lecture library with on-device transcript where the Apple speech framework allows it; export of audio and text to Files/share sheet.

**Not building:** AI summaries, flashcards or quizzes (that is a different job, see the source-faithful item); cloud accounts for the MVP; sharing or collaboration; live captions; video.

**Monetisation:** hard paywall after onboarding has shown a real test recording being interrupted and recovered. 7-day trial (reference default). Proposed price: $4.99/month, an intention only. Competitor prices are not in the scout file, so the price is unverified and the demand-test stage must read them from the store pages before the page shows it. Nothing is charged at the concept stage.

**Target market:** United States first. Median payer value is higher in North America than elsewhere (RevenueCat data per CLAUDE.md/research notes; not in the scout file).

**Demand test plan**
- Page promise: "Record the whole lecture. Never lose it." Concept page, "in development / early access", nothing charged.
- 6 post angles: (1) the fear of the stopped recording at minute 55; (2) phone call arrives mid-lecture; (3) phone storage full; (4) "what happens to your recording if the app is closed" explainer; (5) finals week checklist for recordings; (6) side-by-side demonstration of the recovery behaviour, only after it is built.

**Review risk:** microphone and background-audio permission text (5.1.1); recording consent laws vary by state and classroom, so the app needs a plain reminder, not legal advice; 4.3(b) similarity to built-in recorders and other note apps; 2.1 completeness if background recording is flaky.

**Claims** (each needs evidence from the shipped build)
- "Saves your recording as you record." — test: kill the app mid-recording, confirm recovered audio length.
- "Recovers an interrupted recording on next launch." — same test.
- "Works with the screen locked." — device test.
Not claimed: "never fails" as an absolute guarantee.
