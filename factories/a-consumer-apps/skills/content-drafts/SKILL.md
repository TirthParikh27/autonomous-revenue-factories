---
name: content-drafts
description: Stage 8 of Factory A. Use weekly for each app at `winner`, to render short-form slideshows and screen-recording videos from real screenshots and schedule them in Postiz as drafts for the operator to publish. Never use to publish.
---

# Content drafts

Runs on the operator's Mac, because the HeyGen CLI and login are there (verified 2026-11-16). Demo videos follow `skills/ad-creative/SKILL.md`, with the app's character and real screens from the shipped build. Read `CLAUDE.md` and `budget.yaml` first. You produce drafts. The operator picks audio and publishes from a warmed account.

## Inputs

- One app at `winner`. Organic content is made for winners only. Demand tests and paid tests use ads, prepared by their own skills.
- `state/build/<id>/screenshots.json` and the screenshot files (live mode). Spec angles (concept mode).
- `demand/<id>/claims.yaml` or the app's updated `claims.yaml`.
- `data/content_formats.yaml`: approved formats and hook templates.
- `state/metrics/` for the last batches, to see which angles produced signups or downloads.
- `content` section of `budget.yaml`.

## Formats

1. **Slideshow:** 3 to 6 frames built from real app screenshots with text overlays. This is the cheapest format and, per a secondary summary of TikTok policy, the least likely to need an AI label.
2. **Screen-recording demo:** a simulator recording of the core job taken from the CI build (the Mac has no Xcode), with motion graphics from HyperFrames or HeyGen, assembled with ffmpeg, optional ElevenLabs voiceover in the brand's voice.
3. **Concept (demand test only):** designed mock-ups visibly labelled as concept with "in development" on every frame.

Generative video and realistic AI people or scenes are disabled in `budget.yaml`.

## Steps

1. Count drafts already created for this app this week. Do not exceed `content.max_drafts_per_app_per_week`.
2. Choose angles: keep the top angle by signups or downloads per published post, drop the bottom one, add one new one. Views alone do not count.
3. Write scripts and captions, then render assets into `content/<id>/<batch>/`. Check the ElevenLabs price against the ledger before any voiceover call.
4. Write `manifest.json`: for each post the format, asset paths, caption, hashtags, source screenshot hashes, claims used, `concept`, `ai_generated_elements` (for example synthetic voice), and `ai_label_required`.
5. Set `ai_label_required: true` if any realistic AI-generated person or scene is present. For synthetic voiceover only, set `ai_label_review: true` so the operator decides at publish time. TikTok's rule for voice was not confirmed from a primary source.
6. Run `checks/copy_lint --claims` with the item's `claims.yaml` on every caption and overlay. Confirm every live-mode frame has a source hash in `screenshots.json`, every concept frame carries the concept wording, and every post has its label fields.
7. If this is the first batch for the app, a new format, or any post has `ai_label_required: true`: raise `A-CNT-1` and stop before Postiz.
8. Otherwise run `python3 publish.py drafts content/<id>/<batch>/manifest.json --claims <claims.yaml>`. It creates each post as a draft and reads it back. Until Postiz credentials exist it runs dry and writes `drafts.json` without contacting Postiz.
9. Post one Slack message: number of drafts, the app, and anything the operator must decide when publishing (audio, label).

## Tools

Simulator recording from CI artefacts, HeyGen CLI and HyperFrames skills as installed locally (verified 2026-11-16; run HyperFrames with `npx hyperframes`), ffmpeg, ElevenLabs API, `publish.py drafts`, Read, Write, Bash.

## Hard check

`checks/copy_lint` fails testimonial patterns, ratings, counts and claims not in `claims.yaml`. Then the Postiz read-back for every post must return a draft state. If any post is not a draft, treat it as an incident: report it first in the run report and raise `GEN-1`.

## Outputs

- `content/<id>/<batch>/` assets and `manifest.json` with Postiz draft ids.

## Stop conditions

- Weekly draft cap or paid API cap reached.
- No screenshots from the shipped build exist: stop. Do not substitute mock-ups for a live app.
- The app has an open `A-SUN-1` or `A-ACCT-1`: do not draft.

## Never

- Never publish, schedule for automatic posting, or change a draft's state.
- Never write a testimonial, a customer quote, a "my experience" script, or a before-and-after result. Never depict a person as a user of the app.
- Never use the likeness or voice of a real person. Never clone a voice.
- Never use copyrighted music or attach audio. Audio is the operator's choice on the device.
- Never drive a phone, an emulator or the TikTok app. Never use ADB.
- Never buy or exchange engagement, and never draft comment replies posing as a user.
- Never strip provenance metadata from a rendered file.

## Finish

End by calling the shared `run-report` skill. Include the lint output and the read-back state of each Postiz post.
