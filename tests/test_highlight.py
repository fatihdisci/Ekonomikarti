"""Tests for the Sunday star/loser highlight card."""

from __future__ import annotations

from datetime import date

from PIL import Image

from src.data.calculator import build_highlight_payload
from src.pipeline import run_highlight


def test_render_dry_run():
    output_path = run_highlight(dry_run=True)
    assert output_path.exists()
    with Image.open(output_path) as img:
        assert img.size == (1080, 1350)

    caption_path = output_path.parent / "caption_highlight.txt"
    assert caption_path.exists()
    assert "#fiyathafizasi" in caption_path.read_text(encoding="utf-8")


def test_star_and_loser_selection():
    sunday = date(2026, 5, 10)
    friday = date(2026, 5, 8)
    prev_friday = date(2026, 5, 1)

    series_map = {
        "usd_try":    {prev_friday: 40.0,    friday: 40.4},      # +1.00%
        "eur_try":    {prev_friday: 50.0,    friday: 49.5},      # -1.00%
        "gram_altin": {prev_friday: 6500.0,  friday: 6630.0},    # +2.00%
        "brent":      {prev_friday: 100.0,   friday: 96.0},      # -4.00%  ← kaybeden
        "bist_100":   {prev_friday: 14000.0, friday: 14700.0},   # +5.00%  ← yıldız
    }
    payload = build_highlight_payload(series_map, target_date=sunday)
    assert payload["star"]["key"] == "bist_100"
    assert payload["star"]["weekly_pct"] == 5.00
    assert payload["loser"]["key"] == "brent"
    assert payload["loser"]["weekly_pct"] == -4.00
