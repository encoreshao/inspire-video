<!--
Adapted from references/aesthetic-rules.md of video-shotcraft (https://github.com/Vincentwei1021/video-shotcraft),
Copyright Vincentwei1021, licensed under the Apache License 2.0 (see NOTICE at the repo root).
Changes: translated from Chinese and condensed to the rules that apply to a 9:16 bilingual showcase; thresholds
re-derived for this repo's layout; rule R4 and the Q and S sections that need shot cards or sound design were left out.
-->
# Aesthetic rules

Check the preview against every rule and write `ID ✓` or `ID ✗ (beat or time)`. Break a rule on purpose only when the video needs it, and then say which rule and why in your message to the user.

## Rhythm

- **R1. Let the key beat breathe.** The beat that carries the main message, and the last beat, must sit still long enough to read twice (at least 1 s after the text is fully in). Self-check: which beat do you want remembered, and does it hold?
- **R2. Slower is safer.** First drafts run fast. Without narration a beat lasts at least `max(4, 40 / beats)` s; give the zoom time to finish before the beat ends. Self-check: watch each beat as a stranger: what was not seen?
- **R3. One idea per beat.** One feature, one focus ring, one caption. Drop a repeated feature or call to action.

## Image and text

- **Q1. Real screenshots only.** Show the real product. Fake or redrawn interfaces are not allowed (`rights-and-safety.md`).
- **Q2. Text is either read or texture.** A caption must be readable on a phone: keep the caption sizes `fit()` chooses (English 26 to 32 px, Chinese 2 px more, on the 1080 px frame) and never shrink them to fit a longer sentence; shorten the sentence instead. Small text inside a screenshot is texture; if the beat needs it read, set `focus` on it so the zoom enlarges it. Self-check: scale a frame to 480 px wide; is every caption still readable?
- **Q3. Sharp sources.** Use screenshots at least as wide as the device frame; a zoom into a small image goes soft. Re-capture at 2x instead of enlarging.
- **Q4. Steady camera.** Only the planned slow zoom; no shake, no jumps, no overshoot.
- **Q5. Focus on content.** A ring sits on the element the caption names and stays out of the safe margins (`checks.py` tests the margins). A callout is short and never covers the thing it labels.
- **Q6. No decoration.** No glow, flash or sweep effects; one clean motion per beat.

## Copy

- **C1. Say a new thing each time.** Each caption adds information; none restates the headline.
- **C2. Concrete beats abstract.** Prefer what the product does for the user over adjectives, and only with facts from `brief.json`.
- **C3. The two languages carry the same meaning.** The Chinese is written for Chinese readers; it is not a word-for-word copy of the English.

## Process

- **P1. Deterministic render.** No `Date.now()`, `Math.random()` or `new Date()` in the video code; a render must be reproducible frame by frame (`tests/test_determinism.py` enforces it).
- **P2. Check before you tell.** Preview, self-check against these rules, run `final-review.md`, then render the final; never hand the first review to the user.
