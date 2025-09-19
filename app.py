import streamlit as st
import pandas as pd
from farmsight.config import load_config
from farmsight.data.loaders import load_weather, load_ndvi
from farmsight.forecasting.prophet_model import forecast_series
from farmsight.simulation.soil_model import run_water_balance
from farmsight.decision.rules import recommend_irrigation
from farmsight.digital_twin import show_digital_twin

ow_api_key = "80e587c9de07760942eb4b9e78dccf46"

# At the bottom of app.py
st.subheader("🌍 Digital Twin")
show_digital_twin(api_key=ow_api_key)

st.set_page_config(page_title="FarmSight", layout="wide")

cfg = load_config()

st.title(cfg.get("site_name", "FarmSight"))

# Sidebar params
st.sidebar.header("Parameters")
lat = st.sidebar.number_input("Latitude", value=float(cfg["latitude"]))
fc_mm = st.sidebar.number_input("Field Capacity (mm)", value=float(cfg["field_capacity_mm"]))
wp_mm = st.sidebar.number_input("Wilting Point (mm)", value=float(cfg["wilting_point_mm"]))
kc_initial = st.sidebar.number_input("Kc (single value demo)", value=float(cfg["kc_values"]["mid"]))
thresh_frac = st.sidebar.slider("Moisture threshold (fraction of FC)", 0.1, 0.9, float(cfg["moisture_threshold_frac"]))
irr_mm = st.sidebar.number_input("Irrigation per event (mm)", value=float(cfg["irrigation_amount_mm"]))
horizon = st.sidebar.number_input("Forecast horizon (days)", min_value=3, max_value=30, value=int(cfg["forecast_horizon_days"]))
roll = st.sidebar.number_input("Rolling window (fallback forecast)", min_value=3, max_value=30, value=int(cfg["rolling_window_days"]))

# ---------------------------
# Weather
# ---------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Weather (sample)")
    wdf = load_weather()
    st.dataframe(wdf.tail(10), use_container_width=True)

# ---------------------------
# NDVI loader (local or GEE)
# ---------------------------
with col2:
    st.subheader("NDVI")

    ndvi_source = st.sidebar.radio("NDVI Source", ["local", "gee"])

    if ndvi_source == "local":
        ndf = load_ndvi(source="local")
    else:
        gee_lat = st.sidebar.number_input("GEE Latitude", value=float(cfg["latitude"]))
        gee_lon = st.sidebar.number_input("GEE Longitude", value=float(cfg["longitude"]))
        gee_start = st.sidebar.date_input("NDVI start date", pd.to_datetime("2024-01-01"))
        gee_end = st.sidebar.date_input("NDVI end date", pd.to_datetime("2024-12-31"))

        st.info("Fetching NDVI from Google Earth Engine… please wait")
        ndf = load_ndvi(
            source="gee",
            lat=float(gee_lat),
            lon=float(gee_lon),
            start=str(gee_start),
            end=str(gee_end),
        )

    st.dataframe(ndf.tail(10), use_container_width=True)

# ---------------------------
# Forecasts
# ---------------------------
tmean_fc = forecast_series(wdf.rename(columns={"tmean_c": "value"}), "date", "value",
                           horizon_days=horizon, rolling_window=roll)
ndvi_fc = forecast_series(ndf.rename(columns={"ndvi": "value"}), "date", "value",
                          horizon_days=horizon, rolling_window=roll)

st.subheader("Forecasts")
c1, c2 = st.columns(2)
with c1:
    st.line_chart(pd.DataFrame({
        "date": pd.concat([wdf["date"], tmean_fc["date"]], ignore_index=True),
        "tmean_c": pd.concat([wdf["tmean_c"], pd.Series([None]*(len(tmean_fc)-1) + [None])], ignore_index=True)
    }).set_index("date"))

with c2:
    st.line_chart(pd.DataFrame({
        "date": pd.concat([ndf["date"], ndvi_fc["date"]], ignore_index=True),
        "ndvi": pd.concat([ndf["ndvi"], pd.Series([None]*(len(ndvi_fc)-1) + [None])], ignore_index=True)
    }).set_index("date"))

# ---------------------------
# Soil water balance + irrigation decision
# ---------------------------
sim_df = run_water_balance(wdf, fc_mm=fc_mm, wp_mm=wp_mm, kc=kc_initial, init_frac=0.8)
sim_df = recommend_irrigation(sim_df, fc_mm=fc_mm, threshold_frac=thresh_frac, irr_amount_mm=irr_mm)

st.subheader("Soil Moisture & Recommendations")
st.line_chart(sim_df.set_index("date")[["soil_moisture_mm"]])

st.dataframe(sim_df.tail(30), use_container_width=True)

st.caption("Demo build. Replace sample data with your field data for Phase-2.")
