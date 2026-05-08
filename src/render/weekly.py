"""Weekly card renderer — HAFTALIK ÖZET (referans tasarıma göre)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import ImageDraw

from src.config import INDICATOR_ORDER, LAYOUT
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


def render_weekly(payload: dict[str, Any], out_path: Path) -> None:
    target_date = datetime.fromisoformat(payload["date"]).date()
    indicators = {ind["key"]: ind for ind in payload.get("indicators", [])}

    img = new_canvas()
    draw = ImageDraw.Draw(img)

    draw_brand_header(draw, target_date)
    draw_card_title(draw, "HAFTALIK ÖZET", "Pazartesi → Cuma", y=180)

    PAD_X = LAYOUT.padding_x
    W = LAYOUT.canvas_w
    x0, x1 = PAD_X, W - PAD_X

    rows_top = 360
    row_h = 130
    row_gap = 12

    name_font = load_font("inter_semibold", 26)
    val_font = load_font("inter_bold", 38)
    unit_font = load_font("inter_regular", 22)
    label_font = load_font("mono_medium", 14)
    pct_font = load_font("mono_medium", 26)

    for i, key in enumerate(INDICATOR_ORDER):
        ind = indicators.get(key)
        if ind is None:
            continue
        ry = rows_top + i * (row_h + row_gap)
        img, draw = composite_rect(
            img,
            [x0, ry, x1, ry + row_h],
            fill_rgba=(*hex_to_rgb(color("surface")), 255),
            radius=22,
        )

        nx = x0 + 30
        draw.text((nx, ry + 22), ind["name"], fill=color("muted"), font=name_font)
        v_str = format_tr(ind["current"], ind["decimals"])
        unit = ind.get("unit", "")
        vy = ry + 22 + 32
        draw.text((nx, vy), v_str, fill=color("text"), font=val_font)
        vw, vh = text_size(val_font, v_str)
        uw, uh = text_size(unit_font, unit)
        draw.text((nx + vw + 12, vy + (vh - uh) - 2), unit, fill=color("text"), font=unit_font)

        # sağ üst: BU HAFTA
        bh_text = "BU HAFTA"
        bw, bhh = text_size(label_font, bh_text)
        draw.text((x1 - 30 - bw, ry + 22), bh_text, fill=color("muted"), font=label_font)

        # sağ alt: yüzde
        wp = ind.get("weekly_pct")
        if wp is not None:
            ptxt = f"{arrow_for(wp)}  {format_pct(wp)}"
            pw, ph = text_size(pct_font, ptxt)
            draw.text(
                (x1 - 30 - pw, ry + row_h - 18 - ph),
                ptxt,
                fill=change_color(wp),
                font=pct_font,
            )

    rows_bottom = rows_top + len(INDICATOR_ORDER) * (row_h + row_gap)
    note_top_y = max(rows_bottom + 24, 1100)
    draw_footer(draw, payload.get("note", "") or "", note_top_y=note_top_y)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
