# Promo style

The `promo` style shows a product by moving a camera over real captures of its page. It sits beside the `device` style: they share the manifest, bilingual captions, narration, rights flow and output checks, but not the layout: the promo has its own frame and cover (see Look). The method (real captures, named shots, a storyboard before the manifest, a review before delivery) comes from [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) (Apache-2.0); see Credits for exactly what was and was not taken.

## Look

The promo style does not use the editorial layout of `inspire-video` and the device style. It has a frame of its own:

- no headline block, panel, caption card, info card or divider in the video body;
- a dark frame (the `ink` theme, the default for promo; `theme` can still be set) with a brand lockup at the top: the project name in both languages, the tagline and the address in a pill;
- a large rounded stage, 880 x 960 px, the full safe width, where the camera moves;
- the bilingual caption straight on the background, left-aligned, English above Chinese, with no card behind it;
- a row of pips at the bottom, one per beat, each filling as its beat plays, in place of one progress bar; with more than 12 beats the pips become one continuous bar with a small gap at every topic change;
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
| `pull-back-isolate` | Tight on the target, then a pull back while everything around it goes dark; ends still with the target alone | a closing move: "only this one matters" | once per video; at least 5 s |
| `crane-rise` | A close-up of the target, then one decelerating rise to the whole page while the dim around it lifts | going from the detail to the whole ("this is one part of all of it") | once per video; at least 5 s |
| `cursor-tour` | A cursor glides to the target on a light arc, clicks (a small press and a ring that fades), and the camera arrives behind it | feature tours, where the cursor is the viewer's attention | at most 3 per video; at least 5 s |
| `scroll-brake` | A fast travel down a tall page that brakes onto the target, a reticle locking on as it stops | landing on one block after a long page | a tall page (at least 1350 px); at most 2 per video; at least 5 s |
| `statement` | The beat's `statement` text large on the theme background, words arriving 4 frames apart | the hook and the call to action | at most 2 per video; no capture; at most 28 width units; Chinese or English |

Every shot needs at least 4 s (the five newer camera shots, `pan-reveal` among them, 5 s). Two beats in a row may not use the same shot ("back to back"): one idea per beat, so vary them.

## Storyboard

Write the storyboard in the reply before the manifest, and keep it to this shape:

| # | seconds | shot | target | caption |
|---|---|---|---|---|
| hook | 8 | `statement` | (text) | the first sentence |
| problem | 8 | `spotlight-focus` | `heading-3` | the second sentence |

Choose each target by what its caption talks about, so the camera lands on the thing the sentence names. Give the hook and the call to action a `statement` when the page has no element that carries them. Use `crash-zoom-punch` once, on the beat that matters most.

## Transitions and topic labels

The stage frame (card, border, shadow) never moves or fades; only the picture inside it changes. A topic change is when a beat's `topic` differs from the previous beat's, or, when neither beat has a `topic`, when its `asset` differs. A topic change dissolves over 18 frames (eased) while the incoming picture settles from a slight scale and rise and the outgoing one drifts the other way; a beat that stays on the same page dissolves over 8 frames with a much smaller drift. The caption is handled separately: the old text is gone by about half the dissolve and the new text fades in only when the beat's audio starts, so two captions never overlap.

A template can name how a topic change looks (its `transition`): `dissolve` (the default), `whip-pan` (the new picture slides in from the right, fast then settling, while the old one leaves to the left, both blurred while they move) or `flash-cut` (the picture swaps at the middle of a short white flash). A move between two beats of the same page always stays the short dissolve, so the sections of one page never whip or flash. One seam uses one transition; they are never stacked. They are pure functions in `video/src/showcase/transitions.mjs`, and `TRANSITIONS` there is the list `templates.py` accepts.

An optional beat field `topic` shows a small pill in the stage's top-left corner for about 1.5 s after a topic change (and on the first beat if it has one). Rules: one string, at most 28 width units (a Chinese character counts 2), letters, digits, CJK, spaces and `& / - . , '` and the middle dot, no leading or trailing space. A bilingual label is written `Our services · 服务`. A beat without `topic` has no label.

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
- The last 18 frames of a beat (8 within the same topic) dissolve into the next, so a still near the end of a beat is a blend. Judge a beat's own framing from 20 or more frames before its end.
- The cover shows the first beat's final framing (a statement-first project gets the finished statement). A `spotlight-focus` first beat gets a plain `hero-push` cover (no dimming).
- Text is sharp because the captures are 2x and the zoom is capped at the capture's resolution; do not capture at a smaller size to save space.
- The video is determinism-checked: no random or time-based motion in shots.
- A half-scale preview can pass the safe-area check where the full-size render fails (a glyph one pixel inside the margin averages away at half size). Run `checks.py --final` on the real render before delivering.

## Not included

- `tilt-glide`: the card behind it, `steep-tilt-glide`, defines the technique by a 60 degree angle with the camera fixed and the page sliding past it, and says that leaving 55 to 65 degrees means a different technique. A gentle 8 degree tilt would carry the name without the technique, and a 3D layer softens text. It is left out until it can be built faithfully and sharp.
- Sound design, beat sync and sound-effect sourcing, the JianYing export and the Motion Workbench from video-shotcraft.

## Templates

A template is a whole-video recipe: the look (theme), the shot palette with weights and limits, an opening and closing shot, a transition and pacing advice. Pick one per video; the manifest names it with `"template": "<id>"`.

- Recipes are `templates/<id>.yaml`; the shots they use are defined in `video/src/showcase/shots.json` (the one table read by both the renderer and the validator).
- Shipped: `cinematic` (default), `punchy`, `calm`, `minimal`, `tour`. List them with `python3 scripts/showcase/templates.py list [--json]`, inspect one with `show <id>`, and check all with `validate`.
- Add a recipe by adding a file: `id` equal to the file name, `style: promo`, at least three shots of which two are unlimited camera shots (`hero-push`, `spotlight-focus`), a `weight` of 1 or more for each, and optionally `max`, `theme`, `opening`, `closing`, `pacing.beat_seconds` and `transition`. Run `templates.py validate`.
- `python3 scripts/showcase/templates.py preview <id>` (or `--all`) renders a short sample clip of the recipe, with its own shots, theme and transition on a bundled sample page, into `templates/covers/<id>.mp4` and a cover frame `<id>.png`; `list --json` gives their paths so a picker can show them. The sample page is drawn by `templates/sample/make_sample.py`; a preview manifest has `"sample": true` and `sample_seconds`, which relax only the 10-beat and 2-minute rules.
- The recipe suggests, the beat decides: a beat may use a shot outside the palette (validate warns), but a template `max` is an error.

## Credits

Written from scratch after reading the named cards of video-shotcraft (Apache-2.0); no code, copy, UI or colours are reused, and each shot's source comment says what it borrowed.

- `hero-push` and `spotlight-focus`: `spotlight-hero-card`. Borrowed: a single hero target per beat, a card-shaped light hole instead of a circle, and a hold that is dead still (the card forbids tail drift). Not borrowed: its action arc (spotlight, rise, hover, reseat), dark theatre, light beam and outline light.
- `crash-zoom-punch`: `crash-zoom-punch`. Borrowed: the rebound variant, with its numbers (a push of about 6 frames, the target filling about 70% of the frame, a small rebound, a wide hold before and a long hold after). Not borrowed: the screen-shake variant, the motion blur, the pre-pull-back (the punch never moves backwards; only `pull-back-isolate` and `crane-rise` pull back, on purpose) and the allowance of a second punch per video (this tool allows one).
- `pull-back-isolate`: `tension-camera-moves`, move B. Borrowed: a pull back from a close-up while the surroundings go dark from the nearest outwards, ending still with one element alone. Not borrowed: the glow, the sibling-card grid, the blur and sinking of each card, the closing sentence in screen space, and move A (the frozen orbit, which needs a 3D scene).
- `crane-rise`: `crane-rise-reveal`. Borrowed: the opposite of a push, a close-up that holds a breath and then one decelerating rise to the whole, with the zoom and the centre on one progress, the rest of the page held down while close and lifting as it fills the frame. Not borrowed: the row-by-row light wash, the counting numbers and the status flip (they need a live interface).
- `cursor-tour`: `cursor-flyover`. Borrowed: the cursor is the hand and the camera the eye, so the cursor goes first on a light arc, aims, clicks (a press and a ring), and the camera arrives behind it. Not borrowed: the four-station tour, the interface that answers each click and the motion blur.
- `scroll-brake`: `scroll-brake-moves`. Borrowed: a travel that starts fast and brakes onto the target, with a reticle that locks on as it stops. Not borrowed: the changelog content, the reticle's scan and the screen shake.
- `whip-pan` and `flash-cut` (transitions): `shot-transitions`, moves A and B. Borrowed: the white flash covers a hard cut and is not used as decoration, and the whip-pan changes scene on blurred frames and arrives with a long settling tail; one seam, one style. Not borrowed: the continuous velocity curve (a decelerating ease and an accelerating ease stand in for it), the portal-wipe (move C), which needs a real detail page to open into.
- `pan-reveal` and `statement`: no card.
- Read and not shipped: `steep-tilt-glide` (see above).
