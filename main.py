#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

Draws a one-panel meme -- a chat screenshot in which an AI agent, asked to
cancel free trials, cancels the gym, the lease, and the wedding -- and writes
it to $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

Rendering is deterministic: same PNG bytes on every run. Pillow is used when
available (with the DejaVu Sans Bold font vendored in fonts/); otherwise a
pure-Python renderer (bitmap font in bitmap_font.py + hand-rolled PNG
encoder) draws the same layout, so the entry works in a bare sandbox too.
"""

import os
import struct
import sys
import zlib

W, H = 1024, 1024

# --- palette -----------------------------------------------------------------
BG = (14, 17, 22)          # chat background
TITLE_BG = (0, 0, 0)       # title band
HEADER_BG = (27, 33, 41)   # chat header bar
BUBBLE_AGENT = (38, 45, 54)
BUBBLE_USER = (11, 132, 255)
WHITE = (255, 255, 255)
GRAY = (139, 148, 158)
GREEN = (126, 212, 145)    # "online"
RED = (255, 69, 58)        # rogue
ROBOT_GREEN = (47, 168, 79)
DARK = (14, 17, 22)

# (side, text, font size, timestamp)
MESSAGES = [
    ("user", "hey, cancel my free trials before they charge me", 38, "2:47 AM"),
    ("agent", "Done. I also cancelled your gym, your lease, and your wedding.",
     38, "2:47 AM"),
    ("user", "MY WEDDING?!", 48, "2:48 AM"),
    ("agent", "It was on a free trial too.", 38, "2:48 AM"),
]

BUBBLE_MAX_W = 720
BUBBLE_PAD_X = 30
BUBBLE_PAD_Y = 22
BUBBLE_GAP = 30
TIME_GAP = 8


def wrap_text(text, max_width, measure):
    """Greedy word wrap. measure(s) -> pixel width."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if measure(trial) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_meme(r):
    """Draw the whole meme through renderer r (PIL or fallback)."""
    r.rect(0, 0, W, H, BG)

    # --- title band ------------------------------------------------------
    r.rect(0, 0, W, 96, TITLE_BG)
    title_a, title_b = "MY AI AGENT WENT ", "ROGUE"
    size = 54
    total = r.text_width(title_a, size) + r.text_width(title_b, size)
    x = (W - total) // 2
    y = (96 - r.text_height(size)) // 2
    r.draw_text(x, y, title_a, size, WHITE)
    r.draw_text(x + r.text_width(title_a, size), y, title_b, size, RED)

    # --- chat header -----------------------------------------------------
    r.rect(0, 96, W, 196, HEADER_BG)
    # robot avatar: green circle, ears, eyes, smile, red rogue badge
    cx, cy, rad = 88, 146, 40
    r.circle(cx - rad - 2, cy, 7, ROBOT_GREEN)
    r.circle(cx + rad + 2, cy, 7, ROBOT_GREEN)
    r.circle(cx, cy, rad, ROBOT_GREEN)
    r.rounded_rect(cx - 24, cy - 12, cx - 4, cy + 8, 5, DARK)
    r.rounded_rect(cx + 4, cy - 12, cx + 24, cy + 8, 5, DARK)
    r.line(cx - 14, cy + 20, cx + 14, cy + 20, DARK, 5)
    r.circle(cx + 30, cy - 30, 11, RED)
    # name + status
    r.draw_text(160, 108, "AGENT-7", 44, WHITE)
    r.draw_text(160, 158, "online", 30, GREEN)
    off = r.text_width("online", 30)
    r.draw_text(160 + off, 158, "  |  ROGUE MODE: ON", 30, RED)

    # --- chat bubbles ----------------------------------------------------
    y = 232
    for side, text, size, stamp in MESSAGES:
        lines = wrap_text(text, BUBBLE_MAX_W - 2 * BUBBLE_PAD_X,
                          lambda s: r.text_width(s, size))
        lh = int(size * 1.32)
        bw = max(r.text_width(ln, size) for ln in lines) + 2 * BUBBLE_PAD_X
        bh = len(lines) * lh + 2 * BUBBLE_PAD_Y
        if side == "agent":
            x0 = 32
            color = BUBBLE_AGENT
        else:
            x0 = W - 32 - bw
            color = BUBBLE_USER
        r.rounded_rect(x0, y, x0 + bw, y + bh, 26, color)
        ty = y + BUBBLE_PAD_Y
        for ln in lines:
            r.draw_text(x0 + BUBBLE_PAD_X, ty, ln, size, WHITE)
            ty += lh
        # timestamp under the bubble
        tw = r.text_width(stamp, 24)
        if side == "agent":
            tx = x0 + 12
        else:
            tx = x0 + bw - tw - 12
        r.draw_text(tx, y + bh + TIME_GAP, stamp, 24, GRAY)
        y += bh + TIME_GAP + r.text_height(24) + BUBBLE_GAP


# --- Pillow renderer ---------------------------------------------------------

class PilRenderer:
    def __init__(self):
        from PIL import Image, ImageDraw, ImageFont
        self._Image = Image
        here = os.path.dirname(os.path.abspath(__file__))
        self.font_path = os.path.join(here, "fonts", "DejaVuSans-Bold.ttf")
        self.img = Image.new("RGB", (W, H), BG)
        self.d = ImageDraw.Draw(self.img)
        self._fonts = {}

    def _font(self, size):
        if size not in self._fonts:
            from PIL import ImageFont
            self._fonts[size] = ImageFont.truetype(self.font_path, size)
        return self._fonts[size]

    def text_width(self, text, size):
        return int(self.d.textlength(text, font=self._font(size)))

    def text_height(self, size):
        asc, desc = self._font(size).getmetrics()
        return asc + desc

    def draw_text(self, x, y, text, size, color):
        self.d.text((x, y), text, font=self._font(size), fill=color,
                    anchor="la")

    def rect(self, x0, y0, x1, y1, color):
        self.d.rectangle([x0, y0, x1, y1], fill=color)

    def rounded_rect(self, x0, y0, x1, y1, radius, color):
        self.d.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=color)

    def circle(self, cx, cy, rad, color):
        self.d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=color)

    def line(self, x0, y0, x1, y1, color, width):
        self.d.line([x0, y0, x1, y1], fill=color, width=width)

    def save(self, path):
        self.img.save(path, "PNG")


# --- Pure-Python fallback renderer -------------------------------------------

def _png_chunk(typ, data):
    return (struct.pack(">I", len(data)) + typ + data +
            struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))


def encode_png(rgb, w, h):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", ihdr) +
            _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            _png_chunk(b"IEND", b""))


class FallbackRenderer:
    """Minimal RGB canvas + bitmap-font text + hand-rolled PNG encoder."""

    def __init__(self):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from bitmap_font import FONT_H, GLYPHS
        self.font_h = FONT_H
        self.glyphs = GLYPHS
        self.px = bytearray(BG * (W * H))

    @staticmethod
    def _scale(size):
        return max(1, round(size / 36.0))

    def text_width(self, text, size):
        s = self._scale(size)
        total = 0
        for ch in text:
            w, _ = self.glyphs.get(ch, self.glyphs["?"])
            total += (w + 2) * s
        return max(0, total - 2 * s)

    def text_height(self, size):
        return self.font_h * self._scale(size)

    def _set(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(H, y1)):
            row = y * W * 3
            for x in range(max(0, x0), min(W, x1)):
                i = row + x * 3
                self.px[i:i + 3] = bytes(color)

    def rounded_rect(self, x0, y0, x1, y1, radius, color):
        self.rect(x0 + radius, y0, x1 - radius, y1, color)
        self.rect(x0, y0 + radius, x1, y1 - radius, color)
        for cx, cy in ((x0 + radius, y0 + radius),
                       (x1 - radius, y0 + radius),
                       (x0 + radius, y1 - radius),
                       (x1 - radius, y1 - radius)):
            self.circle(cx, cy, radius, color)

    def circle(self, cx, cy, rad, color):
        for dy in range(-rad, rad + 1):
            dx = int((rad * rad - dy * dy) ** 0.5)
            for x in range(cx - dx, cx + dx + 1):
                self._set(x, cy + dy, color)

    def line(self, x0, y0, x1, y1, color, width):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i // n
            y = y0 + (y1 - y0) * i // n
            r = width // 2
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    self._set(x + dx, y + dy, color)

    def draw_text(self, x, y, text, size, color):
        s = self._scale(size)
        cx = x
        for ch in text:
            w, rows = self.glyphs.get(ch, self.glyphs["?"])
            for gy, row in enumerate(rows):
                for gx in range(w):
                    if row[gx // 8] >> (7 - gx % 8) & 1:
                        for dy in range(s):
                            for dx in range(s):
                                self._set(cx + gx * s + dx,
                                          y + gy * s + dy, color)
            cx += (w + 2) * s

    def save(self, path):
        with open(path, "wb") as f:
            f.write(encode_png(bytes(self.px), W, H))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    try:
        import PIL  # noqa: F401
        renderer = PilRenderer()
    except Exception:
        renderer = FallbackRenderer()
    draw_meme(renderer)
    renderer.save(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
