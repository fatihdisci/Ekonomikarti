"""Weekly "Haftalık Özet" renderer (Cumartesi): ranked rows with sparklines."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from src.config import INDICATOR_ORDER, LAYOUT
from src.render.base import (
    arrow_for,
    change_color,
    color,
    color_rgba,
    composite_rect,
    draw_corner_marks,
    draw_eyebrow,
    draw_footer,
    draw_header,
    draw_sparkline,
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
    draw_eyebrow(draw, _PAD, ty, "04", "Hafta Sonu · Geçen Hafta")
    h1f = load_font("inter_bold", 58)
    _, lh = text_size(h1f, "A")
    draw.text((_PAD, ty + 22), "Haftalık Özet", fill=color("text"), font=h1f)
    mf = load_font("inter_regular", 28)
    draw.text((_PAD, ty + 22 + int(lh * 0.95) + 4), "Pazartesi → Cuma", fill=color("muted"), font=mf)


def _draw_ranked_rows(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    indicators: list[dict[str, Any]],
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    if not indicators:
        return img, draw

    # Sort by weekly_pct descending
    sorted_inds = sorted(
        [i for i in indicators if i.get("weekly_pct") is not None],
        key=lambda x: float(x["weekly_pct"]),
        reverse=True,
    )
    # Append any without weekly_pct at the end
    sorted_inds += [i for i in indicators if i.get("weekly_pct") is None]

    max_abs = max((abs(float(i["weekly_pct"])) for i in sorted_inds if i.get("weekly_pct") is not None), default=1.0)

    START_Y = _TBL + 16
    n = len(sorted_inds)
    table_end = LAYOUT.header_h + LAYOUT.title_h + LAYOUT.table_h
    avail = table_end - START_Y
    ROW_H = min((avail - (n - 1) * 12) // n, 150)
    ROW_GAP = 12

    SPARK_W, SPARK_H = 140, 36
    BAR_W = 100

    for i, ind in enumerate(sorted_inds):
        row_y = START_Y + i * (ROW_H + ROW_GAP)
        card_end = row_y + ROW_H

        s = color("surface")
        img, draw = composite_rect(
            img,
            [_PAD, row_y, _W - _PAD, card_end],
            fill_rgba=(*hex_to_rgb(s), 255),
            outline_rgba=color_rgba("border"),
            radius=14,
        )

        ix = _PAD + 22
        cy = row_y + ROW_H // 2

        weekly = ind.get("weekly_pct")

        # Rank badge
        rank_f = load_font("mono_bold", 14)
        badge_color = color("accent") if i == 0 else color("dim")
        draw.text((ix, cy - text_size(rank_f, "#1")[1] // 2), f"#{i+1}", fill=badge_color, font=rank_f)

        # Name + value
        name_f = load_font("inter_semibold", 18)
        val_f  = load_font("mono_medium", 13)
        name_x = ix + 42
        draw.text((name_x, cy - 14), ind.get("name", ""), fill=color("text"), font=name_f)
        decimals = int(ind.get("decimals", 2))
        current = float(ind["current"])
        unit = ind.get("unit", "")
        val_str = f"{format_tr(current, decimals)} {unit}".strip()
        draw.text((name_x, cy + 8), val_str, fill=color("dim"), font=val_f)

        # Sparkline
        spark = ind.get("sparkline") or []
        spark_x = _W // 2 - SPARK_W // 2 - 30
        spark_y = cy - SPARK_H // 2
        fc = change_color(float(weekly)) if weekly is not None else color("muted")
        if spark:
            draw_sparkline(draw, spark, spark_x, spark_y, SPARK_W, SPARK_H,
                           fc, pad=2, line_width=2, dot=False)

        # Diverging bar
        if weekly is not None:
            wf = float(weekly)
            bar_center_x = _W - _PAD - 130 - 16
            bar_y = cy - 5
            bar_h = 10
            # Track
            draw.rounded_rectangle(
                [bar_center_x - BAR_W // 2, bar_y + bar_h // 4,
                 bar_center_x + BAR_W // 2, bar_y + 3 * bar_h // 4],
                radius=2, fill=color_rgba("border")[:3],
            )
            # Center mark
            img, draw = composite_rect(
                img,
                [bar_center_x - 1, bar_y, bar_center_x + 1, bar_y + bar_h],
                fill_rgba=color_rgba("border_hi"),
                radius=1,
            )
            # Fill bar
            fill_w = int(abs(wf) / max_abs * (BAR_W // 2 - 2))
            if fill_w > 0:
                fc_rgb = hex_to_rgb(fc)
                if wf >= 0:
                    bx1, bx2 = bar_center_x, bar_center_x + fill_w
                else:
                    bx1, bx2 = bar_center_x - fill_w, bar_center_x
                img, draw = composite_rect(
                    img,
                    [bx1, bar_y + 1, bx2, bar_y + bar_h - 1],
                    fill_rgba=(*fc_rgb, 180),
                    radius=2,
                )

        # Weekly pct
        if weekly is not None:
            pf_font = load_font("mono_bold", 20)
            pct_str = f"{arrow_for(float(weekly))} {format_pct(float(weekly))}"
            pw, ph = text_size(pf_font, pct_str)
            draw.text((_W - _PAD - 30 - pw, cy - ph // 2), pct_str, fill=fc, font=pf_font)

    return img, draw


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

    img = Image.new("RGB", (_W, _H), color=color("bg"))
    draw = ImageDraw.Draw(img)

    draw_corner_marks(draw)
    img, draw = draw_header(img, target_date, "WEEKLY · CUMARTESİ")
    _draw_title(draw)
    img, draw = _draw_ranked_rows(img, draw, indicators)
    draw_footer(draw, note)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG", optimize=True)
    return output_path
