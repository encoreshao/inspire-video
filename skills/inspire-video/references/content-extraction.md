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

## Rubric by content type

<!-- The per-type emphasis is condensed from the outline prompts of autoclip (MIT, https://github.com/zhouxiaoka/autoclip), rewritten for one 40-150 s clip. -->

Decide the dominant type of the source first, from the transcript, and say which you chose. The weights above stay the same; the type changes what to look for and what ruins a candidate. For mixed content use the type of the stretch you are cutting.

| Type | Look for | Reject | The clip must contain |
|---|---|---|---|
| Speech or talk | one core idea told with a story, image or turn of phrase; emotional lift | applause-only stretches, housekeeping, a story cut before its point | opening, development and the line that lands |
| Interview or conversation | a clear question and its complete answer; a surprising admission | small talk, an answer that needs the question's context to make sense | the question's gist (as lead-in) through the end of the answer |
| Opinion or commentary | a distinct position with its reason; a counterpoint handled fairly | a claim without its argument, a one-sided cut of a balanced discussion | position, reason and conclusion |
| Experience or how-to | a concrete method, the result and a caveat | vague advice, steps cut in half | background, method and outcome |
| Business or finance | a specific fact, case or trend with cause and consequence | forecasts stated as certainty, numbers without their source or date | the claim with its figure and its qualifier |
| Entertainment or banter | a complete exchange with the payoff intact | a joke cut before the punchline, an in-joke that needs earlier context | setup and payoff |

Two rules apply to every type: never start or end on a filler phrase, and never cut a qualifier ("might", "in my experience", "for some people") out of a claim, because that strengthens it.

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
