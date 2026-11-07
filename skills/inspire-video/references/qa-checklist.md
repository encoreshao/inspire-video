# Quality assurance checklist

Inspect the rendered video, not just the source composition.
Check:
- exact output dimensions, duration, frame rate and codecs;
- no black frames, missing media, frozen frame, or audio drift;
- no clipped or overlapping text;
- correct Chinese glyphs and punctuation;
- English quote matches transcript;
- Chinese translation matches the English meaning;
- speaker and source attribution are accurate;
- video crop keeps the speaker visible;
- safe margins are respected: all content at least 120 px from the left and right edges (WeChat/Douyin crop the sides on tall phones), at least 190 px from the top and 330 px from the bottom; verify with a simulated 864 px center crop;
- audio is clear and not clipped;
- final MP4 plays from beginning to end.

Use `ffprobe` and, where possible, extract representative frames for visual inspection. If any critical check fails, fix and re-render. Do not report success until the output file exists and validation passes.

## Other platform formats

When a 4:5 render exists (`<slug>-portrait-4x5.mp4`):
- the file is 1080 x 1350 (check with `ffprobe`);
- all content is at least 60 px from the left and right edges, at least 90 px from the top, and ends above y = 1200;
- the video panel is clearly visible and the longest caption is not clipped;
- the speaker block, talk title, source line and progress bar are all complete;
- `cover-portrait-4x5.png` is 1080 x 1350 with the poster visible.
