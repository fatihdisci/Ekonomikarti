"""Tests for the evening "Kapanış Kartı" pipeline."""

from __future__ import annotations

from datetime import date

from PIL import Image

from src.data.calculator import build_evening_payload
from src.pipeline import run_evening


def test_render_dry_run():
    output_path = run_evening(dry_run=True)
    assert output_path.exists()
    assert output_path.suffix == ".png"
    with Image.open(output_path) as img:
        assert img.size == (1080, 1350)

    caption_path = output_path.parent / "caption_evening.txt"
    assert caption_path.exists()
    assert "#fiyathafizasi" in caption_path.read_text(encoding="utf-8")


def test_biggest_mover_picks_largest_absolute():
    target = date(2026, 5, 5)
    yesterday = date(2026, 5, 4)
    series_map = {
        # USD: +0.10%
        "usd_try":  {yesterday: 45.0,    target: 45.045},
        # EUR: -0.20%
        "eur_try":  {yesterday: 53.0,    target: 52.894},
        # BIST: +0.50%
        "bist_100": {yesterday: 14000.0, target: 14070.0},
        # Brent: -2.00%  (en sert mutlak hareket)
        "brent":    {yesterday: 100.0,   target: 98.0},
    }
    payload = build_evening_payload(series_map, target_date=target)

    assert payload["biggest_mover"]["key"] == "brent"
    assert payload["biggest_mover"]["daily_pct"] == -2.00


def test_evening_excludes_gram_altin():
    target = date(2026, 5, 5)
    yesterday = date(2026, 5, 4)
    series_map = {
        "usd_try":  {yesterday: 45.0, target: 45.0},
        "eur_try":  {yesterday: 53.0, target: 53.0},
        "bist_100": {yesterday: 14000.0, target: 14000.0},
        "brent":    {yesterday: 100.0, target: 100.0},
        "gram_altin": {yesterday: 6500.0, target: 6700.0},
    }
    payload = build_evening_payload(series_map, target_date=target)
    keys = [ind["key"] for ind in payload["indicators"]]
    assert "gram_altin" not in keys
    assert set(keys) == {"usd_try", "eur_try", "bist_100", "brent"}
