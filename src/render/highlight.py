"""Sunday "Haftanın Yıldızı/Kaybedeni" renderer."""

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

    title = "HAFTANIN ÖZETİ"
    subtitle = "Yıldız ve Kaybeden"

    tw, th = text_size(title_font, title)
    tx = (LAYOUT.canvas_w - tw) // 2
    ty = LAYOUT.header_h + 10
    draw.text((tx, ty), title, fill=color("text"), font=title_font)

    sw, _ = text_size(subtitle_font, subtitle)
    sx = (LAYOUT.canvas_w - sw) // 2
    sy = ty + th + 15
    draw.text((sx, sy), subtitle, fill=color("muted"), font=subtitle_font)


def _draw_tile(
    draw: ImageDraw.ImageDraw,
    block_top: int,
    block_h: int,
    label: str,
    item: dict[str, Any] | None,
) -> None:
    """Tek bir vurgu kutusu (yıldız ya da kaybeden)."""
    card_h = block_h - 20
    card_top = block_top + 10

    draw.rounded_rectangle(
        [LAYOUT.padding_x, card_top, LAYOUT.canvas_w - LAYOUT.padding_x, card_top + card_h],
        radius=LAYOUT.card_radius,
        fill=color("surface")
    )

    label_font = load_font("inter_regular", 20)
    name_font = load_font("inter_bold", 50)
    pct_font = load_font("mono_bold", 78)
    value_font = load_font("mono_medium", 24)

    if item is None:
        lw, _ = text_size(label_font, label)
        draw.text(
            ((LAYOUT.canvas_w - lw) // 2, card_top + 60),
            label,
            fill=color("muted"),
            font=label_font,
        )
        return

    name = item["name"].upper()
    pct = float(item["weekly_pct"])
    pct_text = f"{arrow_for(pct)} {format_pct(pct)}"

    decimals = int(item["decimals"])
    unit = item.get("unit", "")
    value_text = f"{format_tr(float(item['current']), decimals)} {unit}".strip()

    lw, lh = text_size(label_font, label)
    nw, nh = text_size(name_font, name)
    pw, ph = text_size(pct_font, pct_text)
    vw, vh = text_size(value_font, value_text)

    gap1, gap2, gap3 = 22, 18, 16
    total_h = lh + gap1 + nh + gap2 + ph + gap3 + vh
    y = card_top + (card_h - total_h) // 2

    draw.text(((LAYOUT.canvas_w - lw) // 2, y), label, fill=color("muted"), font=label_font)
    y += lh + gap1
    draw.text(((LAYOUT.canvas_w - nw) // 2, y), name, fill=color("text"), font=name_font)
    y += nh + gap2
    draw.text(((LAYOUT.canvas_w - pw) // 2, y), pct_text, fill=change_color(pct), font=pct_font)
    y += ph + gap3
    draw.text(((LAYOUT.canvas_w - vw) // 2, y), value_text, fill=color("muted"), font=value_font)


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
    lines = wrap_lines(note_font, note, max_width=max_width, max_lines=6)
    line_h = note_font.getbbox("Ay")[3] + 12
    for i, line in enumerate(lines):
        lw, _ = text_size(note_font, line)
        draw.text(
            ((LAYOUT.canvas_w - lw) // 2, note_y + i * line_h),
            line,
            fill=color("muted"),
            font=note_font,
        )

    meta_font = load_font("inter_regular", 14)
    source_text = "Kaynak: Yahoo Finance"
    meta_y = LAYOUT.canvas_h - 50 - meta_font.getbbox("Ay")[3]
    draw.text((LAYOUT.padding_x, meta_y), source_text, fill=color("divider"), font=meta_font)
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


def render_highlight(payload: dict[str, Any], output_path: Path) -> Path:
    """Pazar 'Haftanın Yıldızı/Kaybedeni' kartını üret."""
    target_date = _parse_target_date(payload)
    star = payload.get("star")
    loser = payload.get("loser")
    note = payload.get("note") or ""

    img = Image.new("RGB", (LAYOUT.canvas_w, LAYOUT.canvas_h), color=color("bg"))
    draw = ImageDraw.Draw(img)

    _draw_header(draw, target_date)
    _draw_title_block(draw)

    block_top = LAYOUT.header_h + LAYOUT.title_h
    half = LAYOUT.table_h // 2
    _draw_tile(draw, block_top, half, "HAFTANIN YILDIZI", star)
    _draw_tile(draw, block_top + half, half, "HAFTANIN KAYBEDENİ", loser)

    _draw_footer(draw, note)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG", optimize=True)
    return output_path
