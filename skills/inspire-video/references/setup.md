# Setup procedure

When the user asks to install, set up or fix InspireVideo (or runs `setup`):
- If the skill is not installed, pick one way. Claude Code plugin: the user runs `/plugin marketplace add encoreshao/inspire-video` and then `/plugin install inspire-video@inspire-video` (these are slash commands, so the user types them; the same two commands work in any Claude Code profile, such as one started with `CLAUDE_CONFIG_DIR=~/.claude-loopx`). Script install: run `curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash -s -- claude` (use `codex` for Codex).
- Do not keep both: a plugin install next to the script install's links lists every skill twice. Remove the links with `bash scripts/uninstall.sh` (the clone and its outputs stay), or remove the plugin with `/plugin uninstall inspire-video@inspire-video`.
- From the engine root (the folder two levels above the skill's own folder), run `bash scripts/prepare.sh` and then `python3 scripts/check_env.py`, and report each missing item. `scripts/prepare.sh` installs the Python packages and runs `npm install` when they are missing; in a clone, `bash scripts/install.sh <claude|codex>` reinstalls them.
- To update: a plugin install with `/plugin marketplace update inspire-video` and then `/plugin update inspire-video@inspire-video` (or turn on auto-update for the marketplace in `/plugin`); a script install by running its install command again. Outputs and voices stay in `~/.inspire-video` either way.
- Ask before installing system packages (Python 3.11+, Node.js 20+, ffmpeg) with brew or apt, and never use sudo without the user's approval.
- Tell the user to start a new session so the skill loads. Do not process any video during setup.
