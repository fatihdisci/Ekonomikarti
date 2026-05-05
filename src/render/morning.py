"""Morning card renderer: 1080x1350 PNG summarising six indicators."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from src.config import (
    CHANGE_WINDOWS,
    HASHTAG,
    INDICATOR_ORDER,
    LAYOUT,
)
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

    brand = "FİYAT HAFIZASI"
    draw.text((LAYOUT.padding_x, 50), brand, fill=color("accent"), font=brand_font)

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

    title = "AÇILIŞ KARTI"
    subtitle = "Güncel Değerler ve Tarihsel Değişimler"

    tw, th = text_size(title_font, title)
    tx = (LAYOUT.canvas_w - tw) // 2
    ty = LAYOUT.header_h + 10
    draw.text((tx, ty), title, fill=color("text"), font=title_font)

    sw, _ = text_size(subtitle_font, subtitle)
    sx = (LAYOUT.canvas_w - sw) // 2
    sy = ty + th + 15
    draw.text((sx, sy), subtitle, fill=color("muted"), font=subtitle_font)


def _draw_column_headers(draw: ImageDraw.ImageDraw) -> None:
    header_font = load_font("inter_regular", 13)
    table_y = LAYOUT.header_h + LAYOUT.title_h
    # Y is just above the first row. We align them horizontally.
    y = table_y - 20
    
    # We define right-side geometry for the 4 percentage columns.
    # Total right side width from x=480 to 1020
    row_right_x = 420
    row_right_end_x = LAYOUT.canvas_w - LAYOUT.padding_x
    col_w = (row_right_end_x - row_right_x) // 4
    
    for i, window in enumerate(CHANGE_WINDOWS):
        col_center = row_right_x + col_w * i + col_w // 2
        w, _ = text_size(header_font, window.label)
        draw.text(
            (col_center - w // 2, y),
            window.label,
            fill=color("muted"),
            font=header_font,
        )


def _draw_row(
    draw: ImageDraw.ImageDraw,
    indicator: dict[str, Any],
    row_index: int,
) -> None:
    table_y = LAYOUT.header_h + LAYOUT.title_h
    # 160px row height -> card height 140, margin 20
    card_h = LAYOUT.row_h - 20
    card_top = table_y + LAYOUT.row_h * row_index
    
    # Draw rounded card background
    draw.rounded_rectangle(
        [LAYOUT.padding_x, card_top, LAYOUT.canvas_w - LAYOUT.padding_x, card_top + card_h],
        radius=LAYOUT.card_radius,
        fill=color("surface")
    )

    name_font = load_font("inter_semibold", 24)
    value_font = load_font("mono_bold", 30)
    pct_font = load_font("mono_bold", 20)

    # Left zone: Indicator name & current value
    text_left_x = LAYOUT.padding_x + 20
    name_y = card_top + 35
    draw.text(
        (text_left_x, name_y),
        indicator["name"],
        fill=color("muted"),
        font=name_font,
    )

    decimals = int(indicator.get("decimals", 2))
    current_value = float(indicator["current"])
    unit = indicator.get("unit", "")
    value_text = f"{format_tr(current_value, decimals)} {unit}".strip()
    value_y = name_y + 36
    draw.text(
        (text_left_x, value_y),
        value_text,
        fill=color("text"),
        font=value_font,
    )

    # Right zone: Horizontal row of percentage changes
    row_right_x = 420
    row_right_end_x = LAYOUT.canvas_w - LAYOUT.padding_x
    col_w = (row_right_end_x - row_right_x) // 4
    pct_y = card_top + (card_h - 20) // 2
    
    changes = indicator.get("changes_pct", {})
    
    for i, window in enumerate(CHANGE_WINDOWS):
        raw = changes.get(window.key)
        col_center = row_right_x + col_w * i + col_w // 2
        
        if raw is None:
            text = "—"
            fill = color("muted")
        else:
            value = float(raw)
            text = f"{arrow_for(value)} {format_pct(value)}"
            fill = change_color(value)
            
        pw, _ = text_size(pct_font, text)
        draw.text((col_center - pw//2, pct_y), text, fill=fill, font=pct_font)


def _draw_table(draw: ImageDraw.ImageDraw, indicators_by_key: dict[str, dict[str, Any]]) -> None:
    _draw_column_headers(draw)
    for i, key in enumerate(INDICATOR_ORDER):
        ind = indicators_by_key.get(key)
        if ind is None:
            continue
        _draw_row(draw, ind, i)


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

    note_font = load_font("inter_regular", 24)
    note_y = footer_y + 40
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
    draw.text(
        (LAYOUT.padding_x, meta_y),
        source_text,
        fill=color("footer_note"),
        font=meta_font,
    )
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


def render_morning(payload: dict[str, Any], output_path: Path) -> Path:
    """Sabah kartını oluştur ve PNG olarak kaydet."""
    target_date = _parse_target_date(payload)
    indicators_list = payload.get("indicators", []) or []
    indicators_by_key = {ind["key"]: ind for ind in indicators_list}
    note = payload.get("note") or ""

    img = Image.new("RGB", (LAYOUT.canvas_w, LAYOUT.canvas_h), color=color("bg"))
    draw = ImageDraw.Draw(img)

    _draw_header(draw, target_date)
    _draw_title_block(draw)
    _draw_table(draw, indicators_by_key)
    _draw_footer(draw, note)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG", optimize=True)
    return output_path
