"""Evening "Kapanış Kartı" renderer: kapanış snapshot + günün en sert hareketi."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from src.config import HASHTAG, LAYOUT
from src.render.base import (
    arrow_for,
    change_color,
    color,
    format_pct,
    format_tr,
    format_tr_date,
    load_font,
    text_size,
    wrap_lines,
)


def _draw_header(draw: ImageDraw.ImageDraw, target_date: date) -> None:
    brand_font = load_font("inter_bold", 32)
    date_font = load_font("mono_medium", 18)

    draw.text((LAYOUT.padding_x, 50), "FİYAT HAFIZASI", fill=color("accent"), font=brand_font)
    date_str = format_tr_date(target_date)
    w, _ = text_size(date_font, date_str)
    draw.text(
        (LAYOUT.canvas_w - LAYOUT.padding_x - w, 60),
        date_str,
        fill=color("muted"),
        font=date_font,
    )


def _draw_title_block(draw: ImageDraw.ImageDraw) -> None:
    title_font = load_font("inter_bold", 56)
    subtitle_font = load_font("inter_regular", 18)

    title = "KAPANIŞ KARTI"
    subtitle = "Günü Kapatırken"

    tw, th = text_size(title_font, title)
    tx = (LAYOUT.canvas_w - tw) // 2
    ty = LAYOUT.header_h + 10
    draw.text((tx, ty), title, fill=color("text"), font=title_font)

    sw, _ = text_size(subtitle_font, subtitle)
    sx = (LAYOUT.canvas_w - sw) // 2
    sy = ty + th + 15
    draw.text((sx, sy), subtitle, fill=color("muted"), font=subtitle_font)


def _draw_snapshot_table(draw: ImageDraw.ImageDraw, indicators: list[dict[str, Any]]) -> None:
    """Üstte 4 göstergenin kapanış snapshot'ı."""
    block_top = LAYOUT.header_h + LAYOUT.title_h
    block_h = LAYOUT.table_h // 2  # 400

    if not indicators:
        return
    rows = len(indicators)
    row_h = block_h // rows
    card_h = row_h - 12
    margin_y = 12

    name_font = load_font("inter_semibold", 28)
    value_font = load_font("mono_bold", 36)
    pct_font = load_font("mono_bold", 26)

    for i, ind in enumerate(indicators):
        row_top = block_top + row_h * i

        # Card bg
        draw.rounded_rectangle(
            [LAYOUT.padding_x, row_top, LAYOUT.canvas_w - LAYOUT.padding_x, row_top + card_h],
            radius=LAYOUT.card_radius,
            fill=color("surface")
        )

        name_text = ind.get("name", "")
        nh = text_size(name_font, name_text)[1]
        name_y = row_top + (card_h - nh) // 2 - 4
        draw.text((LAYOUT.padding_x + 30, name_y), name_text, fill=color("muted"), font=name_font)

        decimals = int(ind.get("decimals", 2))
        unit = ind.get("unit", "")
        current = float(ind["current"])
        value_text = f"{format_tr(current, decimals)} {unit}".strip()
        vw, vh = text_size(value_font, value_text)
        
        center_x = LAYOUT.canvas_w // 2 + 60
        value_x = center_x - vw // 2
        value_y = row_top + (card_h - vh) // 2 - 4
        draw.text((value_x, value_y), value_text, fill=color("text"), font=value_font)

        pct = ind.get("daily_pct")
        if pct is not None:
            pct_text = f"{arrow_for(pct)} {format_pct(pct)}"
            pw, ph = text_size(pct_font, pct_text)
            pct_x = LAYOUT.canvas_w - LAYOUT.padding_x - 30 - pw
            pct_y = row_top + (card_h - ph) // 2 - 4
            draw.text((pct_x, pct_y), pct_text, fill=change_color(pct), font=pct_font)


def _draw_biggest_mover(draw: ImageDraw.ImageDraw, mover: dict[str, Any] | None) -> None:
    """Alt yarıda 'Günün Hareketi' vurgu bloğu."""
    block_top = LAYOUT.header_h + LAYOUT.title_h + LAYOUT.table_h // 2
    block_h = LAYOUT.table_h // 2  # 400
    card_h = block_h - 20
    card_top = block_top + 10

    draw.rounded_rectangle(
        [LAYOUT.padding_x, card_top, LAYOUT.canvas_w - LAYOUT.padding_x, card_top + card_h],
        radius=LAYOUT.card_radius,
        fill=color("surface")
    )

    label_font = load_font("inter_regular", 18)
    name_font = load_font("inter_bold", 52)
    pct_font = load_font("mono_bold", 84)

    label_text = "GÜNÜN HAREKETİ"
    if mover is None:
        lw, _ = text_size(label_font, label_text)
        draw.text(
            ((LAYOUT.canvas_w - lw) // 2, card_top + 60),
            label_text,
            fill=color("muted"),
            font=label_font,
        )
        return

    name_text = mover["name"].upper()
    pct = float(mover["daily_pct"])
    pct_text = f"{arrow_for(pct)} {format_pct(pct)}"

    lw, lh = text_size(label_font, label_text)
    nw, nh = text_size(name_font, name_text)
    pw, ph = text_size(pct_font, pct_text)

    gap1, gap2 = 28, 24
    total_h = lh + gap1 + nh + gap2 + ph
    y = card_top + (card_h - total_h) // 2

    draw.text(((LAYOUT.canvas_w - lw) // 2, y), label_text, fill=color("muted"), font=label_font)
    y += lh + gap1
    draw.text(((LAYOUT.canvas_w - nw) // 2, y), name_text, fill=color("text"), font=name_font)
    y += nh + gap2
    draw.text(((LAYOUT.canvas_w - pw) // 2, y), pct_text, fill=change_color(pct), font=pct_font)


def _draw_footer(draw: ImageDraw.ImageDraw, note: str) -> None:
    footer_y = LAYOUT.header_h + LAYOUT.title_h + LAYOUT.table_h
    draw.line(
        [
            (LAYOUT.canvas_w // 2 - 100, footer_y),
            (LAYOUT.canvas_w // 2 + 100, footer_y),
        ],
        fill=color("divider"),
        width=2,
    )

    note_font = load_font("inter_regular", 18)
    note_y = footer_y + 36
    max_width = LAYOUT.canvas_w - 2 * LAYOUT.padding_x
    lines = wrap_lines(note_font, note, max_width=max_width, max_lines=3)
    line_h = note_font.getbbox("Ay")[3] + 12
    for i, line in enumerate(lines):
        lw, _ = text_size(note_font, line)
        draw.text(
            ((LAYOUT.canvas_w - lw) // 2, note_y + i * line_h),
            line,
            fill=color("footer_note"),
            font=note_font,
        )

    meta_font = load_font("inter_regular", 14)
    source_text = "Kaynak: Yahoo Finance"
    meta_y = LAYOUT.canvas_h - 50 - meta_font.getbbox("Ay")[3]
    draw.text((LAYOUT.padding_x, meta_y), source_text, fill=color("footer_note"), font=meta_font)
    hw, _ = text_size(meta_font, HASHTAG)
    draw.text(
        (LAYOUT.canvas_w - LAYOUT.padding_x - hw, meta_y),
        HASHTAG,
        fill=color("accent"),
        font=meta_font,
    )


def _parse_target_date(payload: dict[str, Any]) -> date:
    raw = payload.get("date")
    if isinstance(raw, str):
        return datetime.strptime(raw, "%Y-%m-%d").date()
    return date.today()


def render_evening(payload: dict[str, Any], output_path: Path) -> Path:
    """Akşam "Kapanış Kartı"nı oluştur ve PNG olarak kaydet."""
    target_date = _parse_target_date(payload)
    indicators = payload.get("indicators") or []
    mover = payload.get("biggest_mover")
    note = payload.get("note") or ""

    img = Image.new("RGB", (LAYOUT.canvas_w, LAYOUT.canvas_h), color=color("bg"))
    draw = ImageDraw.Draw(img)

    _draw_header(draw, target_date)
    _draw_title_block(draw)
    _draw_snapshot_table(draw, indicators)
    _draw_biggest_mover(draw, mover)
    _draw_footer(draw, note)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG", optimize=True)
    return output_path
