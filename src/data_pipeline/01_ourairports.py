"""
OurAirports -> airports, runways, navaids, frequencies for India.
No account needed. Run this FIRST: the weather script uses its output.

Usage: python 01_ourairports.py [--country IN]
"""
import argparse, io
import pandas as pd
from common import RAW, session

BASE = "https://davidmegginson.github.io/ourairports-data/"
MIL_WORDS = r"Air Force|Air Base|\bAFS\b|\bAFB\b|Naval Air|Air Station|Military"


def get(name: str) -> pd.DataFrame:
    r = session().get(f"{BASE}{name}.csv", timeout=60)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text), low_memory=False)


def main(country: str):
    airports = get("airports")
    airports = airports[airports["iso_country"] == country].copy()
    airports["is_military_guess"] = airports["name"].str.contains(
        MIL_WORDS, case=False, regex=True, na=False)
    airports.to_csv(RAW / "airports_india.csv", index=False)

    idents = set(airports["ident"])
    runways = get("runways")
    runways[runways["airport_ident"].isin(idents)].to_csv(
        RAW / "runways_india.csv", index=False)

    freqs = get("airport-frequencies")
    freqs[freqs["airport_ident"].isin(idents)].to_csv(
        RAW / "frequencies_india.csv", index=False)

    navaids = get("navaids")
    navaids[navaids["iso_country"] == country].to_csv(
        RAW / "navaids_india.csv", index=False)

    mil = airports["is_military_guess"].sum()
    print(f"Airports: {len(airports)} (name-based military guess: {mil})")
    print(f"Saved to {RAW}")
    print("Note: 'is_military_guess' is only a name match. Verify manually "
          "and cross-check with OpenStreetMap (military=airfield).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="IN")
    main(ap.parse_args().country)
