#!/usr/bin/env python3
"""Draw the bundled sample page that `templates.py preview` films: a made-up product site with a hero, cards, a chart and a
call to action. It is invented for this tool (no real company, no logos), drawn with Pillow so the PNG is the same on every
machine once generated. Run it only to regenerate the two files next to this script:

  python3 templates/sample/make_sample.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from showcase import page_layout as L  # noqa: E402

HERE = Path(__file__).resolve().parent
W, H, SCALE = 1440, 3200, 2
INK, MUTED, ACCENT, SOFT, LINE = "#111827", "#6b7280", "#4f46e5", "#eef2ff", "#e5e7eb"
FONT_PATHS = ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


def font(size: int, bold: bool = False):
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size * SCALE, index=1 if bold and path.endswith(".ttc") else 0)
        except OSError:
            continue
    return ImageFont.load_default(size * SCALE)


def draw_page() -> tuple[Image.Image, list[dict]]:
    img = Image.new("RGB", (W * SCALE, H * SCALE), "#fafafa")
    d = ImageDraw.Draw(img)
    els: list[dict] = []

    def rect(x, y, w, h, fill, radius=18, outline=None):
        d.rounded_rectangle([x * SCALE, y * SCALE, (x + w) * SCALE, (y + h) * SCALE], radius=radius * SCALE, fill=fill,
                            outline=outline, width=2 * SCALE if outline else 0)

    def text(x, y, s, size, fill=INK, bold=False):
        d.text((x * SCALE, y * SCALE), s, font=font(size, bold), fill=fill)

    def add(role, x, y, w, h, label=""):
        els.append({"role": role, "text": label, "x": x, "y": y, "w": w, "h": h})

    rect(0, 0, W, 90, "#ffffff", 0)
    d.line([0, 90 * SCALE, W * SCALE, 90 * SCALE], fill=LINE, width=2)
    rect(96, 28, 34, 34, ACCENT, 10)
    text(142, 28, "Northwind", 30, INK, True)
    for i, label in enumerate(("Product", "Pricing", "Customers", "Docs")):
        text(560 + i * 130, 32, label, 22, MUTED)
    rect(1180, 22, 164, 46, INK, 23)
    text(1214, 32, "Get started", 20, "#ffffff", True)
    add("nav", 0, 0, W, 90, "navigation")
    add("button", 1180, 22, 164, 46, "Get started")

    text(96, 170, "Ship launches", 84, INK, True)
    text(96, 262, "people remember.", 84, ACCENT, True)
    add("heading", 96, 170, 760, 190, "Ship launches people remember.")
    text(96, 392, "One workspace to plan, write and publish every", 28, MUTED)
    text(96, 434, "announcement your team is proud of.", 28, MUTED)
    rect(96, 510, 220, 66, ACCENT, 33)
    text(138, 528, "Start free", 26, "#ffffff", True)
    add("button", 96, 510, 220, 66, "Start free")
    rect(340, 510, 220, 66, "#ffffff", 33, LINE)
    text(378, 528, "See a demo", 26, INK, True)
    add("button", 340, 510, 220, 66, "See a demo")
    rect(900, 150, 444, 440, SOFT, 28)
    for i in range(4):
        rect(930, 186 + i * 96, 384 - i * 40, 64, "#ffffff", 16)
        rect(950, 204 + i * 96, 28, 28, ACCENT if i % 2 == 0 else "#a5b4fc", 8)
    add("image", 900, 150, 444, 440, "product preview")

    text(96, 700, "Everything a launch needs", 52, INK, True)
    add("heading", 96, 700, 760, 70, "Everything a launch needs")
    cards = (("Plan", "Roadmaps that your whole team can read."), ("Write", "Drafts, reviews and approvals in one thread."),
             ("Publish", "Every channel at once, on the day it counts."))
    for i, (title, body) in enumerate(cards):
        x = 96 + i * 440
        rect(x, 820, 408, 300, "#ffffff", 24, LINE)
        rect(x + 32, 852, 56, 56, SOFT, 16)
        text(x + 32, 940, title, 36, INK, True)
        text(x + 32, 996, body[:30], 22, MUTED)
        text(x + 32, 1028, body[30:].strip(), 22, MUTED)
        add("card", x, 820, 408, 300, title)

    stats = (("12k", "teams"), ("3.4x", "faster launches"), ("98%", "on-time"), ("40+", "integrations"))
    for i, (big, small) in enumerate(stats):
        x = 96 + i * 330
        rect(x, 1240, 300, 190, SOFT, 24)
        text(x + 30, 1262, big, 68, ACCENT, True)
        text(x + 30, 1360, small, 26, MUTED)
        add("card", x, 1240, 300, 190, f"{big} {small}")

    text(96, 1560, "See how every launch is doing", 52, INK, True)
    add("heading", 96, 1560, 900, 70, "See how every launch is doing")
    rect(96, 1680, 1248, 620, "#ffffff", 28, LINE)
    for i, h in enumerate((200, 280, 240, 360, 320, 440, 400, 520)):
        rect(150 + i * 140, 2230 - h, 90, h, ACCENT if i == 7 else "#c7d2fe", 14)
    add("image", 96, 1680, 1248, 620, "launch analytics chart")

    rect(96, 2420, 1248, 360, SOFT, 28)
    text(150, 2470, "“We went from a scramble to a calm launch day.”", 44, INK, True)
    text(150, 2570, "Priya N., Head of Product", 26, MUTED)
    rect(150, 2640, 90, 90, ACCENT, 45)
    add("card", 96, 2420, 1248, 360, "testimonial")

    rect(96, 2860, 1248, 260, INK, 32)
    text(150, 2910, "Make your next launch the one they remember.", 46, "#ffffff", True)
    add("heading", 150, 2910, 1100, 60, "Make your next launch the one they remember.")
    rect(150, 3000, 220, 66, "#ffffff", 33)
    text(190, 3018, "Start free", 26, INK, True)
    add("button", 150, 3000, 220, 66, "Start free")
    return img, els


def main() -> int:
    img, raw = draw_page()
    png = HERE / "page@2x.png"
    img.save(png, optimize=True)
    layout = L.build_layout(raw, url="https://northwind.example/", page_w=W, page_h=H, image="assets/page@2x.png")
    (HERE / "page.layout.json").write_text(json.dumps(layout, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {png} ({img.width}x{img.height}) and its layout with {len(layout['elements'])} elements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
