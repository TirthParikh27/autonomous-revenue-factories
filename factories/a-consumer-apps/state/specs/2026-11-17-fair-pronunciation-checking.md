# Spec (killed at the gate): 2026-11-17-fair-pronunciation-checking

**Job:** Language learners practising speaking want pronunciation judged correctly.
**Differentiation statement (attempted):** Unlike Speak, Mondly, Babbel, Busuu and Pimsleur, this app would accept right speech, reject wrong speech and say what to fix, which matters because 10 dated 2026 complaints point both ways (Speak 2026-10-28 "accept any word", Speak 2026-11-15 "pronounce perfectly yet it will not recognize"). Source: scout edu-b3.

**Why it does not pass**
1. The capability is a measurement of pronunciation accuracy. Doing it needs a speech-assessment service or a trained model, i.e. a credential or data source the factory does not hold; on-device recognition is the same technology the reviewers complain about. The spec skill forbids promising a feature that needs one.
2. Complaints contradict each other (over-accepts and over-rejects); the scout says the reviews cannot show which. Accuracy cannot be shown in an ad before building, so a demand test would test a claim the factory cannot demonstrate.
3. Language-pair, adaptive-explanation and gamification complaints (edu-b4, edu-b5) are other jobs and are not blended in.
Revised once: restricted to on-device recognition with a "fix this sound" tip. That is the incumbents' own mechanism and gives no distinct capability.

Competitor URLs (from scout file): Speak id1286609883, Mondly id987873536, Babbel id829587759, Busuu id379968583, Pimsleur id1405735469.

Not checked: whether it matches the earlier language-gamification candidate (state/scout/2026-11-17-education.json); moot because killed.
