"""
UCDP GED -> georeferenced conflict events (free, no account, no API key).
Replacement for ACLED. Output: data/raw/conflict_events.csv

Tries to download the latest GED CSV zip automatically. If that fails:
  1. Open https://ucdp.uu.se/downloads/  ->  "UCDP Georeferenced Event Dataset (GED)"
  2. Download the CSV version (a .zip or .csv file)
  3. Save it inside data/raw/ and run:  python 05_ucdp.py --file data/raw/<yourfile>

Usage:
  python 05_ucdp.py --countries "India,Pakistan,China" --start 2018-01-01 --end 2024-12-31
"""
import argparse, io, sys, zipfile
from pathlib import Path
import pandas as pd
from common import RAW, session

# Tried in order (newest first). Version numbers may change over time.
URLS = [f"https://ucdp.uu.se/downloads/ged/ged{v}-csv.zip"
        for v in ("261", "251", "241", "231")]
VIOLENCE = {1: "State-based conflict", 2: "Non-state conflict", 3: "One-sided violence"}


def download():
    s = session()
    for url in URLS:
        try:
            print(f"Trying {url} ...")
            r = s.get(url, timeout=300)
            if r.status_code == 200 and r.content[:2] == b"PK":
                print(f"Downloaded {len(r.content) / 1e6:.1f} MB")
                return r.content
            print(f"  not available (HTTP {r.status_code})")
        except Exception as e:
            print(f"  failed: {e}")
    return None


def read_ged(path=None, blob=None) -> pd.DataFrame:
    if blob is not None:
        z = zipfile.ZipFile(io.BytesIO(blob))
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        return pd.read_csv(z.open(name), low_memory=False)
    if str(path).lower().endswith(".zip"):
        z = zipfile.ZipFile(path)
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        return pd.read_csv(z.open(name), low_memory=False)
    return pd.read_csv(path, low_memory=False)


def main(a):
    local = None
    if a.file:
        local = Path(a.file)
        if not local.exists():
            sys.exit(f"File not found: {local.resolve()}\n"
                     "Check the filename, or save the UCDP download into "
                     f"{RAW} and run again without --file.")
    else:  # auto-detect a manually downloaded file
        found = sorted(list(RAW.glob("ged*.zip")) + list(RAW.glob("ged*.csv"))
                       + list(RAW.glob("GED*.zip")) + list(RAW.glob("GED*.csv")))
        if found:
            local = found[-1]
            print(f"Using local file: {local}")
    if local:
        df = read_ged(path=local)
    else:
        blob = download()
        if blob is None:
            sys.exit("\nAutomatic download failed. Download GED manually "
                     "(see instructions at top of this file), then use --file.")
        df = read_ged(blob=blob)

    print(f"Loaded {len(df):,} events worldwide")
    df["date_start"] = pd.to_datetime(df["date_start"], errors="coerce")
    countries = [c.strip().lower() for c in a.countries.split(",")]
    df = df[df["country"].str.lower().isin(countries)]
    df = df[(df["date_start"] >= a.start) & (df["date_start"] <= a.end)]

    out = pd.DataFrame({
        "event_id": df["id"],
        "event_date": df["date_start"].dt.date,
        "event_type": df["type_of_violence"].map(VIOLENCE),
        "actor1": df["side_a"],
        "actor2": df["side_b"],
        "country": df["country"],
        "admin1": df.get("adm_1"),
        "location": df["where_description"],
        "latitude": df["latitude"],
        "longitude": df["longitude"],
        "fatalities": df["best"],
        "conflict_name": df["conflict_name"],
    }).sort_values("event_date")

    if out.empty:
        print("No events matched. Try wider dates or check country spelling.")
        return
    path = RAW / "conflict_events.csv"
    out.to_csv(path, index=False)
    print(f"Saved {len(out):,} events ({out['event_date'].min()} to "
          f"{out['event_date'].max()}) -> {path}")
    print(out["country"].value_counts().to_string())


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--countries", default="India,Pakistan,China")
    p.add_argument("--start", default="2018-01-01")
    p.add_argument("--end", default="2024-12-31")
    p.add_argument("--file", help="Path to a manually downloaded GED .csv or .zip")
    main(p.parse_args())
