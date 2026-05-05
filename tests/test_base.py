import pytest
from src.render.base import format_tr, format_pct, load_font, text_size

def test_format_tr():
    assert format_tr(1234.56, 2) == "1.234,56"
    assert format_tr(38.4521, 4) == "38,4521"
    assert format_tr(-1234567.0, 0) == "-1.234.567"
    assert format_tr(0.0, 2) == "0,00"
    
    with pytest.raises(ValueError):
        format_tr(123.45, -1)

def test_pct_format():
    assert format_pct(0.42) == "+0,42%"
    assert format_pct(-3.15) == "-3,15%"
    assert format_pct(425.3) == "+425%"
    assert format_pct(-100.0) == "-100%"
    assert format_pct(0.0) == "+0,00%"

def test_turkish_chars():
    """Ensure font loading works and Turkish characters are rendered with non-zero dimensions."""
    font = load_font("inter_regular", 32)
    tr_text = "İĞŞÜÇÖ ığşüçö"
    width, height = text_size(font, tr_text)
    
    assert width > 0
    assert height > 0
