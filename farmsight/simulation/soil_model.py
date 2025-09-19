from __future__ import annotations
import math
import pandas as pd

def _eto_hargreaves(tmin_c: float, tmax_c: float, tmean_c: float) -> float:
    # Simplified Hargreaves (no Ra). For demo ONLY.
    td = max(0.0, tmax_c - tmin_c)
    return max(0.0, 0.0023 * math.sqrt(td) * (tmean_c + 17.8))

def run_water_balance(weather: pd.DataFrame, fc_mm: float, wp_mm: float, kc: float, init_frac: float = 0.8) -> pd.DataFrame:
    """
    Simple bucket model with daily step.
    Returns weather joined with 'soil_moisture_mm' and 'etc_mm'.
    """
    sm = fc_mm * init_frac
    out = []
    for _, row in weather.iterrows():
        eto = _eto_hargreaves(row["tmin_c"], row["tmax_c"], row["tmean_c"])
        etc = kc * eto  # mm/day
        rainfall = float(row.get("rain_mm", 0.0))
        sm = sm + rainfall - etc
        drainage = max(0.0, sm - fc_mm)
        sm = sm - drainage
        sm = min(fc_mm, max(wp_mm, sm))  # clamp
        out.append({"date": row["date"], "soil_moisture_mm": sm, "etc_mm": etc})
    return weather.merge(pd.DataFrame(out), on="date")
