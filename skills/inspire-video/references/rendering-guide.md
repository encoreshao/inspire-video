# Rendering guide

## Renderer

Remotion renders the layout deterministically (`video/`, compositions `InspireShort` and `InspireCover`). FFmpeg handles probing, audio extraction, cutting and validation. Run everything through `scripts/render.py`.

## Composition order

Top to bottom: title block, joined panel (video + auto-height caption area), bottom speaker/source block with progress bar. See `visual-style.md`.

## Render contract

Input: a project folder with a validated `video_manifest.json` and `assets/clip.mp4` (H.264/AAC; AV1 or Opus sources must be re-encoded when cutting).

Commands (from the skill root):

```bash
python3 scripts/render.py output/projects/<slug> --preview    # half-scale draft -> <project>/preview.mp4
python3 scripts/render.py output/projects/<slug> --force      # final -> output/final/<slug>/<slug>.mp4 + cover.png
python3 scripts/render.py output/projects/<slug> --cover --force   # cover only -> output/final/<slug>/cover.png
```
If the designed cover fails to render, `render.py` writes a frame grab (from the finished video, else the clip) as the cover and prints a WARNING, so delivery is never blocked. Tell the user the cover is a frame grab and re-run with `--cover --force` once the cause is fixed.


Add `--theme light|mist|ivory|sage|ink` to override the manifest theme.

Defaults: 1080 x 1920, 30 fps, h264, aac, yuv420p, CRF 18.

## Platform formats

`config/platforms.yaml` maps each platform to a video profile. Render for the platforms the user publishes to; profiles shared by several platforms render once:

```bash
python3 scripts/render.py output/projects/<slug> --platform wechat_channels,douyin,linkedin
python3 scripts/render.py output/projects/<slug> --profile portrait-4x5      # one profile only
python3 scripts/render.py output/projects/<slug> --platform linkedin --preview
```

| Profile | Size | Used by | Files |
|---|---|---|---|
| `vertical-9x16` | 1080 x 1920 | `wechat_channels`, `douyin`, `rednote`, `bilibili` | `<slug>.mp4`, `cover.png` |
| `portrait-4x5` | 1080 x 1350 | `linkedin`, `facebook` | `<slug>-portrait-4x5.mp4`, `cover-portrait-4x5.png` |
| `square-1x1` | 1080 x 1080 | none yet (not supported: falls back to `portrait-4x5` with a warning) | |
| `landscape-16x9` | 1920 x 1080 | none yet (not supported: falls back to `vertical-9x16` with a warning) | |

Without `--platform` or `--profile` the render is the default 9:16, exactly as before. The clip length is also checked against each listed platform's range. Showcase projects are 9:16 only and reject these flags.

`render.py` rejects: schema violations, `rights_confirmed: false`, `review_status: rejected`, clips outside 40-150 s, cues that overlap, run out of order, hold more than one sentence, exceed 100 English characters, reference an unknown speaker, start within 0.1 s of the clip start, or end within 0.2 s of the clip end.

## Cutting the clip

In a sandboxed run, prefix every `ffmpeg` / `ffprobe` command below with `python scripts/media.py` (`python scripts/media.py ffmpeg -ss ...`); it checks that every file is under `output/`.

```bash
ffmpeg -ss <start> -to <end> -i source.mp4 -vf "scale=1280:720,fps=30" \
  -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k assets/clip.mp4
ffmpeg -ss 46 -i assets/clip.mp4 -frames:v 1 -q:v 2 assets/poster.jpg   # cover photo
```

Choose `start` a little before the first spoken word and `end` a little after the last, so no speech is cut off.

## Validation

```bash
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of json output/final/<slug>/<slug>.mp4
ffmpeg -i output/final/<slug>/<slug>.mp4 -af volumedetect -vn -f null -
ffmpeg -i output/final/<slug>/<slug>.mp4 -vf blackdetect=d=0.5 -an -f null -
```

Extract frames at the start of each caption and inspect them at phone size: no clipped text, correct glyphs, speaker in frame.

Simulate a platform's side crop on a frame (9:20 screen, keeps the center 864 px of 1080):

```bash
ffmpeg -ss 12 -i output/final/<slug>/<slug>.mp4 -frames:v 1 -vf "crop=864:1920" output/projects/<slug>/crop920.png
```

Nothing (text, panel edge, progress bar) may touch or pass the crop edges.

## Preview of a layout change without a full render

```bash
cd video && npx remotion still src/index.ts InspireShort output/projects/<slug>/still.png --props=<project>/props.json --frame=750 --scale=0.5
```
