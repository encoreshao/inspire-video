# Promo style

The `promo` style shows a product by moving a camera over real captures of its page. It sits beside the `device` style: both use the same headline, bilingual caption card, narration, cover, rights flow and output checks. The method (real captures, named shots, a storyboard before the manifest, a review before delivery) comes from [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) (Apache-2.0); see Credits for exactly what was and was not taken.

## Look

The promo style does not use the editorial layout of `inspire-video` and the device style. It has a frame of its own:

- no headline block, panel, caption card, info card or divider in the video body;
- a dark frame (the `ink` theme, the default for promo; `theme` can still be set) with a brand lockup at the top: the project name in both languages, the tagline and the address in a pill;
- a large rounded stage, 880 x 960 px, the full safe width, where the camera moves;
- the bilingual caption straight on the background, left-aligned, English above Chinese, with no card behind it;
- a row of pips at the bottom, one per beat, each filling as its beat plays, in place of one progress bar;
- a cover of its own: the headline large, the hero framing in the same rounded stage, the brand and address below.

The `headline` and `subtitle` fields are used for the cover only; the video body shows the brand lockup instead.

## When to use it

- `device`: a phone or browser frame, a highlight ring and a callout. Works with any screenshot, including the user's own.
- `promo`: the camera flies over a full-page capture and lands on named elements. Use it for a site or product page with several distinct sections, when the user wants something more cinematic than a frame.

## Capture

Ingest the project first (the capture registers itself in `brief.json`), then capture one page per command:

```bash
python3 scripts/showcase/capture_page.py <url> --project output/projects/<slug> [--hide <css>]...
```

Look at the PNG it wrote. Hide a cookie banner or chat widget with `--hide ".banner"` and capture again. The captures are registered with unresolved rights, so the usual confirmation applies before a public render. List the elements the camera can target:

```bash
python3 - <<'EOF'
import json
d = json.load(open("output/projects/<slug>/assets/promo-1.layout.json"))
for e in d["elements"]:
    print(e["id"], e["role"], e["box"], repr(e["text"][:40]))
EOF
```

A user's own screenshot has no layout file; give the beat a `focus` rectangle instead of a `target`.

## Shots

| Shot | What it does | Use it for | Rules |
|---|---|---|---|
| `hero-push` | A slow push from the page-width framing onto the target, then dead still | the opening, the product itself, the proof | none; the default |
| `spotlight-focus` | A gentler push while everything outside the target dims to 55% | pointing at one block among many | none |
| `crash-zoom-punch` | A wide hold with a slow creep, a 6-frame punch with a 3% overshoot, then still | the one moment that must land ("this one") | once per video; the target must be small enough to punch in on (the validator rejects one that would not move) |
| `pan-reveal` | Travels down a tall page from its top to the target, then rests | showing how much page there is before landing | a tall page (at least 1350 px), at least 5 s |
| `statement` | The beat's `statement` text large on the theme background, words arriving 4 frames apart | the hook and the call to action | at most 2 per video; no capture; at most 28 width units; Chinese or English |

Every shot needs at least 4 s (`pan-reveal` 5 s). Two beats in a row may not use the same shot ("back to back"): one idea per beat, so vary them.

## Storyboard

Write the storyboard in the reply before the manifest, and keep it to this shape:

| # | seconds | shot | target | caption |
|---|---|---|---|---|
| hook | 8 | `statement` | (text) | the first sentence |
| problem | 8 | `spotlight-focus` | `heading-3` | the second sentence |

Choose each target by what its caption talks about, so the camera lands on the thing the sentence names. Give the hook and the call to action a `statement` when the page has no element that carries them. Use `crash-zoom-punch` once, on the beat that matters most.

## Manifest

Set `"style": "promo"`. A camera beat takes `shot` and exactly one of `target` (an element id from the layout) or `focus` (a rectangle). A statement beat takes `statement` and nothing else about a capture. `callout` is not used.

```json
{"style": "promo", "beats": [
  {"id": "hook", "en": "Handled while you do the real work.", "zh": "琐事交给 LoopX，你专注真正的工作",
   "shot": "statement", "statement": "琐事交给 LoopX"},
  {"id": "problem", "en": "Issues sit untouched, urgent mail gets buried.", "zh": "issue 没人管，紧急邮件被淹没",
   "asset": "assets/promo-1@2x.png", "shot": "spotlight-focus", "target": "heading-3"}
]}
```

Run `python3 scripts/showcase/manifest.py validate output/projects/<slug>`; every error names the beat.

## Pitfalls

- A very large target (a full-width dashboard image) hardly pushes, because it already fills the frame. Pick a smaller element inside it, or a different shot.
- The last 9 frames of a beat cross-fade into the next, so a still at the last frame of a beat is a blend. Judge a beat's own framing from 10 or more frames before its end.
- The cover shows the first beat's final framing (a statement-first project gets the finished statement). A `spotlight-focus` first beat gets a plain `hero-push` cover (no dimming).
- Text is sharp because the captures are 2x and the zoom is capped at the capture's resolution; do not capture at a smaller size to save space.
- The video is determinism-checked: no random or time-based motion in shots.
- A half-scale preview can pass the safe-area check where the full-size render fails (a glyph one pixel inside the margin averages away at half size). Run `checks.py --final` on the real render before delivering.

## Not included

- `tilt-glide`: the card behind it, `steep-tilt-glide`, defines the technique by a 60 degree angle with the camera fixed and the page sliding past it, and says that leaving 55 to 65 degrees means a different technique. A gentle 8 degree tilt would carry the name without the technique, and a 3D layer softens text. It is left out until it can be built faithfully and sharp.
- Sound design, beat sync and sound-effect sourcing, the JianYing export and the Motion Workbench from video-shotcraft.

## Credits

Written from scratch after reading the named cards of video-shotcraft (Apache-2.0); no code, copy, UI or colours are reused, and each shot's source comment says what it borrowed.

- `hero-push` and `spotlight-focus`: `spotlight-hero-card`. Borrowed: a single hero target per beat, a card-shaped light hole instead of a circle, and a hold that is dead still (the card forbids tail drift). Not borrowed: its action arc (spotlight, rise, hover, reseat), dark theatre, light beam and outline light.
- `crash-zoom-punch`: `crash-zoom-punch`. Borrowed: the rebound variant, with its numbers (a push of about 6 frames, the target filling about 70% of the frame, a small rebound, a wide hold before and a long hold after). Not borrowed: the screen-shake variant, the motion blur, the pre-pull-back (the camera never moves backwards, a tested rule) and the allowance of a second punch per video (this tool allows one).
- `pan-reveal` and `statement`: no card.
- Read and not shipped: `steep-tilt-glide` (see above).
