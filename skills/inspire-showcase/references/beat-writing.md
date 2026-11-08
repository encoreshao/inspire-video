# Writing the beats

## Structure

- Write 10 to 40 beats, enough for 2 to 5 minutes at about 7 to 12 seconds a beat. About 16 is a good first video of 2 minutes or a little more; use more beats only when the brief has the facts for them.
- Build the video as a talk with a few topics, not as a list of features:
  1. **Hook** (1 beat): what the project is, in the viewer's terms.
  2. **Problem** (1 to 2 beats): who it is for and what is hard today.
  3. **Topics** (the bulk): one topic per page or section of the source (for a website, the pages in its header navigation, in the order the header lists them; for a repository, its main parts). Give each topic 2 to 4 beats: say what the topic is, then one or two concrete facts from the brief, then why it matters.
  4. **Proof** (1 to 2 beats): numbers, customers or examples that `brief.json` actually states.
  5. **Call to action** (1 beat).
- The scaffold names the beats `hook`, `problem`, `what`, `detail-01` and so on, `proof`, `cta`. Rename the ids to the topic they belong to (for example `services-1`, `services-2`, `work-1`); ids stay lowercase letters, digits, `-` and `_`.
- Write `en` as one sentence of at most 100 characters and `zh` as natural Chinese of at most 45 characters, not a literal translation. Short beats read better than dense ones.
- Choose an image per beat. A topic uses its own page's capture, and one image can serve several beats with different `focus` rectangles or targets. Do not put more than three beats in a row on the same image.

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

## Flow: make the topics follow into one another

A viewer should feel one person talking, not a list being read. The narration is where this is won or lost.

- **Bridge every topic change.** The first beat of a new topic picks up where the last one stopped: it names what is coming ("Next, how it ships.", "那么这些是怎么落地的？") or turns the last point toward it ("That reliability is also why teams rely on its delivery.", "正因为稳定，团队才敢把交付交给它。"). The last beat of a topic may end on the question or the consequence that the next topic answers.
- **Connect beats inside a topic** with the small words people use: "and", "so", "because", "that is why", "for example", "而且", "所以", "比如". Use a different connector each time; the same opener on three beats in a row sounds like a template.
- **Keep one thread.** Return to the hook's idea near the end ("That is the idea: ..."), so the call to action feels earned.
- **Vary the sentences.** Mix a short beat (5 to 8 words) among the longer ones; avoid several beats of the same length and shape in a row.
- **Every claim still comes from `brief.json`.** A bridge sentence carries no new fact; it only points to the next topic.
- Read the English column aloud once from top to bottom. Wherever you would say "okay, now", the text needs a bridge there.

Set the `topic` field on each beat to the topic's name (for example `Services`) so the video shows a small label when the topic changes and the transition between topics is longer and gentler than the one inside a topic. Beats of one topic share the same `topic` value.

## Narration and timing

- Set `"narration_lang": "zh"` in the manifest, or pass `--lang zh` to `narrate.py`, for Chinese narration. The default is English.
- Write what the voice should say, not what the page shows: spell out prices, currency symbols, units, dates and abbreviations in the narrated language ("zero yen", "fifty thousand yen a month", "ten to forty beats"), because the voice engines read "¥50,000" or "9:16" wrongly. Keep brand names as they are.
- After changing a beat's text, run `narrate.py` again: render refuses narration that is out of date, and refuses a manifest `voice` that differs from the voice used for the audio.
- Beat length follows the narration audio, but every beat is held for at least `120 / number of beats` seconds so the total reaches the 120 second minimum. Without narration each beat lasts `max(4, 120 / beats)` seconds. The total must be 120 to 300 seconds. A narrated script of about 16 beats usually lands near 2 minutes; add topics, not longer sentences, to go longer.
