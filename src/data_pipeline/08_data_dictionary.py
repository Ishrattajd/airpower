"""
Phase 1.7: build the data dictionary.

Scans every CSV in data/raw, data/processed and data/synthetic and writes
docs/data_dictionary.md. Column types, examples, ranges and missing-value
percentages are measured from your actual files; the descriptions are written
below. If a column has no description, the script warns you: add it to COLS.

Usage: python 08_data_dictionary.py
"""
import pandas as pd
from common import ROOT, RAW, PROC, SYN

REAL, DERIVED, SYNTH = "REAL", "REAL (curated)", "SYNTHETIC"

# --------------------------------------------------------------- descriptions
FILES = [
 dict(path=RAW / "airports_india.csv", src=REAL, key="ident",
      purpose="All airports/heliports in India (OurAirports). Source for coordinates.",
      links="ident -> runways.airport_ident, frequencies.airport_ident",
      cols=dict(id="OurAirports internal ID", ident="Airport code (ICAO or local); main key",
        type="large/medium/small_airport, heliport, closed, seaplane_base", name="Airport name",
        latitude_deg="Latitude, degrees", longitude_deg="Longitude, degrees",
        elevation_ft="Elevation above sea level, feet", continent="Continent code",
        iso_country="Country code (IN)", iso_region="State/region code", municipality="Nearest town/city",
        scheduled_service="Has airline service (yes/no)", icao_code="ICAO code if any",
        iata_code="IATA code if any", gps_code="GPS code", local_code="Local code",
        home_link="Website", wikipedia_link="Wikipedia page", keywords="Search keywords",
        is_military_guess="OUR flag: name contains Air Force/Air Base/etc. Unreliable; use bases.csv instead")),
 dict(path=RAW / "runways_india.csv", src=REAL, key="id",
      purpose="Runways of Indian airports (OurAirports).",
      links="airport_ident -> airports.ident",
      cols=dict(id="Runway ID", airport_ref="OurAirports airport ID", airport_ident="Airport code -> airports.ident",
        length_ft="Runway length, feet", width_ft="Runway width, feet", surface="Surface (ASP=asphalt, CON=concrete...)",
        lighted="1 if lit", closed="1 if closed", le_ident="Low-end runway number", he_ident="High-end runway number",
        le_latitude_deg="Low-end latitude", le_longitude_deg="Low-end longitude", le_elevation_ft="Low-end elevation, feet",
        le_heading_degT="Low-end heading, true degrees", le_displaced_threshold_ft="Low-end displaced threshold, feet",
        he_latitude_deg="High-end latitude", he_longitude_deg="High-end longitude", he_elevation_ft="High-end elevation, feet",
        he_heading_degT="High-end heading, true degrees", he_displaced_threshold_ft="High-end displaced threshold, feet")),
 dict(path=RAW / "frequencies_india.csv", src=REAL, key="id",
      purpose="Radio frequencies at airports (OurAirports).", links="airport_ident -> airports.ident",
      cols=dict(id="Frequency ID", airport_ref="OurAirports airport ID", airport_ident="Airport code -> airports.ident",
        type="Frequency type (TWR, GND, APP...)", description="Text description", frequency_mhz="Frequency, MHz")),
 dict(path=RAW / "navaids_india.csv", src=REAL, key="id",
      purpose="Navigation aids (VOR/NDB/DME) in India (OurAirports).", links="associated_airport -> airports.ident",
      cols=dict(id="Navaid ID", filename="Source file name", ident="Navaid identifier", name="Name", type="VOR, NDB, DME...",
        frequency_khz="Frequency, kHz", latitude_deg="Latitude", longitude_deg="Longitude", elevation_ft="Elevation, feet",
        iso_country="Country code", dme_frequency_khz="DME frequency, kHz", dme_channel="DME channel",
        dme_latitude_deg="DME latitude", dme_longitude_deg="DME longitude", dme_elevation_ft="DME elevation, feet",
        slaved_variation_deg="Slaved magnetic variation, degrees", magnetic_variation_deg="Magnetic variation, degrees",
        usageType="HIGH/LOW/BOTH/TERMINAL", power="HIGH/MEDIUM/LOW", associated_airport="Airport code served")),
 dict(path=RAW / "weather_forecast.csv", src=REAL, key="ident + time",
      purpose="Hourly weather forecast per base (Open-Meteo), 72 hours.", links="ident -> bases.ident",
      cols=dict(ident="Base code -> bases.ident", name="Base name", lat="Latitude", lon="Longitude",
        time="Hour (UTC), ISO format", temperature_2m="Temperature at 2 m, deg C", wind_speed_10m="Wind speed at 10 m, KNOTS",
        wind_direction_10m="Wind direction, degrees (from)", wind_gusts_10m="Wind gusts, KNOTS", visibility="Visibility, METRES",
        cloud_cover="Total cloud cover, %", cloud_cover_low="Low cloud cover, %", precipitation="Precipitation, mm",
        weather_code="WMO weather code (0 clear ... 95-99 thunderstorm)")),
 dict(path=RAW / "opensky_states.csv", src=REAL, key="snapshot_utc + icao24",
      purpose="Snapshots of live aircraft positions over India (OpenSky). Mostly civil; for traffic density only.",
      links="none",
      cols=dict(snapshot_utc="Snapshot time, Unix seconds UTC", icao24="Aircraft transponder ID", callsign="Callsign",
        origin_country="Country of registration", time_position="Time of last position, Unix s", last_contact="Last contact, Unix s",
        lon="Longitude", lat="Latitude", baro_altitude_m="Barometric altitude, metres", on_ground="True if on ground",
        velocity_ms="Ground speed, m/s", true_track="Track angle, degrees", vertical_rate="Climb rate, m/s",
        sensors="Receiver IDs (empty)", geo_altitude_m="GPS altitude, metres", squawk="Transponder code",
        spi="Special purpose indicator", position_source="0=ADS-B, 1=ASTERIX, 2=MLAT", category="Aircraft category code")),
 dict(path=RAW / "conflict_events.csv", src=REAL, key="event_id",
      purpose="Past conflict events 2018-2024 (UCDP GED). Replayed as intel alerts in the demo; NOT live.",
      links="none",
      cols=dict(event_id="UCDP event ID", event_date="Event date", event_type="State-based / Non-state / One-sided",
        actor1="Side A", actor2="Side B", country="Country", admin1="State/province", location="Place description",
        latitude="Latitude", longitude="Longitude", fatalities="Best estimate of deaths", conflict_name="UCDP conflict name")),
 dict(path=PROC / "bases.csv", src=DERIVED, key="ident",
      purpose="37 curated air bases with real coordinates and runway data (made by 06_make_bases.py from public knowledge; verify).",
      links="ident -> weather_forecast.ident, aircraft.base_ident, crew.base_ident, weapon_stock.base_ident",
      cols=dict(ident="Base code (main key)", base_name="Short display name", name="Full airport name (OurAirports)",
        region="North/East/West/Central/South/Islands (rough, from coordinates)", latitude_deg="Latitude", longitude_deg="Longitude",
        elevation_ft="Elevation, feet", n_runways="Number of open runways", longest_runway_ft="Longest open runway, feet",
        longest_surface="Surface of longest runway", type="OurAirports airport type", iso_region="State code")),
 dict(path=SYN / "bases_scenario.csv", src=SYNTH, key="ident",
      purpose="Bases chosen for the demo scenario (a subset of bases.csv) plus a role.", links="ident -> bases.ident",
      cols=dict(ident="Base code", base_name="Short name", name="Full name", region="Region", latitude_deg="Latitude",
        longitude_deg="Longitude", elevation_ft="Elevation, feet", n_runways="Open runways", longest_runway_ft="Longest runway, feet",
        longest_surface="Surface", type="Airport type", iso_region="State code",
        base_role="SYNTHETIC: fighter or transport (random)",
        dist_to_zone_km="Distance from this base to the centre of the exercise zone, km (used to pick forward bases)")),
 dict(path=SYN / "aircraft_types.csv", src=SYNTH, key="aircraft_type",
      purpose="Performance table per aircraft type. Rough public approximations (placeholders).", links="aircraft_type -> aircraft.aircraft_type",
      cols=dict(aircraft_type="Type name (main key)", role="General role", combat_radius_km="Max distance to target and back, km (approx.)",
        max_payload_kg="Max weapon load, kg (approx.)", crew_seats="Crew needed per aircraft",
        min_runway_ft="Min runway length to operate, feet (assumed)", sortie_h="Typical sortie length, hours (assumed)",
        turnaround_h="Time to refuel/rearm between sorties, hours (assumed)")),
 dict(path=SYN / "aircraft.csv", src=SYNTH, key="tail_id",
      purpose="The fleet: one row per aircraft, with status. Invented tail numbers (SYN-...).",
      links="base_ident -> bases.ident; aircraft_type -> aircraft_types",
      cols=dict(base_ident="Home base", aircraft_type="Type", tail_id="Aircraft ID (main key)",
        status="serviceable / in_maintenance / unserviceable", available_from="When it becomes usable again (empty if serviceable)",
        health_index="RANDOM placeholder 0-1 (higher = healthier); replaced in Phase 2",
        hours_to_next_service="RANDOM flying hours left before scheduled service",
        rul_est_hours="RANDOM placeholder for remaining useful life; replaced by ML in Phase 2",
        risk_fail_next_24h="Derived from the random rul_est_hours; replaced in Phase 2")),
 dict(path=SYN / "crew.csv", src=SYNTH, key="crew_id",
      purpose="Aircrew roster: qualifications, hours, fitness.", links="base_ident -> bases.ident; primary_type -> aircraft_types",
      cols=dict(crew_id="Crew member ID (main key)", base_ident="Home base", role="pilot / wso / transport_pilot",
        primary_type="Main aircraft type", secondary_type="Second type (often empty)",
        qualified_missions="Mission types allowed, separated by |", night_qualified="True if cleared for night",
        experience_hours="Total flying hours", flight_h_last_24h="Hours flown in last 24 h",
        flight_h_last_7d="Hours flown in last 7 days", hours_since_last_sortie="Rest time since last sortie, hours",
        status="fit / medical_grounded / on_leave")),
 dict(path=SYN / "weapon_classes.csv", src=SYNTH, key="weapon_class",
      purpose="Generic weapon classes and unit weight.", links="weapon_class -> weapon_stock, weapon_compat",
      cols=dict(weapon_class="Generic class name (main key)", unit_kg="Weight of one item, kg (approx.)")),
 dict(path=SYN / "weapon_stock.csv", src=SYNTH, key="base_ident + weapon_class",
      purpose="How many of each weapon class are at each base.", links="base_ident -> bases.ident; weapon_class -> weapon_classes",
      cols=dict(base_ident="Base", weapon_class="Weapon class", quantity="Number in stock")),
 dict(path=SYN / "weapon_compat.csv", src=SYNTH, key="weapon_class + aircraft_type",
      purpose="Which aircraft type can carry which weapon class.", links="-> weapon_classes, aircraft_types",
      cols=dict(weapon_class="Weapon class", aircraft_type="Aircraft type that can carry it")),
 dict(path=SYN / "fuel_stock.csv", src=SYNTH, key="base_ident", purpose="Fuel available at each base.",
      links="base_ident -> bases.ident", cols=dict(base_ident="Base", fuel_kilolitres="Fuel in stock, kilolitres")),
 dict(path=SYN / "mission_capability.csv", src=SYNTH, key="mission_type + aircraft_type",
      purpose="Which aircraft types are allowed to fly which mission types.", links="-> aircraft_types",
      cols=dict(mission_type="CAP, ESCORT, STRIKE, SEAD, STANDOFF, RECCE, CAS, AIRLIFT", aircraft_type="Allowed type")),
 dict(path=SYN / "threats.csv", src=SYNTH, key="threat_id",
      purpose="Notional enemy air-defence sites in an adjustable exercise zone. Not real sites.", links="none",
      cols=dict(threat_id="Threat ID (main key)", threat_type="SAM-long / SAM-medium / SAM-short / EW-radar",
        lat="Latitude", lon="Longitude", range_km="Coverage radius, km (generic)")),
 dict(path=SYN / "missions.csv", src=SYNTH, key="mission_id",
      purpose="The 20 missions to plan, with time windows and needs.", links="mission_id -> base_target_distance",
      cols=dict(mission_id="Mission ID (main key)", mission_type="Type (see mission_capability)",
        priority="1 = highest ... 5 = lowest", target_lat="Target latitude", target_lon="Target longitude",
        earliest_start="Earliest allowed start", latest_start="Latest allowed start", duration_h="Mission length, hours",
        aircraft_required="Number of aircraft needed", weapons_per_aircraft="Weapons per aircraft as class:qty, separated by |",
        threats_covering_target="Number of threat sites covering the target")),
 dict(path=SYN / "base_target_distance.csv", src=SYNTH, key="mission_id + base_ident",
      purpose="Straight-line distance from every base to every mission target.", links="-> missions, bases",
      cols=dict(mission_id="Mission", base_ident="Base", distance_km="Great-circle distance, km")),
 dict(path=SYN / "disruption_events.csv", src=SYNTH, key="event_id",
      purpose="Timeline of surprises that trigger re-planning. Weather holds come from the real forecast; intel alerts replay real past events.",
      links="entity_id refers to tail_id, crew_id or base ident depending on event_type",
      cols=dict(event_id="Event ID (main key)", time="When it happens",
        event_type="aircraft_unserviceable, crew_unavailable, runway_closed, new_priority_target, weather_below_minima, intel_alert",
        entity_id="Affected aircraft, crew, base or new target", base_ident="Base involved (may be empty)",
        lat="Latitude (new targets and alerts)", lon="Longitude (new targets and alerts)",
        duration_h="How long it lasts, hours (weather: hours below limits)", detail="Free-text reason or mission type")),
]


def esc(x):
    return str(x).replace("|", "\\|").replace("\n", " ")


def simple_type(s):
    k = s.dtype.kind
    return {"i": "integer", "u": "integer", "f": "decimal", "b": "true/false"}.get(k, "text")


def summarize(s):
    nn = s.dropna()
    if nn.empty:
        return "(all empty)"
    if s.dtype.kind in "iuf":
        return f"{nn.min():g} to {nn.max():g}"
    if s.dtype.kind == "b":
        return "true/false"
    u = nn.astype(str).unique()
    if len(u) <= 8:
        return ", ".join(sorted(u))[:80]
    return f"{len(u)} distinct values"


def main():
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    out, overview, warn = [], [], []
    for f in FILES:
        p = f["path"]
        if not p.exists():
            warn.append(f"MISSING FILE: {p.relative_to(ROOT)}")
            continue
        df = pd.read_csv(p, low_memory=False)
        rel = p.relative_to(ROOT / "data").as_posix()
        overview.append(f"| `{rel}` | {f['src']} | {len(df):,} | {df.shape[1]} | {esc(f['purpose'])} |")
        out.append(f"\n### `{rel}`  ({f['src']})\n")
        out.append(f"{f['purpose']}\n")
        out.append(f"- **Rows:** {len(df):,}  |  **Key:** `{f['key']}`  |  **Links:** {f['links']}\n")
        out.append("| Column | Type | Meaning | Example | Values / range | Missing |")
        out.append("|---|---|---|---|---|---|")
        for c in df.columns:
            d = f["cols"].get(c)
            if d is None:
                warn.append(f"No description: {rel} -> {c}")
                d = "(description missing)"
            nn = df[c].dropna()
            ex = esc(str(nn.iloc[0])[:40]) if len(nn) else ""
            miss = f"{df[c].isna().mean() * 100:.0f}%"
            out.append(f"| `{c}` | {simple_type(df[c])} | {esc(d)} | {ex} | {esc(summarize(df[c]))} | {miss} |")
        for c in f["cols"]:
            if c not in df.columns:
                warn.append(f"Described but not in file: {rel} -> {c}")

    head = [
        "# Data Dictionary: Air Power project",
        "",
        "Generated by `08_data_dictionary.py` from the actual files. Re-run it whenever data changes.",
        "",
        "**Labels:** REAL = downloaded open data. REAL (curated) = real data we filtered by hand. "
        "SYNTHETIC = invented for the demo; NOT real IAF data.",
        "",
        "**Units to remember:** wind and gusts in KNOTS, visibility in METRES, distances in km, "
        "runway length in FEET, times in UTC, mission priority 1 = most important.",
        "",
        "## Files at a glance",
        "",
        "| File | Source | Rows | Columns | Purpose |",
        "|---|---|---|---|---|",
    ] + overview + [
        "",
        "## How the files connect",
        "",
        "```",
        "bases.ident --- aircraft.base_ident --- aircraft.aircraft_type --- aircraft_types",
        "      |--- crew.base_ident            crew.primary_type      --- aircraft_types",
        "      |--- weapon_stock.base_ident --- weapon_stock.weapon_class --- weapon_classes",
        "      |--- weather_forecast.ident",
        "      |--- base_target_distance.base_ident --- missions.mission_id",
        "missions.mission_type --- mission_capability --- aircraft_types",
        "weapon_compat: weapon_class x aircraft_type (who can carry what)",
        "disruption_events.entity_id -> tail_id / crew_id / base ident / new target",
        "```",
        "",
        "## File details",
    ]
    (docs / "data_dictionary.md").write_text("\n".join(head + out) + "\n", encoding="utf-8")
    print(f"Wrote {docs / 'data_dictionary.md'} ({len(overview)} files documented)")
    if warn:
        print("\nWARNINGS:")
        for w in warn:
            print(" -", w)
    else:
        print("No warnings: every column has a description.")


if __name__ == "__main__":
    main()
