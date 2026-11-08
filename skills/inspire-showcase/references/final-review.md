<!--
Adapted from references/final-review.md of video-shotcraft (https://github.com/Vincentwei1021/video-shotcraft),
Copyright Vincentwei1021, licensed under the Apache License 2.0 (see NOTICE at the repo root).
Changes: translated from Chinese; cut the shot-card, Gallery, BGM and sound-effect items; added bilingual caption,
narration and rights items for InspireShowcase and a block (S) for the promo style's shots.
-->
# Independent final review

Run this review on the finished preview or final MP4 before telling the user the video is done. The author of a video is biased toward its own work, so the first review is never left to the user.

## How to run it

Start a subagent with a clean context. Give it only the inputs below, never the reasons for any choice, the edit history or the result you expect. If an input is missing, the reviewer marks that item "cannot verify" and does not guess.

Inputs:

- the MP4 and a contact sheet: `python3 scripts/showcase/checks.py <video> --sheet <sheet.png>` writes 12 evenly spaced frames; ask for more frames when a finding needs evidence;
- `brief.json` and `video_manifest.json` of the project;
- `references/rights-and-safety.md` and `references/aesthetic-rules.md`.

The reviewer reports every item below as `ID ✓` or `ID ✗ (time, evidence)`, then lists must-fix, should-fix and cannot-verify items. A bare "looks good" is not a report, and an all-pass report with no evidence is a failed review.

## Items

**P: product truth**
- P1: Does the video say what the product is and who it is for?
- P2: Is every claim, number, name and feature found in `brief.json`? Report each one that is not.
- P3: Does anything imply a feature, customer or result the brief does not support?

**F: coverage**
- F1: Does each feature the user asked to show appear in a beat that makes it recognisable?
- F2: Does each beat add something new, with no repeated feature and no repeated call to action?
- F3: Does the screenshot behind each beat show what the caption claims?

**C: captions and narration**
- C1: Are the English and Chinese lines both fully visible, not cut off, and a faithful pair rather than a literal translation?
- C2: Is the Chinese natural, with correct terms and no machine-translation phrasing?
- C3: With narration: does the spoken text equal the caption text, and does each beat's audio end before the next beat starts?
- C4: With a cloned or synthetic voice: is it labelled as required by the rights reference?

**V: visual quality** (apply `aesthetic-rules.md`)
- V1: Does the focus ring and zoom land on the thing the caption talks about?
- V2: Is text sharp, readable on a phone and clear of the safe margins?
- V3: Is the pacing calm: each caption readable twice, the key beat held, no beat rushed?
- V4: Are there any seams, cropped screenshots, blurry frames or flashes at the cross-fades?
- V5: Does the first frame show content and the last frame hold the last real image, never black or faded?

**S: promo shots** (only for `style: "promo"`)
- S1: Does every beat use the shot its storyboard row names, and does its target match what its caption talks about?
- S2: At the end of each beat, is the target fully in view and clear of the stage edge?
- S3: Is text sharp at the end of each beat, with no soft zoom?
- S4: Are the shot rules kept: no shot twice in a row, `crash-zoom-punch` once, `pan-reveal` only on a tall page, at most 2 statements?
- S5: Does each beat hold still for its last second, judged at least 10 frames before the cross-fade into the next beat?
- S6: Is the cover the hero view, neither dimmed nor a blend?

**D: data and rights**
- D1: Do the screenshots show customer, personal, internal or secret data (emails, tokens, addresses, names)?
- D2: Is the source labelled, and were the rights questions answered before this public render?
- D3: Are the images captured from the real product rather than faked?

## Report format

```text
P2 ✗ 0:14: the caption says "10,000 users" but brief.json has no user count.
V2 ✗ 0:31: the callout touches the right safe margin, see sheet frame 8.
C1 ✓ both lines fit in all 5 beats.
```

Fix every must-fix item, render again and review again. Stop only when the report has none, or the user accepts a named item.
