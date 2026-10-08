# Air Power: Dynamic Air Operations and Resource Optimisation

AI-enabled decision support for planning and re-planning air operations (MoD / DSSC, PS 26250).
Real open data + synthetic data -> ML predictions -> optimiser -> re-planner -> dashboard.

> All fleet, crew, weapon, mission and threat data is **synthetic**. This project contains no real operational data.

## Where to start
1. Read `docs/MASTER_PLAN.md` (the order of work) and `docs/TEAM_GUIDE.md` (setup and Git).
2. Check the Status table below to see which phase is current.

## Status
| Phase | What | State |
|---|---|---|
| 0 | Setup | in progress (repo, roles) |
| 1 | Data (collect, document, validate, freeze) | **DONE** (validation PASS, data frozen as `frozen_v1`) |
| 2 | ML models | next |
| 3-5 | Optimiser, re-planner, KPIs | not started |
| 6 | Dashboard | not started |
| 7-10 | Integration, docs, submission | not started |

## Quick start (Windows PowerShell)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest                      # must pass: frozen data is intact
```

## Folder map
```
data/frozen_v1/   FINAL input data. Read-only. Everyone reads from here.
data/outputs/     Results of ML / optimiser (see file contracts in the master plan)
data/raw|processed|synthetic/   Rebuildable; not in Git
src/data_pipeline/ Phase 1 scripts (01-11)
src/ml/  src/optimiser/  src/dashboard/   Phases 2 to 6
src/paths.py      Project folders for Phase 2+ code
models/           Saved ML models
docs/             Plan, guides, data dictionary, validation report
tests/            Automatic checks
notebooks/        Exploration only (not part of the final product)
```
