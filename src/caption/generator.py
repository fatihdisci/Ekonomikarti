"""Caption generation via OpenRouter LLM."""

from __future__ import annotations

import json
import os

import requests

from src.config import OPENROUTER_DEFAULT_MODEL, OPENROUTER_URL


SYSTEM_PROMPT = """\
Sen bir ekonomi analisti ve sosyal medya editörüsün.
Sana günlük ekonomi göstergelerinin verileri verilecek.
Kısa, akılda kalıcı, 1-2 cümlelik bir Türkçe analiz notu yaz.
Emoji kullanma.  Hashtag ekleme.
Verilerden ilginç bir karşılaştırma veya trend çıkar.\
"""


def generate_caption(payload: dict) -> str:
    """Call OpenRouter to generate a short analysis note.

    Parameters
    ----------
    payload : dict
        The full indicator payload (same schema as sample_indicators.json).

    Returns
    -------
    str
        A 1-2 sentence Turkish analysis note.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("OPENROUTER_MODEL", OPENROUTER_DEFAULT_MODEL)

    if not api_key:
        return "Analiz notu üretilemedi (API anahtarı eksik)."

    # Build user prompt from the indicators
    lines = []
    for ind in payload.get("indicators", []):
        name = ind["name"]
        current = ind["current"]
        unit = ind.get("unit", "")
        changes = ind.get("changes_pct", {})
        daily = changes.get("daily")
        yearly = changes.get("yearly")
        five_year = changes.get("five_year")

        parts = [f"{name}: {current} {unit}"]
        if daily is not None:
            parts.append(f"günlük %{daily:+.2f}")
        if yearly is not None:
            parts.append(f"yıllık %{yearly:+.2f}")
        if five_year is not None:
            parts.append(f"5 yıl %{five_year:+.0f}")
        lines.append(", ".join(parts))

    user_prompt = (
        f"Tarih: {payload.get('date', 'bugün')}\n\n"
        + "\n".join(lines)
        + "\n\nBu verilere göre kısa bir analiz notu yaz."
    )

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 200,
        "temperature": 0.7,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(OPENROUTER_URL, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        note = data["choices"][0]["message"]["content"].strip()
        return note
    except Exception as e:
        return f"Analiz notu üretilemedi: {e}"
