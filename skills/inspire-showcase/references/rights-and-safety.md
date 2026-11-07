# Rights, consent and safe output

## Rights

- Treat screenshots the user supplied as the user's own.
- Treat assets captured from a page or taken from a repository as unresolved: they carry a rights note in `brief.json` and set `rights_unresolved: true`.
- Ask the user whether they own or may reuse those assets before any public render. Only then set `provenance.rights_confirmed: true` and pass `--allow-unresolved-rights` to the final render. Previews do not need the flag.
- Never claim the content is original, and never write `rights_confirmed: true` without the user's answer.

## Voice

- Use a cloned voice only when it is the user's own voice. Store profiles in the git-ignored `voices/` folder and never commit or share them.
- Remind the user that platforms such as Douyin and WeChat have labelling rules for synthetic voice before publishing narration made with a cloned voice.

## Crawling and capture

- Respect `robots.txt` and the refusal of private addresses (`--allow-private` exists for the user's own local sites only). Do not work around either.
- Page capture uses a headless browser that follows its own redirects; do not point ingest at pages the user does not control or intend to publish about.

## Safe area

- Content stays at or above y = 1590 and 114 px from each side, so tall phones that crop the sides and platform buttons at the bottom do not cut it. `scripts/showcase/checks.py` verifies the real render (size, first frame, bottom margin, side margins). It cannot detect clipped text, so inspect the preview.
