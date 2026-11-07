import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

import platforms

ROOT = Path(__file__).resolve().parent.parent
needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")


@needs_node
def test_layout_unit_tests_pass_under_node_against_the_real_registry():
    reg = platforms.load()
    profiles = {p.id: {**p.props(), "supported": p.supported} for p in reg.profiles.values()}
    r = subprocess.run(["node", "--test", "video/src/layout.test.mjs"], cwd=ROOT, capture_output=True, text=True,
                       timeout=60, env={**os.environ, "PROFILES_JSON": json.dumps(profiles)})
    assert r.returncode == 0, r.stdout + r.stderr
    assert "# fail 0" in r.stdout


@needs_node
def test_the_default_profile_in_layout_matches_the_registry():
    r = subprocess.run(["node", "-e", "import('./video/src/layout.mjs').then(m => console.log(JSON.stringify(m.DEFAULT_PROFILE)))"],
                       cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout) == platforms.load().profile(platforms.DEFAULT_PROFILE).props()
