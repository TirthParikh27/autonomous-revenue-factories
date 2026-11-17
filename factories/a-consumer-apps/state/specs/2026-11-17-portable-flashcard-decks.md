# Spec: DeckKeep (working name) — 2026-11-17-portable-flashcard-decks

**Job:** Lets a student who builds flashcards keep every deck on their own phone, never silently deleted, and move decks in and out of other study apps in standard formats.

**Differentiation statement:** Unlike Noji, Quizlet, Brainscape, Knowt and AnkiMobile, this app keeps decks local-first with automatic versioned backups and import/export in common formats on the free tier, which matters because reviewers report decks deleted, drafts lost, and export locked behind a paid plan (10 dated complaints, e.g. Noji 2026-07-29 "my account is gone and I cannot access any of my decks", Quizlet 2026-11-11 "freshly made quizlets randomly deleting after saving", Brainscape 2026-09-25 "you cannot export your decks until you are a pro user"). Source: state/scout/2026-11-17-education-b.json, edu-b7.

**Weakness stated plainly:** evidence is thin (3 apps, mostly Noji) and Anki is a strong free incumbent that already imports and exports; the scout did not test Anki's export. The verifier is asked whether this is distinct enough.

**Competitor table** (URLs from the scout file)
| App | URL | Lacks (per reviews) |
|---|---|---|
| Noji | https://apps.apple.com/us/app/noji-flashcards-study-app/id1573585542 | decks deleted, different format, few offline |
| Quizlet | https://apps.apple.com/us/app/quizlet-more-than-flashcards/id546473125 | sets deleted, unsaved edits lost |
| Brainscape | https://apps.apple.com/us/app/brainscape-study-flashcards/id442415567 | export needs Pro |
| AnkiMobile | https://apps.apple.com/us/app/ankimobile-flashcards/id373493387 | no deck-loss complaints; listed as the incumbent |
| Knowt | https://apps.apple.com/us/app/knowt-ai-flashcards-notes/id6463744184 | named as an import target; deck loss not read |
| Mochi | https://apps.apple.com/us/app/mochi-flashcards-and-notes/id1507775056 | reviews not read |

**Core features**
1. Local-first deck editor with draft autosave, so a half-made card survives leaving the app.
2. Automatic versioned local backups with one-tap restore.
3. Import and export of decks in CSV and common study-app formats, free.

**Not building:** AI card generation (separate job), social sharing or public decks, accounts for the MVP, a new spaced-repetition algorithm beyond a basic scheduler.

**Monetisation:** hard paywall after onboarding shows a deck imported, edited, deleted and restored. 7-day trial. Proposed price $3.99/month, an intention only; competitor prices not in the scout file (only AnkiMobile $24.99 one-time, from the store listing at scout time); demand-test stage must confirm. Nothing charged at concept stage.

**Target market:** US first (higher median payer value in North America).

**Demand test plan**
- Page promise: "Your flashcards, kept. Import, export, restore." Concept page, early access, nothing charged.
- 6 angles: (1) the deck that vanished after an update; (2) lost a draft switching apps; (3) export without paying; (4) move from Quizlet in one tap; (5) restore yesterday's version; (6) your deck should outlive the app.

**Review risk:** 4.3(b) copycat flashcard apps and Anki similarity; 5.2 intellectual property when importing decks from other services; 2.1 completeness; keep import formats public and documented.

**Claims** (build evidence needed)
- "Imports CSV decks." / "Exports your decks free." — scripted test.
- "Restore a previous version of a deck." — restore test.
- "Saves your card as you type." — test.
Not claimed: compatibility with a named service's private format unless tested.
