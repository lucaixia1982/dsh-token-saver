"""Shared drawing helpers for the dsh-token-saver press figures.

Everything renders at S x supersample then downsamples, so radii/lines stay smooth.
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 2  # supersample factor

FONT_DIR = r"C:\Windows\Fonts"
REG = FONT_DIR + r"\msyh.ttc"
BOLD = FONT_DIR + r"\msyhbd.ttc"
MONO = FONT_DIR + r"\consola.ttf"
MONOB = FONT_DIR + r"\consolab.ttf"

# palette
INK = "#14181F"
INK_SOFT = "#2B323C"
MUTED = "#5D6673"
FAINT = "#8A939F"
LINE = "#E3E7EC"
CARD = "#FFFFFF"
PAPER = "#F7F8FA"
BRAND = "#1F8F6A"
BRAND_DEEP = "#146B4E"
BRAND_SOFT = "#EAF6F1"
ACCENT = "#247BBF"
ACCENT_SOFT = "#EAF2FB"
RED = "#C0392B"
RED_SOFT = "#FBECEA"
AMBER = "#B7791F"
AMBER_SOFT = "#FDF4E3"

_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    path = MONOB if (mono and bold) else MONO if mono else BOLD if bold else REG
    key = (path, size * S)
    f = _cache.get(key)
    if f is None:
        f = ImageFont.truetype(path, size * S)
        _cache[key] = f
    return f


def canvas(w: int, h: int, bg: str = CARD) -> Image.Image:
    return Image.new("RGB", (w * S, h * S), bg)


def _box(box: Sequence[int]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (x0 * S, y0 * S, x1 * S, y1 * S)


def shadow(img: Image.Image, box: Sequence[int], radius: int = 16, blur: int = 14,
           dy: int = 3, alpha: int = 26) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = _box(box)
    d.rounded_rectangle((x0, y0 + dy * S, x1, y1 + dy * S), radius=radius * S,
                        fill=(20, 24, 31, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur * S / 2))
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"), (0, 0))


def rrect(img: Image.Image, box: Sequence[int], radius: int = 16, *,
          fill: str | None = CARD, outline: str | None = LINE, width: int = 1) -> None:
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(_box(box), radius=radius * S, fill=fill,
                        outline=outline, width=max(1, width * S) if outline else 0)


def card(img: Image.Image, box: Sequence[int], radius: int = 16, *,
         fill: str = CARD, outline: str = LINE, soft: bool = True) -> None:
    if soft:
        shadow(img, box, radius=radius)
    rrect(img, box, radius, fill=fill, outline=outline)


def line(img: Image.Image, xy: Sequence[int], fill: str = LINE, width: int = 1) -> None:
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = xy
    d.line((x0 * S, y0 * S, x1 * S, y1 * S), fill=fill, width=max(1, width * S))


def text(img: Image.Image, xy: Sequence[int], s: str, size: int = 16,
         fill: str = INK, *, bold: bool = False, mono: bool = False,
         anchor: str = "la") -> None:
    d = ImageDraw.Draw(img)
    x, y = xy
    d.text((x * S, y * S), s, font=font(size, bold=bold, mono=mono), fill=fill, anchor=anchor)


def width_of(s: str, size: int, *, bold: bool = False, mono: bool = False) -> float:
    f = font(size, bold=bold, mono=mono)
    return f.getlength(s) / S


def chip(img: Image.Image, xy: Sequence[int], s: str, *, size: int = 14,
         fg: str = BRAND_DEEP, bg: str = BRAND_SOFT, pad_x: int = 10, h: int = 26,
         mono: bool = False, bold: bool = True) -> tuple[int, int]:
    x, y = xy
    w = width_of(s, size, bold=bold, mono=mono) + pad_x * 2
    rrect(img, (x, y, x + w, y + h), radius=h // 2, fill=bg, outline=None)
    text(img, (x + pad_x, y + h / 2), s, size, fg, bold=bold, mono=mono, anchor="lm")
    return int(x + w), int(y + h)


def arrow(img: Image.Image, p0: Sequence[float], p1: Sequence[float], *,
          fill: str = "#B7C0CA", width: int = 2, head: int = 9) -> None:
    d = ImageDraw.Draw(img)
    x0, y0 = p0
    x1, y1 = p1
    ang = math.atan2(y1 - y0, x1 - x0)
    bx, by = x1 - math.cos(ang) * head * 1.4, y1 - math.sin(ang) * head * 1.4
    d.line((x0 * S, y0 * S, bx * S, by * S), fill=fill, width=max(1, width * S))
    left = (ang + math.pi - 0.45, ang + math.pi + 0.45)
    pts = [(x1 * S, y1 * S)] + [
        ((x1 + math.cos(a) * head * 1.9) * S, (y1 + math.sin(a) * head * 1.9) * S)
        for a in left
    ]
    d.polygon(pts, fill=fill)


def dashed(img: Image.Image, box: Sequence[int], radius: int = 12, *,
           fill: str = "#CBD3DB", width: int = 2, dash: int = 7, gap: int = 6) -> None:
    """Dashed rounded rectangle border (approximated with short line segments)."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    r = radius

    def seg_h(xa: float, xb: float, y: float) -> None:
        x = xa
        while x < xb:
            d.line((x * S, y * S, min(x + dash, xb) * S, y * S), fill=fill, width=width * S)
            x += dash + gap

    def seg_v(ya: float, yb: float, x: float) -> None:
        y = ya
        while y < yb:
            d.line((x * S, y * S, x * S, min(y + dash, yb) * S), fill=fill, width=width * S)
            y += dash + gap

    seg_h(x0 + r, x1 - r, y0)
    seg_h(x0 + r, x1 - r, y1)
    seg_v(y0 + r, y1 - r, x0)
    seg_v(y0 + r, y1 - r, x1)
    d.arc((x0 * S, y0 * S, (x0 + 2 * r) * S, (y0 + 2 * r) * S), 180, 270, fill=fill, width=width * S)
    d.arc(((x1 - 2 * r) * S, y0 * S, x1 * S, (y0 + 2 * r) * S), 270, 360, fill=fill, width=width * S)
    d.arc((x0 * S, (y1 - 2 * r) * S, (x0 + 2 * r) * S, y1 * S), 90, 180, fill=fill, width=width * S)
    d.arc(((x1 - 2 * r) * S, (y1 - 2 * r) * S, x1 * S, y1 * S), 0, 90, fill=fill, width=width * S)


def badge_icon(img: Image.Image, cx: float, cy: float, r: float = 13,
               fill: str = BRAND, glyph: str = "¥") -> None:
    d = ImageDraw.Draw(img)
    d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), fill=fill)
    text(img, (cx, cy), glyph, int(r * 1.35), "#FFFFFF", bold=True, anchor="mm")


def save(img: Image.Image, path: str, final: tuple[int, int]) -> str:
    img.resize(final, Image.LANCZOS).save(path, optimize=True)
    return path


def ease_out(p: float) -> float:
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


def money(v: float) -> str:
    return f"¥{v:,.2f}"
