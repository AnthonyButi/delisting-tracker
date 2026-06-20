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

if __name__ == "__main__":
    df = get_series("ACTLISCOUUS")
    print(df.tail())
    print("Shape:", df.shape)
    print("Types:", df.dtypes.to_dict())