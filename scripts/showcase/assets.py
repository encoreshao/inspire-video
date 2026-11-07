"""Image assets: header-only size probing, screenshot-folder collection, ranking and rights notes."""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif")
MIN_SIDE = 320
ORIGIN_RANK = {"user": 0, "capture": 1, "repo": 2}
HEADER_BYTES = 2_000_000


class AssetError(ValueError):
    pass


def _jpeg_size(d: bytes) -> tuple[int, int]:
    i = 2
    while i + 9 < len(d):
        if d[i] != 0xFF:
            i += 1
            continue
        marker = d[i + 1]
        if marker == 0xFF:
            i += 1
            continue
        if marker == 0x01 or 0xD0 <= marker <= 0xD8:
            i += 2
            continue
        seglen = struct.unpack(">H", d[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height, width = struct.unpack(">HH", d[i + 5:i + 9])
            return width, height
        i += 2 + seglen
    raise AssetError("JPEG without size information")


def _webp_size(d: bytes) -> tuple[int, int]:
    kind = d[12:16]
    if kind == b"VP8X" and len(d) >= 30:
        return 1 + int.from_bytes(d[24:27], "little"), 1 + int.from_bytes(d[27:30], "little")
    if kind == b"VP8 " and len(d) >= 30:
        w, h = struct.unpack("<HH", d[26:30])
        return w & 0x3FFF, h & 0x3FFF
    if kind == b"VP8L" and len(d) >= 25:
        bits = int.from_bytes(d[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    raise AssetError("unsupported WebP variant")


def image_size(path) -> tuple[int, int]:
    path = Path(path)
    try:
        with open(path, "rb") as f:
            d = f.read(HEADER_BYTES)
        if d[:8] == b"\x89PNG\r\n\x1a\n" and len(d) >= 24:
            size = struct.unpack(">II", d[16:24])
        elif d[:6] in (b"GIF87a", b"GIF89a") and len(d) >= 10:
            size = struct.unpack("<HH", d[6:10])
        elif d[:4] == b"RIFF" and d[8:12] == b"WEBP":
            size = _webp_size(d)
        elif d[:2] == b"\xff\xd8":
            size = _jpeg_size(d)
        else:
            raise AssetError("not a readable PNG, JPEG, GIF or WebP image")
    except (OSError, struct.error, AssetError) as e:
        raise AssetError(f"{path.name}: {e}") from None
    if size[0] <= 0 or size[1] <= 0:
        raise AssetError(f"{path.name}: the image reports a size of {size[0]}x{size[1]}")
    return size


def natural_key(name: str) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def rights_note(origin: str, source_url: str = "", license_name: str = "") -> str:
    if origin == "user":
        return "provided by the user"
    if origin == "capture":
        return f"captured from {source_url}: confirm you may reuse it before publishing"
    return (f"from the repository {source_url} (license: {license_name or 'unknown'}): "
            "confirm you may reuse it before publishing")


def try_describe(path, origin: str, source: str, rights: str):
    """Return (asset, None) for a usable image, or (None, reason)."""
    path = Path(path)
    if path.suffix.lower() not in IMAGE_EXTS:
        return None, "not an image file (png, jpg, webp, gif)"
    try:
        width, height = image_size(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except (AssetError, OSError) as e:
        return None, str(e)
    if min(width, height) < MIN_SIDE:
        return None, f"too small ({width}x{height}): the short side must be at least {MIN_SIDE} px"
    return {"path": str(path), "origin": origin, "source": source, "width": width, "height": height,
            "sha256": digest, "rights": rights, "rights_resolved": origin == "user"}, None


def collect_user_shots(folder):
    folder = Path(folder)
    if not folder.is_dir():
        raise AssetError(f"the screenshots folder {folder} does not exist")
    files = sorted((p for p in folder.iterdir() if p.is_file() and not p.name.startswith(".")),
                   key=lambda p: natural_key(p.name))
    found, rejected = [], []
    for p in files:
        asset, why = try_describe(p, "user", str(p), rights_note("user"))
        if asset is None:
            rejected.append({"path": str(p), "reason": why})
        else:
            found.append(asset)
    kept, dupes = dedupe(found)
    return kept, rejected + dupes


def dedupe(assets):
    seen, kept, dropped = {}, [], []
    for a in assets:
        name = Path(a["path"]).name
        if a["sha256"] in seen:
            dropped.append({"path": a["path"], "reason": f"duplicate of {seen[a['sha256']]}"})
        else:
            seen[a["sha256"]] = name
            kept.append(a)
    return kept, dropped


def rank_assets(assets):
    return sorted(assets, key=lambda a: ORIGIN_RANK[a["origin"]])
