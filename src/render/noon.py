"""Noon card renderer — ODAK KARTI (referans tasarıma göre)."""

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


def render_noon(payload: dict[str, Any], out_path: Path) -> None:
    target_date = datetime.fromisoformat(payload["date"]).date()
    focus = payload["focus"]

    img = new_canvas()
    draw = ImageDraw.Draw(img)

    draw_brand_header(draw, target_date)
    draw_card_title(draw, "ODAK KARTI", "Tarihsel Bakış", y=180)

    PAD_X = LAYOUT.padding_x
    W = LAYOUT.canvas_w

    main_x0, main_x1 = PAD_X, W - PAD_X
    main_y0 = 360
    main_h = 320
    main_y1 = main_y0 + main_h

    img, draw = composite_rect(
        img,
        [main_x0, main_y0, main_x1, main_y1],
        fill_rgba=(*hex_to_rgb(color("surface")), 255),
        radius=24,
    )

    name_font = load_font("inter_bold", 38)
    name = focus["name"]
    nw, nh = text_size(name_font, name)
    name_y = main_y0 + 80
    draw.text(((W - nw) // 2, name_y), name, fill=color("muted"), font=name_font)

    val_font = load_font("inter_bold", 96)
    unit_font = load_font("inter_regular", 50)
    val_str = format_tr(focus["current"], focus["decimals"])
    unit_str = focus.get("unit", "")
    vw, vh = text_size(val_font, val_str)
    uw, uh = text_size(unit_font, unit_str)
    spacing = 24
    total_w = vw + spacing + uw
    val_x = (W - total_w) // 2
    val_y = name_y + nh + 24
    draw.text((val_x, val_y), val_str, fill=color("text"), font=val_font)
    draw.text((val_x + vw + spacing, val_y + (vh - uh) - 6), unit_str, fill=color("text"), font=unit_font)

    daily = focus.get("daily_pct")
    if daily is not None:
        dp_font = load_font("mono_medium", 22)
        arrow = arrow_for(daily)
        dp_text = f"{arrow} {format_pct(daily)} bugün"
        dw, dh = text_size(dp_font, dp_text)
        draw.text(((W - dw) // 2, val_y + vh + 18), dp_text, fill=change_color(daily), font=dp_font)

    history = focus.get("history", []) or []
    hist_top = main_y1 + 24
    hist_h = 130
    hist_gap = 16

    label_font = load_font("mono_medium", 14)
    hval_font = load_font("inter_bold", 44)
    hunit_font = load_font("inter_regular", 22)
    pct_font = load_font("mono_medium", 28)

    for i, h in enumerate(history[:2]):
        hy0 = hist_top + i * (hist_h + hist_gap)
        hy1 = hy0 + hist_h
        img, draw = composite_rect(
            img,
            [main_x0, hy0, main_x1, hy1],
            fill_rgba=(*hex_to_rgb(color("surface")), 255),
            radius=22,
        )
        lx = main_x0 + 30
        draw.text((lx, hy0 + 20), h["label"], fill=color("muted"), font=label_font)
        val = h.get("value")
        if val is not None:
            v_str = format_tr(val, focus["decimals"])
            vy = hy0 + 50
            draw.text((lx, vy), v_str, fill=color("text"), font=hval_font)
            vw2, vh2 = text_size(hval_font, v_str)
            uw2, uh2 = text_size(hunit_font, focus.get("unit", ""))
            draw.text(
                (lx + vw2 + 14, vy + (vh2 - uh2) - 4),
                focus.get("unit", ""),
                fill=color("text"),
                font=hunit_font,
            )
        else:
            draw.text((lx, hy0 + 60), "—", fill=color("dim"), font=hval_font)

        pct = h.get("pct")
        if pct is not None:
            arrow = arrow_for(pct)
            ptxt = f"{arrow}  {format_pct(pct)}"
            pw, ph = text_size(pct_font, ptxt)
            draw.text(
                (main_x1 - 30 - pw, hy0 + (hist_h - ph) // 2),
                ptxt,
                fill=change_color(pct),
                font=pct_font,
            )

    last_hist_bottom = hist_top + min(len(history), 2) * (hist_h + hist_gap)
    note_top_y = max(last_hist_bottom + 24, 1140)

    draw_footer(draw, payload.get("note", "") or "", note_top_y=note_top_y)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
