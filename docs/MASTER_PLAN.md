# Air Power Project: Master Plan

**Problem:** AI-enabled decision support for dynamic air operations and resource optimisation (MoD / DSSC, PS 26250).
**One-line goal:** Given aircraft, crews, weapons, weather and threats, recommend the best mission plan in minutes, and re-plan when something changes.

**How to use this plan**
1. Work top to bottom. Do not start a phase until the previous phase's **Gate** is passed.
2. Tick boxes as you go. `[x]` means already done.
3. Frozen decisions (Phase 0) are not reopened. If something must change, the team lead decides once and updates this file.
4. Times are rough guides for a team of 4 to 6. Scale to your deadline.

---

## The big picture (read once)

```
REAL DATA + SYNTHETIC DATA  ->  ML MODELS (predict)  ->  OPTIMISER (decide)
        ->  RE-PLANNER (react)  ->  DASHBOARD (show)  ->  DEMO + SUBMISSION
```

| Part | Question it answers | Tool |
|---|---|---|
| Data | What do we know right now? | Python, pandas, CSV |
| ML | What is likely to happen? (jet failure, bad weather, risk) | scikit-learn / XGBoost |
| Optimiser | Who should fly what, when, with which weapons? | Google OR-Tools (CP-SAT) |
| Re-planner | A surprise happened; what is the new best plan? | Same optimiser + event rules |
| Dashboard | How does the commander see and approve it? | Streamlit + map |

**Honesty rule for every slide and answer:** real data = bases, runways, weather, air traffic, past conflict events, engine failure data. Synthetic = fleet, crews, weapons, missions, threats. Nothing here is real IAF operational data.

---

## Phase 0: Team setup and frozen decisions (about 0.5 day)

**Roles (one owner each; everyone helps testing)**

| Role | Owns |
|---|---|
| Team lead / integrator | This plan, merging code, final demo |
| Data engineer | Phases 1 and data validation |
| ML engineer | Phase 2 |
| Optimisation engineer | Phases 3, 4 and 5 |
| Dashboard engineer | Phase 6 |
| Documentation / presentation lead | Phases 8 and 9 |

**Tasks**
- [ ] Everyone installs Python 3.11 or newer, VS Code, Git
- [ ] Create one private GitHub repo; push the current `airpower_data` folder as the start
- [ ] Agree the folder layout:
  ```
  airpower/
    data/raw/  data/processed/  data/synthetic/  data/outputs/
    src/data/  src/ml/  src/optimiser/  src/dashboard/
    models/    docs/    tests/
    README.md  requirements.txt
  ```
- [ ] Agree that all code reads/writes CSV files named in this plan (the "contracts" below)
- [ ] Set a backup rule: push to GitHub at the end of every work session

**Frozen decisions**
- Demo scenario: **4 bases, about 64 aircraft, about 111 crew, 20 missions, 72 hours** (already generated)
- Seed `42` for the main demo data. Never change it after Phase 1 (data is frozen in `data/frozen_v1/`)
- Language and tools: Python, pandas, scikit-learn/XGBoost, OR-Tools, Streamlit, Plotly/Folium
- Planning time step: 30 minutes
- Human always approves the final plan (AI recommends only)

**Gate 0:** every member can run `python 07_synthetic.py` on their own laptop and get the same files.

---

## Phase 1: Data foundation (mostly done)

- [x] 1.1 Airports, runways, navaids, frequencies (OurAirports)
- [x] 1.2 Weather forecast for 37 bases (Open-Meteo)
- [x] 1.3 Air traffic snapshots (OpenSky)
- [x] 1.4 Conflict events 2018-2024 (UCDP, ACLED was blocked)
- [x] 1.5 Curated 37 air bases (`06_make_bases.py`)
- [x] 1.6 Synthetic fleet, crew, weapons, missions, threats, events (`07_synthetic.py`)
- [x] 1.7 **Data dictionary** (`08_data_dictionary.py` -> `docs/data_dictionary.md`)
- [ ] 1.8 **Validation** (`09_validate_data.py` -> `docs/validation_report.md`): must say RESULT: PASS. Fix every FAIL; read every WARN
- [ ] 1.9 Download **NASA C-MAPSS** (`10_download_cmapss.py`) into `data/raw/cmapss/`
- [ ] 1.10 Optional: OpenAIP airspace (no-fly zones) if time allows. Skip if not
- [ ] 1.11 Freeze the data (`11_freeze_data.py` -> `data/frozen_v1/`); check any time with `--verify`; never regenerate it

**Gate 1:** validation says PASS, data dictionary exists, C-MAPSS is downloaded, `data/frozen_v1/` is on GitHub and `--verify` passes.

*Fixes found by validation (already applied in the generator):* demo bases are now the 4 nearest to the exercise zone (not random), the C-130J crew need is 2 seats, and the fleet always includes a type that can fly every mission type. After pulling these changes, re-run `python 07_synthetic.py --max-bases 4 --missions 20` before validating.

---

## Phase 2: ML models (about 3 days)

Goal: replace the random columns (`health_index`, `rul_est_hours`) with real predictions.

**2A. Aircraft failure prediction (main ML model)**
- [ ] 2.1 Explore C-MAPSS: sensors, engines, cycles. Plot a few engines
- [ ] 2.2 Create the target: Remaining Useful Life (RUL) for each row
- [ ] 2.3 Split **by engine**, not by row (train / validation / test)
- [ ] 2.4 Baseline: a simple model (linear or mean) so you can show improvement
- [ ] 2.5 Main model: XGBoost or Random Forest on rolling-window sensor features
- [ ] 2.6 Evaluate: RMSE and MAE on test engines; plot predicted vs actual RUL
- [ ] 2.7 Save the model to `models/rul_model.pkl`
- [ ] 2.8 Link to our fleet: for each synthetic aircraft, assign a C-MAPSS engine at a random life stage as its sensor history; run the model; save `rul_pred_hours`
- [ ] 2.9 Convert RUL into `risk_fail_next_24h` (probability a jet fails within 24 h)
- [ ] 2.10 Output: `data/outputs/aircraft_risk.csv` (tail_id, rul_pred_hours, risk_fail_next_24h)

*Say clearly in the submission: C-MAPSS is a civil engine simulation used as a stand-in for military engine health data.*

**2B. Weather flyability**
- [ ] 2.11 Define flying limits (assumed, adjustable): visibility, gusts, thunderstorm code, cloud
- [ ] 2.12 Rule-based check on the forecast: `flyable = yes/no` per base per hour
- [ ] 2.13 Stretch: download 1 year of past weather, train a simple classifier to predict bad weather 6 h ahead; compare with the rule-based version
- [ ] 2.14 Output: `data/outputs/weather_flyability.csv` (base_ident, time, flyable, reason)

**2C. Mission risk score**
- [ ] 2.15 Build a **transparent formula** (not a trained model): threats covering the target, distance vs aircraft range, weather, priority
- [ ] 2.16 Output: `data/outputs/mission_risk.csv` (mission_id, risk_score 0 to 1, reasons)
- [ ] 2.17 Label it "rule-based risk score" everywhere; do not call it learned

**2D. Wrap up**
- [ ] 2.18 One script `python src/ml/run_all_ml.py` regenerates all three output files
- [ ] 2.19 Short notebook or doc with the charts for the slides

**Gate 2:** the three output CSVs exist, RUL model beats the baseline, one command regenerates them.

---

## Phase 3: Optimiser, the core (about 4 days)

**3A. Write the rules first (no code)**
- [ ] 3.1 List every rule in plain words in `docs/rules.md`:
  - aircraft must be serviceable at mission time
  - aircraft type must be allowed for that mission type (`mission_capability.csv`)
  - target must be within the aircraft's combat radius from the launch base
  - runway long enough for the type; runway not closed; weather flyable at launch base
  - one aircraft cannot fly two missions at once; respect turnaround time
  - crew: fit, qualified for the type and mission, night-qualified if needed, within duty hours and rest limits
  - weapons: compatible with the aircraft, within payload, within base stock
  - mission needs N aircraft; either fully served or not served
- [ ] 3.2 Team lead signs off the rules list

**3B. Build in three versions (do not skip ahead)**
- [ ] 3.3 **V1:** missions start at their earliest time. Assign aircraft only. Rules: capability, range, runway, serviceable, no double booking
- [ ] 3.4 **V2:** add crews and weapons (stock, compatibility, payload)
- [ ] 3.5 **V3:** add start-time choice inside the time window, turnaround, weather, runway closures, risk penalty
- [ ] 3.6 Objective (V3): maximise priority-weighted missions served, minus risk, minus unnecessary resource use
- [ ] 3.7 Use OR-Tools CP-SAT. Set a time limit (about 30 seconds) and save the best plan found

**3C. Baseline for comparison**
- [ ] 3.8 Build a simple "manual-style" planner (first-come, first-served by priority) so we can prove the optimiser is better

**3D. Output and tests**
- [ ] 3.9 Output: `data/outputs/plan.csv` (mission_id, aircraft tail_id, crew_id, launch_base, start_time, weapons, status)
- [ ] 3.10 Output: `data/outputs/unserved.csv` (mission_id, reason)
- [ ] 3.11 Write tests: a plan never breaks any rule (automatic rule checker)
- [ ] 3.12 Run V3 on the demo scenario 5 times; results should be stable

**Gate 3:** plan passes the rule checker, beats the baseline on priority-weighted missions served, runs in under 60 seconds.

---

## Phase 4: Re-planner (about 3 days)

- [ ] 4.1 Write the event handler for each event type in `disruption_events.csv`:
  aircraft_unserviceable, crew_unavailable, runway_closed, weather_below_minima, new_priority_target, intel_alert
- [ ] 4.2 Define the "locked" rule: missions already airborne or starting within 1 hour cannot be changed
- [ ] 4.3 Update the state (remove aircraft/crew/runway, add new mission) and re-run the optimiser
- [ ] 4.4 Add a **stability penalty** so the new plan changes as little as possible
- [ ] 4.5 Produce **3 options** by changing the objective: Max mission success / Min risk / Min changes
- [ ] 4.6 For each option calculate: missions served, priority score, risk, number of changes
- [ ] 4.7 Produce a "what changed" list: which missions moved, dropped or were added and why
- [ ] 4.8 Output: `data/outputs/replan_<event_id>.csv` and `replan_<event_id>_options.csv`
- [ ] 4.9 Replay test: run all 31 events in order and check nothing crashes

**Gate 4:** one command replays events and gives 3 options with a change list in under 30 seconds each.

---

## Phase 5: Explainability and KPIs (about 1.5 days)

- [ ] 5.1 Reason codes for every unserved mission (no capable aircraft in range, no crew, no weapons, weather...)
- [ ] 5.2 Plain-language "why this aircraft/crew was chosen" for each assignment
- [ ] 5.3 KPI table: planning time (baseline vs ours), priority-weighted missions served, aircraft utilisation, resource waste, risk, number of changes after disruption
- [ ] 5.4 Run baseline vs optimiser on 5 different seeds and report the average
- [ ] 5.5 What-if function: "what if 2 jets fewer / one runway closed?" shows the effect on KPIs

**Gate 5:** a KPI table with real numbers exists for the slides.

---

## Phase 6: Dashboard (about 4 days)

Build in this order. Each page works before the next starts.
- [ ] 6.1 App skeleton in Streamlit; loads the CSVs; sidebar navigation
- [ ] 6.2 **Overview:** map with bases, targets, threat circles, live status counts
- [ ] 6.3 **Resources:** tables for aircraft, crew, weapons with filters; colour by status and risk
- [ ] 6.4 **Plan:** mission timeline chart (Gantt) and plan table; click a mission to see why
- [ ] 6.5 **Events:** event list; "Trigger event" button that runs the re-planner
- [ ] 6.6 **Compare options:** the 3 revised plans side by side with trade-offs
- [ ] 6.7 **Approve:** commander picks an option; the plan updates and is saved
- [ ] 6.8 **Export:** download the plan as CSV (and a simple ATO-style PDF if time allows)
- [ ] 6.9 **What-if** page from 5.5
- [ ] 6.10 Basic polish: titles, colours, labels, "SYNTHETIC DATA" banner

**Gate 6:** a person who has never seen the project can run the whole flow without help.

---

## Phase 7: Integration and testing (about 2 days)

- [ ] 7.1 Single entry point: `python run_demo.py` rebuilds outputs from frozen data
- [ ] 7.2 Test on a clean laptop from scratch: clone repo, install, run
- [ ] 7.3 Write the **demo script** (exact clicks and words, see Phase 9)
- [ ] 7.4 Test edge cases: no serviceable aircraft, duplicate events, two events at once
- [ ] 7.5 Check speed: every click responds within a few seconds (optimiser limited to 30 s)
- [ ] 7.6 Freeze code: tag the GitHub release `v1.0-demo`

**Gate 7:** the demo works three times in a row on two different laptops.

---

## Phase 8: Documentation (about 2 days, can start during Phase 6)

- [ ] 8.1 README: what it is, how to install, how to run, folder map
- [ ] 8.2 Architecture diagram (data -> ML -> optimiser -> re-planner -> dashboard)
- [ ] 8.3 Data sheet: every source, real vs synthetic, licences
- [ ] 8.4 Assumptions and limitations list (see below)
- [ ] 8.5 Security and deployment note: runs fully offline, air-gapped, role-based access, audit log, no external calls at runtime
- [ ] 8.6 Future scope: real data connectors, more aircraft types, reinforcement learning, airspace deconfliction

---

## Phase 9: Submission and demo (about 3 days)

- [ ] 9.1 Slides in this order: Problem -> Users -> Solution idea -> Architecture -> Data (real vs synthetic) -> ML -> Optimiser -> Live re-plan -> Results (KPIs) -> Security and deployment -> Limitations and next steps
- [ ] 9.2 Record the demo video (about 3 minutes), following the demo script
- [ ] 9.3 Demo script (one story):
  1. Show the 12-hour plan (Overview + Plan)
  2. Trigger "aircraft unserviceable"
  3. Show the 3 new options and their trade-offs
  4. Approve one; show what changed
  5. Show KPIs: minutes instead of hours
- [ ] 9.4 Prepare answers to likely judge questions (below)
- [ ] 9.5 Two full rehearsals with timing
- [ ] 9.6 Final upload checklist: slides, video, repo link, README, any forms required by the organisers

---

## Phase 10: Final freeze

- [ ] 10.1 No new features 48 hours before the deadline; only bug fixes
- [ ] 10.2 Final backup: GitHub plus a copy on a USB drive
- [ ] 10.3 Everyone knows their talking part
- [ ] 10.4 Submit early, not at the last minute

---

## File contracts (never rename without telling everyone)

| File | Made by | Used by |
|---|---|---|
| `data/frozen_v1/` (synthetic, processed, raw, cmapss) | Phase 1 | everyone |
| `outputs/aircraft_risk.csv` | Phase 2 | optimiser, dashboard |
| `outputs/weather_flyability.csv` | Phase 2 | optimiser, dashboard |
| `outputs/mission_risk.csv` | Phase 2 | optimiser, dashboard |
| `outputs/plan.csv`, `unserved.csv` | Phase 3 | re-planner, dashboard |
| `outputs/replan_<event>.csv` and `_options.csv` | Phase 4 | dashboard |

## Likely judge questions

- *Is the data real?* Part of it. Bases, runways, weather, air traffic, conflict events and engine failure data are real open data. Fleet, crew, weapons, missions and threats are synthetic because real data is classified.
- *Why trust the AI?* The human approves. Every choice has a reason. Rule checker proves no plan breaks a rule.
- *What did you train?* A remaining-life model on NASA engine data. The risk score is rule-based and labelled as such.
- *Will it work with real systems?* The input files are simple tables, so real systems can feed the same format.
- *What about security?* Offline, air-gapped, role-based access, audit log.

## Known limitations (say them before you are asked)

- Aircraft figures are rough public approximations; duty limits and flying limits are assumed values
- C-MAPSS is a civil engine simulation used as a stand-in
- Conflict events are historical and replayed, not live
- Targets and threats sit in a notional exercise zone, not at real sites
- Small demo scenario (4 bases); the method scales, the demo does not claim full-force scale

## Effort summary

| Phase | Days | Owner |
|---|---|---|
| 0 Setup | 0.5 | Lead |
| 1 Data | 1 | Data |
| 2 ML | 3 | ML |
| 3 Optimiser | 4 | Optimisation |
| 4 Re-planner | 3 | Optimisation |
| 5 Explain + KPIs | 1.5 | Optimisation |
| 6 Dashboard | 4 | Dashboard |
| 7 Integration | 2 | Lead |
| 8 Documentation | 2 | Docs |
| 9 Submission | 3 | Docs + all |
| 10 Freeze | 1 | All |

Phases 2 and 3 can run in parallel (ML engineer and optimisation engineer), and Phase 8 can start during Phase 6. Everything else follows in order.
