# Writing the beats

## Structure

- Write 4 to 6 beats: hook, problem, what it does, key features, proof or example, call to action. The scaffold names them `hook`, `problem`, `what`, `features`, `proof`, `cta` (4 beats: `hook`, `problem`, `what`, `cta`; 5 beats add `features`).
- Write `en` as one sentence of at most 100 characters and `zh` as natural Chinese of at most 45 characters, not a literal translation. Short beats read better than dense ones.
- Choose an image per beat. One image can serve several beats with different `focus` rectangles.

## Fields

- `focus` is a normalised rectangle `{x, y, w, h}` on the beat's image (0 to 1). The camera zooms toward it and a ring marks it. Look at the image before choosing it. A whole-image focus `{0, 0, 1, 1}` means no zoom and no visible ring.
- `callout` is a short label on the ring: at most 22 width units, where a Chinese character counts as 2 (about 11 Chinese characters or 22 letters). Omit it when the ring speaks for itself.
- `project.name`, `project.name_zh`, `project.tagline` and `project.tagline_zh` fill the bilingual info card. Fill all four.
- `source.label` is shown on screen and in the browser bar. The scaffold sets it from the repo or host, or the folder name for a local repository. Check that it reads well.

## Limits that `manifest.py validate` enforces

The layout cannot wrap these lines, so validation refuses them before a render:

- `headline` fits one line: about 19 Chinese characters.
- `subtitle` fits two lines: about 70 characters.
- `project.name` plus `project.name_zh`, `project.tagline`, `project.tagline_zh` and `source.label` each stay on one line.
- Screenshots far from the device shape (a browser window about 16:10, a phone screen about 9:19) get a crop warning at render time: the image is cropped to fit, never stretched.

## Narration and timing

- Set `"narration_lang": "zh"` in the manifest, or pass `--lang zh` to `narrate.py`, for Chinese narration. The default is English.
- After changing a beat's text, run `narrate.py` again: render refuses narration that is out of date, and refuses a manifest `voice` that differs from the voice used for the audio.
- Beat length follows the narration audio, but every beat is held for at least `40 / number of beats` seconds so the total reaches the 40 second minimum. Without narration each beat lasts `max(4, 40 / beats)` seconds. The total must be 40 to 150 seconds.
