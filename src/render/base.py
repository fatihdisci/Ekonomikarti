"""Rendering primitives: font loader, Turkish formatting, drawing utilities."""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.config import COLORS, COLORS_RGBA, FONT_DIR, FONTS, HASHTAG, LAYOUT, TR_MONTHS, TR_WEEKDAYS


@lru_cache(maxsize=64)
def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
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


def color_rgba(name: str) -> tuple[int, int, int, int]:
    return COLORS_RGBA[name]


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def change_color(value: float) -> str:
    return color("positive") if value >= 0 else color("negative")


def format_tr(value: float, decimals: int) -> str:
    if decimals < 0:
        raise ValueError("decimals must be >= 0")
    negative = value < 0
    formatted = f"{abs(value):.{decimals}f}"
    if "." in formatted:
        int_part, frac_part = formatted.split(".")
    else:
        int_part, frac_part = formatted, ""
    grouped = ""
    for i, ch in enumerate(reversed(int_part)):
        if i > 0 and i % 3 == 0:
            grouped = "." + grouped
        grouped = ch + grouped
    out = grouped if not frac_part else f"{grouped},{frac_part}"
    return f"-{out}" if negative else out


def format_pct(value: float) -> str:
    decimals = 0 if abs(value) >= 100 else 2
    body = format_tr(abs(value), decimals)
    sign = "+" if value >= 0 else "-"
    return f"{sign}{body}%"


def arrow_for(value: float) -> str:
    return "▲" if value >= 0 else "▼"


def format_tr_date(d: date) -> str:
    return f"{d.day} {TR_MONTHS[d.month - 1]} {d.year}, {TR_WEEKDAYS[d.weekday()]}"


def text_size(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_lines(
    font: ImageFont.FreeTypeFont,
    text: str,
    max_width: int,
    max_lines: int = 3,
) -> list[str]:
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
        last = lines[-1]
        while last and text_size(font, last + "…")[0] > max_width:
            last = last[:-1].rstrip()
        lines[-1] = (last + "…") if last else "…"
    return lines


def _composite(
    img: Image.Image,
    draw_fn,
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(overlay))
    result = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    return result, ImageDraw.Draw(result)


def composite_rect(
    img: Image.Image,
    bbox: tuple[int, int, int, int],
    fill_rgba: tuple[int, int, int, int] | None = None,
    outline_rgba: tuple[int, int, int, int] | None = None,
    radius: int = 18,
    width: int = 1,
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    def _draw(d: ImageDraw.ImageDraw) -> None:
        if fill_rgba:
            d.rounded_rectangle(bbox, radius=radius, fill=fill_rgba)
        if outline_rgba:
            d.rounded_rectangle(bbox, radius=radius, outline=outline_rgba, width=width)
    return _composite(img, _draw)


def new_canvas() -> Image.Image:
    return Image.new("RGB", (LAYOUT.canvas_w, LAYOUT.canvas_h), color("bg"))


def draw_brand_header(
    draw: ImageDraw.ImageDraw,
    target_date: date,
) -> None:
    """Sade üst bant: sol 'FİYAT HAFIZASI' (sarı), sağ tarih."""
    PAD_X = LAYOUT.padding_x
    Y = 60

    brand_font = load_font("inter_bold", 32)
    draw.text((PAD_X, Y), "FİYAT HAFIZASI", fill=color("accent"), font=brand_font)

    date_font = load_font("mono_medium", 20)
    date_str = f"{target_date.day} {TR_MONTHS[target_date.month - 1]} {target_date.year}, {TR_WEEKDAYS[target_date.weekday()]}"
    dw, dh = text_size(date_font, date_str)
    bw, bh = text_size(brand_font, "FİYAT HAFIZASI")
    # baseline'ı eşitle: brand metnin alt kenarına hizala
    draw.text(
        (LAYOUT.canvas_w - PAD_X - dw, Y + (bh - dh)),
        date_str,
        fill=color("muted"),
        font=date_font,
    )


def draw_card_title(
    draw: ImageDraw.ImageDraw,
    title: str,
    subtitle: str,
    y: int = 180,
) -> int:
    """Ortalanmış büyük başlık + altyazı. Altyazının alt y'sini döner."""
    title_font = load_font("inter_bold", 70)
    sub_font = load_font("inter_regular", 22)

    tw, th = text_size(title_font, title)
    draw.text(((LAYOUT.canvas_w - tw) // 2, y), title, fill=color("text"), font=title_font)

    sy = y + th + 14
    sw, sh = text_size(sub_font, subtitle)
    draw.text(((LAYOUT.canvas_w - sw) // 2, sy), subtitle, fill=color("muted"), font=sub_font)
    return sy + sh


def draw_footer(
    draw: ImageDraw.ImageDraw,
    note: str,
    note_top_y: int,
) -> None:
    """Note + 'Kaynak: Yahoo Finance' (sol) + '#fiyathafizasi' sarı (sağ).

    note_top_y: küçük dekoratif çizginin başlayacağı y (notun üstü).
    """
    W = LAYOUT.canvas_w
    PAD_X = LAYOUT.padding_x

    # Küçük orta divider
    div_w = 80
    draw.line(
        [((W - div_w) // 2, note_top_y), ((W + div_w) // 2, note_top_y)],
        fill=color("divider"),
        width=2,
    )

    if note:
        note_font = load_font("inter_regular", 22)
        max_w = W - 2 * PAD_X - 60
        lines = wrap_lines(note_font, note, max_width=max_w, max_lines=3)
        line_h = note_font.getbbox("Ay")[3] + 14
        ny = note_top_y + 36
        for i, line in enumerate(lines):
            lw, _ = text_size(note_font, line)
            draw.text(((W - lw) // 2, ny + i * line_h), line, fill=color("muted"), font=note_font)

    meta_f = load_font("mono_medium", 14)
    meta_y = LAYOUT.canvas_h - 56
    draw.text((PAD_X, meta_y), "Kaynak: Yahoo Finance", fill=color("dim"), font=meta_f)
    hw, _ = text_size(meta_f, HASHTAG)
    draw.text((W - PAD_X - hw, meta_y), HASHTAG, fill=color("accent"), font=meta_f)
