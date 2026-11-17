# Spec: CaptionLock (working name) — 2026-11-17-caption-editing-with-stable-timing

**KILLED at spec stage (2026-11-17).** The evidence is iOS reviews (the lowest complaint count of the batch; only two apps really support the editing-timing complaint, the InShot quote is about AI cuts), but the web product's nearest competitors were never scouted, and ordinary SRT editors already keep timestamps when text changes. The verifier could not tell it from them. A web spec needs web competitors sourced first. Reopen after a scout run that reads web caption tools.

**Job:** Lets a short-video creator fix the words of auto-generated captions and export them, with every other word keeping its timing, so editing one word never breaks the rest of the captions.

**Platform:** `web`. Caption fixing is detail work at a timeline, buyers can search for the problem, and web ships without store review and uses no release slot. Risk: the complaints come from phone editors, so creators may prefer the phone; the cheap web concept test shows this before any build. The scout also flagged web as a likely fit.

**Differentiation statement:** Unlike Captions, Captiono and InShot, this product treats the caption as per-word timed text and keeps each untouched word's timestamps fixed when another word is corrected, which matters because reviewers report that editing words breaks timing (Captions 2026-11-08 "you can't edit the words without messing up the timing"), that timing must be fixed word by word (Captiono 2025-12-06) and that timings are wrong after an edit (InShot 2026-11-12 "when applies the timings off"). Source: state/scout/2026-11-17-photo-video.json, pv-c2 (8 dated complaints, 3 apps; count is modest). Quotes spot-checked against state/scout/reviews: found in the Captions and Captiono files; the InShot quote was not rechecked.

**Competitor table** (URLs from the scout file)
| App | URL | Lacks (per reviews) |
|---|---|---|
| Captions | https://apps.apple.com/us/app/captions-ai-edits-your-video/id1541407007 | word edits shift timing, caption/voice delay, keyframes harder |
| Captiono | https://apps.apple.com/us/app/captiono-ai-subtitles/id6538722927 | edit and re-time word by word, captions do not match video |
| InShot | https://apps.apple.com/us/app/inshot-video-editor/id997362197 | timings off after the AI cut is applied |
| CapCut | https://apps.apple.com/us/app/capcut-photo-video-editor/id1500855883 | read by the scout; no caption-timing complaint sourced |
| Lowdeo (web) | https://trustmrr.com/startup/lowdeo | web AI clipper with word-by-word captions; TrustMRR verified 30-day revenue $1,157.78 (a revenue signal, not a complaint) |
Not in the table because the scout did not source them: desktop and web caption tools (the real nearest web competitors). The scout was iOS-only, so differentiation against them is unproven; this is the main weakness of the spec.

**Core features** (at most 3)
1. Upload a video (audio is extracted in the browser); hosted speech-to-text returns word-level timestamps; captions shown as editable text over a timeline.
2. Edit words with timing preserved: a replaced word inherits the span of the word it replaces, split or merged words share the span proportionally, no other word moves; a visible "timing locked" marker on untouched words.
3. Export captions as SRT and VTT, and a burned-in MP4 produced in the browser (ffmpeg compiled to WebAssembly) so no video is stored by us.

**Not building:** video editing, cuts, B-roll, templates and animated styles, AI clipping, translation, dubbing, team accounts.

**Running cost (estimate, unverified):** speech-to-text on the audio track only, called from a Supabase edge function. I cannot browse in this stage, so the vendor price per audio minute is unknown; it must be confirmed from the vendor page before build. Cap each subscriber at a monthly audio-minute allowance chosen so worst-case cost stays under half the price. Burn-in runs in the visitor's browser at no server cost. Audio is deleted after transcription.

**Monetisation:** Stripe Checkout (test mode only in agent runs). Free: one short clip with watermark-free SRT export; paid for longer clips and burned-in MP4 (intention). Proposed price $9/month, an intention only; competitor prices are not in the scout file and must be read before a page shows a price. Price, billing period and trial terms visible before payment; cancel inside the product; terms, privacy and refund pages that respect Australian Consumer Law.

**How buyers find it:** ad angle "Fix a caption word. Nothing else moves." Search terms from complaint wording, volume not checked (no keyword source): "edit auto captions without changing timing", "fix caption timing after editing", "caption editor word timestamps", "edit subtitles keep timing".

**Target market:** United States first, English captions first (the scout notes non-English quality issues it could not quote). The research notes say median payer value is higher in North America than elsewhere; the scout has no regional figure, so this is an assumption.

**Demand test plan**
- Page promise: "Edit the words. Keep the timing." Concept page, "in development / early access", nothing charged.
- 6 post angles: (1) the typo fix that shifts every caption; (2) word-by-word re-timing is wasted time; (3) timing-locked words explained with an animation of the timeline, no real people; (4) export SRT once, reuse everywhere; (5) fix a name the transcript got wrong; (6) before-versus-after screen recording, after it is built.

**Review risk (web):** privacy of uploaded audio and video that may contain other people's voices; hosted speech provider terms; consumer-law refund wording; browser memory limits for large video burn-in (2.1-like completeness risk: the product must say supported length). No store rules apply.

**Claims** (each needs evidence from the shipped build)
- "Editing a word does not move the other words." — compare timestamps before and after an edit on a test clip.
- "Export SRT and VTT." — open exports in a standard player.
- "Your video is not uploaded." — only if burn-in runs fully in the browser; verify network traffic. The audio track is sent for transcription and must be disclosed.
