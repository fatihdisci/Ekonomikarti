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
TITLE_H = 150
TABLE_H = 800
FOOTER_H = 260
ROW_COUNT = 5
ROW_H = TABLE_H // ROW_COUNT

# Palette - Modern Dark Theme
COLORS = {
    "bg": "#0B132B",
    "surface": "#1C2A46",
    "text": "#F8FAFC",
    "accent": "#FBBF24",
    "positive": "#10B981",
    "negative": "#EF4444",
    "muted": "#B4C6D8",
    "divider": "#334155",
    "footer_note": "#3A5068",
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
    IndicatorSpec("gram_altin", "Gram Altın", "TL", "%.2f", 2),
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


# Noon "Odak Kartı" — weekday-based rotation (Pzt-Cum).
# Index = weekday() (0=Mon ... 4=Fri). Hafta sonu için ayrı format kullanılır.
NOON_ROTATION: list[str] = [
    "usd_try",      # Pazartesi
    "eur_try",      # Salı
    "gram_altin",   # Çarşamba
    "brent",        # Perşembe
    "bist_100",     # Cuma
]


@dataclass(frozen=True)
class HistoryWindow:
    """Öğle kartında gösterilecek tarihsel pencereler."""

    key: str        # JSON key
    label: str      # uppercase Turkish label rendered on card
    days: int


NOON_HISTORY_WINDOWS: list[HistoryWindow] = [
    HistoryWindow("one_year", "1 YIL ÖNCE BUGÜN", 365),
    HistoryWindow("five_year", "5 YIL ÖNCE BUGÜN", 1825),
]


# Evening "Kapanış Kartı" — 4 gösterge (gram altın hariç).
EVENING_INDICATORS: list[str] = [
    "usd_try",
    "eur_try",
    "bist_100",
    "brent",
]


def noon_focus_key_for(target_date: "date | None" = None) -> str:
    """Verilen güne göre rotasyondan göstergeyi seç. Hafta sonu Pazartesi'ye düşer (fallback)."""
    from datetime import date as _date
    if target_date is None:
        target_date = _date.today()
    wd = target_date.weekday()
    if wd >= len(NOON_ROTATION):
        return NOON_ROTATION[0]
    return NOON_ROTATION[wd]

# yfinance tickers.
YF_BIST_100 = "XU100.IS"
YF_BRENT = "BZ=F"
YF_GOLD_OZ = "GC=F"
TROY_OZ_GRAM = 31.1035

# Caption / OpenRouter.
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_DEFAULT_MODEL = "google/gemini-2.5-flash-lite"

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
    """Bundle of geometry numbers used by renderers."""

    canvas_w: int = CANVAS_W
    canvas_h: int = CANVAS_H
    padding_x: int = PADDING_X
    header_h: int = HEADER_H
    title_h: int = TITLE_H
    table_h: int = TABLE_H
    footer_h: int = FOOTER_H
    row_h: int = ROW_H
    card_radius: int = 24  # Yeni kart köşe yuvarlaklığı


LAYOUT = CardLayout()
