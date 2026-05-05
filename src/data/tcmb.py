from __future__ import annotations

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
    
    # Normally we take the last item
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
