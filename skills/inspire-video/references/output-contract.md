# Output contract

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
