"""Noon "Odak Kartı" renderer: tek gösterge × tarihsel snapshot."""

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

    title = "ODAK KARTI"
    subtitle = "Tarihsel Bakış"

    tw, th = text_size(title_font, title)
    tx = (LAYOUT.canvas_w - tw) // 2
    ty = LAYOUT.header_h + 30
    draw.text((tx, ty), title, fill=color("text"), font=title_font)

    sw, _ = text_size(subtitle_font, subtitle)
    sx = (LAYOUT.canvas_w - sw) // 2
    sy = ty + th + 20
    draw.text((sx, sy), subtitle, fill=color("muted"), font=subtitle_font)


def _draw_focus_block(draw: ImageDraw.ImageDraw, focus: dict[str, Any]) -> None:
    """Üstteki büyük blok: gösterge adı + bugünkü değer + günlük % değişim."""
    block_top = LAYOUT.header_h + LAYOUT.title_h
    # Aynı 600px alanı paylaşacağız: üst yarısı focus blok, alt yarısı tarih satırları.
    focus_h = LAYOUT.table_h // 2

    name_font = load_font("inter_semibold", 40)
    value_font = load_font("mono_bold", 96)
    daily_font = load_font("mono_medium", 22)

    name = focus["name"]
    decimals = int(focus["decimals"])
    unit = focus.get("unit", "")
    current = float(focus["current"])
    value_text = f"{format_tr(current, decimals)} {unit}".strip()

    nw, nh = text_size(name_font, name)
    vw, vh = text_size(value_font, value_text)

    # İçeriği focus_h içinde dikey ortala.
    daily_pct = focus.get("daily_pct")
    if daily_pct is not None:
        daily_text = f"{arrow_for(daily_pct)} {format_pct(daily_pct)} bugün"
        dw, dh = text_size(daily_font, daily_text)
        gap1, gap2 = 20, 16
        total_h = nh + gap1 + vh + gap2 + dh
    else:
        daily_text = None
        dw = dh = 0
        gap1 = 20
        gap2 = 0
        total_h = nh + gap1 + vh

    y = block_top + (focus_h - total_h) // 2

    draw.text(((LAYOUT.canvas_w - nw) // 2, y), name, fill=color("muted"), font=name_font)
    y += nh + gap1
    draw.text(((LAYOUT.canvas_w - vw) // 2, y), value_text, fill=color("text"), font=value_font)
    y += vh + gap2
    if daily_text is not None:
        fill = change_color(daily_pct)
        draw.text(((LAYOUT.canvas_w - dw) // 2, y), daily_text, fill=fill, font=daily_font)


def _draw_history_rows(draw: ImageDraw.ImageDraw, focus: dict[str, Any]) -> None:
    """Alt yarıda tarihsel satırlar."""
    block_top = LAYOUT.header_h + LAYOUT.title_h + LAYOUT.table_h // 2
    block_h = LAYOUT.table_h - LAYOUT.table_h // 2  # 300

    history = focus.get("history", []) or []
    if not history:
        return

    label_font = load_font("inter_regular", 18)
    value_font = load_font("mono_bold", 44)
    pct_font = load_font("mono_bold", 28)

    decimals = int(focus["decimals"])
    unit = focus.get("unit", "")

    row_h = block_h // len(history)
    for i, item in enumerate(history):
        row_top = block_top + row_h * i

        # Satırın üstünde divider (en üst satırda title_block ile ayrım için).
        draw.line(
            [
                (LAYOUT.padding_x, row_top),
                (LAYOUT.canvas_w - LAYOUT.padding_x, row_top),
            ],
            fill=color("divider"),
            width=1,
        )

        label = item.get("label", "")
        value = item.get("value")
        pct = item.get("pct")

        if value is None:
            value_text = "—"
        else:
            value_text = f"{format_tr(float(value), decimals)} {unit}".strip()

        # Üstte küçük label, altta büyük değer (sol); sağda yüzde değişim büyük.
        label_y = row_top + 30
        draw.text((LAYOUT.padding_x, label_y), label, fill=color("muted"), font=label_font)

        value_y = label_y + 28
        draw.text((LAYOUT.padding_x, value_y), value_text, fill=color("text"), font=value_font)

        if pct is not None:
            pct_text = f"{arrow_for(pct)} {format_pct(pct)}"
            pw, ph = text_size(pct_font, pct_text)
            pct_x = LAYOUT.canvas_w - LAYOUT.padding_x - pw
            pct_y = row_top + (row_h - ph) // 2
            draw.text((pct_x, pct_y), pct_text, fill=change_color(pct), font=pct_font)


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


def render_noon(payload: dict[str, Any], output_path: Path) -> Path:
    """Öğle "Odak Kartı"nı oluştur ve PNG olarak kaydet.

    Payload schema: see tests/fixtures/sample_noon.json.
    """
    target_date = _parse_target_date(payload)
    focus = payload.get("focus") or {}
    if not focus:
        raise ValueError("noon payload missing 'focus' block")
    note = payload.get("note") or ""

    img = Image.new("RGB", (LAYOUT.canvas_w, LAYOUT.canvas_h), color=color("bg"))
    draw = ImageDraw.Draw(img)

    _draw_header(draw, target_date)
    _draw_title_block(draw)
    _draw_focus_block(draw, focus)
    _draw_history_rows(draw, focus)
    _draw_footer(draw, note)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG", optimize=True)
    return output_path
