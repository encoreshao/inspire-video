---
name: inspire-video
description: Turn a Podcast, interview, speech, YouTube URL, or local video into a polished 9:16 bilingual Chinese-English inspirational short video. Use when asked to create, edit, batch-produce, or render this style of short video as an MP4.
---

# InspireVideo — Inspirational Short Video Generator

## Mission

Create a finished vertical MP4 inspired by the supplied visual references:
- background from a theme (`light` soft off-white default; `mist`, `ivory`, `sage` and dark `ink` also available via manifest `theme` or `--theme`);
- editorial Chinese headline with dark brown and terracotta-red emphasis;
- English subtitle beneath the headline;
- cinematic podcast/interview footage in a framed horizontal window;
- a large, highly readable caption card immediately BELOW the central video that shows one sentence at a time, synced to the speech: English original first, Chinese translation second (cues come from the manifest `subtitles`, timed from the transcript; ONE sentence (or one clause of a long sentence) per cue, kept short (<=100 English characters) so little text shows at once; never two sentences together; `render.py` rejects multi-sentence cues);
- no karaoke captions or large subtitles over the footage by default;
- when several people appear, list each person's name (and title/company) in the bottom block via `copy.speakers` and tag cues with `speaker` ids so the current speaker is highlighted; names must come from the source (description, on-screen captions, the user), never guessed from a voice or face, otherwise omit or mark unknown;
- a bottom block with the speaker's name in English and Chinese, job title and company (only if supported by the source), talk title, show/source, year, excerpt range and a progress bar;
- restrained transitions and subtle motion;
- no imitation of the source app's status bar, navigation, engagement icons, or account UI.

Default output: 1080×1920, 30 fps, H.264 MP4, 40 seconds to 2 min 30 s (40–150 s), bilingual Chinese/English.

## Operating principles

1. **Inspect before modifying.** Check the input file, duration, codecs, aspect ratio, audio streams, and available disk space.
2. **Rights and provenance.** Use only media the user owns, has permission to use, or is otherwise licensed for the requested use. A public URL is not proof of reuse rights. If rights are unclear, ask before downloading or rendering a public-facing derivative. Preserve source attribution.
3. **No fabricated quotes or credentials.** Quote wording, speaker identity, title, show, date and source must be supported by the supplied material or verified metadata. Mark uncertain fields as unknown; never invent.
4. **Faithful translation.** Preserve meaning and tone. Keep the English quote faithful to the transcript; make Chinese natural, not mechanically literal.
5. **Editorial integrity.** Do not stitch unrelated sentences into a misleading quote. Keep each selected clip contiguous unless the user explicitly requests a montage; disclose edits in project metadata.
6. **Human review for uncertainty.** If transcript confidence is low, speakers are unclear, attribution is uncertain, or a clip loses context, create a review report and ask for approval before final rendering.
7. **Deterministic rendering.** The model produces structured content data. Remotion renders typography and layout. Never ask an image model to draw Chinese/English text that must be accurate.
8. **Reproducibility.** Save source metadata, transcript, selected segments, translations, render settings and final output in a project folder.

## Inputs

Accept one of:
- local video: MP4, MOV, MKV, WebM;
- local audio: MP3, WAV, M4A, AAC;
- a user-provided YouTube or other video URL, subject to site terms, access restrictions and reuse rights.

Ask only for missing information that blocks the task. Defaults:
- language: English source, Simplified Chinese translation;
- aspect ratio: 9:16;
- duration: 40–150 seconds (choose the natural length of one complete thought);
- one best segment;
- output: one folder per project, `output/final/<project-slug>/`, holding `<project-slug>.mp4`, `cover.png` and the publishing copy;
- visual style: `references/visual-style.md`;
- no generated music unless explicitly requested.

## Workflow

### 1. Environment and input validation

- Read `README.md` and `config/default.yaml`.
- Run `python scripts/check_env.py`.
- Confirm Python, Node.js, npm, FFmpeg and ffprobe availability.
- In a sandboxed run (for example one started by the LoopX Creator page) `ffmpeg` and `ffprobe` cannot be started directly. Run them as `python scripts/media.py ffmpeg <args>` and `python scripts/media.py ffprobe <args>` instead: same arguments, but every file must be under `output/` (frames and temp files too, never `/tmp`), and it refuses network or pipe inputs, filters that read files, and code-file outputs. Outside a sandbox the plain commands work as well.
- Confirm the Remotion project dependencies are installed.
- For URLs, first ask the user to confirm they own the video or have permission to reuse it. Then run `python scripts/fetch.py <url> --yes-rights`. It caches each video under `output/cache/<extractor>-<id>/` and never downloads the same video twice; its last stdout line is the source path and `source_metadata.json` sits beside it (use it for attribution). Never pass `--yes-rights` without the user's confirmation. Do not bypass DRM, paywalls, login restrictions, geo-restrictions, or platform safeguards; if fetch fails (for example YouTube's "confirm you're not a bot" check), ask for a local file and import it with `python scripts/fetch.py --file <path> --yes-rights` (add `--source-url <url>` for attribution). The opt-in `--cookies-from-browser <browser>` flag uses the user's own signed-in browser session and may violate the platform's terms or flag their account: use it only when the user explicitly asks for it after being told this, never by default.
- Skill root is `~/.inspire-video`; run all `scripts/` commands from there.
- Create a unique project directory under `output/projects/<slug>/`.
- Copy or reference the source; do not overwrite it.

### 2. Probe and extract audio

Use `ffprobe` to record:
- duration, dimensions, frame rate, codecs, audio streams and rotation metadata.

Extract a high-quality mono audio track for transcription. Preserve the original video and audio for final editing. If the source is vertical or horizontal, plan a crop that keeps the active speaker visible; do not stretch footage.

### 3. Transcribe

Use `faster-whisper` or an equivalent configured speech-to-text engine.
- Generate word/segment timestamps where supported.
- Detect source language.
- Keep original-language transcript as canonical.
- Record confidence or quality indicators when available.
- If diarization is needed, use an optional diarization provider only when configured and authorized.
- Never infer speaker identity from voice alone.

Save:
- `transcript.json`
- `transcript.txt`
- `source_metadata.json`

### 4. Select the strongest segment

Score candidate contiguous segments using:
- standalone clarity and context;
- emotional or practical value;
- a memorable central idea;
- completeness of the thought;
- audio/video quality;
- suitability for a 40–150 second short;
- lack of misleading edits.

Prefer one coherent passage. Avoid clips that start mid-sentence, end before the thought resolves, rely on unexplained pronouns, or make a factual claim without context.

Return 1–3 candidates with:
- exact start/end timestamps;
- verbatim transcript;
- concise reason for selection;
- any context caveat;
- estimated duration.

If no candidate is sufficiently clear, ask the user to choose or provide more source material.

### 5. Generate editorial copy and bilingual text

Produce:
- Chinese main headline (ideally 8–18 Chinese characters, one or two lines);
- English subtitle (short, natural, title case or sentence case);
- verbatim English quote from the selected passage;
- Simplified Chinese translation;
- speaker name in English and Simplified Chinese (mark the Chinese name as a transliteration to verify), job title and company/organization (`speaker_title`, `speaker_title_zh`, `speaker_org`), only if verified from the source or the speaker's own words;
- show / channel / event name and year, if available;
- concise category label;
- optional closing takeaway (clearly identified as editorial copy, not a direct quote).

Headline should express the clip's idea, not exaggerate it. Do not attribute the headline to the speaker as a direct quote unless it is verbatim.

### 6. Prepare video segment

- Trim the source to selected timestamps with a small configurable lead-in/tail-out when useful.
- Keep original speaker audio synchronized.
- Crop to 9:16 using face/speaker-aware framing when available; otherwise use a safe center crop and inspect it.
- Do not synthesize lip movement or alter the speaker's appearance.
- Pick `assets/poster.jpg` (the cover image) deliberately: view 6-8 candidate frames across the clip and choose one with the speaker alone, face clear, eyes open, centered, and NO montage/split screen, lower-third, date or location text, or other people. Never take a fixed timestamp blindly. Then check the rendered `cover.png`: every text line (headline, subtitle, speaker, title, talk, source) must be fully visible, match `video_manifest.json`, and stay inside the safe margins.
- Use subtle cuts/fades only. Avoid flashy transitions, emoji overlays and excessive zoom.
- If the source is 16:9, place it in a framed landscape window within the vertical editorial layout rather than cropping away important people by default.

### 7. Build the render manifest

Write `video_manifest.json` matching `references/manifest-schema.json`.
It must include:
- project id and output settings;
- source file and source time range;
- headline and English subtitle;
- quote in both languages;
- speaker/source attribution;
- video segment path;
- subtitle cues with start/end times;
- theme and layout options;
- rights/provenance note and review status.

Validate JSON before rendering. Reject missing required fields, negative timestamps, end times before start times, and cues outside the selected clip duration.

### 8. Render

Use the Remotion composition `InspireShort`.
- Render at 1080×1920, 30 fps, H.264.
- Use bundled/local fonts; never depend on a remote font at render time.
- Ensure Chinese glyph coverage. Preferred fallback chain: Noto Serif CJK SC / Source Han Serif SC / Songti SC; English: Inter / Arial.
- Use FFmpeg for final audio normalization and muxing only when required.
- Keep source audio intelligible; background music is off by default.
- Render a low-resolution preview first when the project is new or layout changed.
- Render final MP4 only after checks pass.

### 9. Quality assurance

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

### 10. Publishing copy (title, description, tags)

After the video passes QA, write `publish.json` in the project folder for WeChat Channels (视频号) and Douyin (抖音), then run `python scripts/publish_meta.py output/projects/<slug>`. It validates the lengths against `config/publish.yaml` and writes `publish.md`, `publish_wechat.txt` and `publish_douyin.txt` into `output/final/<slug>/`, ready to paste, plus `project.json` (schema in `references/publishing.md`, read by the LoopX Creator page; re-run after the cover exists so it lists `cover.png`). `--init` scaffolds a draft from `copy.json`. Follow `references/publishing.md`:
- Simplified Chinese; truthful to the clip; no clickbait, invented statistics or claims the speaker did not make.
- WeChat: a short title plus a description; Douyin: a title plus a description; 3-5 relevant hashtags each, written without `#`.
- Always include a credit line (source, speaker, year, and that the subtitles are your own translation); it is appended to every description.
- If the rights are not cleared, say so in `notes`; `publish.md` then shows a "NOT CLEARED FOR PUBLICATION" banner. Never claim the content is original.
- Platform limits are unverified defaults: tell the user to check them in each publish page.

## Output contract

For each project, produce:

```text
output/projects/<slug>/
├── source_metadata.json
├── transcript.json
├── transcript.txt
├── selected_segments.json
├── copy.json
├── video_manifest.json
├── review.md
├── publish.json
├── render.log
└── assets/
    ├── source.mp4
    ├── clip.mp4
    └── poster.jpg

output/final/<slug>/
├── <slug>.mp4
├── cover.png          # rendered automatically with the video
├── publish.md
├── publish_wechat.txt
└── publish_douyin.txt
```

Also provide a concise completion report:
- output file path;
- duration and resolution;
- selected source time range;
- headline;
- quote and translation;
- attribution;
- QA result;
- any caveats or manual review items.

## Setup

When the user asks to install, set up or fix InspireVideo (or runs `setup`):
- If the skill is not installed, run `curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash -s -- claude` (use `codex` for Codex).
- Run `python3 ~/.inspire-video/scripts/check_env.py` and report each missing item. Python packages and `npm install` can be fixed with `bash ~/.inspire-video/scripts/install.sh <claude|codex>`.
- Ask before installing system packages (Python 3.11+, Node.js 20+, ffmpeg) with brew or apt, and never use sudo without the user's approval.
- Tell the user to start a new session so the skill loads. Do not process any video during setup.

## Error handling

- Missing dependencies: explain exactly what is missing and provide the install command for the user's OS.
- Missing API key: do not print secrets; explain which environment variable is needed.
- Unsupported URL or blocked source: ask for a local upload or an authorized downloadable file.
- Low-confidence transcription: do not silently guess; request review.
- Unverified attribution: omit it or mark it unknown.
- Render failure: preserve intermediate assets and logs; report the failing command and likely cause.
- Insufficient disk space: stop before copying large files and explain the required space.

## Commands

Support natural-language requests and these suggested commands:
- `setup` — install and verify the environment (see Setup below);
- `publish <project-dir>` — write title, description and hashtags for WeChat Channels and Douyin;
- `create from <path-or-url>` — full pipeline;
- `analyze <path-or-url>` — transcribe and propose segments without rendering;
- `render <project-dir>` — render an existing validated manifest;
- `revise <project-dir>` — revise copy/layout and re-render;
- `batch <directory>` — process multiple authorized source files, one project per source.

For batch mode, process sequentially by default to control memory and CPU. Never overwrite an existing final file without explicit approval.
