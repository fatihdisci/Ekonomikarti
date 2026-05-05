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


NOON_SYSTEM_PROMPT = """\
Sen bir ekonomi analisti ve sosyal medya editörüsün.
Sana tek bir göstergenin bugünkü değeri ve geçmiş değerleri verilecek.
Tarihsel perspektifi vurgulayan, "hatırlatma" tonunda kısa bir Türkçe analiz notu yaz.
1-2 cümle. Emoji kullanma. Hashtag ekleme.\
"""


def generate_noon_caption(payload: dict) -> str:
    """Öğle "Odak Kartı" için tek göstergeye odaklı LLM notu üret."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("OPENROUTER_MODEL", OPENROUTER_DEFAULT_MODEL)

    if not api_key:
        return "Analiz notu üretilemedi (API anahtarı eksik)."

    focus = payload.get("focus") or {}
    name = focus.get("name", "")
    current = focus.get("current")
    unit = focus.get("unit", "")
    daily_pct = focus.get("daily_pct")

    parts = [f"{name}: {current} {unit}"]
    if daily_pct is not None:
        parts.append(f"günlük %{daily_pct:+.2f}")
    for item in focus.get("history", []) or []:
        if item.get("value") is None:
            continue
        parts.append(
            f"{item['label']}: {item['value']} {unit} (%{item['pct']:+.2f})"
        )

    user_prompt = (
        f"Tarih: {payload.get('date', 'bugün')}\n\n"
        + "\n".join(parts)
        + "\n\nBu tek gösterge için kısa bir analiz/hatırlatma notu yaz."
    )

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": NOON_SYSTEM_PROMPT},
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
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Analiz notu üretilemedi: {e}"


WEEKLY_SYSTEM_PROMPT = """\
Sen bir ekonomi analisti ve sosyal medya editörüsün.
Sana haftanın 5 göstergesinin Cuma kapanışı ve haftalık % değişimi verilecek.
Haftayı zoom-out perspektifinde özetleyen kısa bir Türkçe analiz notu yaz.
1-2 cümle. Emoji kullanma. Hashtag ekleme.\
"""


def generate_weekly_caption(payload: dict) -> str:
    """Cumartesi 'Haftalık Özet' için kısa hafta özeti üret."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("OPENROUTER_MODEL", OPENROUTER_DEFAULT_MODEL)

    if not api_key:
        return "Analiz notu üretilemedi (API anahtarı eksik)."

    lines = []
    for ind in payload.get("indicators", []) or []:
        name = ind["name"]
        current = ind["current"]
        unit = ind.get("unit", "")
        weekly = ind.get("weekly_pct")
        parts = [f"{name}: {current} {unit} (Cuma kapanışı)"]
        if weekly is not None:
            parts.append(f"haftalık %{weekly:+.2f}")
        lines.append(", ".join(parts))

    user_prompt = (
        f"Tarih: {payload.get('date', 'bugün')} (Cuma: {payload.get('friday', '?')})\n\n"
        + "\n".join(lines)
        + "\n\nBu hafta özetini kısa bir analiz notuyla yaz."
    )

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": WEEKLY_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 200,
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        resp = requests.post(OPENROUTER_URL, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Analiz notu üretilemedi: {e}"


HIGHLIGHT_SYSTEM_PROMPT = """\
Sen bir ekonomi analisti ve sosyal medya editörüsün.
Sana haftanın en çok yükselen ve en çok düşen göstergesi verilecek.
İki uç noktayı karşılaştıran, kısa ve hikaye odaklı bir Türkçe analiz notu yaz.
1-2 cümle. Emoji kullanma. Hashtag ekleme.\
"""


def generate_highlight_caption(payload: dict) -> str:
    """Pazar 'Yıldız/Kaybeden' için kısa karşılaştırma yorumu üret."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("OPENROUTER_MODEL", OPENROUTER_DEFAULT_MODEL)

    if not api_key:
        return "Analiz notu üretilemedi (API anahtarı eksik)."

    star = payload.get("star") or {}
    loser = payload.get("loser") or {}

    lines = []
    if star:
        lines.append(
            f"Haftanın yıldızı: {star.get('name')} {star.get('current')} {star.get('unit', '')} "
            f"(haftalık %{star.get('weekly_pct'):+.2f})"
        )
    if loser:
        lines.append(
            f"Haftanın kaybedeni: {loser.get('name')} {loser.get('current')} {loser.get('unit', '')} "
            f"(haftalık %{loser.get('weekly_pct'):+.2f})"
        )

    user_prompt = (
        f"Tarih: {payload.get('date', 'bugün')}\n\n"
        + "\n".join(lines)
        + "\n\nBu iki uç hareketi karşılaştıran kısa bir not yaz."
    )

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": HIGHLIGHT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 200,
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        resp = requests.post(OPENROUTER_URL, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Analiz notu üretilemedi: {e}"


EVENING_SYSTEM_PROMPT = """\
Sen bir ekonomi analisti ve sosyal medya editörüsün.
Sana günü kapatırken piyasaların kapanış değerleri ve günün en sert hareketi verilecek.
"Günü kapatma" tonunda kısa bir Türkçe analiz notu yaz.
1-2 cümle. Emoji kullanma. Hashtag ekleme.\
"""


def generate_evening_caption(payload: dict) -> str:
    """Akşam "Kapanış Kartı" için kısa kapanış yorumu üret."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("OPENROUTER_MODEL", OPENROUTER_DEFAULT_MODEL)

    if not api_key:
        return "Analiz notu üretilemedi (API anahtarı eksik)."

    lines = []
    for ind in payload.get("indicators", []) or []:
        name = ind["name"]
        current = ind["current"]
        unit = ind.get("unit", "")
        daily = ind.get("daily_pct")
        parts = [f"{name}: {current} {unit}"]
        if daily is not None:
            parts.append(f"günlük %{daily:+.2f}")
        lines.append(", ".join(parts))

    mover = payload.get("biggest_mover")
    if mover:
        lines.append(
            f"Günün en sert hareketi: {mover['name']} (%{mover['daily_pct']:+.2f})"
        )

    user_prompt = (
        f"Tarih: {payload.get('date', 'bugün')}\n\n"
        + "\n".join(lines)
        + "\n\nGünü kapatan bir analiz notu yaz."
    )

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": EVENING_SYSTEM_PROMPT},
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
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Analiz notu üretilemedi: {e}"
