"""Morning card renderer: hero indicator + 2×2 compact grid (1080×1350)."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from src.config import CHANGE_WINDOWS, INDICATOR_ORDER, LAYOUT
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
    draw_range_bar,
    format_pct,
    format_tr,
    hex_to_rgb,
    load_font,
    text_size,
    wrap_lines,
)

# ── Layout constants ───────────────────────────────────────────────────────────
_PAD = LAYOUT.padding_x          # 60
_W   = LAYOUT.canvas_w           # 1080
_H   = LAYOUT.canvas_h           # 1350
_TBL = LAYOUT.header_h + LAYOUT.title_h  # 290 (table area start)

_HERO_Y  = _TBL + 18             # 308
_HERO_H  = 338
_HERO_END = _HERO_Y + _HERO_H    # 646

_GRID_Y   = _HERO_END + 22       # 668
_GRID_RH  = 218                  # row height
_GRID_GAP = 16                   # column gap
_GRID_CW  = (_W - 2 * _PAD - _GRID_GAP) // 2  # 452

_GRID_R1  = _GRID_Y               # 668
_GRID_R2  = _GRID_R1 + _GRID_RH + 16  # 902


def _draw_title(draw: ImageDraw.ImageDraw) -> None:
    ty = LAYOUT.header_h + 14
    ey = draw_eyebrow(draw, _PAD, ty, "01", "Açılış · Opening Snapshot")
    h1f = load_font("inter_bold", 62)
    draw.text((_PAD, ey + 14), "Bugün piyasa", fill=color("text"), font=h1f)
    _, lh = text_size(h1f, "A")
    draw.text((_PAD, ey + 14 + int(lh * 0.95) + 4), "nasıl açıyor?", fill=color("text"), font=h1f)


def _draw_hero(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    hero: dict[str, Any],
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Hero card: big value, sparkline, 5y range, 4 change columns."""
    sh_rgb = hex_to_rgb(color("surface_hi"))
    img, draw = composite_rect(
        img,
        [_PAD, _HERO_Y, _W - _PAD, _HERO_END],
        fill_rgba=(*sh_rgb, 255),
        outline_rgba=color_rgba("border_hi"),
        radius=18,
    )

    inner_x = _PAD + 30
    inner_y = _HERO_Y + 26

    # ── Left zone ────────────────────────────────────────────────────────────
    # Label
    lf = load_font("mono_medium", 11)
    draw.text((inner_x, inner_y), "★  ANA GÖSTERGE", fill=color("accent"), font=lf)

    # Indicator name
    nf = load_font("inter_semibold", 22)
    draw.text((inner_x, inner_y + 20), hero.get("name", ""), fill=color("muted"), font=nf)

    # Value
    decimals = int(hero.get("decimals", 2))
    current = float(hero["current"])
    unit = hero.get("unit", "")
    vf = load_font("mono_bold", 62)
    uf = load_font("mono_medium", 16)
    val_text = format_tr(current, decimals)
    vw, vh = text_size(vf, val_text)
    draw.text((inner_x, inner_y + 46), val_text, fill=color("text"), font=vf)
    draw.text((inner_x + vw + 10, inner_y + 46 + vh - text_size(uf, unit)[1]), unit, fill=color("muted"), font=uf)

    # Daily change
    changes = hero.get("changes_pct", {})
    daily = changes.get("daily")
    if daily is not None:
        af = load_font("mono_medium", 16)
        arrow_text = arrow_for(daily)
        pct_text = f"{format_pct(daily)} bugün"
        aw, _ = text_size(af, arrow_text + " ")
        draw.text((inner_x, inner_y + 126), arrow_text + " ", fill=change_color(daily), font=af)
        draw.text((inner_x + aw, inner_y + 126), pct_text, fill=change_color(daily), font=af)

    # ── Right zone: sparkline ─────────────────────────────────────────────────
    spark = hero.get("sparkline") or []
    RIGHT_X = _W - _PAD - 30 - 310
    SPARK_W, SPARK_H = 310, 88

    spark_label_f = load_font("mono_medium", 10)
    draw.text((RIGHT_X, inner_y), "SON 12 AY", fill=color("dim"), font=spark_label_f)

    if spark:
        img, draw = draw_sparkline_with_area(
            img, draw, spark,
            RIGHT_X, inner_y + 16, SPARK_W, SPARK_H,
            color("accent"), pad=4, line_width=2, area_alpha=55,
        )

    # 5-year range bar
    r5y = hero.get("range_5y")
    if r5y:
        lo, hi = float(r5y["lo"]), float(r5y["hi"])
        rng = hi - lo or 1.0
        pct = max(0.0, min(100.0, (current - lo) / rng * 100))
        bar_y = inner_y + 16 + SPARK_H + 18
        draw.text((RIGHT_X, bar_y), "5 YIL ARALIĞI", fill=color("dim"), font=spark_label_f)
        draw_range_bar(draw, RIGHT_X, bar_y + 14, SPARK_W, 12, pct,
                       track_color=color("surface"), dot_color=color("accent"))
        lof = load_font("mono_medium", 10)
        draw.text((RIGHT_X, bar_y + 30), format_tr(lo, 2), fill=color("muted"), font=lof)
        hi_str = format_tr(hi, 2)
        hiw, _ = text_size(lof, hi_str)
        draw.text((RIGHT_X + SPARK_W - hiw, bar_y + 30), hi_str, fill=color("muted"), font=lof)

    # ── Bottom: 4 change columns ──────────────────────────────────────────────
    sep_y = _HERO_Y + _HERO_H - 108
    draw.line(
        [(_PAD + 16, sep_y), (_W - _PAD - 16, sep_y)],
        fill=color_rgba("border")[:3],
        width=1,
    )

    col_labels = [("GÜNLÜK", "daily"), ("AYLIK", "monthly"), ("YILLIK", "yearly"), ("5 YIL", "five_year")]
    col_w = (_W - 2 * _PAD) // 4
    col_y = sep_y + 16
    lbl_f = load_font("mono_medium", 10)
    val_f = load_font("mono_bold", 20)

    for i, (lbl, key) in enumerate(col_labels):
        cx = _PAD + col_w * i + col_w // 2
        raw = changes.get(key)

        lw, _ = text_size(lbl_f, lbl)
        draw.text((cx - lw // 2, col_y), lbl, fill=color("dim"), font=lbl_f)

        if raw is None:
            txt = "—"
            fc = color("muted")
        else:
            v = float(raw)
            txt = f"{arrow_for(v)} {format_pct(v)}"
            fc = change_color(v)
        vw2, _ = text_size(val_f, txt)
        draw.text((cx - vw2 // 2, col_y + 18), txt, fill=fc, font=val_f)

    return img, draw


def _draw_compact_card(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    ind: dict[str, Any],
    idx: int,
    x: int,
    y: int,
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Single compact 2×2 indicator card."""
    s = color("surface")
    s_rgb = (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))
    img, draw = composite_rect(
        img,
        [x, y, x + _GRID_CW, y + _GRID_RH],
        fill_rgba=(*s_rgb, 255),
        outline_rgba=color_rgba("border"),
        radius=16,
    )

    ix = x + 20
    iy = y + 18

    # Header row: number + name label + daily badge
    num_f = load_font("mono_medium", 11)
    nm_f = load_font("inter_semibold", 14)
    pct_badge_f = load_font("mono_medium", 11)

    draw.text((ix, iy), f"{idx+2:02d} ·", fill=color("dim"), font=num_f)
    nw, _ = text_size(num_f, f"{idx+2:02d} · ")
    draw.text((ix + nw, iy), ind.get("name", ""), fill=color("muted"), font=nm_f)

    changes = ind.get("changes_pct", {})
    daily = changes.get("daily")
    if daily is not None:
        dv = float(daily)
        badge_text = format_pct(dv)
        bw, bh = text_size(pct_badge_f, badge_text)
        bx = x + _GRID_CW - 20 - bw - 16
        by = iy - 1
        bc = change_color_rgba(dv)
        img, draw = composite_rect(
            img,
            [bx - 8, by - 2, bx + bw + 8, by + bh + 2],
            fill_rgba=bc,
            radius=4,
        )
        draw.text((bx, by), badge_text, fill=change_color(dv), font=pct_badge_f)

    # Value
    decimals = int(ind.get("decimals", 2))
    current = float(ind["current"])
    unit = ind.get("unit", "")
    vf = load_font("mono_bold", 28)
    uf = load_font("mono_medium", 11)
    val_str = format_tr(current, decimals)
    vw, vh = text_size(vf, val_str)
    draw.text((ix, iy + 30), val_str, fill=color("text"), font=vf)
    draw.text((ix + vw + 6, iy + 30 + vh - text_size(uf, unit)[1] - 2), unit, fill=color("dim"), font=uf)

    # 1Y / 5Y row
    y1y = changes.get("yearly")
    y5y = changes.get("five_year")
    mf = load_font("mono_medium", 11)
    bottom_y = y + _GRID_RH - 28
    parts = []
    if y1y is not None:
        parts.append(("1Y ", color("dim")))
        parts.append((format_pct(float(y1y)) + "  ", change_color(float(y1y))))
    if y5y is not None:
        parts.append(("5Y ", color("dim")))
        parts.append((format_pct(float(y5y)), change_color(float(y5y))))
    cx2 = ix
    for txt, fc in parts:
        draw.text((cx2, bottom_y), txt, fill=fc, font=mf)
        cx2 += text_size(mf, txt)[0]

    return img, draw


def _draw_grid(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    inds: list[dict[str, Any]],
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    positions = [
        (_PAD, _GRID_R1),
        (_PAD + _GRID_CW + _GRID_GAP, _GRID_R1),
        (_PAD, _GRID_R2),
        (_PAD + _GRID_CW + _GRID_GAP, _GRID_R2),
    ]
    for i, (x, y) in enumerate(positions):
        if i >= len(inds):
            break
        img, draw = _draw_compact_card(img, draw, inds[i], i, x, y)
    return img, draw


def _parse_target_date(payload: dict[str, Any]) -> date:
    raw = payload.get("date")
    if isinstance(raw, str):
        return datetime.strptime(raw, "%Y-%m-%d").date()
    return date.today()


def render_morning(payload: dict[str, Any], output_path: Path) -> Path:
    """Sabah açılış kartını oluştur ve PNG olarak kaydet."""
    target_date = _parse_target_date(payload)
    indicators_list = payload.get("indicators", []) or []
    note = payload.get("note") or ""

    by_key = {ind["key"]: ind for ind in indicators_list}
    ordered = [by_key[k] for k in INDICATOR_ORDER if k in by_key]
    hero = ordered[0] if ordered else {}
    grid_inds = ordered[1:5]  # max 4 in 2×2

    img = Image.new("RGB", (_W, _H), color=color("bg"))
    draw = ImageDraw.Draw(img)

    draw_corner_marks(draw)
    img, draw = draw_header(img, target_date, "MORNING · 09:00")
    _draw_title(draw)
    img, draw = _draw_hero(img, draw, hero)
    img, draw = _draw_grid(img, draw, grid_inds)
    draw_footer(draw, note)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG", optimize=True)
    return output_path
