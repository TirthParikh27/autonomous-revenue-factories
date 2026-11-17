# Spec: InkSafe (working name) — 2026-11-17-private-journal-that-never-loses-entries

**Job:** Lets a person who keeps a private daily journal on their iPhone keep every entry on the device behind an app lock, with a backup file they control that they can prove restores, so years of entries survive a phone change or update.

**Differentiation statement:** Unlike Day One, Daylio, Stoic, DailyBean and Apple's Journal, this app keeps entries only on the device behind a lock, contains no AI, and writes a verified backup file to a place the user picks (Files, iCloud Drive, AirDrop) with a "test restore" that proves the backup opens, which matters because reviewers of four of them (Apple Journal, Day One, Daylio, Stoic; not DailyBean) report lost entries (8 dated 2026 complaints, e.g. Journal 2026-11-14 "my phone failed and I have a new one but seemingly have lost all of my journaling", Day One 2026-07-19 "deleted years of journaling with an update", Daylio 2026-08-06 "I closed my app out once and everything is GONE") and unwanted AI or cloud (7 complaints, e.g. Day One 2026-09-08, Stoic 2026-10-02, DailyBean 2026-11-14). Source: state/scout/2026-11-17-lifestyle.json, lifestyle-j1 and j2. Spot-checked 3 quotes against state/scout/reviews/ (found).

**Competitor table** (URLs from the scout file; "lacks" is from sampled complaints only)
| App | URL | Lacks (per reviews) |
|---|---|---|
| Day One | https://apps.apple.com/us/app/day-one-daily-journal-diary/id1044867788 | AI can't be turned off, lost entries, sync stopped |
| Daylio | https://apps.apple.com/us/app/daylio-journal-mood-tracker/id1194023242 | entries vanish, AI prompts worry users |
| Stoic | https://apps.apple.com/us/app/stoic-journal-mental-health/id1312926037 | no lock found, entries not saved, AI |
| DailyBean | https://apps.apple.com/us/app/dailybean-simplest-journal/id1553223828 | cloud storage, complaint of data harvesting |
| Journal (Apple) | https://apps.apple.com/us/app/journal/id6447391597 | entries lost, no restore after phone change |
Not sourced by the scout: whether Apple Journal has its own lock or backup; the scout did not say. Some Day One users like its AI, so the no-AI audience size is unknown. Cause of the data loss (sync, update, user error) is unverified.

**Core features** (at most 3)
1. Local-only journal: text and photos stored on device, app lock (Face ID / passcode), no account, no analytics, no AI.
2. User-controlled backup: backup file encrypted with a passphrase the user sets (key derived from the passphrase, not stored in the Keychain, so it opens on a new phone), written to a location the user chooses, with reminders if the last backup is old.
3. Restore check: open any backup and see entry count and date range before restoring; restore onto a new phone from the file alone.

**Not building:** AI prompts or summaries, mood or mental-health tracking, streak gamification, cloud sync, sharing, a web app.

**Running cost:** none per subscriber (no server, no hosted model). Price covers store fee and RevenueCat only.

**Monetisation:** hard paywall after onboarding has shown writing an entry, exporting a backup and opening it. 7-day trial (reference default). Proposed price $3.99/month, an intention only. Competitor prices are not in the scout file, so it is unverified; demand-test must read the store pages first. Nothing is charged at concept stage.

**Target market:** United States first. The claim that median payer value is higher in North America is from the research notes, not verified here (not in CLAUDE.md or the scout file). The 7-day trial is a reference default from budget.yaml. Apple Journal's "no restore after phone change" rests on one review. Distinctiveness against Apple Journal's own lock and backup is unchecked; the demand test and a store-page read must settle it.

**Demand test plan**
- Page promise: "A private journal that lives on your phone, with a backup you can actually open." Concept page, "in development / early access", nothing charged.
- 6 post angles: (1) "I lost two years of entries" fear; (2) new phone, where did my journal go; (3) a journal with no AI, ever; (4) lock your journal, nothing leaves the phone; (5) the one-minute backup you can test; (6) what happens to your entries when an app update goes wrong.

**Review risk:** 4.3(b) similarity to the many journal apps and Apple's own; 5.1.1 data and Face ID text; 2.1 completeness if restore fails; any mental-health wording would pull in health guidelines, so none is used.

**Claims** (each needs evidence from the shipped build)
- "Your entries stay on your phone." — network inspection of the build shows no requests with entry data.
- "No AI." — code and dependency review.
- "Backup file restores on a new phone." — test restore on a clean install.
Not claimed: "never loses data", anything about mental health, anything about competitors' practices.
