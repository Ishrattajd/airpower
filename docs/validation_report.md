# Data Validation Report

**RESULT: PASS**  (82 passed, 0 warnings, 0 failed)

FAIL = must fix before freezing. WARN = look at it and decide. INFO = good to know.

## Files

| Result | Check | Detail |
|---|---|---|
| PASS | bases_scenario: has data and required columns | 4 rows |
| PASS | aircraft_types: has data and required columns | 7 rows |
| PASS | aircraft: has data and required columns | 64 rows |
| PASS | crew: has data and required columns | 111 rows |
| PASS | weapon_classes: has data and required columns | 7 rows |
| PASS | weapon_stock: has data and required columns | 28 rows |
| PASS | weapon_compat: has data and required columns | 30 rows |
| PASS | fuel_stock: has data and required columns | 4 rows |
| PASS | mission_capability: has data and required columns | 26 rows |
| PASS | threats: has data and required columns | 15 rows |
| PASS | missions: has data and required columns | 20 rows |
| PASS | base_target_distance: has data and required columns | 80 rows |
| PASS | disruption_events: has data and required columns | 30 rows |
| PASS | weather: has data and required columns | 2664 rows |

## Keys

| Result | Check | Detail |
|---|---|---|
| PASS | bases_scenario: ident unique |  |
| PASS | aircraft_types: aircraft_type unique |  |
| PASS | aircraft: tail_id unique |  |
| PASS | crew: crew_id unique |  |
| PASS | weapon_classes: weapon_class unique |  |
| PASS | weapon_stock: base_ident+weapon_class unique |  |
| PASS | weapon_compat: weapon_class+aircraft_type unique |  |
| PASS | fuel_stock: base_ident unique |  |
| PASS | mission_capability: mission_type+aircraft_type unique |  |
| PASS | threats: threat_id unique |  |
| PASS | missions: mission_id unique |  |
| PASS | base_target_distance: mission_id+base_ident unique |  |
| PASS | disruption_events: event_id unique |  |
| PASS | weather: ident+time unique |  |

## Links

| Result | Check | Detail |
|---|---|---|
| PASS | aircraft.base_ident -> bases_scenario.ident |  |
| PASS | aircraft.aircraft_type -> aircraft_types.aircraft_type |  |
| PASS | crew.base_ident -> bases_scenario.ident |  |
| PASS | crew.primary_type -> aircraft_types.aircraft_type |  |
| PASS | crew.secondary_type -> aircraft_types.aircraft_type |  |
| PASS | weapon_stock.base_ident -> bases_scenario.ident |  |
| PASS | weapon_stock.weapon_class -> weapon_classes.weapon_class |  |
| PASS | weapon_compat.weapon_class -> weapon_classes.weapon_class |  |
| PASS | weapon_compat.aircraft_type -> aircraft_types.aircraft_type |  |
| PASS | mission_capability.aircraft_type -> aircraft_types.aircraft_type |  |
| PASS | fuel_stock.base_ident -> bases_scenario.ident |  |
| PASS | base_target_distance.base_ident -> bases_scenario.ident |  |
| PASS | base_target_distance.mission_id -> missions.mission_id |  |
| PASS | every mission type has capable aircraft types |  |
| PASS | weapons named in missions exist |  |
| PASS | distance table covers every mission x base | 80 rows, expected 80 |
| PASS | distances match coordinates (50 sampled) | max diff 0.05 km |
| PASS | events 'aircraft_unserviceable' point to real tail_id |  |
| PASS | events 'crew_unavailable' point to real crew_id |  |
| PASS | events 'runway_closed' point to real ident |  |
| PASS | new-target events use valid mission types |  |

## Events

| Result | Check | Detail |
|---|---|---|
| PASS | new targets and intel alerts have coordinates |  |
| PASS | events fall inside the forecast window |  |

## Values

| Result | Check | Detail |
|---|---|---|
| PASS | base latitude within India box |  |
| PASS | base longitude within India box |  |
| PASS | runway length 3000 to 16000 ft |  |
| PASS | aircraft status values valid |  |
| PASS | health_index 0 to 1 |  |
| PASS | risk_fail_next_24h 0 to 1 |  |
| PASS | available_from empty only for serviceable aircraft |  |
| PASS | at least 1 serviceable aircraft | 50 serviceable of 64 |
| PASS | crew status values valid |  |
| PASS | crew hours last 24h 0 to 24 |  |
| PASS | 7-day hours >= 24-hour hours |  |
| PASS | weapon stock never negative |  |
| PASS | fuel stock positive |  |
| PASS | mission priority 1 to 5 |  |
| PASS | aircraft_required 1 to 12 |  |
| PASS | mission duration 0.5 to 12 h |  |
| PASS | latest_start is not before earliest_start |  |
| PASS | mission target coordinates present |  |
| PASS | aircraft performance numbers positive |  |

## Weather

| Result | Check | Detail |
|---|---|---|
| PASS | no gaps: same hours for every base | 37 bases, 72 hours each |
| PASS | values plausible (visibility>=0, wind>=0) |  |
| PASS | weather exists for every scenario base |  |
| PASS | forecast covers all mission times | forecast ends 2026-10-10 23:00:00, last mission starts 2026-10-10 15:15:00 |

## Feasibility

| Result | Check | Detail |
|---|---|---|
| PASS | every mission has capable serviceable aircraft in range |  |
| PASS | enough capable aircraft in range for each mission |  |
| INFO | missions flyable from a single base (best case) | 19 of 20 |

## Scarcity

| Result | Check | Detail |
|---|---|---|
| INFO | aircraft demanded vs serviceable | 54 aircraft-slots needed in total vs 50 serviceable (turnaround lets aircraft fly more than once) |
| PASS | weapon stock covers total demand: Anti-Radiation-Missile | demand 12 vs stock 168 |
| PASS | weapon stock covers total demand: BVR-AAM | demand 64 vs stock 450 |
| PASS | weapon stock covers total demand: PGM-1000lb | demand 88 vs stock 493 |
| PASS | weapon stock covers total demand: Recon-pod | demand 5 vs stock 18 |
| PASS | weapon stock covers total demand: Unguided-500lb | demand 24 vs stock 1046 |
| PASS | weapon stock covers total demand: WVR-AAM | demand 78 vs stock 571 |
