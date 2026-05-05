"""End-to-end pipeline for daily cards (morning, noon, ...).

Supports both dry-run (fixture data) and live mode (yfinance + OpenRouter).
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from src.config import (
    DATA_OUTPUT_DIR,
    FIXTURES_DIR,
    HASHTAG,
    IMAGE_OUTPUT_DIR,
    noon_focus_key_for,
)
from src.render.evening import render_evening
from src.render.highlight import render_highlight
from src.render.morning import render_morning
from src.render.noon import render_noon
from src.render.weekly import render_weekly

load_dotenv()


def _load_fixture(filename: str = "sample_indicators.json") -> dict:
    path = FIXTURES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Test verisi bulunamadı: {path}."
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


def _fetch_live_noon_payload(focus_key: str | None, today: date) -> dict:
    """Fetch series and build the noon payload for one focus indicator."""
    from src.data.yfinance_api import fetch_yfinance_data
    from src.data.calculator import build_noon_payload, compute_gram_altin

    if focus_key is None:
        focus_key = noon_focus_key_for(today)

    print(f"  > Yahoo Finance verisi çekiliyor (odak: {focus_key})...")
    yf_data = fetch_yfinance_data(end_date=today)

    print("  > Gram Altın hesaplanıyor...")
    gram_altin = compute_gram_altin(yf_data["gold_oz"], yf_data["usd_try"])

    series_map = {
        "usd_try": yf_data["usd_try"],
        "eur_try": yf_data["eur_try"],
        "gram_altin": gram_altin,
        "brent": yf_data["brent"],
        "bist_100": yf_data["bist_100"],
    }

    payload = build_noon_payload(series_map, focus_key=focus_key, target_date=today)
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    return payload


def run_noon(dry_run: bool = False, focus_key: str | None = None) -> Path:
    """Öğle "Odak Kartı"nı üret. Dönen değer üretilen PNG dosyasının yolu."""
    if dry_run:
        payload = _load_fixture("sample_noon.json")
        out_dir = IMAGE_OUTPUT_DIR / "test"
    else:
        today = date.today()
        payload = _fetch_live_noon_payload(focus_key, today)

        from src.caption.generator import generate_noon_caption
        print("  > LLM caption üretiliyor…")
        payload["note"] = generate_noon_caption(payload)

        out_dir = IMAGE_OUTPUT_DIR / "live"

        json_dir = DATA_OUTPUT_DIR
        json_dir.mkdir(parents=True, exist_ok=True)
        json_path = json_dir / f"noon_{payload['date']}_{payload['focus']['key']}.json"
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  > JSON kaydedildi: {json_path}")

    png_path = out_dir / "noon.png"
    render_noon(payload, png_path)

    caption_path = out_dir / "caption_noon.txt"
    note = payload.get("note") or ""
    caption_path.write_text(f"{note}\n\n{HASHTAG}\n", encoding="utf-8")

    return png_path


def _fetch_live_evening_payload(today: date) -> dict:
    """Fetch series and build evening payload (snapshot + biggest mover)."""
    from src.data.yfinance_api import fetch_yfinance_data
    from src.data.calculator import build_evening_payload

    print("  > Yahoo Finance verisi cekiliyor...")
    yf_data = fetch_yfinance_data(end_date=today)

    series_map = {
        "usd_try": yf_data["usd_try"],
        "eur_try": yf_data["eur_try"],
        "bist_100": yf_data["bist_100"],
        "brent": yf_data["brent"],
    }

    payload = build_evening_payload(series_map, target_date=today)
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    return payload


def run_evening(dry_run: bool = False) -> Path:
    """Akşam Kapanış Kartı'nı üret. Dönen değer üretilen PNG dosyasının yolu."""
    if dry_run:
        payload = _load_fixture("sample_evening.json")
        out_dir = IMAGE_OUTPUT_DIR / "test"
    else:
        today = date.today()
        payload = _fetch_live_evening_payload(today)

        from src.caption.generator import generate_evening_caption
        print("  > LLM caption üretiliyor…")
        payload["note"] = generate_evening_caption(payload)

        out_dir = IMAGE_OUTPUT_DIR / "live"

        json_dir = DATA_OUTPUT_DIR
        json_dir.mkdir(parents=True, exist_ok=True)
        json_path = json_dir / f"evening_{payload['date']}.json"
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  > JSON kaydedildi: {json_path}")

    png_path = out_dir / "evening.png"
    render_evening(payload, png_path)

    caption_path = out_dir / "caption_evening.txt"
    note = payload.get("note") or ""
    caption_path.write_text(f"{note}\n\n{HASHTAG}\n", encoding="utf-8")

    return png_path


def _fetch_live_weekly_payload(today: date) -> dict:
    """Fetch series and build the weekly payload."""
    from src.data.yfinance_api import fetch_yfinance_data
    from src.data.calculator import build_weekly_payload, compute_gram_altin

    print("  > Yahoo Finance verisi cekiliyor...")
    yf_data = fetch_yfinance_data(end_date=today)

    print("  > Gram Altin hesaplaniyor...")
    gram_altin = compute_gram_altin(yf_data["gold_oz"], yf_data["usd_try"])

    series_map = {
        "usd_try": yf_data["usd_try"],
        "eur_try": yf_data["eur_try"],
        "gram_altin": gram_altin,
        "brent": yf_data["brent"],
        "bist_100": yf_data["bist_100"],
    }

    payload = build_weekly_payload(series_map, target_date=today)
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    return payload


def run_weekly(dry_run: bool = False) -> Path:
    """Cumartesi 'Haftalık Özet' kartını üret."""
    if dry_run:
        payload = _load_fixture("sample_weekly.json")
        out_dir = IMAGE_OUTPUT_DIR / "test"
    else:
        today = date.today()
        payload = _fetch_live_weekly_payload(today)

        from src.caption.generator import generate_weekly_caption
        print("  > LLM caption üretiliyor…")
        payload["note"] = generate_weekly_caption(payload)

        out_dir = IMAGE_OUTPUT_DIR / "live"

        json_dir = DATA_OUTPUT_DIR
        json_dir.mkdir(parents=True, exist_ok=True)
        json_path = json_dir / f"weekly_{payload['date']}.json"
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  > JSON kaydedildi: {json_path}")

    png_path = out_dir / "weekly.png"
    render_weekly(payload, png_path)

    caption_path = out_dir / "caption_weekly.txt"
    note = payload.get("note") or ""
    caption_path.write_text(f"{note}\n\n{HASHTAG}\n", encoding="utf-8")

    return png_path


def _fetch_live_highlight_payload(today: date) -> dict:
    from src.data.yfinance_api import fetch_yfinance_data
    from src.data.calculator import build_highlight_payload, compute_gram_altin

    print("  > Yahoo Finance verisi cekiliyor...")
    yf_data = fetch_yfinance_data(end_date=today)

    print("  > Gram Altin hesaplaniyor...")
    gram_altin = compute_gram_altin(yf_data["gold_oz"], yf_data["usd_try"])

    series_map = {
        "usd_try": yf_data["usd_try"],
        "eur_try": yf_data["eur_try"],
        "gram_altin": gram_altin,
        "brent": yf_data["brent"],
        "bist_100": yf_data["bist_100"],
    }

    payload = build_highlight_payload(series_map, target_date=today)
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    return payload


def run_highlight(dry_run: bool = False) -> Path:
    """Pazar 'Haftanın Yıldızı/Kaybedeni' kartını üret."""
    if dry_run:
        payload = _load_fixture("sample_highlight.json")
        out_dir = IMAGE_OUTPUT_DIR / "test"
    else:
        today = date.today()
        payload = _fetch_live_highlight_payload(today)

        from src.caption.generator import generate_highlight_caption
        print("  > LLM caption üretiliyor…")
        payload["note"] = generate_highlight_caption(payload)

        out_dir = IMAGE_OUTPUT_DIR / "live"

        json_dir = DATA_OUTPUT_DIR
        json_dir.mkdir(parents=True, exist_ok=True)
        json_path = json_dir / f"highlight_{payload['date']}.json"
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  > JSON kaydedildi: {json_path}")

    png_path = out_dir / "highlight.png"
    render_highlight(payload, png_path)

    caption_path = out_dir / "caption_highlight.txt"
    note = payload.get("note") or ""
    caption_path.write_text(f"{note}\n\n{HASHTAG}\n", encoding="utf-8")

    return png_path
