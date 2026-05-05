"""End-to-end pipeline for the morning card.

Supports both dry-run (fixture data) and live mode (TCMB + yfinance + OpenRouter).
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from src.config import FIXTURES_DIR, HASHTAG, IMAGE_OUTPUT_DIR, DATA_OUTPUT_DIR
from src.render.morning import render_morning

load_dotenv()


def _load_fixture() -> dict:
    path = FIXTURES_DIR / "sample_indicators.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Test verisi bulunamadı: {path}. tests/fixtures/sample_indicators.json gerekli."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _fetch_live_data() -> dict:
    """Fetch real data from yfinance; compute payload."""
    from src.data.yfinance_api import fetch_yfinance_data
    from src.data.calculator import compute_gram_altin, build_indicator_payload

    today = date.today()

    print("  > Yahoo Finance verisi cekiliyor (doviz, borsa, petrol, altin)...")
    yf_data = fetch_yfinance_data(end_date=today)

    print("  > Gram Altin hesaplaniyor...")
    gram_altin = compute_gram_altin(yf_data["gold_oz"], yf_data["usd_try"])

    # Merge all series
    series_map = {
        "usd_try": yf_data["usd_try"],
        "eur_try": yf_data["eur_try"],
        "gram_altin": gram_altin,
        "brent": yf_data["brent"],
        "bist_100": yf_data["bist_100"],
    }

    payload = build_indicator_payload(series_map, target_date=today)
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat()

    return payload


def _generate_caption(payload: dict) -> str:
    """Generate LLM caption note."""
    from src.caption.generator import generate_caption
    print("  > LLM caption üretiliyor…")
    return generate_caption(payload)


def run_morning(dry_run: bool = False) -> Path:
    """Sabah kartını üret. Dönen değer üretilen PNG dosyasının yolu."""
    if dry_run:
        payload = _load_fixture()
        out_dir = IMAGE_OUTPUT_DIR / "test"
    else:
        payload = _fetch_live_data()

        # Generate caption via LLM
        note = _generate_caption(payload)
        payload["note"] = note

        out_dir = IMAGE_OUTPUT_DIR / "live"

        # Save the JSON payload for records
        json_dir = DATA_OUTPUT_DIR
        json_dir.mkdir(parents=True, exist_ok=True)
        json_path = json_dir / f"morning_{payload['date']}.json"
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  > JSON kaydedildi: {json_path}")

    png_path = out_dir / "morning.png"
    render_morning(payload, png_path)

    caption_path = out_dir / "caption.txt"
    note = payload.get("note") or ""
    caption_path.write_text(f"{note}\n\n{HASHTAG}\n", encoding="utf-8")

    return png_path
