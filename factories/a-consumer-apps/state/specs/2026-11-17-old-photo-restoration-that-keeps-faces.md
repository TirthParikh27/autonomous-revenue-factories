# Spec: TrueFace Restore (working name) — 2026-11-17-old-photo-restoration-that-keeps-faces

**Job:** Lets a person restoring old family photos repair damage (scratches, dust, fading) while every face stays exactly as it was in the original, so relatives are still recognisable.

**Platform:** `web`. Photos are uploaded from a phone or a scan, processing happens on a server anyway, and buyers plausibly search the web for "restore old photo" (an assumption: the scout has no keyword data, the demand test checks it). Both would work; web is cheaper to build, has no store review (the category is crowded, so 4.3(b) is a real risk on iOS) and uses no release slot. Face detection runs in the browser, so no face data is sent for detection.

**Differentiation statement:** Unlike FixMyPics, RetroFix and Photo Scan Plus, this product locks every detected face to its original pixels (only gentle, non-generative cleanup is applied there) and restores the rest of the photo, with per-face control and an original-versus-result overlay, which matters because reviewers of all three report faces being changed (RetroFix 2026-06-07 "Made a baby photo into a 20 year old man's face"; FixMyPics 2025-04-22 "disfigured faces"; Photo Scan Plus 2026-01-02 "making people look like someone else") and one wants a manual override (Photo Scan Plus 2025-12-08 "cannot find a manual override ability to identify the missed face"). Source: state/scout/2026-11-17-photo-video.json, pv-c1 (12 dated complaints, 3 apps). Quotes spot-checked against state/scout/reviews: found in the FixMyPics, RetroFix and Photo Scan Plus files.

The differentiator is structural, not a model-quality claim: face regions are blanked in the browser before upload, so the hosted model never sees a face, and the output face regions are composited back from the original pixels, so a face cannot be re-invented by construction. Seams are handled by a feathered edge and tone matching along the boundary; a seam test ("floating head" defect, Photo Scan Plus 2025-12-06) is required before release. Trade-off stated honestly: a face with its own heavy damage stays damaged unless the user turns on the optional "enhance this face" (non-generative cleanup in the browser: levels, denoise, mild sharpen), which is off by default, shown beside the original, and reverts in one click.

Competitor status: every sourced competitor is an iOS app and no web competitor was scouted, and the scout notes that free chat AI tools and Google PhotoScan are reported as doing better. Whether a first-time visitor sees a difference from those is unproven and is what the demand test must show. The scout does not show that these three apps lack face preservation, only that their users report faces changed.

**Competitor table** (URLs from the scout file)
| App | URL | Lacks (per reviews) |
|---|---|---|
| FixMyPics | https://apps.apple.com/us/app/fixmypics-restore-old-photos/id1600979855 | faces disfigured, cartoonish; scratches blurred not removed |
| RetroFix | https://apps.apple.com/us/app/retrofix-old-picture-restore/id6478808149 | changes faces, glasses and gender |
| Photo Scan Plus | https://apps.apple.com/us/app/photo-scan-plus/id951627022 | AI face reconstruction makes people look like someone else; no manual face override |
Also named in the scout, not read: Renew, Yore, Colorize (no URLs in the scout file, so not tabled). The scout notes reviewers saying general chat AI tools or Google PhotoScan do better; those free substitutes are a demand risk. Only three sourced competitors, below the five-competitor reference point; not padded.

**Core features** (at most 3)
1. Upload a photo; faces are detected in the browser and shown with outlines; the user can add or remove a face box by hand.
2. Restore: hosted model repairs scratches, dust, tone and sharpness everywhere except face boxes (blanked before upload); face boxes keep their original pixels.
3. Review: original-versus-result overlay, per-face optional enhance, download at full resolution.

**Not building:** colourisation, animation of photos, face swap, background replacement, video, albums or sharing, public galleries (so no user-generated content is shown to anyone else).

**Running cost (estimate, unverified):** one hosted image-restoration call per photo through a Supabase edge function. I cannot browse in this stage, so the vendor price is unknown. A hosted image-restore call is typically in the cents range per image; before the build stage the price must be confirmed from the vendor page and recorded. Cap each subscriber at a fixed number of photos a month, chosen so the worst-case cost stays well under half the price (for example 30 photos at an assumed $0.05 is $1.50 against a proposed $7.99/month). The edge function holds the key; photos are deleted after processing. Vendor: not chosen and no account exists (this stage cannot browse); the build stage must pick one, confirm the price and the maximum output resolution from the vendor page, and read its data-retention terms, and build runs stay in dry-run until the account exists. "Full resolution" download is promised only up to what that vendor returns.

**Monetisation:** Stripe Checkout (test mode only in any agent run). Free preview of the first restored photo at reduced size, then a paid plan. 3-day trial is an intention. Proposed price $7.99/month, an intention only; competitor prices are not in the scout file and must be read by the demand-test stage before a page shows a price. Price, billing period and trial terms visible before payment; cancel inside the product; terms, privacy and refund pages; the refund text must not exclude Australian Consumer Law guarantees.

**How buyers find it:** ad angle "Fix the scratches. Keep their faces." Search terms taken from the scout's wording, volume not checked (no keyword source configured): "restore old photos", "fix old family photo faces", "old photo restoration keeps face", "AI photo restoration changes face".

**Target market:** United States first. The research notes say median payer value is higher in North America than elsewhere; the scout file has no regional figure, so this is an assumption.

**Demand test plan**
- Page promise: "Restore the photo, not the face." Concept page, "in development / early access", nothing charged, no mock-up shown as a shipping product.
- 6 post angles: (1) "AI turned my grandfather into someone else" explainer; (2) how face lock works as a diagram, no real people; (3) scratches removed, not blurred; (4) a checklist for scanning old prints; (5) manual face boxes for faces the detector misses; (6) before-versus-after on public-domain or operator-owned photos only, after it is built.

**Review risk (web):** privacy: photos of people (possibly minors) are sent to a third-party model, so the privacy policy must say so, uploads must be user-owned, and retention must be minimal; face detection is client-side, face regions are blanked before upload and no face template is stored (this avoids biometric-identifier rules but needs a legal check by the operator before launch); consumer law on refunds and trials; Stripe billing disclosures. Flagged in the run report: I judged this does not need `LEGAL-1` at spec stage because nothing is shared publicly and no face data is collected, but the operator should confirm.

**Claims** (each needs evidence from the shipped build)
- "Faces are never regenerated: with enhance off they are your original pixels." — pixel comparison of face regions with enhance off (exact match expected, nothing else applied).
- "Faces are never sent to the restoration service." — inspect the upload payload: face boxes blank.
- "Scratches and dust are removed, not blurred." — before and after on a test set.
- "Your photos are deleted from our storage after processing." — inspect storage after a job. Vendor retention is stated separately from the vendor's terms; not claimed as ours.
Not claimed: "perfect" or "AI-accurate" restoration.
