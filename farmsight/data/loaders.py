import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_weather(path: str | None = None) -> pd.DataFrame:
    """Load weather data from CSV (local)."""
    p = Path(path) if path else DATA_DIR / "sample_weather.csv"
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["tmean_c"] = (df["tmin_c"] + df["tmax_c"]) / 2.0
    return df


def load_ndvi_local(path: str | None = None) -> pd.DataFrame:
    """Load NDVI data from CSV (local)."""
    p = Path(path) if path else DATA_DIR / "sample_ndvi.csv"
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def load_ndvi_gee(lat: float, lon: float, start: str, end: str, buffer_m: int = 250) -> pd.DataFrame:
    """
    Load NDVI time series from Google Earth Engine (MODIS MOD13Q1).
    Args:
        lat, lon: Coordinates of the field
        start, end: Date range ('YYYY-MM-DD')
        buffer_m: Buffer radius in meters around the point
    Returns:
        pd.DataFrame with ['date', 'ndvi']
    """
    import ee

    # Initialize GEE
    try:
        ee.Initialize(project="earthengine-public") 
    except Exception:
        ee.Authenticate()
        ee.Initialize(project="earthengine-public")


    point = ee.Geometry.Point(lon, lat)
    region = point.buffer(buffer_m)

    collection = (
        ee.ImageCollection("MODIS/006/MOD13Q1")
        .filterBounds(region)
        .filterDate(start, end)
        .select("NDVI")
    )

    def extract(img):
        mean_dict = img.reduceRegion(ee.Reducer.mean(), region, 250)
        return ee.Feature(
            None,
            {
                "date": img.date().format("YYYY-MM-dd"),
                "ndvi": mean_dict.get("NDVI"),
            },
        )

    ndvi_fc = collection.map(extract)
    ndvi_list = ndvi_fc.getInfo()["features"]

    rows = []
    for f in ndvi_list:
        props = f["properties"]
        if props["ndvi"] is not None:
            rows.append(
                {
                    "date": props["date"],
                    "ndvi": float(props["ndvi"]) * 0.0001,  # apply MODIS scale factor
                }
            )

    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
    return df


def load_ndvi(source: str = "local", path: str | None = None,
              lat: float = 12.97, lon: float = 77.59,
              start: str = "2024-01-01", end: str = "2024-12-31") -> pd.DataFrame:
    """
    Unified NDVI loader.
    source: "local" (CSV) or "gee" (Google Earth Engine)
    """
    if source == "local":
        return load_ndvi_local(path)
    elif source == "gee":
        return load_ndvi_gee(lat, lon, start, end)
    else:
        raise ValueError("Invalid NDVI source. Choose 'local' or 'gee'.")
