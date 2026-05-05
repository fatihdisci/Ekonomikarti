"""Tests for the Saturday weekly summary card."""

from __future__ import annotations

from datetime import date

from PIL import Image

from src.data.calculator import _last_friday_on_or_before, build_weekly_payload
from src.pipeline import run_weekly


def test_render_dry_run():
    output_path = run_weekly(dry_run=True)
    assert output_path.exists()
    with Image.open(output_path) as img:
        assert img.size == (1080, 1350)

    caption_path = output_path.parent / "caption_weekly.txt"
    assert caption_path.exists()
    assert "#fiyathafizasi" in caption_path.read_text(encoding="utf-8")


def test_last_friday_resolution():
    # Cumartesi 2026-05-09 → bir önceki gün Cuma 2026-05-08
    assert _last_friday_on_or_before(date(2026, 5, 9)) == date(2026, 5, 8)
    # Pazar 2026-05-10 → 2026-05-08
    assert _last_friday_on_or_before(date(2026, 5, 10)) == date(2026, 5, 8)
    # Cuma'nın kendisi → kendisi
    assert _last_friday_on_or_before(date(2026, 5, 8)) == date(2026, 5, 8)
    # Salı 2026-05-05 → bir önceki Cuma 2026-05-01
    assert _last_friday_on_or_before(date(2026, 5, 5)) == date(2026, 5, 1)


def test_weekly_pct_calculation():
    saturday = date(2026, 5, 9)
    friday = date(2026, 5, 8)
    prev_friday = date(2026, 5, 1)

    series_map = {
        # +5.00%
        "usd_try":  {prev_friday: 40.0, friday: 42.0},
        # -2.00%
        "eur_try":  {prev_friday: 50.0, friday: 49.0},
        "gram_altin": {prev_friday: 6500.0, friday: 6630.0},  # +2.00%
        "brent":      {prev_friday: 100.0, friday: 97.0},     # -3.00%
        "bist_100":   {prev_friday: 14000.0, friday: 14350.0},# +2.50%
    }
    payload = build_weekly_payload(series_map, target_date=saturday)
    assert payload["friday"] == "2026-05-08"

    by_key = {ind["key"]: ind for ind in payload["indicators"]}
    assert by_key["usd_try"]["weekly_pct"] == 5.00
    assert by_key["eur_try"]["weekly_pct"] == -2.00
    assert by_key["brent"]["weekly_pct"] == -3.00
