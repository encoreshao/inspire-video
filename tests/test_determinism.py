import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN = re.compile(r"Math\.random\s*\(|Date\.now\s*\(|new Date\s*\(|performance\.now\s*\(")


def test_the_video_code_is_deterministic():
    # A render must be reproducible frame by frame (skills/inspire-showcase/references/aesthetic-rules.md, P1).
    hits = [f"{f.relative_to(ROOT)}:{n}" for f in sorted((ROOT / "video" / "src").rglob("*.ts*"))
            for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1) if FORBIDDEN.search(line)]
    assert hits == []
