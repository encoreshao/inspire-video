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
