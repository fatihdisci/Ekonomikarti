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


# ─── Color helpers ────────────────────────────────────────────────────────────

def color(name: str) -> str:
    return COLORS[name]


def color_rgba(name: str) -> tuple[int, int, int, int]:
    return COLORS_RGBA[name]


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def change_color(value: float) -> str:
    return color("positive") if value >= 0 else color("negative")


def change_color_rgba(value: float) -> tuple[int, int, int, int]:
    return color_rgba("pos_dim") if value >= 0 else color_rgba("neg_dim")


# ─── Formatting ───────────────────────────────────────────────────────────────

def format_tr(value: float, decimals: int) -> str:
    """Türkçe sayı formatı: '.' binlik ayraç, ',' ondalık.

    >>> format_tr(1234.56, 2)
    '1.234,56'
    >>> format_tr(38.4521, 4)
    '38,4521'
    """
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
    """Yüzdelik: |değer| ≥ 100 ise ondalık yok; işaret zorunlu.

    >>> format_pct(0.42)
    '+0,42%'
    >>> format_pct(425.3)
    '+425%'
    """
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
    max_lines: int = 2,
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


# ─── RGBA compositing ─────────────────────────────────────────────────────────

def _composite(
    img: Image.Image,
    draw_fn,
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Run draw_fn on a transparent overlay, composite onto img."""
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
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    def _draw(d: ImageDraw.ImageDraw) -> None:
        if fill_rgba:
            d.rounded_rectangle(bbox, radius=radius, fill=fill_rgba)
        if outline_rgba:
            d.rounded_rectangle(bbox, radius=radius, outline=outline_rgba, width=1)

    return _composite(img, _draw)


def composite_poly(
    img: Image.Image,
    points: list[tuple[float, float]],
    fill_rgba: tuple[int, int, int, int],
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    int_pts = [(int(x), int(y)) for x, y in points]

    def _draw(d: ImageDraw.ImageDraw) -> None:
        d.polygon(int_pts, fill=fill_rgba)

    return _composite(img, _draw)


# ─── Drawing primitives ───────────────────────────────────────────────────────

def draw_corner_marks(
    draw: ImageDraw.ImageDraw,
    w: int = LAYOUT.canvas_w,
    h: int = LAYOUT.canvas_h,
    pad: int = 30,
    size: int = 14,
) -> None:
    c = color("dim")
    # top-left
    draw.line([(pad, pad), (pad + size, pad)], fill=c, width=1)
    draw.line([(pad, pad), (pad, pad + size)], fill=c, width=1)
    # top-right
    draw.line([(w - pad - size, pad), (w - pad, pad)], fill=c, width=1)
    draw.line([(w - pad, pad), (w - pad, pad + size)], fill=c, width=1)
    # bottom-left
    draw.line([(pad, h - pad), (pad + size, h - pad)], fill=c, width=1)
    draw.line([(pad, h - pad - size), (pad, h - pad)], fill=c, width=1)
    # bottom-right
    draw.line([(w - pad - size, h - pad), (w - pad, h - pad)], fill=c, width=1)
    draw.line([(w - pad, h - pad - size), (w - pad, h - pad)], fill=c, width=1)


def draw_grid_lines(
    img: Image.Image,
    spacing: int = 90,
    alpha: int = 15,
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    c = (255, 255, 255, alpha)
    for x in range(0, w, spacing):
        d.line([(x, 0), (x, h)], fill=c, width=1)
    for y in range(0, h, spacing):
        d.line([(0, y), (w, y)], fill=c, width=1)
    result = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    return result, ImageDraw.Draw(result)


def draw_sparkline(
    draw: ImageDraw.ImageDraw,
    values: list[float],
    x: int,
    y: int,
    w: int,
    h: int,
    line_color: str,
    pad: int = 4,
    line_width: int = 2,
    dot: bool = True,
) -> None:
    if not values or len(values) < 2:
        return
    min_v = min(values)
    max_v = max(values)
    rng = max_v - min_v or 1.0
    step_x = (w - pad * 2) / (len(values) - 1)
    pts = []
    for i, val in enumerate(values):
        px = x + pad + i * step_x
        py = y + pad + (h - pad * 2) - ((val - min_v) / rng) * (h - pad * 2)
        pts.append((px, py))
    draw.line(pts, fill=line_color, width=line_width, joint="curve")
    if dot:
        lx, ly = int(pts[-1][0]), int(pts[-1][1])
        r = line_width + 2
        draw.ellipse([lx - r, ly - r, lx + r, ly + r], fill=line_color)


def draw_sparkline_with_area(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    values: list[float],
    x: int,
    y: int,
    w: int,
    h: int,
    line_color: str,
    pad: int = 4,
    line_width: int = 2,
    area_alpha: int = 50,
    dot: bool = True,
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    if not values or len(values) < 2:
        return img, draw
    min_v = min(values)
    max_v = max(values)
    rng = max_v - min_v or 1.0
    step_x = (w - pad * 2) / (len(values) - 1)
    pts = []
    for i, val in enumerate(values):
        px = x + pad + i * step_x
        py = y + pad + (h - pad * 2) - ((val - min_v) / rng) * (h - pad * 2)
        pts.append((px, py))

    # Area polygon (close at bottom)
    area_pts = list(pts) + [(x + w - pad, y + h - pad), (x + pad, y + h - pad)]
    r, g, b = hex_to_rgb(line_color)
    img, draw = composite_poly(img, area_pts, (r, g, b, area_alpha))

    draw.line(pts, fill=line_color, width=line_width, joint="curve")
    if dot:
        lx, ly = int(pts[-1][0]), int(pts[-1][1])
        rd = line_width + 2
        draw.ellipse([lx - rd, ly - rd, lx + rd, ly + rd], fill=line_color)
    return img, draw


def draw_range_bar(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    pct: float,
    track_color: str | None = None,
    dot_color: str | None = None,
) -> None:
    tc = track_color or color("surface")
    dc = dot_color or color("accent")
    draw.rounded_rectangle([x, y + h // 2 - 2, x + w, y + h // 2 + 2], radius=2, fill=tc)
    dot_x = int(x + pct / 100 * w)
    r = h // 2
    draw.ellipse([dot_x - r, y, dot_x + r, y + h], fill=dc)


# ─── Shared card sections ─────────────────────────────────────────────────────

def draw_header(
    img: Image.Image,
    target_date: date,
    slot: str,
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Premium header: ₺ brand logo (left) + slot badge + date (right)."""
    PAD_X = LAYOUT.padding_x
    TOP_Y = 58

    # ── ₺ icon box ──────────────────────────────────────────────────────────
    ICON = 42
    accent_rgb = hex_to_rgb(color("accent"))
    img, draw = composite_rect(
        img,
        [PAD_X, TOP_Y, PAD_X + ICON, TOP_Y + ICON],
        fill_rgba=(*accent_rgb, 255),
        radius=10,
    )
    tl_font = load_font("inter_bold", 24)
    tl_text = "₺"
    tw, th = text_size(tl_font, tl_text)
    draw.text(
        (PAD_X + (ICON - tw) // 2, TOP_Y + (ICON - th) // 2 - 1),
        tl_text,
        fill="#0B0F1E",
        font=tl_font,
    )

    # ── Brand text ───────────────────────────────────────────────────────────
    bf = load_font("inter_bold", 16)
    mf = load_font("mono_medium", 11)
    bx = PAD_X + ICON + 14
    draw.text((bx, TOP_Y + 2), "FİYAT HAFIZASI", fill=color("text"), font=bf)
    draw.text((bx, TOP_Y + 24), "SINCE · 2024", fill=color("dim"), font=mf)

    # ── Slot badge (right) ───────────────────────────────────────────────────
    sf = load_font("mono_medium", 11)
    sw, sh = text_size(sf, slot)
    bpad_x, bpad_y = 10, 5
    badge_w = sw + bpad_x * 2
    badge_h = sh + bpad_y * 2
    badge_x = LAYOUT.canvas_w - PAD_X - badge_w
    badge_y = TOP_Y

    img, draw = composite_rect(
        img,
        [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
        fill_rgba=(*accent_rgb, 13),
        outline_rgba=(*accent_rgb, 90),
        radius=20,
    )
    draw.text((badge_x + bpad_x, badge_y + bpad_y), slot, fill=color("accent"), font=sf)

    # ── Date line ────────────────────────────────────────────────────────────
    df = load_font("mono_medium", 13)
    date_str = f"{target_date.day} {TR_MONTHS[target_date.month - 1]} {target_date.year}"
    weekday = TR_WEEKDAYS[target_date.weekday()]
    date_text = f"{date_str} · "
    dt_w, _ = text_size(df, date_text)
    wd_w, _ = text_size(df, weekday)
    date_y = badge_y + badge_h + 6
    right_x = LAYOUT.canvas_w - PAD_X
    draw.text((right_x - dt_w - wd_w, date_y), date_text, fill=color("muted"), font=df)
    draw.text((right_x - wd_w, date_y), weekday, fill=color("text"), font=df)

    return img, draw


def draw_eyebrow(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    no: str,
    label: str,
) -> int:
    """Returns bottom y of eyebrow."""
    nf = load_font("mono_medium", 11)
    lf = load_font("inter_semibold", 11)
    nw, nh = text_size(nf, no)
    draw.text((x, y), no, fill=color("dim"), font=nf)
    line_x = x + nw + 12
    draw.line([(line_x, y + nh // 2), (line_x + 24, y + nh // 2)], fill=color("dim"), width=1)
    draw.text((line_x + 36, y), label.upper(), fill=color("muted"), font=lf)
    return y + nh


def draw_footer(
    draw: ImageDraw.ImageDraw,
    note: str,
    footer_y: int | None = None,
) -> None:
    if footer_y is None:
        footer_y = LAYOUT.header_h + LAYOUT.title_h + LAYOUT.table_h
    W = LAYOUT.canvas_w
    PAD_X = LAYOUT.padding_x

    # Gradient divider (approximated as a wide faint line)
    draw.line(
        [(W // 2 - 180, footer_y), (W // 2 + 180, footer_y)],
        fill=color("divider"),
        width=1,
    )

    if note:
        note_font = load_font("inter_regular", 17)
        note_y = footer_y + 32
        max_w = W - 2 * PAD_X
        lines = wrap_lines(note_font, note, max_width=max_w, max_lines=3)
        line_h = note_font.getbbox("Ay")[3] + 10
        for i, line in enumerate(lines):
            lw, _ = text_size(note_font, line)
            draw.text(((W - lw) // 2, note_y + i * line_h), line, fill=color("muted"), font=note_font)

    meta_f = load_font("mono_medium", 11)
    meta_y = LAYOUT.canvas_h - 52
    draw.text((PAD_X, meta_y), "SOURCE · YAHOO FINANCE", fill=color("dim"), font=meta_f)
    hw, _ = text_size(meta_f, HASHTAG.upper())
    draw.rounded_rectangle(
        [W - PAD_X - hw - 20, meta_y - 4, W - PAD_X, meta_y + meta_f.getbbox("A")[3] + 4],
        radius=4,
        outline=color_rgba("accent_dim"),
        width=1,
    )
    draw.text((W - PAD_X - hw - 10, meta_y), HASHTAG.upper(), fill=color("accent"), font=meta_f)
