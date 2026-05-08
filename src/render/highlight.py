"""Sunday "Haftanın Yıldızı/Kaybedeni" renderer: side-by-side VS tiles."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from src.config import LAYOUT
from src.render.base import (
    arrow_for,
    change_color,
    change_color_rgba,
    color,
    color_rgba,
    composite_rect,
    draw_corner_marks,
    draw_eyebrow,
    draw_footer,
    draw_header,
    draw_sparkline_with_area,
    format_pct,
    format_tr,
    hex_to_rgb,
    load_font,
    text_size,
    wrap_lines,
)

_PAD = LAYOUT.padding_x
_W   = LAYOUT.canvas_w
_H   = LAYOUT.canvas_h
_TBL = LAYOUT.header_h + LAYOUT.title_h  # 290


def _draw_title(draw: ImageDraw.ImageDraw) -> None:
    ty = LAYOUT.header_h + 14
    draw_eyebrow(draw, _PAD, ty, "05", "Hafta Sonu · Yıldız & Kaybeden")
    h1f = load_font("inter_bold", 58)
    _, lh = text_size(h1f, "A")
    draw.text((_PAD, ty + 22), "Haftanın iki", fill=color("text"), font=h1f)
    draw.text((_PAD, ty + 22 + int(lh * 0.95) + 4), "yüzü.", fill=color("text"), font=h1f)


def _draw_tile(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    item: dict[str, Any] | None,
    tile_type: str,  # "star" or "loser"
    x: int,
    y: int,
    w: int,
    h: int,
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    is_star = tile_type == "star"
    tile_color = color("positive") if is_star else color("negative")
    tint_rgba = change_color_rgba(1.0 if is_star else -1.0)

    # Base surface
    s = color("surface")
    img, draw = composite_rect(
        img, [x, y, x + w, y + h],
        fill_rgba=(*hex_to_rgb(s), 255), radius=20,
    )
    # Tint overlay (gradient-like)
    img, draw = composite_rect(
        img, [x, y, x + w, y + h],
        fill_rgba=tint_rgba, radius=20,
    )
    # Border
    bc = hex_to_rgb(tile_color)
    img, draw = composite_rect(
        img, [x, y, x + w, y + h],
        outline_rgba=(*bc, 90), radius=20,
    )

    ix = x + 30
    iy = y + 30

    # ── Header badge ──────────────────────────────────────────────────────────
    badge_sym = "★" if is_star else "↓"
    badge_f = load_font("inter_bold", 16)
    label = "HAFTANIN YILDIZI" if is_star else "HAFTANIN KAYBEDENİ"
    label_f = load_font("mono_medium", 11)

    bs = 28
    b_rgb = hex_to_rgb(tile_color)
    img, draw = composite_rect(
        img, [ix, iy, ix + bs, iy + bs],
        fill_rgba=(*b_rgb, 255), radius=8,
    )
    bsw, bsh = text_size(badge_f, badge_sym)
    draw.text((ix + (bs - bsw) // 2, iy + (bs - bsh) // 2), badge_sym, fill="#0B0F1E", font=badge_f)
    draw.text((ix + bs + 12, iy + (bs - text_size(label_f, label)[1]) // 2), label, fill=tile_color, font=label_f)

    if item is None:
        return img, draw

    # ── Indicator name ────────────────────────────────────────────────────────
    name_f = load_font("inter_bold", 40)
    name = item.get("name", "")
    draw.text((ix, iy + bs + 16), name, fill=color("text"), font=name_f)

    # Current value
    decimals = int(item.get("decimals", 2))
    current = float(item["current"])
    unit = item.get("unit", "")
    val_str = f"{format_tr(current, decimals)} {unit}".strip()
    valf = load_font("mono_medium", 14)
    draw.text((ix, iy + bs + 16 + text_size(name_f, name)[1] + 8), val_str, fill=color("muted"), font=valf)

    # ── Sparkline ─────────────────────────────────────────────────────────────
    spark = item.get("sparkline") or []
    SPARK_Y_OFFSET = iy + bs + 16 + text_size(name_f, name)[1] + 36
    SPARK_W = w - 60
    SPARK_H = 72

    if spark:
        img, draw = draw_sparkline_with_area(
            img, draw, spark,
            ix, SPARK_Y_OFFSET, SPARK_W, SPARK_H,
            tile_color, pad=4, line_width=2, area_alpha=45,
        )

    day_f = load_font("mono_medium", 10)
    days = ["PZT", "SAL", "ÇAR", "PER", "CUM"]
    n = min(len(spark), len(days))
    if n > 1:
        step = SPARK_W // (n - 1)
        for j in range(n):
            draw.text((ix + j * step, SPARK_Y_OFFSET + SPARK_H + 4), days[j], fill=color("dim"), font=day_f)

    # ── Weekly pct ────────────────────────────────────────────────────────────
    weekly = item.get("weekly_pct")
    if weekly is not None:
        sep_y = SPARK_Y_OFFSET + SPARK_H + 22
        draw.line([(ix, sep_y), (ix + SPARK_W, sep_y)], fill=color_rgba("border")[:3], width=1)
        lbl_f = load_font("mono_medium", 10)
        draw.text((ix, sep_y + 10), "HAFTALIK", fill=color("dim"), font=lbl_f)

        wf = load_font("mono_bold", 60)
        af = load_font("inter_bold", 28)
        wv = float(weekly)
        wstr = format_pct(wv)
        astr = arrow_for(wv)
        aw, ah = text_size(af, astr)
        draw.text((ix, sep_y + 28), astr, fill=tile_color, font=af)
        draw.text((ix + aw + 10, sep_y + 22), wstr, fill=tile_color, font=wf)

    return img, draw


def _parse_target_date(payload: dict[str, Any]) -> date:
    raw = payload.get("date")
    if isinstance(raw, str):
        return datetime.strptime(raw, "%Y-%m-%d").date()
    return date.today()


def render_highlight(payload: dict[str, Any], output_path: Path) -> Path:
    """Pazar 'Haftanın Yıldızı/Kaybedeni' kartını üret."""
    target_date = _parse_target_date(payload)
    star = payload.get("star")
    loser = payload.get("loser")
    note = payload.get("note") or ""

    img = Image.new("RGB", (_W, _H), color=color("bg"))
    draw = ImageDraw.Draw(img)

    draw_corner_marks(draw)
    img, draw = draw_header(img, target_date, "WEEKEND · PAZAR")
    _draw_title(draw)

    # Vertical tiles (full-width stacked, not side-by-side, to stay on 1080px)
    START_Y = _TBL + 16
    table_end = LAYOUT.header_h + LAYOUT.title_h + LAYOUT.table_h
    avail = table_end - START_Y
    TILE_H = (avail - 20) // 2
    TILE_W = _W - 2 * _PAD

    img, draw = _draw_tile(img, draw, star,  "star",  _PAD, START_Y,             TILE_W, TILE_H)
    img, draw = _draw_tile(img, draw, loser, "loser", _PAD, START_Y + TILE_H + 20, TILE_W, TILE_H)

    draw_footer(draw, note)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG", optimize=True)
    return output_path
