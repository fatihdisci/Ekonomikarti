"""Calculate percentage changes and build the final indicator payload."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from src.config import (
    CHANGE_WINDOWS,
    EVENING_INDICATORS,
    INDICATORS,
    NOON_HISTORY_WINDOWS,
    TROY_OZ_GRAM,
)


def _nearest_value(series: dict[date, float], target: date, lookback: int = 30) -> float | None:
    """Find the value on target date, or the closest previous date (ffill).

    Searches up to `lookback` days backwards from target.
    """
    for offset in range(lookback + 1):
        d = target - timedelta(days=offset)
        if d in series:
            return series[d]
    return None


def _pct_change(current: float, previous: float) -> float:
    """Percentage change from previous to current."""
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100


def compute_gram_altin(
    gold_oz: dict[date, float],
    usd_try: dict[date, float],
) -> dict[date, float]:
    """Compute Gram Altın (TL) = (Gold Oz USD / 31.1035) * USD/TRY.

    Only dates present in BOTH series are included.
    """
    result: dict[date, float] = {}
    for d in gold_oz:
        if d in usd_try:
            gram_usd = gold_oz[d] / TROY_OZ_GRAM
            result[d] = gram_usd * usd_try[d]
    return result


def build_indicator_payload(
    series_map: dict[str, dict[date, float]],
    target_date: date | None = None,
) -> dict[str, Any]:
    """Build the final JSON payload consumed by the renderer.

    Parameters
    ----------
    series_map : dict
        Mapping indicator keys ("usd_try", "eur_try", "gram_altin",
        "brent", "bist_100", "benzin_95") to {date: float} time-series.
    target_date : date, optional
        The "today" date. Defaults to date.today().

    Returns
    -------
    dict
        Payload matching the renderer schema (same as sample_indicators.json).
    """
    if target_date is None:
        target_date = date.today()

    indicators_list: list[dict[str, Any]] = []

    for spec in INDICATORS:
        series = series_map.get(spec.key, {})
        current = _nearest_value(series, target_date, lookback=10)
        if current is None:
            # No data at all — skip this indicator
            continue

        changes: dict[str, float | None] = {}
        for window in CHANGE_WINDOWS:
            ref_date = target_date - timedelta(days=window.days)
            ref_val = _nearest_value(series, ref_date, lookback=10)
            if ref_val is not None:
                changes[window.key] = round(_pct_change(current, ref_val), 2)
            else:
                changes[window.key] = None

        indicators_list.append({
            "key": spec.key,
            "name": spec.name,
            "current": round(current, spec.decimals),
            "format": spec.fmt,
            "unit": spec.unit,
            "decimals": spec.decimals,
            "changes_pct": changes,
        })

    return {
        "date": target_date.isoformat(),
        "generated_at_utc": None,  # filled by pipeline
        "indicators": indicators_list,
        "note": "",  # filled by caption generator
    }


def build_noon_payload(
    series_map: dict[str, dict[date, float]],
    focus_key: str,
    target_date: date | None = None,
) -> dict[str, Any]:
    """Build payload for the noon "Odak Kartı" — single indicator, historical snapshots.

    Returns
    -------
    dict
        {
          "date": "2026-05-05",
          "focus": {
            "key": "usd_try", "name": "USD/TRY", "unit": "TL", "decimals": 4,
            "current": 45.2187,
            "daily_pct": 0.07,
            "history": [
              {"key": "one_year", "label": "1 YIL ÖNCE BUGÜN", "days": 365,
               "value": 38.5712, "pct": 17.23},
              ...
            ]
          },
          "note": ""
        }
    """
    if target_date is None:
        target_date = date.today()

    spec = next((s for s in INDICATORS if s.key == focus_key), None)
    if spec is None:
        raise ValueError(f"unknown focus indicator: {focus_key}")

    series = series_map.get(focus_key, {})
    current = _nearest_value(series, target_date, lookback=10)
    if current is None:
        raise ValueError(f"no data for indicator {focus_key} near {target_date}")

    # Daily change (small subtitle under current value).
    prev = _nearest_value(series, target_date - timedelta(days=1), lookback=10)
    daily_pct = round(_pct_change(current, prev), 2) if prev is not None else None

    history: list[dict[str, Any]] = []
    for window in NOON_HISTORY_WINDOWS:
        ref_date = target_date - timedelta(days=window.days)
        ref_val = _nearest_value(series, ref_date, lookback=10)
        if ref_val is None:
            history.append({
                "key": window.key,
                "label": window.label,
                "days": window.days,
                "value": None,
                "pct": None,
            })
        else:
            history.append({
                "key": window.key,
                "label": window.label,
                "days": window.days,
                "value": round(ref_val, spec.decimals),
                "pct": round(_pct_change(current, ref_val), 2),
            })

    return {
        "date": target_date.isoformat(),
        "generated_at_utc": None,
        "focus": {
            "key": spec.key,
            "name": spec.name,
            "unit": spec.unit,
            "decimals": spec.decimals,
            "current": round(current, spec.decimals),
            "daily_pct": daily_pct,
            "history": history,
        },
        "note": "",
    }


def build_evening_payload(
    series_map: dict[str, dict[date, float]],
    target_date: date | None = None,
) -> dict[str, Any]:
    """Build payload for the evening "Kapanış Kartı" — kapanış snapshot + biggest mover.

    Returns
    -------
    dict
        {
          "date": "2026-05-05",
          "indicators": [
             {"key": "usd_try", "name": "USD/TRY", "current": 45.21, ...,
              "daily_pct": 0.07},
             ...
          ],
          "biggest_mover": {"key": "brent", "name": "Brent Petrol",
                            "daily_pct": -1.55, "current": 112.67, "unit": "USD",
                            "decimals": 2},
          "note": ""
        }
    """
    if target_date is None:
        target_date = date.today()

    indicators_list: list[dict[str, Any]] = []

    for spec in INDICATORS:
        if spec.key not in EVENING_INDICATORS:
            continue
        series = series_map.get(spec.key, {})
        current = _nearest_value(series, target_date, lookback=10)
        if current is None:
            continue
        prev = _nearest_value(series, target_date - timedelta(days=1), lookback=10)
        daily_pct = round(_pct_change(current, prev), 2) if prev is not None else None

        indicators_list.append({
            "key": spec.key,
            "name": spec.name,
            "current": round(current, spec.decimals),
            "format": spec.fmt,
            "unit": spec.unit,
            "decimals": spec.decimals,
            "daily_pct": daily_pct,
        })

    biggest = None
    for ind in indicators_list:
        pct = ind.get("daily_pct")
        if pct is None:
            continue
        if biggest is None or abs(pct) > abs(biggest["daily_pct"]):
            biggest = {
                "key": ind["key"],
                "name": ind["name"],
                "current": ind["current"],
                "unit": ind["unit"],
                "decimals": ind["decimals"],
                "daily_pct": pct,
            }

    return {
        "date": target_date.isoformat(),
        "generated_at_utc": None,
        "indicators": indicators_list,
        "biggest_mover": biggest,
        "note": "",
    }


def _last_friday_on_or_before(d: date) -> date:
    """Return the most recent Friday on or before `d`."""
    # weekday(): Mon=0 ... Fri=4 ... Sun=6
    offset = (d.weekday() - 4) % 7
    return d - timedelta(days=offset)


def build_weekly_payload(
    series_map: dict[str, dict[date, float]],
    target_date: date | None = None,
) -> dict[str, Any]:
    """Build payload for the Saturday "Haftalık Özet" — Cuma kapanışı + bu hafta %.

    `target_date` is the publish date (typically Saturday). Friday close is the most
    recent Friday ≤ target_date; previous Friday is 7 days earlier.
    """
    if target_date is None:
        target_date = date.today()

    friday = _last_friday_on_or_before(target_date)
    prev_friday = friday - timedelta(days=7)

    indicators_list: list[dict[str, Any]] = []
    for spec in INDICATORS:
        series = series_map.get(spec.key, {})
        close = _nearest_value(series, friday, lookback=5)
        prev_close = _nearest_value(series, prev_friday, lookback=5)
        if close is None:
            continue
        weekly_pct = round(_pct_change(close, prev_close), 2) if prev_close is not None else None
        
        sparkline = []
        for i in range(4, -1, -1):
            day_date = friday - timedelta(days=i)
            v = _nearest_value(series, day_date, lookback=3)
            if v is not None:
                sparkline.append(round(v, spec.decimals))
                
        indicators_list.append({
            "key": spec.key,
            "name": spec.name,
            "current": round(close, spec.decimals),
            "format": spec.fmt,
            "unit": spec.unit,
            "decimals": spec.decimals,
            "weekly_pct": weekly_pct,
            "sparkline": sparkline,
        })

    return {
        "date": target_date.isoformat(),
        "friday": friday.isoformat(),
        "generated_at_utc": None,
        "indicators": indicators_list,
        "note": "",
    }


def build_highlight_payload(
    series_map: dict[str, dict[date, float]],
    target_date: date | None = None,
) -> dict[str, Any]:
    """Pazar 'Haftanın Yıldızı/Kaybedeni' payload'ı.

    Haftalık veriden en yüksek (star) ve en düşük (loser) weekly_pct'i seçer.
    """
    weekly = build_weekly_payload(series_map, target_date=target_date)
    indicators = [ind for ind in weekly["indicators"] if ind.get("weekly_pct") is not None]

    star = max(indicators, key=lambda i: i["weekly_pct"], default=None)
    loser = min(indicators, key=lambda i: i["weekly_pct"], default=None)

    def _strip(ind: dict[str, Any] | None) -> dict[str, Any] | None:
        if ind is None:
            return None
        return {
            "key": ind["key"],
            "name": ind["name"],
            "current": ind["current"],
            "unit": ind["unit"],
            "decimals": ind["decimals"],
            "weekly_pct": ind["weekly_pct"],
        }

    return {
        "date": weekly["date"],
        "friday": weekly["friday"],
        "generated_at_utc": None,
        "star": _strip(star),
        "loser": _strip(loser),
        "note": "",
    }
