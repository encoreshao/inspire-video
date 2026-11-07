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
├── <slug>-portrait-4x5.mp4   (only with --platform / --profile for 4:5 platforms)
├── cover-portrait-4x5.png
├── publish.md
└── publish_<platform>.txt   (one per platform listed in publish.json)
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
