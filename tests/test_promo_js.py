import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_promo_camera_unit_tests_pass_under_node():
    r = subprocess.run(["node", "--test", "video/src/showcase/promo.test.mjs"], cwd=ROOT,
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "# pass 14" in r.stdout and "# fail 0" in r.stdout
