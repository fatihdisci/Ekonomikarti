"""Noon "Odak Kartı" renderer: huge value + 5-year sparkline + history rows."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from src.config import LAYOUT
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
    draw_sparkline_with_area,
    format_pct,
    format_tr,
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
    draw_eyebrow(draw, _PAD, ty, "02", "Odak · Tarihsel Bakış")
    h1f = load_font("inter_bold", 62)
    _, lh = text_size(h1f, "A")
    lh_actual = int(lh * 0.95)
    draw.text((_PAD, ty + 22), "Bir göstergenin", fill=color("text"), font=h1f)
    draw.text((_PAD, ty + 22 + lh_actual + 4), "5 yıllık hafızası.", fill=color("text"), font=h1f)


def _draw_focus_hero(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    focus: dict[str, Any],
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    CARD_Y = _TBL + 16
    CARD_H = 410
    CARD_END = CARD_Y + CARD_H

    sh = color("surface_hi")
    sh_rgb = (int(sh[1:3], 16), int(sh[3:5], 16), int(sh[5:7], 16))
    img, draw = composite_rect(
        img,
        [_PAD, CARD_Y, _W - _PAD, CARD_END],
        fill_rgba=(*sh_rgb, 255),
        outline_rgba=color_rgba("border_hi"),
        radius=20,
    )

    ix = _PAD + 36
    iy = CARD_Y + 30

    # ── Header row ─────────────────────────────────────────────────────────
    lf = load_font("mono_medium", 11)
    draw.text((ix, iy), "◆  ODAK", fill=color("accent"), font=lf)

    daily = focus.get("daily_pct")
    if daily is not None:
        af = load_font("mono_medium", 18)
        at = f"{arrow_for(daily)} {format_pct(daily)}"
        aw, _ = text_size(af, at)
        draw.text((_W - _PAD - 36 - aw, iy), at, fill=change_color(daily), font=af)

    # ── Indicator name ──────────────────────────────────────────────────────
    nf = load_font("inter_bold", 36)
    name = focus.get("name", "")
    draw.text((ix, iy + 20), name, fill=color("text"), font=nf)

    # ── Big value ───────────────────────────────────────────────────────────
    decimals = int(focus.get("decimals", 4))
    current = float(focus["current"])
    unit = focus.get("unit", "")
    vf = load_font("mono_bold", 96)
    uf = load_font("mono_medium", 22)
    val_str = format_tr(current, decimals)
    vw, vh = text_size(vf, val_str)
    draw.text((ix, iy + 68), val_str, fill=color("text"), font=vf)
    draw.text((ix + vw + 14, iy + 68 + vh - text_size(uf, unit)[1] - 2), unit, fill=color("muted"), font=uf)

    # ── Sparkline ───────────────────────────────────────────────────────────
    spark = focus.get("sparkline") or []
    SPARK_Y = iy + 68 + vh + 16
    SPARK_H = 96
    SPARK_W = _W - 2 * _PAD - 72

    if spark:
        img, draw = draw_sparkline_with_area(
            img, draw, spark,
            ix, SPARK_Y, SPARK_W, SPARK_H,
            color("accent"), pad=4, line_width=2, area_alpha=45, dot=True,
        )

    # ── Axis labels ─────────────────────────────────────────────────────────
    year_f = load_font("mono_medium", 10)
    ax_y = SPARK_Y + SPARK_H + 4
    years = ["2021", "2022", "2023", "2024", "2025", "2026"]
    step = SPARK_W // (len(years) - 1)
    for i, yr in enumerate(years):
        xpos = ix + i * step
        fc = color("accent") if yr == "2026" else color("dim")
        draw.text((xpos, ax_y), yr + (" ★" if yr == "2026" else ""), fill=fc, font=year_f)

    return img, draw, CARD_END


def _draw_history_rows(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    focus: dict[str, Any],
    start_y: int,
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    history = focus.get("history") or []
    if not history:
        return img, draw

    decimals = int(focus.get("decimals", 4))
    unit = focus.get("unit", "")
    current = float(focus["current"])

    n = len(history)
    avail = LAYOUT.header_h + LAYOUT.title_h + LAYOUT.table_h - start_y - 10
    row_h = min(avail // n, 210)

    for i, item in enumerate(history):
        row_y = start_y + 14 + i * (row_h + 14)
        card_h = row_h

        s = color("surface")
        s_rgb = (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))
        img, draw = composite_rect(
            img,
            [_PAD, row_y, _W - _PAD, row_y + card_h],
            fill_rgba=(*s_rgb, 255),
            outline_rgba=color_rgba("border"),
            radius=16,
        )

        ix = _PAD + 30
        iy = row_y + 18

        # Label + date
        lbl_f = load_font("mono_medium", 10)
        lbl = item.get("label", "")
        days = item.get("days")
        lbl_date = item.get("date", "")
        draw.text((ix, iy), lbl, fill=color("dim"), font=lbl_f)

        # Value
        val = item.get("value")
        vf = load_font("mono_bold", 38)
        uf_sm = load_font("mono_medium", 13)
        if val is None:
            val_str = "—"
        else:
            val_str = format_tr(float(val), decimals)
        draw.text((ix, iy + 18), val_str, fill=color("text"), font=vf)
        vw, vh = text_size(vf, val_str)
        draw.text((ix + vw + 8, iy + 18 + vh - text_size(uf_sm, unit)[1] - 2), unit, fill=color("dim"), font=uf_sm)

        # ×multiplier
        if val is not None and float(val) != 0:
            multiple = current / float(val)
            mf = load_font("mono_bold", 24)
            ml = load_font("mono_medium", 10)
            m_str = f"×{multiple:.1f}"
            mw, _ = text_size(mf, m_str)
            mx = _W - _PAD - 36 - mw - 100
            draw.text((mx, iy + 16), "KAT", fill=color("dim"), font=ml)
            draw.text((mx, iy + 28), m_str, fill=color("accent"), font=mf)

        # Percentage change
        pct = item.get("pct")
        if pct is not None:
            pf = load_font("mono_bold", 26)
            pct_str = f"{arrow_for(float(pct))} {format_pct(float(pct))}"
            pw, _ = text_size(pf, pct_str)
            pl = load_font("mono_medium", 10)
            draw.text((_W - _PAD - 36 - pw, iy + 16), "DEĞİŞİM", fill=color("dim"), font=pl)
            draw.text((_W - _PAD - 36 - pw, iy + 28), pct_str, fill=change_color(float(pct)), font=pf)

    return img, draw


def _parse_target_date(payload: dict[str, Any]) -> date:
    raw = payload.get("date")
    if isinstance(raw, str):
        return datetime.strptime(raw, "%Y-%m-%d").date()
    return date.today()


def render_noon(payload: dict[str, Any], output_path: Path) -> Path:
    """Öğle Odak Kartı'nı oluştur ve PNG olarak kaydet."""
    target_date = _parse_target_date(payload)
    focus = payload.get("focus") or {}
    if not focus:
        raise ValueError("noon payload missing 'focus' block")
    note = payload.get("note") or ""

    img = Image.new("RGB", (_W, _H), color=color("bg"))
    draw = ImageDraw.Draw(img)

    draw_corner_marks(draw)
    img, draw = draw_header(img, target_date, "NOON · 13:00")
    _draw_title(draw)
    img, draw, hero_end = _draw_focus_hero(img, draw, focus)
    img, draw = _draw_history_rows(img, draw, focus, hero_end)
    draw_footer(draw, note)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG", optimize=True)
    return output_path
