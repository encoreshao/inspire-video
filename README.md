# InspireVideo

A Claude Code / Codex skill that turns authorized podcast or interview footage (a local file or a video URL) into a 9:16 bilingual Chinese-English short video with synced captions, plus a cover image.

The agent follows `SKILL.md` to transcribe, pick a segment, write the copy and translation, and cut the clip. Layout and typography are then rendered deterministically with [Remotion](https://www.remotion.dev/), so on-screen text is always exact.

> **Status:** tested end to end on macOS with one real video. `fetch.py`, `transcribe.py`, `render.py` and the Remotion renderer are implemented. The modules in `src/inspire_video/` are placeholders: probing, segment selection, translation and clip cutting are done by the agent, guided by `SKILL.md`. Linux and Windows have not been tested.

## Features

- **Output:** 1080×1920 MP4 (H.264 + AAC, 30 fps), 40 seconds to 2 min 30 s, plus a 1080×1920 cover PNG.
- **Synced bilingual captions:** one short sentence (or one clause of a long sentence) at a time, English first and Chinese second, appearing as it is spoken. Each cue is at most 100 English characters, and two sentences never share a cue.
- **Platform-safe layout:** WeChat Channels and Douyin crop the sides of 9:16 video on tall phones (about 100 px per side). All content stays 120 px inside the left and right edges, and clear of the top (190 px) and bottom (330 px) button zones.
- **Joined panel:** the video and its caption area form one rounded panel with no gap. The caption area is only as tall as its text.
- **Title block:** category label, Chinese headline and English subtitle at the same size.
- **Bottom block:** speaker name in English and Chinese, job title, company, talk title, source, year, excerpt range and a progress bar.
- **Several people on screen:** list them in `copy.speakers` and tag cues with a `speaker` id. All names show at the bottom and the current speaker is highlighted.
- **Themes:** `light` (default), `mist`, `ivory`, `sage` and a dark `ink`.
- **URL input:** download with `yt-dlp` after a rights confirmation, cached by video id so the same video is never downloaded twice.
- **Publishing copy:** a WeChat Channels short title and description, a Douyin title and description, and hashtags, validated against editable length limits and written to ready-to-paste files, with a source credit and a "not cleared" banner when the rights are unresolved.
- **Safety checks:** `render.py` validates the manifest and refuses to render when rights are not confirmed, captions are malformed, or speech could be cut off.

## Requirements

- macOS (tested) or Linux
- Python 3.11+
- Node.js 20+ (20.19+ recommended; npm prints an engine warning on 20.15 but it works)
- FFmpeg and ffprobe (`brew install ffmpeg` or `apt install ffmpeg`)
- Linux only: a CJK font such as `fonts-noto-cjk` (macOS ships Songti SC). Fonts are system fonts and are not bundled.
- About 4 GB of free disk for the Whisper model, Chrome and the project files

## Install

### Option 1: one command (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash
```

This clones the repo into `~/.inspire-video`, links the skill into Claude Code and Codex, installs the Python and npm dependencies, and runs the environment check. Pick one tool, or skip dependency installation:

```bash
curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash -s -- claude
curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash -s -- codex --no-deps
```

Prefer to read it first? Open [`install.sh`](install.sh), or download it and run `bash install.sh`. Set `INSPIRE_VIDEO_HOME` to install somewhere other than `~/.inspire-video` (`SKILL.md` refers to `~/.inspire-video`, so the default is simplest).

**Update:** run the same command again; it pulls the latest version and re-links.
**Uninstall:** `bash ~/.inspire-video/scripts/uninstall.sh` removes the links (your outputs stay; delete the folder yourself to remove everything).

### Option 2: let Claude Code or Codex install it

Open Claude Code or Codex and paste one of these prompts.

**Claude Code**

```text
Install the InspireVideo skill from https://github.com/encoreshao/inspire-video for Claude Code.
1. Run: curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash -s -- claude
2. Run python3 ~/.inspire-video/scripts/check_env.py and fix anything missing (Python 3.11+, Node.js 20+, ffmpeg). Ask me before installing any system package with brew or apt.
3. Tell me to start a new session, then summarize how to use /inspire-video. Do not process any video yet.
```

**Codex**

```text
Install the InspireVideo skill from https://github.com/encoreshao/inspire-video for Codex.
1. Run: curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash -s -- codex
2. Run python3 ~/.inspire-video/scripts/check_env.py and fix anything missing (Python 3.11+, Node.js 20+, ffmpeg). Ask me before installing any system package with brew or apt.
3. Tell me to start a new session, then summarize how to use the inspire-video skill. Do not process any video yet.
```

**Update or uninstall** (either tool)

```text
Update the InspireVideo skill by re-running its install command from https://github.com/encoreshao/inspire-video, then run its environment check and report the result.
```

```text
Uninstall the InspireVideo skill with bash ~/.inspire-video/scripts/uninstall.sh and confirm the links are gone. Do not delete my outputs.
```

Once installed, `/inspire-video setup` (or "set up InspireVideo") makes the agent re-run the environment check and fix what is missing.

### Option 3: manual

```bash
git clone https://github.com/encoreshao/inspire-video.git ~/.inspire-video
bash ~/.inspire-video/scripts/install.sh claude    # or: codex | both   (add --no-deps to skip dependencies)
```

### What the installer does

1. symlinks the skill into `~/.claude/skills` and/or `~/.agents/skills`;
2. installs the Python dependencies (`faster-whisper`, `yt-dlp`, `pydantic`, `jsonschema`, `PyYAML`) with `pip install -e`;
3. runs `npm install` for the Remotion project;
4. runs the environment check.

Downloads that happen later, on first use: headless Chrome (about 100 MB, on the first render) and the Whisper model (about 250 MB for `small.en`, about 3 GB for `large-v3`).

Check your setup any time: `python3 ~/.inspire-video/scripts/check_env.py`

Optional: copy `.env.example` to `.env` only if you use a hosted LLM provider. Never commit `.env`. Windows is not supported; use WSL.

## Quick start

In Claude Code (start a new session after installing):

```text
/inspire-video create from ./podcast.mp4
/inspire-video create from https://www.youtube.com/watch?v=VIDEO_ID
```

For a URL, add a rights statement so the agent can download it, for example: "I own this video / have permission to reuse it." The agent then:

1. checks your environment and, for a URL, downloads the video once into the cache;
2. extracts audio and transcribes it;
3. proposes 1–3 candidate segments and asks you to choose;
4. writes the headline, subtitle, captions, translation and speaker details;
5. cuts the clip, writes `video_manifest.json`, and renders a preview, then the final MP4 and cover after you approve;
6. writes the publishing copy (title, description, hashtags) for WeChat Channels and Douyin.

Other commands:

```text
/inspire-video analyze <file-or-url>        # transcribe and propose segments only
/inspire-video render output/projects/<slug>
/inspire-video revise output/projects/<slug>
/inspire-video batch <directory>
```

Everything is written under `~/.inspire-video/output/`:

| Path | Contents |
| --- | --- |
| `projects/<slug>/` | transcript, selected segments, copy, `video_manifest.json`, `review.md`, `assets/` (clip, poster) |
| `projects/<slug>/publish.md` | title, description and hashtags for WeChat Channels and Douyin (plus `publish_wechat.txt`, `publish_douyin.txt`) |
| `final/<slug>.mp4` | the finished video |
| `final/<slug>-cover.png` | the cover image |
| `cache/` | downloaded URL sources |

## Manual workflow (without the agent)

Run from the skill root (`cd ~/.inspire-video`). Replace `<slug>` with a folder name.

```bash
# 1. (URL only) download once; asks for rights confirmation
python3 scripts/fetch.py "https://www.youtube.com/watch?v=VIDEO_ID"

# 2. extract 16 kHz mono audio and transcribe
mkdir -p output/projects/<slug>/assets
ffmpeg -i source.mp4 -vn -ac 1 -ar 16000 output/projects/<slug>/assets/audio.wav
python3 scripts/transcribe.py output/projects/<slug>/assets/audio.wav output/projects/<slug> small.en

# 3. cut the clip (start/end in seconds, a little outside the speech) and grab a cover photo
ffmpeg -ss 699.6 -to 756.4 -i source.mp4 -vf "scale=1280:720,fps=30" \
  -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k output/projects/<slug>/assets/clip.mp4
ffmpeg -ss 46 -i output/projects/<slug>/assets/clip.mp4 -frames:v 1 -q:v 2 output/projects/<slug>/assets/poster.jpg

# 4. write output/projects/<slug>/video_manifest.json (see below), then render
python3 scripts/render.py output/projects/<slug> --preview        # half-scale draft
python3 scripts/render.py output/projects/<slug>                  # final MP4
python3 scripts/render.py output/projects/<slug> --cover          # cover PNG
```

### Publishing copy

```bash
python3 scripts/publish_meta.py output/projects/<slug> --init   # draft publish.json from copy.json
# edit publish.json (or ask the agent: "/inspire-video publish output/projects/<slug>")
python3 scripts/publish_meta.py output/projects/<slug>          # validate, then write publish.md + .txt files
```

`publish.json` holds `wechat_channels` (`short_title`, `description`, `hashtags`), `douyin` (`title`, `description`, `hashtags`), a required `credit` line and optional `notes`; see `references/publishing.md`. Hashtags are written without `#`. The credit is appended to every description. If the project's `review_status` is not `approved`, `publish.md` carries a "NOT CLEARED FOR PUBLICATION" banner. Length limits live in `config/publish.yaml` and are unverified defaults (WeChat short title 6–16, Douyin title ≤ 30, descriptions ≤ 1000, hashtags ≤ 5): check each platform's publish page and edit the file.

Add `--force` to overwrite an existing final file, and `--theme light|mist|ivory|sage|ink` to override the theme. `fetch.py --yes-rights` skips the interactive rights prompt; only use it when you have confirmed the rights.

### The manifest

`video_manifest.json` follows `references/manifest-schema.json`. A minimal example:

```json
{
  "project_id": "my-clip",
  "theme": "light",
  "settings": {"width": 1080, "height": 1920, "fps": 30},
  "source": {"path": "assets/source.mp4", "start_seconds": 699.6, "end_seconds": 756.4},
  "copy": {
    "headline_zh": "长期拖延，让你成了人生的旁观者",
    "subtitle_en": "Long-term procrastination can make you a spectator in your own life",
    "quote_en": "…", "quote_zh": "…",
    "speaker_name": "Tim Urban", "speaker_name_zh": "蒂姆·厄班",
    "speaker_title": "Writer & Blogger", "speaker_title_zh": "作家、博主", "speaker_org": "Wait But Why",
    "talk_title": "Inside the Mind of a Master Procrastinator",
    "source_name": "TED", "year": 2016, "excerpt_label": "Excerpt 11:40–12:36",
    "category": "PROCRASTINATION / 拖延"
  },
  "video": {"clip_path": "assets/clip.mp4", "fit": "cover", "crop_x": 0.5, "crop_y": 0.5},
  "subtitles": [
    {"start": 0.15, "end": 4.9, "en": "Now, if the procrastinator's only mechanism of doing these hard things", "zh": "如果拖延者做这些难事的唯一机制"}
  ],
  "provenance": {"rights_confirmed": true, "source_reference": "https://…", "review_status": "pending", "edit_notes": "…"}
}
```

Notes:

- Caption `start` and `end` are seconds **relative to the clip**, not the source. Build them at sentence or clause boundaries from the transcript timestamps.
- Keep the clip starting at least 0.1 s before the first cue and ending at least 0.2 s after the last, so no speech is cut off.
- `video.fit` is `contain` (default, whole 16:9 frame) or `cover` (taller window, crops some width). `crop_x` / `crop_y` (0–1) move the crop.
- Several people: add `copy.speakers` as `[{"id": "a", "name": "…", "name_zh": "…", "title": "…", "title_zh": "…", "org": "…"}]` and set `"speaker": "a"` on each cue. Names must come from the source (description, on-screen captions, you), never from guessing a voice or face.
- Only include a title or company that the source or the speaker's own words support.

### What `render.py` checks

It refuses to render when: the manifest breaks the schema; `rights_confirmed` is false; `review_status` is `rejected`; the clip is outside 40–150 s; cues overlap, are out of order, hold more than one sentence, exceed 100 English characters or name an unknown speaker; or the first/last cue is too close to the clip's start/end. It stages the clip and poster into `video/public/` (git-ignored) and runs Remotion with `--crf=18`.

## Customizing

- **Theme:** the `theme` manifest field or `--theme`. Colors are defined in `video/src/Video.tsx` (`themes`).
- **Sizes and layout:** constants at the top of `video/src/Video.tsx` (`HEAD`, `MAX_EN`, panel and spacing values) and `video/src/Cover.tsx`.
- **Preview a layout change quickly:** `cd video && npx remotion still src/index.ts InspireShort out.png --props=../output/projects/<slug>/props.json --frame=750 --scale=0.5`. `npm run preview` opens Remotion Studio.
- `config/default.yaml` documents the defaults but is not read by the code. `config/publish.yaml` is read by `publish_meta.py`.
- `references/visual-style.md` and `references/rendering-guide.md` describe the design rules the agent follows.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| First render seems stuck | Remotion is downloading headless Chrome; wait a few minutes on slow connections |
| `Could not find a tsconfig.json` | Run commands inside `video/` or via `render.py`; `video/tsconfig.json` ships with the repo |
| `open() got an unexpected keyword argument 'metadata_errors'` | `transcribe.py` reads 16 kHz mono WAV directly to avoid this; extract audio with the ffmpeg command above instead of passing an MP4 |
| Chinese text shows as boxes (Linux) | Install `fonts-noto-cjk` |
| Video is black or missing in the render | Re-encode the clip to H.264 + AAC; AV1 or Opus sources may not decode in Chrome |
| `render.py` says a cue is too long or has two sentences | Split the cue at a clause boundary and give each part its own timing |
| `fetch.py` fails | The video may be private, live, age-restricted or blocked; download an authorized copy yourself and use the local file |
| Output file exists | Pass `--force` to overwrite |
| Sides are cut off on WeChat / Douyin | They crop 9:16 video on tall screens. Re-render with the current version (120 px side margins); if a platform still crops, raise `SAFE_X` in `video/src/Video.tsx` |

## Known limits

- Caption timing comes from the transcript and is accurate to a fraction of a second. Watch the output once before publishing.
- Chinese translations and Chinese name transliterations are written by the agent; have a fluent reader review them.
- The video window shows the whole 16:9 frame (`contain`) so nothing is cropped. Set `video.fit` to `cover` for a taller window that crops about 20% of the width; `crop_x` / `crop_y` move the crop.
- Content sits inside the platform safe area, so the video window is about 840 px wide and there is empty space above and below. Adjust `SAFE_X`, `SAFE_TOP` and `SAFE_BOTTOM` in `video/src/Video.tsx` if a platform behaves differently.
- No speaker-aware cropping or automatic speaker identification yet.
- Fonts are system fonts, not bundled.
- Tested on macOS only.

## Rights

A URL does not grant reuse rights. Only use media you own or are licensed to use, never bypass DRM or access controls, and verify every quote and attribution before publishing. Some sources, such as TED talks (CC BY-NC-ND), forbid derivative works, so a re-edited clip must not be published without permission. You are responsible for complying with the terms of the sites you download from.

## Repository layout

```text
SKILL.md              agent workflow and quality rules
README.md             this file
LICENSE               MIT
config/default.yaml   documented defaults (reference only)
config/publish.yaml   platform length limits used by publish_meta.py
references/           visual style, rendering guide, content extraction policy, manifest schema
install.sh            online installer (clone + link + dependencies)
scripts/              install.sh, uninstall.sh, check_env.py, fetch.py, transcribe.py, render.py, publish_meta.py
video/                Remotion project (InspireShort video, InspireCover cover)
src/inspire_video/    placeholder Python modules
output/               projects, final files, download cache (git-ignored)
```

## License

MIT, see `LICENSE`.
