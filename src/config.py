"""Static configuration: palette, canvas geometry, paths, indicator definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Filesystem layout.
FONT_DIR = ROOT / "assets" / "fonts"
DATA_OUTPUT_DIR = ROOT / "data" / "output"
MANUAL_DATA_DIR = ROOT / "data" / "manual"
IMAGE_OUTPUT_DIR = ROOT / "output"
FIXTURES_DIR = ROOT / "tests" / "fixtures"

# Canvas geometry (Instagram portrait, also good for X).
CANVAS_W = 1080
CANVAS_H = 1350
PADDING_X = 60

HEADER_H = 140
TITLE_H = 180
TABLE_H = 600
FOOTER_H = 430
ROW_COUNT = 5
ROW_H = TABLE_H // ROW_COUNT  # 120

# Vertical y-anchors derived from band heights.
HEADER_Y = 0
TITLE_Y = HEADER_H
TABLE_Y = HEADER_H + TITLE_H
FOOTER_Y = HEADER_H + TITLE_H + TABLE_H

# Row interior split.
ROW_LEFT_X = 60
ROW_SPLIT_X = 480
ROW_RIGHT_X = 480
ROW_RIGHT_END_X = CANVAS_W - PADDING_X  # 1020
CHANGE_COL_COUNT = 4
CHANGE_COL_W = (ROW_RIGHT_END_X - ROW_RIGHT_X) // CHANGE_COL_COUNT  # 135


# Palette.
COLORS = {
    "bg": "#F5F1E8",
    "text": "#1A2332",
    "accent": "#C9A961",
    "positive": "#2D5F3F",
    "negative": "#A33B2A",
    "muted": "#6B7280",
    "divider": "#E5DFD0",
}


# Font registry: logical name -> (filename, default size).
# `weight` is informational; the file already encodes the weight.
@dataclass(frozen=True)
class FontSpec:
    family: str
    weight: str
    filename: str


FONTS: dict[str, FontSpec] = {
    "inter_regular": FontSpec("Inter", "Regular", "Inter-Regular.ttf"),
    "inter_semibold": FontSpec("Inter", "SemiBold", "Inter-SemiBold.ttf"),
    "inter_bold": FontSpec("Inter", "Bold", "Inter-Bold.ttf"),
    "mono_medium": FontSpec("JetBrainsMono", "Medium", "JetBrainsMono-Medium.ttf"),
    "mono_bold": FontSpec("JetBrainsMono", "Bold", "JetBrainsMono-Bold.ttf"),
}


# Indicator definitions. Keys mirror the output JSON `key` field.
@dataclass(frozen=True)
class IndicatorSpec:
    key: str
    name: str
    unit: str
    fmt: str  # printf-style applied via format_tr; carries decimals only here
    decimals: int


INDICATORS: list[IndicatorSpec] = [
    IndicatorSpec("usd_try", "USD/TRY", "TL", "%.4f", 4),
    IndicatorSpec("eur_try", "EUR/TRY", "TL", "%.4f", 4),
    IndicatorSpec("gram_altin", "Gram Altin", "TL", "%.2f", 2),
    IndicatorSpec("brent", "Brent Petrol", "USD", "%.2f", 2),
    IndicatorSpec("bist_100", "BIST 100", "puan", "%.2f", 2),
]

# Order is significant — drives row order in the morning card.
INDICATOR_ORDER: list[str] = [spec.key for spec in INDICATORS]


# Change windows used both in JSON output and as table column headers.
@dataclass(frozen=True)
class ChangeWindow:
    key: str        # JSON key in changes_pct
    label: str      # uppercase Turkish header
    days: int       # rough day count for reference date lookup


CHANGE_WINDOWS: list[ChangeWindow] = [
    ChangeWindow("daily", "GÜNLÜK", 1),
    ChangeWindow("monthly", "AYLIK", 30),
    ChangeWindow("yearly", "YILLIK", 365),
    ChangeWindow("five_year", "5 YIL", 1825),
]

# TCMB EVDS API.
TCMB_BASE_URL = "https://evds3.tcmb.gov.tr/igmevdsms-dis/"
TCMB_USD_TRY = "TP.DK.USD.A.YTL"
TCMB_EUR_TRY = "TP.DK.EUR.A.YTL"

# yfinance tickers.
YF_BIST_100 = "XU100.IS"
YF_BRENT = "BZ=F"
YF_GOLD_OZ = "GC=F"
TROY_OZ_GRAM = 31.1035

# Caption / OpenRouter.
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_DEFAULT_MODEL = "z-ai/glm-4.5"

# Posting hashtag (rendered on footer + appended to caption.txt).
HASHTAG = "#fiyathafizasi"

# Turkish weekday and month names for header date string.
TR_WEEKDAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
TR_MONTHS = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


@dataclass(frozen=True)
class CardLayout:
    """Bundle of geometry numbers used by render/morning.py."""

    canvas_w: int = CANVAS_W
    canvas_h: int = CANVAS_H
    padding_x: int = PADDING_X
    header_h: int = HEADER_H
    title_h: int = TITLE_H
    table_h: int = TABLE_H
    footer_h: int = FOOTER_H
    row_h: int = ROW_H
    row_split_x: int = ROW_SPLIT_X
    row_right_x: int = ROW_RIGHT_X
    row_right_end_x: int = ROW_RIGHT_END_X
    change_col_w: int = CHANGE_COL_W
    change_col_count: int = CHANGE_COL_COUNT


LAYOUT = CardLayout()
