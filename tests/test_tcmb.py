import json
from pathlib import Path
from src.data.tcmb import parse_tcmb_evds
from src.config import FIXTURES_DIR

def test_tcmb_parser():
    fixture_path = FIXTURES_DIR / "tcmb_evds.json"
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    
    result = parse_tcmb_evds(payload)
    
    assert "TP_DK_USD_A_YTL" in result
    assert result["TP_DK_USD_A_YTL"] == 32.1234
    
    assert "TP_DK_EUR_A_YTL" in result
    assert result["TP_DK_EUR_A_YTL"] == 34.5678
    
    # Tarih and UNIXTIME should be ignored
    assert "Tarih" not in result
    assert "UNIXTIME" not in result
