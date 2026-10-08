"""
Build a curated list of air bases from the real OurAirports data.

Replaces the weak name-matching ("is_military_guess"). The list below comes
from general public knowledge of Indian Air Force stations. It is an
APPROXIMATION: some are civil-enclave airfields, and it may omit or include
stations you disagree with. Edit CURATED freely.

Input : data/raw/airports_india.csv, data/raw/runways_india.csv
Output: data/processed/bases.csv   (real coordinates + real runway data)
"""
import pandas as pd
from common import RAW, PROC

# ICAO/OurAirports ident -> short display name
CURATED = {
    "VIAM": "Ambala", "VIBT": "Bhatinda", "VIPK": "Pathankot", "VIAX": "Adampur",
    "VIHX": "Halwara", "VISA": "Sirsa", "VIUX": "Udhampur", "VIAW": "Awantipura",
    "VISR": "Srinagar", "VILH": "Leh", "VI57": "Thoise", "VIDX": "Hindon",
    "VIAG": "Agra", "VIBY": "Bareilly", "VISP": "Sarsawa", "VIBL": "Bakshi Ka Talab",
    "VIGR": "Gwalior", "VIJO": "Jodhpur", "VIJR": "Jaisalmer", "VIBK": "Nal (Bikaner)",
    "VIUT": "Uttarlai", "VA1K": "Naliya", "VABJ": "Bhuj", "VAJM": "Jamnagar",
    "VAPO": "Pune", "VETZ": "Tezpur", "VEJT": "Jorhat", "VECA": "Chabua",
    "VEBD": "Bagdogra", "VEHX": "Hasimara", "VEPH": "Panagarh",
    "VEDX": "Kalaikunda", "VE62": "Charbatia", "VOSX": "Sulur",
    "VOTJ": "Thanjavur", "VOYK": "Yelahanka", "VOCX": "Car Nicobar",
}


def region(lat, lon):
    if lon > 92 or (lat < 14 and lon > 90):
        return "Islands/Far-East" if lat < 14 else "East"
    if lat >= 29.5:
        return "North"
    if lon >= 85:
        return "East"
    if lat >= 22 and lon <= 73.5:
        return "West"
    if lat >= 22:
        return "Central"
    return "South"


def main():
    ap = pd.read_csv(RAW / "airports_india.csv")
    rw = pd.read_csv(RAW / "runways_india.csv")
    rw = rw[rw["closed"] == 0].dropna(subset=["length_ft"])
    best = (rw.sort_values("length_ft", ascending=False)
              .groupby("airport_ident").first().reset_index())
    cnt = rw.groupby("airport_ident").size().rename("n_runways").reset_index()

    b = ap[ap["ident"].isin(CURATED)].copy()
    missing = sorted(set(CURATED) - set(b["ident"]))
    if missing:
        print("Not found in airports file (skipped):", missing)
    b = b.merge(best[["airport_ident", "length_ft", "width_ft", "surface"]],
                left_on="ident", right_on="airport_ident", how="left")
    b = b.merge(cnt, left_on="ident", right_on="airport_ident", how="left")
    b["base_name"] = b["ident"].map(CURATED)
    b["region"] = [region(a, o) for a, o in zip(b.latitude_deg, b.longitude_deg)]
    b = b.rename(columns={"length_ft": "longest_runway_ft", "surface": "longest_surface"})
    b = b.dropna(subset=["longest_runway_ft"])
    cols = ["ident", "base_name", "name", "region", "latitude_deg", "longitude_deg",
            "elevation_ft", "n_runways", "longest_runway_ft", "longest_surface",
            "type", "iso_region"]
    b = b[cols].sort_values(["region", "base_name"])
    b.to_csv(PROC / "bases.csv", index=False)
    print(f"Saved {len(b)} bases -> {PROC / 'bases.csv'}")
    print(b["region"].value_counts().to_string())


if __name__ == "__main__":
    main()
