"""The site's accent colour, read from its captures: the promo frame's background is tinted and lit with it.

It looks for the dominant saturated hue (white, grey and near-black pages have none) with Pillow, which is optional: without
it, or without a usable colour, there is no accent and the frame keeps the theme's plain background.
"""
from __future__ import annotations

import colorsys
from pathlib import Path

HUES = 24                    # hue buckets
MIN_SAT, MIN_VAL, MAX_VAL = 0.35, 0.30, 0.95
MIN_SHARE = 0.0004           # the winning hue must cover at least this share of the pixels (weighted), or it is noise: a clean page has a small accent


def dominant_accent(path, width: int = 160) -> str | None:
    """'#rrggbb' of the dominant saturated colour of an image, or None when there is none or the image cannot be read."""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as im:
            im = im.convert("RGB")
            im.thumbnail((width, 4000))
            pixels = list(im.getdata())
    except (OSError, ValueError, Image.DecompressionBombError):
        return None
    weight = [0.0] * HUES
    sums = [[0.0, 0.0, 0.0] for _ in range(HUES)]
    for r, g, b in pixels:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s < MIN_SAT or not MIN_VAL <= v <= MAX_VAL:
            continue
        k = min(HUES - 1, int(h * HUES))
        w = s * v
        weight[k] += w
        for i, c in enumerate((r, g, b)):
            sums[k][i] += c * w
    best = max(range(HUES), key=lambda k: weight[k])
    if not pixels or weight[best] < MIN_SHARE * len(pixels):
        return None
    r, g, b = (round(c / weight[best]) for c in sums[best])
    return f"#{r:02x}{g:02x}{b:02x}"


def first_accent(paths) -> str | None:
    """The accent of the first image that has one."""
    for p in paths:
        colour = dominant_accent(p)
        if colour:
            return colour
    return None
