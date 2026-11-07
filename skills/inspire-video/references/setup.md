# Setup procedure

When the user asks to install, set up or fix InspireVideo (or runs `setup`):
- If the skill is not installed, run `curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash -s -- claude` (use `codex` for Codex).
- Run `python3 ~/.inspire-video/scripts/check_env.py` and report each missing item. Python packages and `npm install` can be fixed with `bash ~/.inspire-video/scripts/install.sh <claude|codex>`.
- Ask before installing system packages (Python 3.11+, Node.js 20+, ffmpeg) with brew or apt, and never use sudo without the user's approval.
- Tell the user to start a new session so the skill loads. Do not process any video during setup.
