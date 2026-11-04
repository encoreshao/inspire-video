# Visual style specification

## Design intent

A calm, editorial bilingual quote video. The footage is the visual anchor; the caption area is attached directly beneath it so the two read as one panel. Reproduce the visual grammar, not any source app's UI.

## Canvas and themes

- 1080 x 1920 px, 9:16, 30 fps (the file is true 9:16, square pixels).
- **Safe area (mandatory):** WeChat Channels and Douyin scale the video to the screen height on tall phones (9:19.5 to 9:20) and center-crop the sides, losing about 97-108 px per side. Keep every element at least 120 px from the left and right edges (`SAFE_X`), at least 190 px from the top and 330 px from the bottom (platform buttons and captions). Content is vertically centered inside that zone.
- Themes are defined in `video/src/Video.tsx` (`themes`): `light` (soft off-white, default), `mist` (cool light gray-blue), `ivory` (warm parchment), `sage` (soft green) and dark `ink`.
- Select with the manifest `theme` field or `render.py --theme`. Avoid pure white pages, oversaturated colors and gradients.

## Composition (top to bottom)

1. **Title block**: small category label, Chinese headline (bold serif) and English subtitle. The headline and subtitle share one font size (42 px) so they read as a pair. The Chinese headline stays on one line when it fits.
2. **Joined panel**: the video window and the caption area form a single rounded panel (about 24 px radius, 3 px border) with a square seam and no gap between them.
   - Panel width 840 px. Default `contain` shows the whole 16:9 frame (about 470 px tall). `video.fit: "cover"` gives a taller window that crops about 20% of the width; `crop_x` / `crop_y` move the crop. Always inspect the crop; never cut off people.
3. **Caption area** directly under the video, auto-height to its text:
   - One sentence (or one clause of a long sentence) per cue, synced to speech, at most 100 English characters. English first, Chinese second, centered.
   - English up to 34 px semibold, Chinese +2 px regular; the size is reduced per cue so text never overflows. Padding about 12 px top and bottom.
   - The space for the tallest cue is reserved so nothing else moves between captions.
4. **Bottom block**: speaker name in English and Chinese (accent color), job title and company, talk title in italics, source / year / excerpt range under a hairline, and a thin progress bar. With several people, `copy.speakers` are listed side by side and the current speaker (cue `speaker` id) is highlighted.

## Typography

- Chinese: Noto Serif CJK SC / Source Han Serif SC / Songti SC. English: Arial (system).
- Fonts are system fonts, not bundled. On Linux install `fonts-noto-cjk` and check glyph coverage in a still.
- Keep side margins at least 120 px (see the safe area above); keep text at or above 19 px for secondary metadata.
- Never shrink text just to fit a very long cue: split the cue instead.

## What NOT to do

- No karaoke or word-by-word captions, and no large subtitles over the speaker's face.
- Never show two sentences in one cue.
- Do not reproduce app chrome (status bar, tabs, like/share icons, avatars, engagement counters).
- Do not generate text inside images; all text is native text layers.

## Motion

- The layout stays fixed while the video plays. Captions fade in over about 0.1 s; the whole composition fades in and out over about 0.2-0.3 s.
- No bouncing, glitch, particles or flashy transitions.
