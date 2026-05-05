"""Yahoo Finance data fetching for currencies, BIST 100, Brent Crude, and Gold."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import yfinance as yf

from src.config import YF_BIST_100, YF_BRENT, YF_GOLD_OZ

# Currency tickers (replaces TCMB for historical data)
YF_USD_TRY = "USDTRY=X"
YF_EUR_TRY = "EURTRY=X"


def _ticker_to_dict(ticker_symbol: str, start: date, end: date) -> dict[date, float]:
    """Download daily Close prices for a yfinance ticker, return {date: close}."""
    # yfinance end is exclusive, so add 1 day
    end_plus = end + timedelta(days=1)
    df = yf.download(
        ticker_symbol,
        start=start.isoformat(),
        end=end_plus.isoformat(),
        progress=False,
        auto_adjust=True,
    )
    if df.empty:
        return {}

    result: dict[date, float] = {}
    close_col = "Close"
    # yfinance may return MultiIndex columns for single ticker
    if hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)
    for idx, row in df.iterrows():
        try:
            d = idx.date() if hasattr(idx, "date") else idx
            val = float(row[close_col])
            result[d] = val
        except (ValueError, TypeError, KeyError):
            continue
    return result


def fetch_yfinance_data(
    end_date: date | None = None,
) -> dict[str, dict[date, float]]:
    """Fetch USD/TRY, EUR/TRY, BIST 100, Brent, Gold (oz) daily closes for ~6 years.

    Returns::

        {
            "usd_try":  {date(...): 38.45, ...},
            "eur_try":  {date(...): 41.78, ...},
            "bist_100": {date(...): 11248.73, ...},
            "brent":    {date(...): 71.42, ...},
            "gold_oz":  {date(...): 2345.60, ...},
        }
    """
    if end_date is None:
        end_date = date.today()
    start_date = end_date - timedelta(days=2200)

    return {
        "usd_try": _ticker_to_dict(YF_USD_TRY, start_date, end_date),
        "eur_try": _ticker_to_dict(YF_EUR_TRY, start_date, end_date),
        "bist_100": _ticker_to_dict(YF_BIST_100, start_date, end_date),
        "brent": _ticker_to_dict(YF_BRENT, start_date, end_date),
        "gold_oz": _ticker_to_dict(YF_GOLD_OZ, start_date, end_date),
    }

