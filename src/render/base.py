"""Rendering primitives: font loader, Turkish number formatting, arrow glyphs."""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

from src.config import COLORS, FONT_DIR, FONTS, TR_MONTHS, TR_WEEKDAYS


@lru_cache(maxsize=64)
def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Yazı tipi dosyasını yükle ve cache'le.

    `name` is a key from `src.config.FONTS`.
    """
    spec = FONTS.get(name)
    if spec is None:
        raise KeyError(f"unknown font: {name}")
    path = Path(FONT_DIR) / spec.filename
    if not path.exists():
        raise FileNotFoundError(
            f"Font dosyası bulunamadı: {path}. "
            "scripts/download_fonts.py betiğini çalıştırın."
        )
    return ImageFont.truetype(str(path), size)


def color(name: str) -> str:
    return COLORS[name]


def format_tr(value: float, decimals: int) -> str:
    """Türkçe sayı formatı: '.' binlik, ',' ondalık ayraç.

    >>> format_tr(1234.56, 2)
    '1.234,56'
    >>> format_tr(38.4521, 4)
    '38,4521'
    >>> format_tr(-1234567.0, 0)
    '-1.234.567'
    """
    if decimals < 0:
        raise ValueError("decimals must be >= 0")
    negative = value < 0
    n = abs(value)
    # Quantise to requested precision before splitting.
    formatted = f"{n:.{decimals}f}"
    if "." in formatted:
        int_part, frac_part = formatted.split(".")
    else:
        int_part, frac_part = formatted, ""
    # Group integer part with periods from the right.
    grouped = ""
    for i, ch in enumerate(reversed(int_part)):
        if i > 0 and i % 3 == 0:
            grouped = "." + grouped
        grouped = ch + grouped
    out = grouped if not frac_part else f"{grouped},{frac_part}"
    return f"-{out}" if negative else out


def format_pct(value: float) -> str:
    """Yüzdelik formatla: işaret zorunlu, |değer| >= 100 ise ondalık yok.

    >>> format_pct(0.42)
    '+0,42%'
    >>> format_pct(-3.15)
    '-3,15%'
    >>> format_pct(425.3)
    '+425%'
    >>> format_pct(-100.0)
    '-100%'
    """
    decimals = 0 if abs(value) >= 100 else 2
    body = format_tr(abs(value), decimals)
    sign = "+" if value >= 0 else "-"
    return f"{sign}{body}%"


def arrow_for(value: float) -> str:
    """Pozitif değer için ▲, negatif için ▼."""
    return "▲" if value >= 0 else "▼"


def change_color(value: float) -> str:
    return color("positive") if value >= 0 else color("negative")


def format_tr_date(d: date) -> str:
    """Tarihi Türkçe biçimde döndür: '5 Mayıs 2026, Salı'."""
    return f"{d.day} {TR_MONTHS[d.month - 1]} {d.year}, {TR_WEEKDAYS[d.weekday()]}"


def text_size(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    """Bir metin parçasının (genişlik, yükseklik) ölçüsü."""
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_lines(font: ImageFont.FreeTypeFont, text: str, max_width: int, max_lines: int = 2) -> list[str]:
    """Metni belirtilen genişliğe sığacak satırlara böl. En çok `max_lines` satır."""
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = current + " " + word
        if text_size(font, candidate)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
            if len(lines) >= max_lines:
                break
    if len(lines) < max_lines:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        # Ellipsise the last line if we truncated.
        last = lines[-1]
        while last and text_size(font, last + "…")[0] > max_width:
            last = last[:-1].rstrip()
        lines[-1] = (last + "…") if last else "…"
    return lines
