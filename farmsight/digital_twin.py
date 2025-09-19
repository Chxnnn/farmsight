import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from farmsight.data.loaders import load_ndvi
import datetime as dt
import random




# 🌦 Weather API (OpenWeatherMap)
def get_weather(lat, lon, api_key):
    if not api_key:
        st.error("⚠️ Missing OpenWeatherMap API key")
        return pd.DataFrame()

    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    try:
        r = requests.get(url).json()
    except Exception as e:
        st.error(f"Weather API error: {e}")
        return pd.DataFrame()

    if "list" not in r:
        st.warning("No weather data returned. Check API key or location.")
        return pd.DataFrame()

    data = [
        {
            "date": item["dt_txt"],
            "tmean_c": item["main"]["temp"],
            "rain_mm": item.get("rain", {}).get("3h", 0),
        }
        for item in r["list"]
    ]
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df



# 🌱 Fake soil data generator
def generate_fake_soil_data():
    return {
        "moisture": round(random.uniform(20, 45), 1),      # %
        "temperature": round(random.uniform(18, 32), 1),   # °C
        "ph": round(random.uniform(5.5, 7.5), 1),          # pH
        "nitrogen": round(random.uniform(10, 50), 1),      # mg/kg
        "phosphorus": round(random.uniform(5, 30), 1),     # mg/kg
        "potassium": round(random.uniform(50, 200), 1),    # mg/kg
    }


# 🪱 Soil data fetcher (sensor API or fake generator)
def get_soil_data(sensor_url=None, use_fake=True):
    if use_fake:
        return generate_fake_soil_data()
    if sensor_url:
        try:
            r = requests.get(sensor_url, timeout=5).json()
            return {
                "moisture": r.get("moisture", 30.0),
                "temperature": r.get("temperature", 25.0),
                "ph": r.get("ph", 6.5),
                "nitrogen": r.get("nitrogen", 20.0),
                "phosphorus": r.get("phosphorus", 15.0),
                "potassium": r.get("potassium", 100.0),
            }
        except Exception:
            return generate_fake_soil_data()
    return generate_fake_soil_data()


# 🌍 Digital Twin Dashboard
def show_digital_twin(api_key, default_lat=12.97, default_lon=77.59):
    st.header("🌍 Farm Digital Twin")

    # Location input
    lat = st.sidebar.number_input("Latitude", value=default_lat, format="%.6f")
    lon = st.sidebar.number_input("Longitude", value=default_lon, format="%.6f")

    # Map
    m = folium.Map(location=[lat, lon], zoom_start=12)
    folium.Marker([lat, lon], popup="Farm Location").add_to(m)
    st_folium(m, width=700, height=400)

    # Weather
    st.subheader("🌦 Weather (OpenWeatherMap)")
    wdf = get_weather(lat, lon, api_key)
    if not wdf.empty:
        st.line_chart(wdf.set_index("date")[["tmean_c", "rain_mm"]])

    # NDVI from GEE
    st.subheader("🌱 NDVI (MODIS via GEE)")
    start_date = st.sidebar.date_input("NDVI Start", dt.date(2024, 1, 1))
    end_date = st.sidebar.date_input("NDVI End", dt.date.today())
    ndf = load_ndvi(source="gee", lat=lat, lon=lon,
                    start=str(start_date), end=str(end_date))
    if not ndf.empty:
        st.line_chart(ndf.set_index("date")[["ndvi"]])

    # Soil data
    st.subheader("🪱 Soil Sensor Data")
    soil = get_soil_data(use_fake=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Moisture (%)", soil["moisture"])
    col2.metric("Soil Temp (°C)", soil["temperature"])
    col3.metric("pH", soil["ph"])

    col4, col5, col6 = st.columns(3)
    col4.metric("Nitrogen (mg/kg)", soil["nitrogen"])
    col5.metric("Phosphorus (mg/kg)", soil["phosphorus"])
    col6.metric("Potassium (mg/kg)", soil["potassium"])

    st.caption("Prototype Digital Twin: Weather (API), NDVI (GEE), Soil (simulated/random).")
