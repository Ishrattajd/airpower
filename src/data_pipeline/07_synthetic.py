"""
Synthetic data generator for the Air Power project.

Builds everything that real open data cannot provide, ON TOP of the real
bases (06_make_bases.py), real weather (02) and real conflict events (05).

ALL OF THE FOLLOWING IS SYNTHETIC / ASSUMED, NOT REAL IAF DATA:
  * which aircraft are at which base, their serviceability and health
  * crew rosters, hours and qualifications
  * weapon and fuel stocks
  * missions, targets and enemy air-defence sites (a NOTIONAL exercise zone)
  * aircraft performance figures are rough public-domain approximations
    (placeholders; replace with official figures when available)
  * duty limits are assumed values (replace with actual IAF/DGCA rules)

Weapon classes are generic (BVR-AAM, PGM-1000lb ...) on purpose.

Usage:
  python 07_synthetic.py                       # full scenario
  python 07_synthetic.py --max-bases 3 --missions 8   # small demo scenario
"""
import argparse
import numpy as np
import pandas as pd
from common import RAW, PROC, SYN

# ---------------------------------------------------------------- assumptions
AIRCRAFT_TYPES = pd.DataFrame([
    # type, role, combat_radius_km, max_payload_kg, crew_seats, min_runway_ft, sortie_h, turnaround_h
    ("Su-30MKI",    "multirole",       1500,  8000, 2, 4000, 2.5, 2.5),
    ("Rafale",      "multirole",       1850,  9500, 1, 4000, 2.5, 2.0),
    ("Tejas-Mk1A",  "light-multirole",  500,  3500, 1, 3000, 1.5, 1.5),
    ("Mirage-2000", "multirole",       1000,  6300, 1, 4500, 2.0, 2.0),
    ("MiG-29UPG",   "air-superiority",  700,  4500, 1, 4000, 2.0, 2.0),
    ("Jaguar",      "strike",           900,  4750, 1, 4500, 2.5, 2.5),
    ("C-130J",      "transport",       2400, 20000, 2, 3000, 4.0, 3.0),  # 2 pilots; loadmaster ignored
], columns=["aircraft_type", "role", "combat_radius_km", "max_payload_kg",
            "crew_seats", "min_runway_ft", "sortie_h", "turnaround_h"])

CAN_FLY = {  # mission type -> aircraft types able to fly it
    "CAP":      ["Su-30MKI", "Rafale", "Tejas-Mk1A", "Mirage-2000", "MiG-29UPG"],
    "ESCORT":   ["Su-30MKI", "Rafale", "Tejas-Mk1A", "MiG-29UPG"],
    "STRIKE":   ["Su-30MKI", "Rafale", "Tejas-Mk1A", "Mirage-2000", "Jaguar"],
    "SEAD":     ["Su-30MKI", "Rafale"],
    "STANDOFF": ["Su-30MKI", "Rafale", "Mirage-2000"],
    "RECCE":    ["Rafale", "Mirage-2000", "Jaguar"],
    "CAS":      ["Su-30MKI", "Tejas-Mk1A", "Jaguar"],
    "AIRLIFT":  ["C-130J"],
}
FIGHTERS = [t for t in AIRCRAFT_TYPES.aircraft_type if t != "C-130J"]
TYPE_WEIGHT = {"Su-30MKI": 30, "Rafale": 12, "Tejas-Mk1A": 18, "Mirage-2000": 10,
               "MiG-29UPG": 6, "Jaguar": 14}

WEAPONS = pd.DataFrame([  # generic classes
    ("BVR-AAM", 150), ("WVR-AAM", 90), ("PGM-1000lb", 450), ("Standoff-ASM", 1300),
    ("Anti-Radiation-Missile", 600), ("Unguided-500lb", 230), ("Recon-pod", 200),
], columns=["weapon_class", "unit_kg"])
WEAPON_COMPAT = {
    "BVR-AAM": ["Su-30MKI", "Rafale", "Tejas-Mk1A", "Mirage-2000", "MiG-29UPG"],
    "WVR-AAM": ["Su-30MKI", "Rafale", "Tejas-Mk1A", "Mirage-2000", "MiG-29UPG", "Jaguar"],
    "PGM-1000lb": ["Su-30MKI", "Rafale", "Tejas-Mk1A", "Mirage-2000", "Jaguar"],
    "Standoff-ASM": ["Su-30MKI", "Rafale", "Mirage-2000"],
    "Anti-Radiation-Missile": ["Su-30MKI", "Rafale", "Jaguar"],
    "Unguided-500lb": ["Su-30MKI", "Tejas-Mk1A", "Mirage-2000", "MiG-29UPG", "Jaguar"],
    "Recon-pod": ["Rafale", "Mirage-2000", "Jaguar"],
}
STOCK_PER_AIRCRAFT = {"BVR-AAM": 8, "WVR-AAM": 8, "PGM-1000lb": 8, "Standoff-ASM": 2,
                      "Anti-Radiation-Missile": 3, "Unguided-500lb": 16, "Recon-pod": 0.3}

MISSION_PROFILES = {  # type: (weapons per aircraft, min/max aircraft, duration h)
    "CAP":      ([("BVR-AAM", 4), ("WVR-AAM", 2)], (2, 4), 3.0),
    "ESCORT":   ([("BVR-AAM", 4), ("WVR-AAM", 2)], (2, 4), 3.0),
    "STRIKE":   ([("PGM-1000lb", 4), ("WVR-AAM", 2)], (2, 6), 3.0),
    "SEAD":     ([("Anti-Radiation-Missile", 2), ("BVR-AAM", 2)], (2, 4), 2.5),
    "STANDOFF": ([("Standoff-ASM", 2)], (2, 4), 2.5),
    "RECCE":    ([("Recon-pod", 1)], (1, 2), 2.5),
    "CAS":      ([("Unguided-500lb", 6), ("WVR-AAM", 2)], (2, 4), 2.0),
    "AIRLIFT":  ([], (1, 2), 4.0),
}
MISSION_MIX = {"CAP": .18, "ESCORT": .08, "STRIKE": .22, "SEAD": .10,
               "STANDOFF": .08, "RECCE": .12, "CAS": .10, "AIRLIFT": .12}

THREAT_TYPES = [("SAM-long", 250), ("SAM-medium", 100), ("SAM-short", 30),
                ("EW-radar", 300)]
DUTY_LIMITS = {"max_flight_h_per_24h": 6.0, "max_flight_h_per_7d": 30.0,
               "min_rest_h_between_sorties": 10.0}  # ASSUMED values


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def main(a):
    rng = np.random.default_rng(a.seed)
    bases = pd.read_csv(PROC / "bases.csv")
    zlat, zlon = (a.zone[0] + a.zone[2]) / 2, (a.zone[1] + a.zone[3]) / 2
    bases["dist_to_zone_km"] = haversine(bases.latitude_deg, bases.longitude_deg, zlat, zlon).round(0)
    if a.max_bases and a.max_bases < len(bases):  # forward bases = nearest to the zone
        bases = bases.sort_values("dist_to_zone_km").head(a.max_bases)
    bases = bases.reset_index(drop=True)
    n_transport = max(1, len(bases) // 12) if len(bases) > 2 else 0
    transport_idx = set(rng.choice(len(bases), n_transport, replace=False)) if n_transport else set()
    bases["base_role"] = ["transport" if i in transport_idx else "fighter"
                          for i in range(len(bases))]

    # scenario clock: start of the weather forecast if available
    wpath = RAW / "weather_forecast.csv"
    weather = pd.read_csv(wpath) if wpath.exists() else None
    start = (pd.to_datetime(weather["time"].min()) if weather is not None
             else pd.Timestamp.utcnow().tz_localize(None).normalize())
    end = start + pd.Timedelta(hours=a.hours)

    # ------------------------------------------------------------- aircraft
    ac = []
    tw = np.array([TYPE_WEIGHT[t] for t in FIGHTERS], float)
    tw /= tw.sum()
    plan = []
    for _, b in bases.iterrows():
        if b.base_role == "transport":
            types_here = [("C-130J", int(rng.integers(4, 9)))]
        else:
            k = int(rng.integers(1, 3))
            chosen = rng.choice(FIGHTERS, k, replace=False, p=tw)
            types_here = [(t, int(rng.integers(a.min_aircraft, a.max_aircraft + 1)) // k + 2)
                          for t in chosen]
        plan.append([b.ident, b.base_role, types_here])
    # coverage guarantee: Su-30MKI covers CAP/ESCORT/STRIKE/SEAD/STANDOFF/CAS;
    # RECCE needs Rafale, Mirage or Jaguar. Add them if the random draw missed them.
    fighter_plans = [p for p in plan if p[1] == "fighter"]
    present = {t for p in plan for t, _ in p[2]}
    if fighter_plans and "Su-30MKI" not in present:
        fighter_plans[0][2].append(("Su-30MKI", 8))
    if fighter_plans and not present & {"Rafale", "Mirage-2000", "Jaguar"}:
        fighter_plans[-1][2].append(("Jaguar", 6))
    for ident, _, types_here in plan:
        for t, n in types_here:
            for _ in range(n):
                ac.append((ident, t))
    ac = pd.DataFrame(ac, columns=["base_ident", "aircraft_type"])
    ac["tail_id"] = [f"SYN-{t[:3].upper()}-{i:04d}" for i, t in enumerate(ac.aircraft_type, 1)]
    ac["status"] = rng.choice(["serviceable", "in_maintenance", "unserviceable"],
                              len(ac), p=[.76, .14, .10])
    ac["available_from"] = pd.NaT
    nsv = ac.status != "serviceable"
    ret_h = np.where(ac.status == "in_maintenance", rng.uniform(4, 72, len(ac)),
                     rng.uniform(2, 48, len(ac)))
    ac.loc[nsv, "available_from"] = [start + pd.Timedelta(hours=h) for h in ret_h[nsv]]
    ac["health_index"] = np.round(rng.beta(6, 2, len(ac)), 3)
    ac["hours_to_next_service"] = np.round(rng.uniform(0, 100, len(ac)), 1)
    ac["rul_est_hours"] = np.round(rng.weibull(2.0, len(ac)) * 300 * ac.health_index, 1)
    ac["risk_fail_next_24h"] = np.round(1 - np.exp(-(24 / ac.rul_est_hours.clip(lower=1)) ** 2), 3)

    # ----------------------------------------------------------------- crew
    crew = []
    seats = AIRCRAFT_TYPES.set_index("aircraft_type").crew_seats
    for (bid, t), g in ac.groupby(["base_ident", "aircraft_type"]):
        n = len(g)
        if t == "C-130J":
            roles = [("transport_pilot", int(np.ceil(2.2 * n)))]
        else:
            roles = [("pilot", int(np.ceil(1.4 * n)))]
            if seats[t] == 2:
                roles.append(("wso", int(np.ceil(1.4 * n))))
        for role, m in roles:
            for _ in range(m):
                crew.append((bid, role, t))
    crew = pd.DataFrame(crew, columns=["base_ident", "role", "primary_type"])
    crew["crew_id"] = [f"CRW-{i:04d}" for i in range(1, len(crew) + 1)]
    second = {}
    types_by_base = ac.groupby("base_ident").aircraft_type.unique().to_dict()
    sec = []
    for _, c in crew.iterrows():
        others = [t for t in types_by_base[c.base_ident] if t != c.primary_type]
        sec.append(rng.choice(others) if others and rng.random() < .25 else "")
    crew["secondary_type"] = sec
    crew["night_qualified"] = rng.random(len(crew)) < .75
    probs = {"CAP": 1, "ESCORT": 1, "CAS": .4, "STRIKE": .7, "SEAD": .25,
             "STANDOFF": .4, "RECCE": .3}
    crew["qualified_missions"] = [
        "|".join(m for m, p in probs.items() if rng.random() < p) if r != "transport_pilot" else "AIRLIFT"
        for r in crew.role]
    crew["experience_hours"] = rng.integers(250, 3500, len(crew))
    z = rng.random(len(crew)) < .6
    crew["flight_h_last_24h"] = np.where(z, 0.0, np.round(rng.uniform(1, 6, len(crew)), 1))
    crew["flight_h_last_7d"] = np.round(crew.flight_h_last_24h + rng.uniform(0, 25, len(crew)), 1)
    crew["hours_since_last_sortie"] = np.round(rng.uniform(8, 72, len(crew)), 1)
    crew["status"] = rng.choice(["fit", "medical_grounded", "on_leave"], len(crew), p=[.93, .04, .03])
    crew = crew[["crew_id", "base_ident", "role", "primary_type", "secondary_type",
                 "qualified_missions", "night_qualified", "experience_hours",
                 "flight_h_last_24h", "flight_h_last_7d", "hours_since_last_sortie", "status"]]

    # -------------------------------------------------- weapons + fuel stock
    stock = []
    per_base = ac.groupby("base_ident").size()
    for bid, n in per_base.items():
        for _, w in WEAPONS.iterrows():
            qty = int(n * STOCK_PER_AIRCRAFT[w.weapon_class] * rng.uniform(.6, 1.4))
            stock.append((bid, w.weapon_class, qty))
    stock = pd.DataFrame(stock, columns=["base_ident", "weapon_class", "quantity"])
    fuel = pd.DataFrame({"base_ident": per_base.index,
                         "fuel_kilolitres": (per_base.values * rng.uniform(12, 30, len(per_base))).round(0)})
    compat = pd.DataFrame([(w, t) for w, ts in WEAPON_COMPAT.items() for t in ts],
                          columns=["weapon_class", "aircraft_type"])
    capability = pd.DataFrame([(m, t) for m, ts in CAN_FLY.items() for t in ts],
                              columns=["mission_type", "aircraft_type"])

    # ------------------------------- notional exercise zone: threats, targets
    lat0, lon0, lat1, lon1 = a.zone
    threats = []
    for i in range(a.threats):
        ttype, rng_km = THREAT_TYPES[int(rng.integers(0, len(THREAT_TYPES)))]
        threats.append((f"THR-{i + 1:03d}", ttype, round(rng.uniform(lat0, lat1), 4),
                        round(rng.uniform(lon0, lon1), 4), rng_km))
    threats = pd.DataFrame(threats, columns=["threat_id", "threat_type", "lat", "lon", "range_km"])

    def exposure(lat, lon):
        d = haversine(lat, lon, threats.lat.values, threats.lon.values)
        return int((d <= threats.range_km.values).sum())

    types = list(MISSION_MIX)
    mt = rng.choice(types, a.missions, p=np.array(list(MISSION_MIX.values())) / sum(MISSION_MIX.values()))
    missions = []
    for i, m in enumerate(mt, 1):
        wl, (lo, hi), dur = MISSION_PROFILES[m]
        if m == "AIRLIFT":
            dest = bases.sample(1, random_state=int(rng.integers(1e6))).iloc[0]
            lat, lon = float(dest.latitude_deg), float(dest.longitude_deg)
        else:
            lat, lon = round(rng.uniform(lat0, lat1), 4), round(rng.uniform(lon0, lon1), 4)
        t0 = start + pd.Timedelta(hours=float(rng.uniform(0, max(a.hours - 8, 1))))
        missions.append(dict(
            mission_id=f"MSN-{i:03d}", mission_type=m,
            priority=int(rng.choice([1, 2, 3, 4, 5], p=[.10, .20, .35, .25, .10])),
            target_lat=lat, target_lon=lon,
            earliest_start=t0.floor("15min"),
            latest_start=(t0 + pd.Timedelta(hours=float(rng.uniform(1, 4)))).floor("15min"),
            duration_h=dur, aircraft_required=int(rng.integers(lo, hi + 1)),
            weapons_per_aircraft="|".join(f"{w}:{q}" for w, q in wl),
            threats_covering_target=0 if m == "AIRLIFT" else exposure(lat, lon)))
    missions = pd.DataFrame(missions).sort_values("earliest_start")

    dist = [(m.mission_id, b.ident, round(float(haversine(m.target_lat, m.target_lon,
             b.latitude_deg, b.longitude_deg)), 1))
            for m in missions.itertuples() for b in bases.itertuples()]
    dist = pd.DataFrame(dist, columns=["mission_id", "base_ident", "distance_km"])

    # ------------------------------------------------ disruption event stream
    ev = []

    def rt():
        return (start + pd.Timedelta(hours=float(rng.uniform(1, a.hours - 1)))).floor("15min")
    sv = ac[ac.status == "serviceable"]
    for _, r in sv.sample(min(a.disruptions, len(sv)), random_state=a.seed).iterrows():
        ev.append((rt(), "aircraft_unserviceable", r.tail_id, r.base_ident, np.nan, np.nan,
                   round(float(rng.uniform(4, 36)), 1), "technical snag"))
    for _, r in crew[crew.status == "fit"].sample(max(a.disruptions // 2, 1), random_state=a.seed).iterrows():
        ev.append((rt(), "crew_unavailable", r.crew_id, r.base_ident, np.nan, np.nan,
                   round(float(rng.uniform(12, 48)), 1), "illness / fatigue"))
    for _, r in bases.sample(min(max(a.disruptions // 4, 1), len(bases)), random_state=a.seed).iterrows():
        ev.append((rt(), "runway_closed", r.ident, r.ident, np.nan, np.nan,
                   round(float(rng.uniform(2, 8)), 1), "runway damage / FOD"))
    for k in range(max(a.disruptions // 3, 1)):
        ev.append((rt(), "new_priority_target", f"NEWTGT-{k + 1:02d}", "",
                   round(rng.uniform(lat0, lat1), 4), round(rng.uniform(lon0, lon1), 4),
                   np.nan, str(rng.choice(["STRIKE", "SEAD", "STANDOFF", "RECCE", "CAS"]))))
    if weather is not None:  # real weather -> weather holds
        w = weather.copy()
        w["time"] = pd.to_datetime(w["time"])
        bad = w[(w.visibility < 800) | (w.wind_gusts_10m > 25) | (w.weather_code >= 95)]
        for ident, g in bad.groupby("ident"):
            if ident in set(bases.ident):
                ev.append((g.time.min(), "weather_below_minima", ident, ident, np.nan, np.nan,
                           float(len(g)), "visibility/gust/thunderstorm (from real forecast)"))
    cpath = RAW / "conflict_events.csv"
    if cpath.exists() and a.intel_alerts:
        c = pd.read_csv(cpath).sort_values("fatalities", ascending=False).head(300)
        for _, r in c.sample(min(a.intel_alerts, len(c)), random_state=a.seed).iterrows():
            ev.append((rt(), "intel_alert", f"EVT-{r.event_id}", "", r.latitude, r.longitude,
                       np.nan, f"replayed real event: {r.event_type}, {r.location}"[:120]))
    events = pd.DataFrame(ev, columns=["time", "event_type", "entity_id", "base_ident",
                                       "lat", "lon", "duration_h", "detail"]).sort_values("time")
    events.insert(0, "event_id", [f"EV-{i:03d}" for i in range(1, len(events) + 1)])

    # ----------------------------------------------------------------- save
    out = {"bases_scenario": bases, "aircraft_types": AIRCRAFT_TYPES, "aircraft": ac,
           "crew": crew, "weapon_classes": WEAPONS, "weapon_stock": stock,
           "weapon_compat": compat, "fuel_stock": fuel, "mission_capability": capability,
           "threats": threats, "missions": missions, "base_target_distance": dist,
           "disruption_events": events}
    for name, df in out.items():
        df.to_csv(SYN / f"{name}.csv", index=False)
    (SYN / "ASSUMPTIONS.txt").write_text(
        "SYNTHETIC DATA: NOT REAL IAF DATA\n"
        f"seed={a.seed}  scenario_start={start}  hours={a.hours}\n"
        f"notional exercise zone (lat0,lon0,lat1,lon1)={a.zone}\n"
        f"duty limits (assumed): {DUTY_LIMITS}\n"
        "Aircraft figures are rough public approximations; weapon classes generic;\n"
        "fleet, crews, stocks, missions, threats and event timings are random.\n")

    print(f"Scenario: {start} -> {end}")
    print(f"Bases {len(bases)} | aircraft {len(ac)} "
          f"({(ac.status == 'serviceable').sum()} serviceable) | crew {len(crew)} | "
          f"missions {len(missions)} | threats {len(threats)} | events {len(events)}")
    print(ac.aircraft_type.value_counts().to_string())
    print("Event types:", events.event_type.value_counts().to_dict())
    print(f"Saved {len(out)} CSV files -> {SYN}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--max-bases", type=int, default=0, help="0 = all curated bases")
    p.add_argument("--min-aircraft", type=int, default=10)
    p.add_argument("--max-aircraft", type=int, default=20)
    p.add_argument("--missions", type=int, default=40)
    p.add_argument("--threats", type=int, default=15)
    p.add_argument("--disruptions", type=int, default=10)
    p.add_argument("--intel-alerts", type=int, default=10)
    p.add_argument("--hours", type=int, default=72)
    p.add_argument("--zone", nargs=4, type=float, default=[25.5, 70.0, 29.5, 75.0],
                   metavar=("LAT0", "LON0", "LAT1", "LON1"),
                   help="notional exercise zone for targets/threats (adjust freely)")
    main(p.parse_args())
