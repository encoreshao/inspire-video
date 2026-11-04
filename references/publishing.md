# Publishing copy guide (WeChat Channels and Douyin)

`publish.json` (source of truth) lives in the project folder. The generated `publish.md` (all copy, ready to paste), `publish_wechat.txt` and `publish_douyin.txt` are written to `output/final/<slug>/`, next to the video and `cover.png`.

## publish.json

```json
{
  "wechat_channels": {"short_title": "6-16 chars", "description": "...", "hashtags": ["拖延症", "TED演讲"]},
  "douyin": {"title": "<= 30 chars", "description": "...", "hashtags": ["拖延症", "TED演讲"]},
  "credit": "内容来源：TED 演讲《…》，演讲者 …，2016。中英字幕为自制翻译，版权归原作者所有。",
  "notes": ["reminders for the publisher"]
}
```

Hashtags are written without `#`; the script adds it. The credit line is appended to every description, followed by the hashtags.

## Writing rules

- Simplified Chinese, natural and concrete. Lead with the clip's real idea, not an exaggeration of it.
- Truthful: no invented statistics, no claims the speaker did not make, no fake urgency. A question at the end is fine.
- Title: the WeChat short title and the Douyin title should differ in wording; each states one idea.
- Description: 2-3 sentences, then the credit line, then hashtags.
- Hashtags: 3-5 relevant ones (topic, speaker or show, format such as 中英双语). No spaces inside a tag.
- Credit: always name the source, speaker and year, and say the subtitles are your own translation. Never present third-party content as original.
- If review_status is not `approved` or the licence forbids derivatives, put that in `notes`.

## Limits

`config/publish.yaml` holds the limits (WeChat short title 6-16, Douyin title <= 30, descriptions <= 1000, hashtags <= 5). They are conservative, unverified defaults: platforms change their rules, so check each publish page and edit the file.

## Commands

```bash
python3 scripts/publish_meta.py output/projects/<slug> --init   # draft from copy.json
python3 scripts/publish_meta.py output/projects/<slug>          # validate + write publish.md and .txt files
```
