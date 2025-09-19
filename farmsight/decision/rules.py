from __future__ import annotations
import pandas as pd

def recommend_irrigation(df: pd.DataFrame, fc_mm: float, threshold_frac: float, irr_amount_mm: float):
    """
    Adds 'recommend_irrigate' (bool) and 'irrigation_mm' columns.
    """
    thresh = fc_mm * threshold_frac
    rec = []
    for _, row in df.iterrows():
        need = row["soil_moisture_mm"] < thresh
        rec.append({
            "date": row["date"],
            "recommend_irrigate": bool(need),
            "irrigation_mm": float(irr_amount_mm if need else 0.0)
        })
    return df.merge(pd.DataFrame(rec), on="date")
