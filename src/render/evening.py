"""Evening card renderer — KAPANIŞ KARTI (referans tasarıma göre)."""

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


def render_evening(payload: dict[str, Any], out_path: Path) -> None:
    target_date = datetime.fromisoformat(payload["date"]).date()
    indicators = payload.get("indicators", []) or []
    biggest = payload.get("biggest_mover")

    img = new_canvas()
    draw = ImageDraw.Draw(img)

    draw_brand_header(draw, target_date)
    draw_card_title(draw, "KAPANIŞ KARTI", "Günü Kapatırken", y=180)

    PAD_X = LAYOUT.padding_x
    W = LAYOUT.canvas_w
    x0, x1 = PAD_X, W - PAD_X

    # ── Üst sıra: 4 kompakt satır ──
    rows_top = 360
    row_h = 88
    row_gap = 10

    name_font = load_font("inter_semibold", 26)
    val_font = load_font("inter_bold", 32)
    unit_font = load_font("inter_regular", 20)
    pct_font = load_font("mono_medium", 24)

    for i, ind in enumerate(indicators):
        ry = rows_top + i * (row_h + row_gap)
        img, draw = composite_rect(
            img,
            [x0, ry, x1, ry + row_h],
            fill_rgba=(*hex_to_rgb(color("surface")), 255),
            radius=20,
        )
        # sol: isim
        draw.text(
            (x0 + 30, ry + (row_h - text_size(name_font, ind["name"])[1]) // 2),
            ind["name"],
            fill=color("muted"),
            font=name_font,
        )
        # orta: değer + birim
        v_str = format_tr(ind["current"], ind["decimals"])
        unit = ind.get("unit", "")
        vw, vh = text_size(val_font, v_str)
        uw, uh = text_size(unit_font, unit)
        center_x = (x0 + x1) // 2
        total_w = vw + 12 + uw
        vx = center_x - total_w // 2
        vy = ry + (row_h - vh) // 2
        draw.text((vx, vy), v_str, fill=color("text"), font=val_font)
        draw.text((vx + vw + 12, vy + (vh - uh) - 2), unit, fill=color("text"), font=unit_font)

        # sağ: günlük yüzde
        dp = ind.get("daily_pct")
        if dp is not None:
            ptxt = f"{arrow_for(dp)} {format_pct(dp)}"
            pw, ph = text_size(pct_font, ptxt)
            draw.text(
                (x1 - 30 - pw, ry + (row_h - ph) // 2),
                ptxt,
                fill=change_color(dp),
                font=pct_font,
            )

    # ── Günün hareketi kartı ──
    table_bottom = rows_top + len(indicators) * (row_h + row_gap)
    hero_y0 = table_bottom + 24
    hero_h = 320
    hero_y1 = hero_y0 + hero_h

    img, draw = composite_rect(
        img,
        [x0, hero_y0, x1, hero_y1],
        fill_rgba=(*hex_to_rgb(color("surface")), 255),
        radius=24,
    )

    if biggest:
        small = load_font("mono_medium", 16)
        st = "GÜNÜN HAREKETİ"
        sw, sh = text_size(small, st)
        draw.text(((W - sw) // 2, hero_y0 + 36), st, fill=color("muted"), font=small)

        big_name_font = load_font("inter_bold", 56)
        nm = biggest["name"].upper()
        nw, nh = text_size(big_name_font, nm)
        draw.text(((W - nw) // 2, hero_y0 + 80), nm, fill=color("text"), font=big_name_font)

        pct = biggest.get("daily_pct", 0.0) or 0.0
        big_pct_font = load_font("inter_bold", 92)
        ptxt = format_pct(pct)
        arrow = arrow_for(pct)
        pw, ph = text_size(big_pct_font, ptxt)
        aw, ah = text_size(big_pct_font, arrow)
        gap = 24
        total = aw + gap + pw
        sx = (W - total) // 2
        sy = hero_y0 + 170
        c = change_color(pct)
        draw.text((sx, sy), arrow, fill=c, font=big_pct_font)
        draw.text((sx + aw + gap, sy), ptxt, fill=c, font=big_pct_font)

    note_top_y = max(hero_y1 + 30, 1140)
    draw_footer(draw, payload.get("note", "") or "", note_top_y=note_top_y)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
