# Keiretsu, the factory console

Two pages over the factories' own files. Nothing here runs a factory.

- **Board**: what needs you, spend, and one column per stage for each factory.
- **Live**: every factory around you on one screen. Click a factory to zoom into its line, a box to open an item.

```
python ui/serve.py --root <checkout of factory-state>
```

Then open http://127.0.0.1:8765. Without `--root` it reads this checkout. Run state is committed on the `factory-state` branch, so point `--root` at a checkout of that branch to see real runs. `--dump` prints the data and exits.

## What it reads

Only the files in [`factories/_shared/CONVENTIONS.md`](../factories/_shared/CONVENTIONS.md): `state/items/`, `escalations/open/`, `ledger/spend.jsonl`, `outbox/pending.jsonl`, `budget.yaml`, STOP files, and c-trading's `paper/`. Spend is counted per UTC month, as the run wrapper counts it. Budgets and caps are the ones in the `budget.yaml` of the checkout it reads, which on `factory-state` can lag `main`. [`data.py`](data.py) turns them into one dict and the pages draw it. A file that cannot be read is an error naming the file, not a gap in the picture.

[`factories.yaml`](factories.yaml) names each factory and orders its stage columns. A stage's `id` picks the machine the Live view draws for it, and `short` is its label in tight places. A new factory folder appears without an entry: its columns come from the stages its items have been through. A factory with no items and no runs shows as planned.

## The on/off switch

Off writes `factories/<name>/STOP`, the file every run checks before it starts. On asks first, then removes that file, but only if the UI wrote it. The run wrapper writes the same file after three failed runs in a row (or `<state-root>/STOP` when it is run with `--state-root`), and the UI will not remove that one: it shows what the file says, and you remove it by hand once you have read it. The root `STOP` is never touched. While any STOP file exists the factory stays off and the UI says which file holds it.

The switch changes the file in the checkout the server reads. A scheduled run in the cloud sees it once that checkout is committed and pushed.

The UI cannot approve anything. A decision is still made by moving its packet to `escalations/approved/` or `rejected/`.

## Safety

The server listens on 127.0.0.1 only and refuses requests that arrive under any other host name, so another site open in the browser cannot read the data or flip a switch.

The pages load fonts and three.js from a CDN. Offline, the Live view falls back to line drawings.

## The demo video

`demo/keiretsu.mp4` is a recording of the real console, following one idea through its morning. To remake it:

- Script the clicks with Playwright and record the page, with the voice's real line lengths setting how long each step lasts. Draw a visible cursor in the page, because recordings have none.
- Record larger than the frame so the camera has real pixels to move into: a 2400 by 1350 viewport with the page zoomed to 1.5 lays out like 1600 by 900. A canvas-drawn page will not take the zoom, so record it at its own size and move in less.
- Use real data, and check every number said or shown against the files it came from.
- In the composition each recording is a `<video>` clip with its own `id`, `data-start` and `data-duration`, inside an untimed wrapper. The camera is a wrapper around the recordings that GSAP scales and moves. Animate `opacity` on a child, never visibility on a clip itself.
