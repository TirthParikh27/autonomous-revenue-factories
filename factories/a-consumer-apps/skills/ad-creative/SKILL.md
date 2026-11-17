---
name: ad-creative
description: Helper skill for Factory A, not a stage. Use from demand-test, paid-test and content-drafts whenever ads are made. It gives each app a character, writes ad scripts, builds HTML mock-ups of the product, and renders short narrated demo videos that walk through them with HyperFrames, reviewed by eye before anyone else sees them.
---

# Ad creative

An ad is the only thing a stranger sees before deciding whether the idea is worth a tap. A weak ad makes a good idea look dead, and that is a false result the factory pays for. Plain text cards are not acceptable output. Every idea gets short demo videos that show the product doing its job.

## What good looks like

These are the patterns behind app ads that work on Meta and TikTok. Weigh them against the idea; they are guidance, not a formula.

- **Vertical, short, silent-safe.** 9:16, about 15 to 25 seconds. Most people watch with sound off, so on-screen words carry the whole story.
- **Hook, problem, demo, ask.** The first two seconds name a moment the viewer has lived, in their words, taken from the sourced complaints. Then the product is shown solving it. Then one clear ask. Walkthrough ads that show the app in use outperform ads that only talk about it.
- **Show, don't describe.** The middle of the ad is a walkthrough of the product. Build the product's screens as HTML mock-ups that look like a real, finished app, then move through them the way a person would: show the whole screen, move in toward the control, tap it, let the screen visibly change, show the result, pull back. The viewer should feel they have used it. One job per ad.
- **A voice that sounds like a person.** A flat, robotic read makes the whole ad feel cheap. Write narration for the ear: how a friend would say it out loud, with contractions, short sentences, one idea per line, and a natural question or pause where a person would take one. Spell out anything a voice might stumble on (numbers, the app's name if it is two words run together). Pick one warm, conversational voice per app and keep it. Listen for energy: the hook has some urgency, the demo is relaxed, the ask is friendly, never a hard sell.
- **Voice leads, pictures follow.** Write the narration first, generate it, and let its real length set each scene. Things appear on screen at the moment the voice names them. The captions carry the same words for viewers with the sound off.
- **Calm, confident motion.** Smooth easing that settles (`power3`), no bouncing, no constant wobble. A steady stage that the camera moves over reads as more expensive than scenes that reset. Let a beat of stillness land before the next move.
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
3. Write one script per ad to `scripts.md`: the hook line, then per scene the narration line, the caption, and what the product screen does (which control is tapped, what changes), and the end card. Read each script against the patterns above before building it.
4. Generate the voice, one file per narration line: `npx -y hyperframes@0.9.59 tts "<line>" -o <ad folder>/audio/vo-<n>.wav --json`. It runs a free local voice and prints `durationSeconds`. The local voice is the fallback: when the operator has connected a premium voice (see `README.md`), use that instead, because it sounds far more human. Use one voice per app. Each scene lasts as long as its line plus a short breath. Place each line in the composition as `<audio class="clip" data-start data-duration data-track-index data-volume="1" src="audio/vo-<n>.wav">`. If the command reports that the voice model is not installed, build the ad silent with captions and say so in the run report; do not stop.
5. Build each video as a HyperFrames composition: one folder per ad holding one `index.html`. `example/index.html` in this skill is a working narrated walkthrough to study for structure (camera, tap, voice clips, captions, character). Write each ad for its own idea; do not reskin the example. The rules HyperFrames needs:
   - A root element with `data-composition-id`, `data-start="0"`, `data-duration`, `data-width="1080"`, `data-height="1920"`.
   - Timed elements carry `class="clip"`, `data-start` and `data-duration`.
   - All motion is one paused GSAP timeline registered as `window.__timelines["main"]`.
   - Nothing random, no clock, no network calls beyond the GSAP script. No endless repeats. Draw screens and the character in HTML and SVG.
   - Draw the phone or browser at full size inside a camera element and animate the camera's position and scale to move in and out. A soft dot that presses and ripples stands for the finger or cursor.
   - When one element gets more than one `fromTo`, give the later ones `immediateRender: false`, or they show too early.
6. Before the app exists, the screens are designed mock-ups of what the spec describes. Show only features in the spec, and keep a small "Concept" mark on screen throughout. After the app ships, use real screenshots and screen recordings from the build and drop the mark.
7. Look at it. Run `npx -y hyperframes@0.9.59 snapshot <ad folder> --at <a time in each scene> --output <ad folder>/frames` and Read the contact sheet. Fix what you see.
8. Render: `npx -y hyperframes@0.9.59 render <ad folder> -o <ad folder>/ad.mp4`.
9. Also make one still per idea (a 1080 by 1350 frame from the strongest scene, saved with `snapshot`), because stills are still cheap to run and some placements want them.
10. Write `ads.json`: per ad, the file, the reason to care it tests, primary text, headline and call to action.
11. Hand the frames, scripts and `ads.json` to the `creative-reviewer` agent. Fix what it reports and send it back once. If an ad still falls short, drop that ad and say so. If fewer than two ads survive for an idea, the idea is not ready for the batch.

## Limits that do not bend

- The character or any presenter speaks as the brand. It never claims to be a user, never says "I tried this", never reports a result. No testimonials, ratings, user counts or invented people.
- Before the app exists, every ad says "in development" or "early access", and the end card says nothing is charged today.
- Every claim is in the idea's `claims.yaml`.
- No real person's likeness, no minors, no public figures, no competitor logos or screens.
- Generated video and realistic generated people stay off unless `budget.yaml` allows them. HyperFrames renders HTML you wrote, so it is not generated video. The built-in local voice is free. A premium voice, music library or realistic presenter needs a paid tool, which is `ACC-1`.
- Run `checks/copy_lint` on the scripts and `ads.json`. Its exit code is final.

## Outputs

In the idea's ads folder: `character.md`, `scripts.md`, `ads.json`, one folder per ad with `index.html`, `audio/`, `frames/` and `ad.mp4`, and one still.
