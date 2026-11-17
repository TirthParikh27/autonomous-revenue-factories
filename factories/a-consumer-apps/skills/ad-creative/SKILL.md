---
name: ad-creative
description: Helper skill for Factory A, not a stage. Use from demand-test, paid-test and content-drafts whenever ads are made. It gives each app a character, writes ad scripts, renders short app-demo videos with HyperFrames and has them reviewed by eye before anyone else sees them.
---

# Ad creative

An ad is the only thing a stranger sees before deciding whether the idea is worth a tap. A weak ad makes a good idea look dead, and that is a false result the factory pays for. Plain text cards are not acceptable output. Every idea gets short demo videos that show the product doing its job.

## What good looks like

These are the patterns behind app ads that work on Meta and TikTok. Weigh them against the idea; they are guidance, not a formula.

- **Vertical, short, silent-safe.** 9:16, about 15 to 25 seconds. Most people watch with sound off, so on-screen words carry the whole story.
- **Hook, problem, demo, ask.** The first two seconds name a moment the viewer has lived, in their words, taken from the sourced complaints. Then the product is shown solving it. Then one clear ask. Walkthrough ads that show the app in use outperform ads that only talk about it.
- **Show, don't describe.** The middle of the ad is the product's screens moving: a tap, a result, the one thing competitors fail at going right. One job per ad.
- **Different reasons to care, not different colours.** The three ads for an idea differ in the reason to tap (the failure avoided, the time saved, the feeling after), so the test tells you which reason works. Build each from swappable parts (hook, demo, end card) so a winning hook can be paired with another demo later.
- **Looks made by a person who cares.** One typeface, a small palette, generous type (nothing under about 40 px on a 1080 px frame), calm motion with purpose. Nothing overlaps, nothing is cut off, nothing important sits in the top 250 px or bottom 400 px where the platform draws its own buttons.
- **Honest.** See the limits below. An ad that over-promises buys clicks that never convert, which is the expensive kind of false positive.

## The character

Each app gets one character that appears in every ad, on the page and later in the app. It need not be human. It makes a batch of ads recognisably one brand, and it gives the ad a narrator.

Write `character.md` in the idea's ads folder once, before the first script:

- **What it is and why.** A shape that fits the product's job (a keeper for something that saves, a guide for something that teaches). A simple silhouette that reads at thumbnail size, drawn as inline SVG so it renders anywhere and can be animated.
- **Its job in the ad.** It reacts and narrates. It is the brand's voice, never a customer.
- **A few states.** Neutral, greeting, thinking, pleased, worried, relieved. Use only what the script needs.
- **Voice.** Two or three lines showing how it talks: short, warm, specific.
- **Palette and typeface** shared with the page.

Keep it restrained. The product is the hero and the character points at it. Do not copy or resemble an existing mascot.

## Steps

1. Read the spec and the scout file's complaints. Pick three different reasons to care.
2. Write `character.md` if the idea has none.
3. Write one script per ad to `scripts.md`: the hook line, each scene with its on-screen words and what the product screen does, the character's lines, the end card, and a voiceover line per scene for when a voice is added. Read each script against the patterns above before building it.
4. Build each video as a HyperFrames composition: one folder per ad holding one `index.html`. `example/index.html` in this skill is a working composition to study for structure. Write each ad for its own idea; do not reskin the example. The rules HyperFrames needs:
   - A root element with `data-composition-id`, `data-start="0"`, `data-duration`, `data-width="1080"`, `data-height="1920"`.
   - Timed elements carry `class="clip"`, `data-start` and `data-duration`.
   - All motion is one paused GSAP timeline registered as `window.__timelines["main"]`.
   - Nothing random, no clock, no network calls beyond the GSAP script. Draw screens and the character in HTML and SVG.
5. Before the app exists, the screens are designed mock-ups of what the spec describes. Show only features in the spec, and keep a small "Concept" mark on screen throughout. After the app ships, use real screenshots and screen recordings from the build and drop the mark.
6. Look at it. Run `npx -y hyperframes@0.9.59 snapshot <ad folder> --at <a time in each scene> --output <ad folder>/frames` and Read the contact sheet. Fix what you see.
7. Render: `npx -y hyperframes@0.9.59 render <ad folder> -o <ad folder>/ad.mp4`.
8. Also make one still per idea (a 1080 by 1350 frame from the strongest scene, saved with `snapshot`), because stills are still cheap to run and some placements want them.
9. Write `ads.json`: per ad, the file, the reason to care it tests, primary text, headline and call to action.
10. Hand the frames, scripts and `ads.json` to the `creative-reviewer` agent. Fix what it reports and send it back once. If an ad still falls short, drop that ad and say so. If fewer than two ads survive for an idea, the idea is not ready for the batch.

## Limits that do not bend

- The character or any presenter speaks as the brand. It never claims to be a user, never says "I tried this", never reports a result. No testimonials, ratings, user counts or invented people.
- Before the app exists, every ad says "in development" or "early access", and the end card says nothing is charged today.
- Every claim is in the idea's `claims.yaml`.
- No real person's likeness, no minors, no public figures, no competitor logos or screens.
- Generated video and realistic generated people stay off unless `budget.yaml` allows them. HyperFrames renders HTML you wrote, so it is not generated video. A voice or a realistic presenter needs a paid tool, which is `ACC-1`.
- Run `checks/copy_lint` on the scripts and `ads.json`. Its exit code is final.

## Outputs

In the idea's ads folder: `character.md`, `scripts.md`, `ads.json`, one folder per ad with `index.html`, `frames/` and `ad.mp4`, and one still.
