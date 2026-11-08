# Content extraction and editorial policy

## Candidate scoring

Score each contiguous candidate from 1–5 on:
- clarity without prior context;
- emotional resonance / practical insight;
- completeness;
- memorable phrasing;
- audio intelligibility;
- visual suitability;
- factual/contextual safety.

Suggested weighted score:
- clarity 20%;
- completeness 20%;
- value 20%;
- memorable phrasing 15%;
- audio 10%;
- visual 10%;
- context safety 5%.

A high score does not override a misleading or incomplete statement. Reject candidates that need extensive edits to make sense.

## Segment boundaries

- Prefer natural pauses and sentence boundaries.
- Include enough lead-in to establish context.
- End after the thought resolves.
- Avoid joining separate moments into one quote.
- Record exact source in/out timestamps.
- After choosing a range from `transcript.json`, run `python scripts/refine_segment.py <project-dir> --start <s> --end <s> --write`. It snaps both ends to transcript cue edges, extends a short range or trims a long one to fit 40-150 s without crossing a pause over 5 s, and writes `segment_report.json`. Use its start and end, not your estimate. Read every `warnings` entry (a clip that starts or ends mid-sentence) and either choose a different range or say why the cut is acceptable. An error means the range has too little connected speech: choose another.

## Translation

- Preserve claims, uncertainty, negation, conditions and emphasis.
- Do not strengthen a cautious statement.
- Prefer idiomatic Simplified Chinese.
- Keep the English original as the canonical quote.
- If a phrase has multiple plausible meanings, include a translator note in `review.md`.

## Attribution

Only use names, credentials, show titles and dates present in the supplied source or independently verified. Do not infer identity from appearance or voice. If uncertain, omit the credential and flag the missing attribution.

## Suggested output JSON

```json
{
  "headline_zh": "先行动，再自信",
  "subtitle_en": "Act First, Then Feel Confident",
  "quote_en": "It removes a little bit of the insecurity.",
  "quote_zh": "那份不安全感就会减轻一点。",
  "speaker": {
    "name": "MEL ROBBINS",
    "credential": ""
  },
  "source": {
    "show": "Podcast name",
    "year": 2025
  },
  "category": "INSPIRATION"
}
```

The sample is illustrative only, not a factual attribution for any particular source clip.
