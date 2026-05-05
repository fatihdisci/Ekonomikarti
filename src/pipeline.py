"""End-to-end pipeline for the morning card.

Phase 1 dry-run support only. Live data, caption generation and JSON output
are stubbed and will be filled in after the visual approval gate.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.config import FIXTURES_DIR, HASHTAG, IMAGE_OUTPUT_DIR
from src.render.morning import render_morning


def _load_fixture() -> dict:
    path = FIXTURES_DIR / "sample_indicators.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Test verisi bulunamadı: {path}. tests/fixtures/sample_indicators.json gerekli."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def run_morning(dry_run: bool = False) -> Path:
    """Sabah kartını üret. Dönen değer üretilen PNG dosyasının yolu."""
    if not dry_run:
        # Filled in after visual approval — Step 8 in the build plan.
        raise NotImplementedError(
            "Canlı veri akışı henüz hazır değil. Görsel onayı bekleniyor; --dry-run ile çalıştırın."
        )

    payload = _load_fixture()
    out_dir = IMAGE_OUTPUT_DIR / "test"
    png_path = out_dir / "morning.png"
    render_morning(payload, png_path)

    caption_path = out_dir / "caption.txt"
    note = payload.get("note") or ""
    caption_path.write_text(f"{note}\n\n{HASHTAG}\n", encoding="utf-8")

    return png_path
