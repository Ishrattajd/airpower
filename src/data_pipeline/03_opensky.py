"""
OpenSky Network -> live aircraft positions (ADS-B) over a bounding box.

Works anonymously (small daily quota) or with an API client:
  export OPENSKY_CLIENT_ID=...   export OPENSKY_CLIENT_SECRET=...
(Create the client in your OpenSky account page. If their auth method has
changed, check https://openskynetwork.github.io/opensky-api/)

Military aircraft often do not broadcast, so use this for traffic density,
corridors and routes, not for order of battle.

Usage: python 03_opensky.py --snapshots 6 --interval 60
       python 03_opensky.py --bbox 20 68 37 80   # lat_min lon_min lat_max lon_max
"""
import argparse, os, time
import pandas as pd
from common import RAW, session

TOKEN_URL = ("https://auth.opensky-network.org/auth/realms/opensky-network/"
             "protocol/openid-connect/token")
STATES_URL = "https://opensky-network.org/api/states/all"
COLS = ["icao24", "callsign", "origin_country", "time_position", "last_contact",
        "lon", "lat", "baro_altitude_m", "on_ground", "velocity_ms",
        "true_track", "vertical_rate", "sensors", "geo_altitude_m", "squawk",
        "spi", "position_source", "category"]


def get_token(s):
    cid, sec = os.getenv("OPENSKY_CLIENT_ID"), os.getenv("OPENSKY_CLIENT_SECRET")
    if not (cid and sec):
        print("No OpenSky credentials set: using anonymous access (low quota).")
        return None
    r = s.post(TOKEN_URL, data={"grant_type": "client_credentials",
                                "client_id": cid, "client_secret": sec}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def main(a):
    s = session()
    token = get_token(s)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    lamin, lomin, lamax, lomax = a.bbox
    frames = []
    for i in range(a.snapshots):
        r = s.get(STATES_URL, headers=headers, timeout=60, params={
            "lamin": lamin, "lomin": lomin, "lamax": lamax, "lomax": lomax,
            "extended": 1})
        if r.status_code == 429:
            print("Rate limited (429). Stopping; try later or use credentials.")
            break
        r.raise_for_status()
        j = r.json()
        states = j.get("states") or []
        df = pd.DataFrame(states, columns=COLS[:len(states[0])] if states else COLS)
        df.insert(0, "snapshot_utc", j["time"])
        frames.append(df)
        print(f"Snapshot {i + 1}/{a.snapshots}: {len(df)} aircraft")
        if i < a.snapshots - 1:
            time.sleep(a.interval)
    if frames:
        out = pd.concat(frames, ignore_index=True)
        out["callsign"] = out["callsign"].str.strip()
        path = RAW / "opensky_states.csv"
        out.to_csv(path, index=False)
        print(f"Saved {len(out)} rows -> {path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--bbox", nargs=4, type=float, default=[6, 68, 37, 98],
                   metavar=("LAT_MIN", "LON_MIN", "LAT_MAX", "LON_MAX"))
    p.add_argument("--snapshots", type=int, default=3)
    p.add_argument("--interval", type=int, default=30)
    main(p.parse_args())
