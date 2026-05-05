"""Weekly "Haftalık Özet" renderer (Cumartesi): 5 gösterge × tek 'Bu Hafta %' sütunu."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from src.config import HASHTAG, INDICATOR_ORDER, LAYOUT
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

    title = "HAFTALIK ÖZET"
    subtitle = "Pazartesi → Cuma"

    tw, th = text_size(title_font, title)
    tx = (LAYOUT.canvas_w - tw) // 2
    ty = LAYOUT.header_h + 30
    draw.text((tx, ty), title, fill=color("text"), font=title_font)

    sw, _ = text_size(subtitle_font, subtitle)
    sx = (LAYOUT.canvas_w - sw) // 2
    sy = ty + th + 20
    draw.text((sx, sy), subtitle, fill=color("muted"), font=subtitle_font)


def _draw_column_header(draw: ImageDraw.ImageDraw) -> None:
    """Sağ tarafa tek sütun başlığı: BU HAFTA."""
    header_font = load_font("inter_regular", 13)
    table_y = LAYOUT.header_h + LAYOUT.title_h
    label = "BU HAFTA"
    w, _ = text_size(header_font, label)
    # Sağa yasla.
    x = LAYOUT.canvas_w - LAYOUT.padding_x - w
    draw.text((x, table_y + 14), label, fill=color("muted"), font=header_font)


def _draw_row(
    draw: ImageDraw.ImageDraw,
    indicator: dict[str, Any],
    row_index: int,
) -> None:
    table_y = LAYOUT.header_h + LAYOUT.title_h
    row_top = table_y + LAYOUT.row_h * row_index

    name_font = load_font("inter_semibold", 28)
    value_font = load_font("mono_bold", 42)
    pct_font = load_font("mono_bold", 30)

    # Sol: ad + Cuma kapanışı.
    name_y = row_top + 30
    draw.text(
        (LAYOUT.padding_x, name_y),
        indicator["name"],
        fill=color("text"),
        font=name_font,
    )
    decimals = int(indicator.get("decimals", 2))
    current = float(indicator["current"])
    unit = indicator.get("unit", "")
    value_text = f"{format_tr(current, decimals)} {unit}".strip()
    draw.text(
        (LAYOUT.padding_x, name_y + 38),
        value_text,
        fill=color("text"),
        font=value_font,
    )

    # Sağ: tek sütun haftalık %.
    pct = indicator.get("weekly_pct")
    if pct is None:
        pct_text = "—"
        fill = color("muted")
    else:
        pct = float(pct)
        pct_text = f"{arrow_for(pct)} {format_pct(pct)}"
        fill = change_color(pct)
    pw, ph = text_size(pct_font, pct_text)
    pct_x = LAYOUT.canvas_w - LAYOUT.padding_x - pw
    pct_y = row_top + (LAYOUT.row_h - ph) // 2
    draw.text((pct_x, pct_y), pct_text, fill=fill, font=pct_font)

    divider_y = row_top + LAYOUT.row_h - 1
    draw.line(
        [
            (LAYOUT.padding_x, divider_y),
            (LAYOUT.canvas_w - LAYOUT.padding_x, divider_y),
        ],
        fill=color("divider"),
        width=1,
    )


def _draw_table(draw: ImageDraw.ImageDraw, indicators: list[dict[str, Any]]) -> None:
    _draw_column_header(draw)
    by_key = {ind["key"]: ind for ind in indicators}
    for i, key in enumerate(INDICATOR_ORDER):
        ind = by_key.get(key)
        if ind is None:
            continue
        _draw_row(draw, ind, i)


def _draw_footer(draw: ImageDraw.ImageDraw, note: str) -> None:
    footer_y = LAYOUT.header_h + LAYOUT.title_h + LAYOUT.table_h
    draw.line(
        [
            (LAYOUT.padding_x, footer_y),
            (LAYOUT.canvas_w - LAYOUT.padding_x, footer_y),
        ],
        fill=color("divider"),
        width=1,
    )

    note_font = load_font("inter_regular", 22)
    note_y = footer_y + 30
    max_width = LAYOUT.canvas_w - 2 * LAYOUT.padding_x
    lines = wrap_lines(note_font, note, max_width=max_width, max_lines=8)
    line_h = note_font.getbbox("Ay")[3] + 12
    for i, line in enumerate(lines):
        draw.text(
            (LAYOUT.padding_x, note_y + i * line_h),
            line,
            fill=color("text"),
            font=note_font,
        )

    meta_font = load_font("inter_regular", 14)
    source_text = "Kaynak: Yahoo Finance"
    meta_y = LAYOUT.canvas_h - 40 - meta_font.getbbox("Ay")[3]
    draw.text((LAYOUT.padding_x, meta_y), source_text, fill=color("muted"), font=meta_font)
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


def render_weekly(payload: dict[str, Any], output_path: Path) -> Path:
    """Cumartesi 'Haftalık Özet' kartını üret."""
    target_date = _parse_target_date(payload)
    indicators = payload.get("indicators") or []
    note = payload.get("note") or ""

    img = Image.new("RGB", (LAYOUT.canvas_w, LAYOUT.canvas_h), color=color("bg"))
    draw = ImageDraw.Draw(img)

    _draw_header(draw, target_date)
    _draw_title_block(draw)
    _draw_table(draw, indicators)
    _draw_footer(draw, note)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG", optimize=True)
    return output_path
