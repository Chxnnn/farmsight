from __future__ import annotations
import pandas as pd

try:
    from prophet import Prophet  # type: ignore
    HAVE_PROPHET = True
except Exception:
    HAVE_PROPHET = False

def forecast_series(df: pd.DataFrame, date_col: str, value_col: str, horizon_days: int = 7, rolling_window: int = 7) -> pd.DataFrame:
    """
    Returns a dataframe with 'date' and 'yhat' (forecast).
    Falls back to rolling mean if Prophet isn't available.
    """
    df = df[[date_col, value_col]].dropna().copy()
    df = df.rename(columns={date_col: "ds", value_col: "y"})
    df = df.sort_values("ds")

    if HAVE_PROPHET and len(df) > 20:
        m = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
        m.fit(df)
        future = m.make_future_dataframe(periods=horizon_days, freq="D")
        fcst = m.predict(future)[["ds", "yhat"]]
        fcst = fcst.tail(horizon_days).rename(columns={"ds": "date"})
        return fcst
    else:
        # naive rolling mean forecast
        hist = df.tail(rolling_window)["y"].mean()
        last_date = df["ds"].max()
        fut_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon_days, freq="D")
        return pd.DataFrame({"date": fut_dates, "yhat": hist})
