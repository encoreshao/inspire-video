"""A promo-style showcase project on disk, for the manifest and render tests."""
import json

from imgs import png
from showcase import page_layout as L

ELEMENTS = [
    {"role": "heading", "text": "Handled while you do the real work.", "x": 100, "y": 100, "w": 600, "h": 80},
    {"role": "button", "text": "Download", "x": 100, "y": 300, "w": 200, "h": 48},
    {"role": "card", "text": "", "x": 100, "y": 500, "w": 900, "h": 400},
]
BEAT_IDS = ("hook", "problem", "what", "cta")
SHOTS = ("hero-push", "spotlight-focus", "hero-push", "spotlight-focus")
TARGETS = ("heading-1", "button-1", "card-1", "heading-1")


def promo_project(tmp_path):
    p = tmp_path / "proj"
    (p / "assets").mkdir(parents=True)
    (p / "assets" / "promo-1@2x.png").write_bytes(png(2880, 3000))
    layout = L.build_layout(ELEMENTS, url="https://example.com/", page_w=1440, page_h=1500,
                            image="assets/promo-1@2x.png")
    (p / "assets" / "promo-1.layout.json").write_text(json.dumps(layout), encoding="utf-8")
    beats = [{"id": bid, "en": f"Beat {bid} says one thing.", "zh": "这是一句中文。", "asset": "assets/promo-1@2x.png",
              "shot": shot, "target": target} for bid, shot, target in zip(BEAT_IDS, SHOTS, TARGETS)]
    m = {"type": "showcase", "project_id": "acme-promo", "style": "promo", "theme": "light",
         "headline": "任何网站都能变成短视频", "subtitle": "Turn any site into a short video", "category": "SHOWCASE",
         "project": {"name": "Acme", "name_zh": "极致", "tagline": "Widgets", "tagline_zh": "小工具"},
         "source": {"kind": "website", "url": "https://example.com/", "label": "example.com"},
         "beats": beats, "provenance": {"rights_confirmed": True, "source_reference": "https://example.com/"}}
    (p / "video_manifest.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    return p, m
