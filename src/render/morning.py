"""Morning card renderer — AÇILIŞ KARTI (referans tasarıma göre)."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from PIL import ImageDraw

from src.config import CHANGE_WINDOWS, INDICATOR_ORDER, LAYOUT
from src.render.base import (
    arrow_for,
    change_color,
    color,
    color_rgba,
    composite_rect,
    draw_brand_header,
    draw_card_title,
    draw_footer,
    format_pct,
    format_tr,
    load_font,
    new_canvas,
    text_size,
)


def render_morning(payload: dict[str, Any], out_path: Path) -> None:
    target_date = datetime.fromisoformat(payload["date"]).date()
    indicators = {ind["key"]: ind for ind in payload["indicators"]}

    img = new_canvas()
    draw = ImageDraw.Draw(img)

    draw_brand_header(draw, target_date)
    draw_card_title(draw, "AÇILIŞ KARTI", "Güncel Değerler ve Tarihsel Değişimler", y=180)

    # Sütun başlıkları
    header_y = 360
    PAD_X = LAYOUT.padding_x
    W = LAYOUT.canvas_w
    label_font = load_font("mono_medium", 14)

    # Satır geometrisi
    rows_x0 = PAD_X
    rows_x1 = W - PAD_X
    rows_w = rows_x1 - rows_x0
    name_col_w = 320  # sol blok (isim+değer)
    pct_zone_x = rows_x0 + name_col_w
    pct_zone_w = rows_w - name_col_w
    col_count = len(CHANGE_WINDOWS)
    col_w = pct_zone_w / col_count

    # Başlık metinleri (her sütunun ortasında)
    for i, win in enumerate(CHANGE_WINDOWS):
        cx = pct_zone_x + col_w * i + col_w / 2
        lw, _ = text_size(label_font, win.label)
        draw.text((cx - lw / 2, header_y), win.label, fill=color("muted"), font=label_font)

    # Satırlar
    rows_top = header_y + 40
    row_h = 130
    row_gap = 14

    name_font = load_font("inter_semibold", 26)
    val_font = load_font("inter_bold", 38)
    unit_font = load_font("inter_regular", 22)
    pct_font = load_font("mono_medium", 22)

    for idx, key in enumerate(INDICATOR_ORDER):
        ind = indicators.get(key)
        if ind is None:
            continue
        ry = rows_top + idx * (row_h + row_gap)

        # Surface row
        img, draw = composite_rect(
            img,
            [rows_x0, ry, rows_x1, ry + row_h],
            fill_rgba=(*_rgb(color("surface")), 255),
            radius=22,
        )

        # İsim + değer
        nx = rows_x0 + 30
        ny = ry + 22
        draw.text((nx, ny), ind["name"], fill=color("muted"), font=name_font)

        val_str = format_tr(ind["current"], ind["decimals"])
        unit_str = ind.get("unit", "")
        vy = ry + 22 + 30
        draw.text((nx, vy), val_str, fill=color("text"), font=val_font)
        vw, vh = text_size(val_font, val_str)
        # Birim biraz aşağıda hizalanır
        draw.text((nx + vw + 12, vy + 12), unit_str, fill=color("text"), font=unit_font)

        # Yüzdelik sütunları
        changes = ind.get("changes_pct", {})
        for ci, win in enumerate(CHANGE_WINDOWS):
            pct = changes.get(win.key)
            cx_center = pct_zone_x + col_w * ci + col_w / 2
            cy_center = ry + row_h / 2

            if pct is None:
                txt = "—"
                tw, th = text_size(pct_font, txt)
                draw.text(
                    (cx_center - tw / 2, cy_center - th / 2),
                    txt,
                    fill=color("dim"),
                    font=pct_font,
                )
                continue

            arrow = arrow_for(pct)
            pct_text = format_pct(pct)
            full = f"{arrow} {pct_text}"
            fw, fh = text_size(pct_font, full)
            c = change_color(pct)
            draw.text(
                (cx_center - fw / 2, cy_center - fh / 2),
                full,
                fill=c,
                font=pct_font,
            )

    # Footer
    note = payload.get("note", "") or ""
    last_row_bottom = rows_top + len(INDICATOR_ORDER) * (row_h + row_gap)
    note_top_y = max(last_row_bottom + 30, 1140)
    draw_footer(draw, note, note_top_y=note_top_y)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")


def _rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
