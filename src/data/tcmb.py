"""TCMB EVDS API: parse fixture & fetch live data."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import requests

from src.config import TCMB_BASE_URL, TCMB_USD_TRY, TCMB_EUR_TRY


def parse_tcmb_evds(payload: dict) -> dict[str, float]:
    """Parse TCMB EVDS API JSON response.

    Returns a dictionary mapping the EVDS series keys to float values.
    Example: {"TP_DK_USD_A_YTL": 32.1234, "TP_DK_EUR_A_YTL": 34.5678}
    """
    if not payload or "items" not in payload:
        raise ValueError("Invalid TCMB JSON payload: missing 'items'")

    items = payload["items"]
    if not items:
        raise ValueError("TCMB JSON payload has empty 'items' list")

    latest_item = items[-1]

    result = {}
    for key, value in latest_item.items():
        if key in ("Tarih", "UNIXTIME"):
            continue
        try:
            result[key] = float(value)
        except (ValueError, TypeError):
            continue

    return result


def fetch_tcmb_series(
    api_key: str,
    series: str,
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    """Fetch a single EVDS series between two dates.

    Returns the raw 'items' list from the EVDS JSON response.
    Each item has 'Tarih' (DD-MM-YYYY) and a column named after the
    series key with dots replaced by underscores.
    """
    start_str = start_date.strftime("%d-%m-%Y")
    end_str = end_date.strftime("%d-%m-%Y")

    url = (
        f"{TCMB_BASE_URL}"
        f"series={series}&startDate={start_str}&endDate={end_str}&type=json"
    )
    headers = {"key": api_key}

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("items", [])


def _series_col(series: str) -> str:
    """EVDS JSON column name: dots become underscores."""
    return series.replace(".", "_")


def _items_to_dict(items: list[dict], col: str) -> dict[date, float]:
    """Convert EVDS items list to {date: value} dict, skipping None/empty."""
    from datetime import datetime

    result: dict[date, float] = {}
    for item in items:
        raw_val = item.get(col)
        if raw_val is None or raw_val == "":
            continue
        try:
            val = float(raw_val)
        except (ValueError, TypeError):
            continue
        try:
            d = datetime.strptime(item["Tarih"], "%d-%m-%Y").date()
        except (KeyError, ValueError):
            continue
        result[d] = val
    return result


def fetch_tcmb_data(
    api_key: str,
    end_date: date | None = None,
) -> dict[str, dict[date, float]]:
    """Fetch USD/TRY and EUR/TRY from TCMB EVDS for the last ~6 years.

    Returns::

        {
            "usd_try": {date(2026,5,5): 38.45, ...},
            "eur_try": {date(2026,5,5): 41.78, ...},
        }
    """
    if end_date is None:
        end_date = date.today()
    start_date = end_date - timedelta(days=2200)  # ~6 years of data

    usd_items = fetch_tcmb_series(api_key, TCMB_USD_TRY, start_date, end_date)
    eur_items = fetch_tcmb_series(api_key, TCMB_EUR_TRY, start_date, end_date)

    return {
        "usd_try": _items_to_dict(usd_items, _series_col(TCMB_USD_TRY)),
        "eur_try": _items_to_dict(eur_items, _series_col(TCMB_EUR_TRY)),
    }
