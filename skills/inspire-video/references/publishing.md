# Publishing copy guide (per platform)

`publish.json` (source of truth) lives in the project folder. The generated `publish.md` (all copy, ready to paste) and one `publish_<platform>.txt` per platform (`publish_wechat.txt` for WeChat Channels, `publish_douyin.txt`, `publish_linkedin.txt`, ...) are written to `output/final/<slug>/`, next to the video and `cover.png`.

Platform ids and their limits live in `config/platforms.yaml`: `wechat_channels`, `douyin`, `rednote`, `bilibili`, `linkedin`, `facebook`. Adding a platform means adding a block there.

## publish.json

```json
{
  "platforms": {
    "wechat_channels": {"title": "6-16 chars", "description": "...", "hashtags": ["拖延症", "TED演讲"]},
    "douyin": {"title": "<= 30 chars", "description": "...", "hashtags": ["拖延症", "TED演讲"]},
    "linkedin": {"title": "English title", "description": "English post text", "hashtags": ["Growth"]}
  },
  "credit": "内容来源：TED 演讲《…》，演讲者 …，2016。中英字幕为自制翻译，版权归原作者所有。",
  "credit_en": "Source: TED talk “…”, speaker …, 2016. Chinese and English subtitles are my own translation; all rights belong to the original author.",
  "notes": ["reminders for the publisher"]
}
```

List only the platforms the user wants. Hashtags are written without `#`; the script adds it. `credit` is appended to Chinese platforms (`lang: zh`), `credit_en` to English platforms (`lang: en`, currently `linkedin` and `facebook`); `credit_en` is required when an English platform is listed. The credit line is followed by the hashtags. The old shape (top-level `wechat_channels` with `short_title`, and `douyin`) still loads.

## project.json (written automatically)

`publish_meta.py` also writes `output/final/<slug>/project.json`, the machine-readable manifest the LoopX Creator page reads. It is regenerated on every run (`created_at` is kept from the first run); do not hand-edit it. It stays `schema: 1`; new keys are additive.

```json
{
  "schema": 1,
  "slug": "<slug>",
  "title": "headline_zh from the video manifest, else the slug",
  "source_url": "provenance.source_reference or null",
  "created_at": "2026-11-04T10:00:00Z",
  "video": "<slug>.mp4",
  "cover": "cover.png",
  "publish": {
    "wechat": {"title": "short title", "caption": "description + credit", "hashtags": ["no #"]},
    "douyin": {"title": "title", "caption": "description + credit", "hashtags": ["no #"]},
    "linkedin": {"title": "title", "caption": "description + credit_en", "hashtags": ["no #"]}
  },
  "videos": {"portrait-4x5": "<slug>-portrait-4x5.mp4"},
  "covers": {"portrait-4x5": "cover-portrait-4x5.png"}
}
```

`publish` is keyed by each platform's `file_stem` (`wechat` for WeChat Channels, the id otherwise). `videos` and `covers` appear only when a listed platform uses a profile other than `vertical-9x16`; they list the files that exist. `cover` is `null` when `cover.png` does not exist yet; run the script again after the cover is rendered.

## Writing rules

- Chinese platforms: simplified Chinese, natural and concrete. English platforms (LinkedIn, Facebook): plain, professional English; the video itself stays bilingual. Lead with the clip's real idea, not an exaggeration of it.
- Truthful: no invented statistics, no claims the speaker did not make, no fake urgency. A question at the end is fine.
- Titles differ between platforms in wording; each states one idea.
- Description: 2-3 sentences, then the credit line, then hashtags.
- Hashtags: 3-5 relevant ones (topic, speaker or show, format such as 中英双语). No spaces inside a tag.
- Credit: always name the source, speaker and year, and say the subtitles are your own translation. Never present third-party content as original.
- If review_status is not `approved` or the licence forbids derivatives, put that in `notes`.

## Limits

`config/platforms.yaml` holds the limits per platform (for example WeChat short title 6-16, Douyin title <= 30, descriptions <= 1000, hashtags <= 5). Each platform has a `verified` flag. Most are `false`: platforms change their rules and official pages could not be read, so the limits are conservative defaults. `publish.md` names the unverified platforms; tell the user to check each publish page and edit the file, then set `verified: true`.

## Commands

```bash
python3 scripts/publish_meta.py output/projects/<slug> --init                           # draft for wechat_channels and douyin
python3 scripts/publish_meta.py output/projects/<slug> --init --platform douyin,linkedin  # draft for chosen platforms
python3 scripts/publish_meta.py output/projects/<slug>                                   # validate + write publish.md and .txt files
```
