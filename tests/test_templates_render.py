import json

import pytest

from promo_fixtures import promo_project
from showcase import manifest as M
from showcase import render_showcase as R
from showcase import templates as T
from test_showcase_manifest import timings


def filled(scaffolded: dict) -> dict:
    """What a writer does with a scaffold: write the text, point every camera beat at a real element, accept the rights."""
    m = json.loads(json.dumps(scaffolded))
    m.update(headline="任何网站变成视频", subtitle="Any site as a short video", project={"name": "Acme", "tagline": "Widgets"},
             source={"kind": "website", "url": "https://example.com/", "label": "example.com"})
    m["provenance"]["rights_confirmed"] = True
    targets = ["heading-1", "button-1", "card-1"]
    for i, b in enumerate(m["beats"]):
        b["en"], b["zh"] = f"Beat {i} says one thing.", "这是一句中文。"
        if b["shot"] == "statement":
            b["statement"] = "One clear idea"
        else:
            b.pop("focus", None)
            b["target"] = "button-1" if b["shot"] == "crash-zoom-punch" else targets[i % 3]
    return m


@pytest.mark.parametrize("tid", sorted(T.load_templates()))
@pytest.mark.parametrize("n", [10, 16, 40])
def test_every_shipped_template_scaffolds_validates_and_builds_props(tmp_path, tid, n):
    p, _ = promo_project(tmp_path)
    brief = {"assets": [{"path": "assets/promo-1@2x.png", "role": "screenshot"}],
             "source": {"kind": "website", "url": "https://example.com/", "host": "example.com"}}
    m = filled(M.scaffold_manifest(brief, "acme-promo", n, template=tid))
    t = timings(m, [max(7.0, 130 / n)] * n)   # a real video takes its beat lengths from narration, not the 4 s default
    M.validate_showcase(m, p, t)
    assert M.template_warnings(m) == []
    props = R.build_props(m, p, t, {b["id"]: {"asset": "a.png" if b.get("asset") else None, "audio": None} for b in m["beats"]})
    assert props["template"] == tid and props["transition"] == "dissolve" and len(props["beats"]) == n
