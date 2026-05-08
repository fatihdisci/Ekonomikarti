"""Highlight card renderer — HAFTANIN ÖZETİ (referans tasarıma göre)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import ImageDraw

from src.config import LAYOUT
from src.render.base import (
    arrow_for,
    change_color,
    color,
    composite_rect,
    draw_brand_header,
    draw_card_title,
    draw_footer,
    format_pct,
    format_tr,
    hex_to_rgb,
    load_font,
    new_canvas,
    text_size,
)


def _draw_tile(
    img,
    draw,
    bbox: tuple[int, int, int, int],
    label: str,
    name: str,
    pct: float,
    value: float,
    unit: str,
    decimals: int,
):
    x0, y0, x1, y1 = bbox
    img, draw = composite_rect(
        img,
        [x0, y0, x1, y1],
        fill_rgba=(*hex_to_rgb(color("surface")), 255),
        radius=24,
    )
    W = LAYOUT.canvas_w

    label_font = load_font("mono_medium", 16)
    lw, lh = text_size(label_font, label)
    draw.text(((W - lw) // 2, y0 + 50), label, fill=color("muted"), font=label_font)

    name_font = load_font("inter_bold", 56)
    nm = name.upper()
    nw, nh = text_size(name_font, nm)
    draw.text(((W - nw) // 2, y0 + 90), nm, fill=color("text"), font=name_font)

    big_pct_font = load_font("inter_bold", 92)
    ptxt = format_pct(pct)
    arrow = arrow_for(pct)
    pw, ph = text_size(big_pct_font, ptxt)
    aw, ah = text_size(big_pct_font, arrow)
    gap = 24
    total = aw + gap + pw
    sx = (W - total) // 2
    sy = y0 + 180
    c = change_color(pct)
    draw.text((sx, sy), arrow, fill=c, font=big_pct_font)
    draw.text((sx + aw + gap, sy), ptxt, fill=c, font=big_pct_font)

    sub_font = load_font("mono_medium", 18)
    sub = f"{format_tr(value, decimals)} {unit}"
    sw, sh = text_size(sub_font, sub)
    draw.text(((W - sw) // 2, sy + ph + 20), sub, fill=color("muted"), font=sub_font)
    return img, draw


def render_highlight(payload: dict[str, Any], out_path: Path) -> None:
    target_date = datetime.fromisoformat(payload["date"]).date()
    star = payload.get("star")
    loser = payload.get("loser")

    img = new_canvas()
    draw = ImageDraw.Draw(img)

    draw_brand_header(draw, target_date)
    draw_card_title(draw, "HAFTANIN ÖZETİ", "Yıldız ve Kaybeden", y=180)

    PAD_X = LAYOUT.padding_x
    W = LAYOUT.canvas_w
    x0, x1 = PAD_X, W - PAD_X

    tile_h = 360
    tile_gap = 22
    tile_top = 360

    if star:
        img, draw = _draw_tile(
            img, draw,
            (x0, tile_top, x1, tile_top + tile_h),
            "HAFTANIN YILDIZI",
            star["name"],
            star.get("weekly_pct", 0.0) or 0.0,
            star["current"],
            star.get("unit", ""),
            star.get("decimals", 2),
        )

    second_y = tile_top + tile_h + tile_gap
    if loser:
        img, draw = _draw_tile(
            img, draw,
            (x0, second_y, x1, second_y + tile_h),
            "HAFTANIN KAYBEDENİ",
            loser["name"],
            loser.get("weekly_pct", 0.0) or 0.0,
            loser["current"],
            loser.get("unit", ""),
            loser.get("decimals", 2),
        )

    note_top_y = max(second_y + tile_h + 24, 1140)
    draw_footer(draw, payload.get("note", "") or "", note_top_y=note_top_y)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
