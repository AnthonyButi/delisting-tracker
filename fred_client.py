import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

def get_series_raw(series_id):
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def get_series(series_id):
    """Fetch a FRED series and return a tidy DataFrame indexed by date."""
    data = get_series_raw(series_id)
    df = pd.DataFrame(data["observations"])
    df = df[["date", "value"]]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.set_index("date")
    df = df.rename(columns={"value": series_id})
    return df

def get_panel(series_ids):
    """Pull several series and join them into one monthly-aligned DataFrame.
    Skips, with a warning, any series that fails to fetch."""
    frames = []
    for sid in series_ids:
        try:
            frames.append(get_series(sid))
        except Exception as e:
            print(f"  ! Skipping {sid}: {e}")
    panel = pd.concat(frames, axis=1)
    return panel

def build_panel(cbsa_code="16980"):
    """Build the full monthly panel of housing metrics for one metro (CBSA)."""
    monthly_series = [
        f"ACTLISCOU{cbsa_code}",   # active listings
        f"NEWLISCOU{cbsa_code}",   # new listings
        f"PENLISCOU{cbsa_code}",   # pending listings
        f"PRIREDCOU{cbsa_code}",   # price-reduced count
    ]
    panel = get_panel(monthly_series)

    # 30-year mortgage rate is weekly and national -> collapse to monthly
    mortgage = get_series("MORTGAGE30US").resample("MS").mean()
    panel = panel.join(mortgage)

    return panel


if __name__ == "__main__":
    panel = build_panel()
    print(panel.tail())
    print("Shape:", panel.shape)
    print("Columns:", list(panel.columns))