"""Tests for the noon "Odak Kartı" pipeline."""

from __future__ import annotations

from datetime import date

from PIL import Image

from src.config import NOON_ROTATION, noon_focus_key_for
from src.pipeline import run_noon


def test_rotation_weekday_mapping():
    # Pazartesi 2026-05-04 → ilk gösterge
    assert noon_focus_key_for(date(2026, 5, 4)) == NOON_ROTATION[0]
    # Cuma 2026-05-08 → beşinci gösterge
    assert noon_focus_key_for(date(2026, 5, 8)) == NOON_ROTATION[4]
    # Cumartesi → fallback (Pazartesi göstergesi)
    assert noon_focus_key_for(date(2026, 5, 9)) == NOON_ROTATION[0]


def test_rotation_unique_per_weekday():
    keys = [noon_focus_key_for(date(2026, 5, 4 + i)) for i in range(5)]
    assert len(set(keys)) == 5  # Pzt-Cum hepsi farklı


def test_render_dry_run():
    output_path = run_noon(dry_run=True)
    assert output_path.exists()
    assert output_path.suffix == ".png"
    with Image.open(output_path) as img:
        assert img.size == (1080, 1350)

    caption_path = output_path.parent / "caption_noon.txt"
    assert caption_path.exists()
    assert "#fiyathafizasi" in caption_path.read_text(encoding="utf-8")
