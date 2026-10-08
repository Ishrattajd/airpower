"""
Open-Meteo -> hourly weather at airbase locations. No API key needed.
(Free tier is for non-commercial use. Keep requests modest.)

Reads data/raw/airports_india.csv (run 01 first).

Usage:
  python 02_openmeteo.py --mode forecast --days 3 --use-bases --limit 60   (recommended)
  python 02_openmeteo.py --mode forecast --days 3 --military-only
  python 02_openmeteo.py --mode history --start 2024-06-01 --end 2024-06-30 --limit 10
"""
import argparse
import pandas as pd
from common import RAW, PROC, session

HOURLY = ["temperature_2m", "wind_speed_10m", "wind_direction_10m",
          "wind_gusts_10m", "visibility", "cloud_cover", "cloud_cover_low",
          "precipitation", "weather_code"]
URLS = {"forecast": "https://api.open-meteo.com/v1/forecast",
        "history": "https://archive-api.open-meteo.com/v1/archive"}


def fetch_chunk(url, chunk, extra):
    params = {
        "latitude": ",".join(str(x) for x in chunk["latitude_deg"]),
        "longitude": ",".join(str(x) for x in chunk["longitude_deg"]),
        "hourly": ",".join(HOURLY),
        "wind_speed_unit": "kn",
        "timezone": "UTC",
        **extra,
    }
    r = session().get(url, params=params, timeout=90)
    r.raise_for_status()
    data = r.json()
    data = data if isinstance(data, list) else [data]  # single vs multi location

    frames = []
    for loc, (_, row) in zip(data, chunk.iterrows()):
        df = pd.DataFrame(loc["hourly"])
        df.insert(0, "ident", row["ident"])
        df.insert(1, "name", row["name"])
        df.insert(2, "lat", row["latitude_deg"])
        df.insert(3, "lon", row["longitude_deg"])
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def main(a):
    if a.use_bases:  # curated list from 06_make_bases.py (recommended)
        ap = pd.read_csv(PROC / "bases.csv")
        ap["name"] = ap["base_name"]
    else:
        ap = pd.read_csv(RAW / "airports_india.csv")
        ap = ap[ap["type"].isin(["large_airport", "medium_airport", "small_airport"])]
        if a.military_only:
            ap = ap[ap["is_military_guess"]]
    ap = ap.dropna(subset=["latitude_deg", "longitude_deg"]).head(a.limit)
    print(f"Fetching {a.mode} weather for {len(ap)} airfields...")

    extra = ({"forecast_days": a.days} if a.mode == "forecast"
             else {"start_date": a.start, "end_date": a.end})
    out = []
    for i in range(0, len(ap), 10):  # small batches keep calls reliable
        out.append(fetch_chunk(URLS[a.mode], ap.iloc[i:i + 10], extra))
    df = pd.concat(out, ignore_index=True)
    path = RAW / f"weather_{a.mode}.csv"
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows -> {path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["forecast", "history"], default="forecast")
    p.add_argument("--days", type=int, default=3)
    p.add_argument("--start", default="2024-06-01")
    p.add_argument("--end", default="2024-06-07")
    p.add_argument("--military-only", action="store_true")
    p.add_argument("--use-bases", action="store_true",
                   help="use data/processed/bases.csv from 06_make_bases.py")
    p.add_argument("--limit", type=int, default=30)
    main(p.parse_args())
