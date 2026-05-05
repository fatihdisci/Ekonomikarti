"""Calculate percentage changes and build the final indicator payload."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from src.config import CHANGE_WINDOWS, INDICATORS, TROY_OZ_GRAM


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
