"""Header-only image files for tests (the code under test only reads headers)."""
import struct
import zlib


def png(w, h):
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IEND", b""))


def jpeg(w, h):
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    sof0 = (b"\xff\xc0" + struct.pack(">H", 17) + b"\x08" + struct.pack(">HH", h, w)
            + b"\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01")
    return b"\xff\xd8" + app0 + sof0 + b"\xff\xd9"


def gif(w, h):
    return b"GIF89a" + struct.pack("<HH", w, h) + b"\x00\x00\x00"


def webp(w, h):
    body = (b"WEBP" + b"VP8X" + struct.pack("<I", 10) + b"\x00\x00\x00\x00"
            + (w - 1).to_bytes(3, "little") + (h - 1).to_bytes(3, "little"))
    return b"RIFF" + struct.pack("<I", len(body)) + body
