"""Evening "Kapanış Kartı" renderer: snapshot table + tinted mover hero."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from src.config import LAYOUT
from src.render.base import (
    arrow_for,
    change_color,
    change_color_rgba,
    color,
    color_rgba,
    composite_rect,
    draw_corner_marks,
    draw_eyebrow,
    draw_footer,
    draw_header,
    draw_sparkline,
    draw_sparkline_with_area,
    format_pct,
    format_tr,
    hex_to_rgb,
    load_font,
    text_size,
    wrap_lines,
)

_PAD = LAYOUT.padding_x
_W   = LAYOUT.canvas_w
_H   = LAYOUT.canvas_h
_TBL = LAYOUT.header_h + LAYOUT.title_h  # 290


def _draw_title(draw: ImageDraw.ImageDraw) -> None:
    ty = LAYOUT.header_h + 14
    draw_eyebrow(draw, _PAD, ty, "03", "Kapanış · Closing Bell")
    h1f = load_font("inter_bold", 62)
    _, lh = text_size(h1f, "A")
    draw.text((_PAD, ty + 22), "Gün nasıl", fill=color("text"), font=h1f)
    draw.text((_PAD, ty + 22 + int(lh * 0.95) + 4), "kapandı?", fill=color("text"), font=h1f)


def _draw_snapshot_table(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    indicators: list[dict[str, Any]],
) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    if not indicators:
        return img, draw, _TBL + 20

    TABLE_Y = _TBL + 16
    TABLE_H = 330
    TABLE_END = TABLE_Y + TABLE_H

    # Container card
    s = color("surface")
    s_rgb = hex_to_rgb(s)
    img, draw = composite_rect(
        img,
        [_PAD, TABLE_Y, _W - _PAD, TABLE_END],
        fill_rgba=(*s_rgb, 255),
        outline_rgba=color_rgba("border"),
        radius=18,
    )

    row_h = TABLE_H // len(indicators)
    name_f = load_font("inter_semibold", 20)
    val_f  = load_font("mono_bold", 24)
    pct_f  = load_font("mono_bold", 20)
    num_f  = load_font("mono_medium", 11)
    unit_f = load_font("mono_medium", 11)

    SPARK_W, SPARK_H = 120, 32

    for i, ind in enumerate(indicators):
        row_y = TABLE_Y + row_h * i
        # separator
        if i > 0:
            img, draw = composite_rect(
                img,
                [_PAD + 16, row_y, _W - _PAD - 16, row_y + 1],
                fill_rgba=color_rgba("border"),
                radius=0,
            )

        cy = row_y + (row_h - text_size(name_f, "A")[1]) // 2

        # Index
        draw.text((_PAD + 22, cy), f"{i+1:02d}", fill=color("dim"), font=num_f)

        # Name
        draw.text((_PAD + 52, cy - 2), ind.get("name", ""), fill=color("text"), font=name_f)

        # Value (centered-right)
        decimals = int(ind.get("decimals", 2))
        current = float(ind["current"])
        unit = ind.get("unit", "")
        val_str = f"{format_tr(current, decimals)} {unit}".strip()
        vw, _ = text_size(val_f, val_str)
        val_x = _W // 2 - vw // 2 + 40
        draw.text((val_x, cy - 2), val_str, fill=color("text"), font=val_f)

        # Sparkline (mini)
        spark = ind.get("sparkline") or []
        daily = ind.get("daily_pct")
        sc = change_color(daily) if daily is not None else color("muted")
        spark_x = _W - _PAD - 30 - 130 - SPARK_W - 16
        spark_y = row_y + (row_h - SPARK_H) // 2
        if spark:
            draw_sparkline(draw, spark, spark_x, spark_y, SPARK_W, SPARK_H,
                           sc, pad=2, line_width=2, dot=False)

        # Daily pct
        if daily is not None:
            pct_str = f"{arrow_for(daily)} {format_pct(daily)}"
            pw, _ = text_size(pct_f, pct_str)
            draw.text((_W - _PAD - 30 - pw, cy - 2), pct_str, fill=change_color(daily), font=pct_f)

    return img, draw, TABLE_END


def _draw_mover_hero(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    mover: dict[str, Any] | None,
    start_y: int,
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    if mover is None:
        return img, draw

    CARD_Y = start_y + 22
    # Fit into remaining table area
    table_end = LAYOUT.header_h + LAYOUT.title_h + LAYOUT.table_h
    CARD_H = table_end - CARD_Y - 10
    CARD_END = CARD_Y + CARD_H

    daily = float(mover.get("daily_pct", 0))
    tint = change_color_rgba(daily)
    s = color("surface")
    s_rgb = hex_to_rgb(s)

    # Base surface
    img, draw = composite_rect(
        img, [_PAD, CARD_Y, _W - _PAD, CARD_END],
        fill_rgba=(*s_rgb, 255), radius=20,
    )
    # Tint overlay
    img, draw = composite_rect(
        img, [_PAD, CARD_Y, _W - _PAD, CARD_END],
        fill_rgba=tint, radius=20,
    )
    # Border
    bc = hex_to_rgb(change_color(daily))
    img, draw = composite_rect(
        img, [_PAD, CARD_Y, _W - _PAD, CARD_END],
        outline_rgba=(*bc, 90), radius=20,
    )

    ix = _PAD + 36
    iy = CARD_Y + 28

    # Label
    lf = load_font("mono_medium", 11)
    draw.text((ix, iy), "⚡  GÜNÜN HAREKETİ", fill=change_color(daily), font=lf)

    # Indicator name
    nf = load_font("inter_bold", 42)
    draw.text((ix, iy + 22), mover.get("name", "").upper(), fill=color("text"), font=nf)

    # Big percentage
    pf = load_font("mono_bold", 72)
    af = load_font("inter_bold", 36)
    pct_str = format_pct(daily)
    arrow_str = arrow_for(daily)
    aw, ah = text_size(af, arrow_str)
    pw, ph = text_size(pf, pct_str)
    draw.text((ix, iy + 80), arrow_str, fill=change_color(daily), font=af)
    draw.text((ix + aw + 14, iy + 72), pct_str, fill=change_color(daily), font=pf)

    # Close price
    decimals = int(mover.get("decimals", 2))
    current = float(mover["current"])
    unit = mover.get("unit", "")
    cf = load_font("mono_medium", 14)
    close_str = f"Kapanış: {format_tr(current, decimals)} {unit}".strip()
    draw.text((ix, iy + 80 + ph + 10), close_str, fill=color("muted"), font=cf)

    # Sparkline (right side)
    spark = mover.get("sparkline") or []
    if spark:
        SPARK_X = _W - _PAD - 36 - 270
        SPARK_Y = iy + 22
        SPARK_W, SPARK_H = 270, 110
        img, draw = draw_sparkline_with_area(
            img, draw, spark,
            SPARK_X, SPARK_Y, SPARK_W, SPARK_H,
            change_color(daily), pad=4, line_width=2, area_alpha=40,
        )
        day_f = load_font("mono_medium", 10)
        labels = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        n = len(spark)
        step = SPARK_W // max(n - 1, 1)
        for j in range(min(n, len(labels))):
            lx = SPARK_X + j * step
            draw.text((lx, SPARK_Y + SPARK_H + 4), labels[j], fill=color("dim"), font=day_f)

    return img, draw


def _parse_target_date(payload: dict[str, Any]) -> date:
    raw = payload.get("date")
    if isinstance(raw, str):
        return datetime.strptime(raw, "%Y-%m-%d").date()
    return date.today()


def render_evening(payload: dict[str, Any], output_path: Path) -> Path:
    """Akşam Kapanış Kartı'nı oluştur ve PNG olarak kaydet."""
    target_date = _parse_target_date(payload)
    indicators = payload.get("indicators") or []
    mover = payload.get("biggest_mover")
    note = payload.get("note") or ""

    img = Image.new("RGB", (_W, _H), color=color("bg"))
    draw = ImageDraw.Draw(img)

    draw_corner_marks(draw)
    img, draw = draw_header(img, target_date, "EVENING · 18:30")
    _draw_title(draw)
    img, draw, table_end = _draw_snapshot_table(img, draw, indicators)
    img, draw = _draw_mover_hero(img, draw, mover, table_end)
    draw_footer(draw, note)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG", optimize=True)
    return output_path
