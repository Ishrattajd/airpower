"""
Phase 1.8: validate the data BEFORE building anything on top of it.

Checks (1) files and columns, (2) unique keys, (3) broken links between files,
(4) impossible values, (5) weather coverage, (6) events, and (7) whether the
missions can actually be flown with the resources we have.

Writes docs/validation_report.md and docs/mission_feasibility.csv.
Exit code 1 if any FAIL, so the freeze step refuses bad data.

Usage: python 09_validate_data.py
"""
import sys
import numpy as np
import pandas as pd
from common import ROOT, RAW, PROC, SYN

R = []  # (level, area, name, detail)


def add(level, area, name, detail=""):
    R.append((level, area, name, detail))


def check(area, name, ok, detail="", level="FAIL"):
    add("PASS" if ok else level, area, name, detail)


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


SCHEMA = {
    "bases_scenario": (SYN, ["ident", "base_name", "latitude_deg", "longitude_deg", "longest_runway_ft", "base_role"]),
    "aircraft_types": (SYN, ["aircraft_type", "combat_radius_km", "max_payload_kg", "crew_seats", "min_runway_ft"]),
    "aircraft": (SYN, ["base_ident", "aircraft_type", "tail_id", "status", "available_from", "health_index", "risk_fail_next_24h"]),
    "crew": (SYN, ["crew_id", "base_ident", "role", "primary_type", "secondary_type", "qualified_missions", "night_qualified", "flight_h_last_24h", "flight_h_last_7d", "status"]),
    "weapon_classes": (SYN, ["weapon_class", "unit_kg"]),
    "weapon_stock": (SYN, ["base_ident", "weapon_class", "quantity"]),
    "weapon_compat": (SYN, ["weapon_class", "aircraft_type"]),
    "fuel_stock": (SYN, ["base_ident", "fuel_kilolitres"]),
    "mission_capability": (SYN, ["mission_type", "aircraft_type"]),
    "threats": (SYN, ["threat_id", "threat_type", "lat", "lon", "range_km"]),
    "missions": (SYN, ["mission_id", "mission_type", "priority", "target_lat", "target_lon", "earliest_start", "latest_start", "duration_h", "aircraft_required", "weapons_per_aircraft", "threats_covering_target"]),
    "base_target_distance": (SYN, ["mission_id", "base_ident", "distance_km"]),
    "disruption_events": (SYN, ["event_id", "time", "event_type", "entity_id", "base_ident", "lat", "lon", "duration_h", "detail"]),
    "weather": (RAW, ["ident", "time", "visibility", "wind_gusts_10m", "wind_speed_10m", "weather_code"]),
}
FILEMAP = {"weather": "weather_forecast.csv"}
KEYS = {"bases_scenario": ["ident"], "aircraft_types": ["aircraft_type"], "aircraft": ["tail_id"],
        "crew": ["crew_id"], "weapon_classes": ["weapon_class"], "weapon_stock": ["base_ident", "weapon_class"],
        "weapon_compat": ["weapon_class", "aircraft_type"], "fuel_stock": ["base_ident"],
        "mission_capability": ["mission_type", "aircraft_type"], "threats": ["threat_id"],
        "missions": ["mission_id"], "base_target_distance": ["mission_id", "base_ident"],
        "disruption_events": ["event_id"], "weather": ["ident", "time"]}


def parse_weapons(s):
    if not isinstance(s, str) or not s.strip():
        return {}
    return {a.split(":")[0]: int(a.split(":")[1]) for a in s.split("|")}


def main():
    D = {}
    # ------------------------------------------------ 1. files and columns
    for name, (folder, cols) in SCHEMA.items():
        p = folder / FILEMAP.get(name, f"{name}.csv")
        if not p.exists():
            add("FAIL", "Files", f"{name} exists", f"missing: {p.relative_to(ROOT)}")
            continue
        df = pd.read_csv(p, low_memory=False)
        miss = [c for c in cols if c not in df.columns]
        check("Files", f"{name}: has data and required columns", len(df) > 0 and not miss,
              f"{len(df)} rows" if not miss else f"missing columns {miss}")
        if len(df) > 0 and not miss:
            D[name] = df
    have = lambda *n: all(x in D for x in n)

    # ------------------------------------------------------ 2. unique keys
    for name, key in KEYS.items():
        if name in D:
            d = D[name].duplicated(key).sum()
            check("Keys", f"{name}: {'+'.join(key)} unique", d == 0, f"{d} duplicates" if d else "")

    # --------------------------------------------- 3. links between files
    def link(child, col, parent, pcol, label=None, allow_blank=False):
        if not have(child, parent):
            return
        vals = D[child][col].dropna()
        if allow_blank:
            vals = vals[vals != ""]
        bad = sorted(set(vals) - set(D[parent][pcol]))
        check("Links", label or f"{child}.{col} -> {parent}.{pcol}", not bad, f"unknown: {bad[:5]}" if bad else "")
    link("aircraft", "base_ident", "bases_scenario", "ident")
    link("aircraft", "aircraft_type", "aircraft_types", "aircraft_type")
    link("crew", "base_ident", "bases_scenario", "ident")
    link("crew", "primary_type", "aircraft_types", "aircraft_type")
    link("crew", "secondary_type", "aircraft_types", "aircraft_type", allow_blank=True)
    link("weapon_stock", "base_ident", "bases_scenario", "ident")
    link("weapon_stock", "weapon_class", "weapon_classes", "weapon_class")
    link("weapon_compat", "weapon_class", "weapon_classes", "weapon_class")
    link("weapon_compat", "aircraft_type", "aircraft_types", "aircraft_type")
    link("mission_capability", "aircraft_type", "aircraft_types", "aircraft_type")
    link("fuel_stock", "base_ident", "bases_scenario", "ident")
    link("base_target_distance", "base_ident", "bases_scenario", "ident")
    link("base_target_distance", "mission_id", "missions", "mission_id")
    if have("missions", "mission_capability"):
        bad = sorted(set(D["missions"].mission_type) - set(D["mission_capability"].mission_type))
        check("Links", "every mission type has capable aircraft types", not bad, f"no capability rows for {bad}" if bad else "")
    if have("missions", "weapon_classes"):
        used = {w for s in D["missions"].weapons_per_aircraft for w in parse_weapons(s)}
        bad = sorted(used - set(D["weapon_classes"].weapon_class))
        check("Links", "weapons named in missions exist", not bad, f"unknown {bad}" if bad else "")
    if have("missions", "bases_scenario", "base_target_distance"):
        exp = len(D["missions"]) * len(D["bases_scenario"])
        check("Links", "distance table covers every mission x base", len(D["base_target_distance"]) == exp,
              f"{len(D['base_target_distance'])} rows, expected {exp}")
        m = D["missions"].set_index("mission_id"); b = D["bases_scenario"].set_index("ident")
        s = D["base_target_distance"].sample(min(50, len(D["base_target_distance"])), random_state=1)
        calc = haversine(m.loc[s.mission_id, "target_lat"].values, m.loc[s.mission_id, "target_lon"].values,
                         b.loc[s.base_ident, "latitude_deg"].values, b.loc[s.base_ident, "longitude_deg"].values)
        check("Links", "distances match coordinates (50 sampled)", np.allclose(calc, s.distance_km.values, atol=0.2),
              f"max diff {np.abs(calc - s.distance_km.values).max():.2f} km")
    if have("disruption_events", "aircraft", "crew", "bases_scenario", "mission_capability"):
        e = D["disruption_events"]
        for et, tab, col in [("aircraft_unserviceable", "aircraft", "tail_id"), ("crew_unavailable", "crew", "crew_id"),
                             ("runway_closed", "bases_scenario", "ident")]:
            ids = e[e.event_type == et].entity_id
            bad = sorted(set(ids) - set(D[tab][col]))
            check("Links", f"events '{et}' point to real {col}", not bad, f"unknown {bad[:5]}" if bad else "")
        wb = e[e.event_type == "weather_below_minima"].entity_id
        if len(wb):
            bad = sorted(set(wb) - set(D["bases_scenario"].ident))
            check("Links", "weather events point to scenario bases", not bad, f"unknown {bad[:5]}" if bad else "")
        npt = e[e.event_type == "new_priority_target"]
        bad = sorted(set(npt.detail) - set(D["mission_capability"].mission_type))
        check("Links", "new-target events use valid mission types", not bad, f"{bad}" if bad else "")
        check("Events", "new targets and intel alerts have coordinates",
              e[e.event_type.isin(["new_priority_target", "intel_alert"])][["lat", "lon"]].notna().all().all())

    # --------------------------------------------------------- 4. values
    def rng(area, name, s, lo, hi):
        bad = int(((s < lo) | (s > hi) | s.isna()).sum())
        check(area, name, bad == 0, f"{bad} values outside [{lo}, {hi}] or empty" if bad else "")
    if have("bases_scenario"):
        b = D["bases_scenario"]
        rng("Values", "base latitude within India box", b.latitude_deg, 6, 38)
        rng("Values", "base longitude within India box", b.longitude_deg, 67, 98)
        rng("Values", "runway length 3000 to 16000 ft", b.longest_runway_ft, 3000, 16000)
    if have("aircraft"):
        a = D["aircraft"]
        check("Values", "aircraft status values valid", set(a.status) <= {"serviceable", "in_maintenance", "unserviceable"})
        rng("Values", "health_index 0 to 1", a.health_index, 0, 1)
        rng("Values", "risk_fail_next_24h 0 to 1", a.risk_fail_next_24h, 0, 1)
        ok = (a.available_from.isna() == (a.status == "serviceable")).all()
        check("Values", "available_from empty only for serviceable aircraft", ok)
        check("Values", "at least 1 serviceable aircraft", (a.status == "serviceable").sum() > 0,
              f"{(a.status == 'serviceable').sum()} serviceable of {len(a)}")
    if have("crew"):
        c = D["crew"]
        check("Values", "crew status values valid", set(c.status) <= {"fit", "medical_grounded", "on_leave"})
        rng("Values", "crew hours last 24h 0 to 24", c.flight_h_last_24h, 0, 24)
        check("Values", "7-day hours >= 24-hour hours", (c.flight_h_last_7d >= c.flight_h_last_24h).all())
    if have("weapon_stock"):
        check("Values", "weapon stock never negative", (D["weapon_stock"].quantity >= 0).all())
    if have("fuel_stock"):
        check("Values", "fuel stock positive", (D["fuel_stock"].fuel_kilolitres > 0).all())
    if have("missions"):
        m = D["missions"]
        rng("Values", "mission priority 1 to 5", m.priority, 1, 5)
        rng("Values", "aircraft_required 1 to 12", m.aircraft_required, 1, 12)
        rng("Values", "mission duration 0.5 to 12 h", m.duration_h, 0.5, 12)
        es, ls = pd.to_datetime(m.earliest_start), pd.to_datetime(m.latest_start)
        check("Values", "latest_start is not before earliest_start", (ls >= es).all())
        check("Values", "mission target coordinates present", m[["target_lat", "target_lon"]].notna().all().all())
    if have("aircraft_types"):
        t = D["aircraft_types"]
        check("Values", "aircraft performance numbers positive", (t[["combat_radius_km", "max_payload_kg", "crew_seats", "min_runway_ft"]] > 0).all().all())

    # ------------------------------------------------------- 5. weather
    start = None
    if have("weather"):
        w = D["weather"]
        w["time"] = pd.to_datetime(w["time"])
        start = w.time.min()
        check("Weather", "no gaps: same hours for every base", w.groupby("ident").size().nunique() == 1,
              f"{w.ident.nunique()} bases, {w.groupby('ident').size().max()} hours each")
        check("Weather", "values plausible (visibility>=0, wind>=0)", (w.visibility >= 0).all() and (w.wind_speed_10m >= 0).all())
        if have("bases_scenario"):
            miss = sorted(set(D["bases_scenario"].ident) - set(w.ident))
            check("Weather", "weather exists for every scenario base", not miss,
                  f"missing {miss} (rerun 02_openmeteo.py with --use-bases)" if miss else "")
        if have("missions"):
            ms = pd.to_datetime(D["missions"].latest_start).max()
            check("Weather", "forecast covers all mission times", w.time.max() >= ms - pd.Timedelta(hours=1),
                  f"forecast ends {w.time.max()}, last mission starts {ms}", level="WARN")
    if have("disruption_events") and start is not None:
        et = pd.to_datetime(D["disruption_events"].time)
        check("Events", "events fall inside the forecast window",
              ((et >= start) & (et <= start + pd.Timedelta(hours=96))).all(), level="WARN")

    # --------------------------------------------- 7. feasibility of missions
    feas = []
    if have("missions", "aircraft", "aircraft_types", "mission_capability", "base_target_distance",
            "bases_scenario", "weapon_stock", "weapon_compat", "weapon_classes", "crew"):
        at = D["aircraft_types"].set_index("aircraft_type")
        wk = D["weapon_classes"].set_index("weapon_class").unit_kg
        comp = D["weapon_compat"].groupby("aircraft_type").weapon_class.apply(set).to_dict()
        stock = D["weapon_stock"].set_index(["base_ident", "weapon_class"]).quantity.to_dict()
        rw = D["bases_scenario"].set_index("ident").longest_runway_ft
        sv = D["aircraft"][D["aircraft"].status == "serviceable"]
        fit = D["crew"][(D["crew"].status == "fit") & D["crew"].role.isin(["pilot", "transport_pilot"])].copy()
        fit["qm"] = fit.qualified_missions.fillna("").str.split("|")
        dist = D["base_target_distance"].set_index(["mission_id", "base_ident"]).distance_km.to_dict()
        # crew seat supply vs need
        for (bid, t), g in D["aircraft"].groupby(["base_ident", "aircraft_type"]):
            seats = at.loc[t, "crew_seats"] * (g.status == "serviceable").sum()
            supply = ((D["crew"].base_ident == bid) & (D["crew"].primary_type == t) & (D["crew"].status == "fit")).sum()
            if supply < seats:
                add("WARN", "Feasibility", f"crew supply low at {bid} for {t}", f"{supply} fit crew for {seats} seats (serviceable aircraft x seats)")
        for m in D["missions"].itertuples():
            capable = set(D["mission_capability"].query("mission_type == @m.mission_type").aircraft_type)
            need_w = parse_weapons(m.weapons_per_aircraft)
            net, best, why = 0, None, []
            for base in D["bases_scenario"].ident:
                d = dist[(m.mission_id, base)]
                c = sv[(sv.base_ident == base) & sv.aircraft_type.isin(capable)]
                c = c[[(d <= at.loc[t, "combat_radius_km"] and rw[base] >= at.loc[t, "min_runway_ft"]
                        and set(need_w) <= comp.get(t, set())
                        and sum(wk[k] * q for k, q in need_w.items()) <= at.loc[t, "max_payload_kg"])
                       for t in c.aircraft_type]]
                n = len(c)
                net += n
                w_ok = all(stock.get((base, k), 0) >= q * m.aircraft_required for k, q in need_w.items())
                cr = fit[(fit.base_ident == base) & fit.qm.apply(lambda x: m.mission_type in x)
                         & (fit.primary_type.isin(capable) | fit.secondary_type.isin(capable))]
                ok = n >= m.aircraft_required and w_ok and len(cr) >= m.aircraft_required
                if ok and best is None:
                    best = base
            if best is None:
                why = ("no capable aircraft in range anywhere" if net == 0 else
                       "enough aircraft only if split across bases (or limited by weapons/crew at each single base)")
            feas.append(dict(mission_id=m.mission_id, mission_type=m.mission_type, priority=m.priority,
                             aircraft_required=m.aircraft_required, capable_aircraft_in_range_all_bases=net,
                             single_base_feasible=best is not None, example_base=best or "", note=why))
        F = pd.DataFrame(feas)
        zero = F[F.capable_aircraft_in_range_all_bases == 0]
        check("Feasibility", "every mission has capable serviceable aircraft in range", zero.empty,
              f"impossible missions: {list(zero.mission_id)}" if len(zero) else "", level="WARN")
        short = F[F.capable_aircraft_in_range_all_bases < F.aircraft_required]
        check("Feasibility", "enough capable aircraft in range for each mission", short.empty,
              f"short: {list(short.mission_id)}" if len(short) else "", level="WARN")
        add("INFO", "Feasibility", "missions flyable from a single base (best case)",
            f"{int(F.single_base_feasible.sum())} of {len(F)}")
        # scarcity
        need_ac = int(D["missions"].aircraft_required.sum())
        add("INFO", "Scarcity", "aircraft demanded vs serviceable",
            f"{need_ac} aircraft-slots needed in total vs {len(sv)} serviceable (turnaround lets aircraft fly more than once)")
        dem = {}
        for m in D["missions"].itertuples():
            for k, q in parse_weapons(m.weapons_per_aircraft).items():
                dem[k] = dem.get(k, 0) + q * m.aircraft_required
        tot = D["weapon_stock"].groupby("weapon_class").quantity.sum()
        for k, q in sorted(dem.items()):
            lvl = "PASS" if tot.get(k, 0) >= q else "WARN"
            add(lvl, "Scarcity", f"weapon stock covers total demand: {k}", f"demand {q} vs stock {int(tot.get(k, 0))}")
        F.to_csv(ROOT / "docs" / "mission_feasibility.csv", index=False)

    # ------------------------------------------------------------ report
    fails = sum(1 for r in R if r[0] == "FAIL")
    warns = sum(1 for r in R if r[0] == "WARN")
    passes = sum(1 for r in R if r[0] == "PASS")
    (ROOT / "docs").mkdir(exist_ok=True)
    L = ["# Data Validation Report", "", f"**RESULT: {'FAIL' if fails else 'PASS'}**  "
         f"({passes} passed, {warns} warnings, {fails} failed)", "",
         "FAIL = must fix before freezing. WARN = look at it and decide. INFO = good to know.", ""]
    for area in dict.fromkeys(r[1] for r in R):
        L += [f"## {area}", "", "| Result | Check | Detail |", "|---|---|---|"]
        for lv, ar, nm, dt in R:
            if ar == area:
                L.append(f"| {lv} | {nm} | {str(dt).replace('|', '/')} |")
        L.append("")
    (ROOT / "docs" / "validation_report.md").write_text("\n".join(L), encoding="utf-8")

    print(f"RESULT: {'FAIL' if fails else 'PASS'}  ({passes} passed, {warns} warnings, {fails} failed)")
    for lv, ar, nm, dt in R:
        if lv != "PASS":
            print(f"  [{lv}] {ar}: {nm} {('- ' + str(dt)) if dt else ''}")
    print("Report: docs/validation_report.md")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    (ROOT / "docs").mkdir(exist_ok=True)
    main()
