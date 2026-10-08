# Rebuild all Phase 1 data from scratch (only needed if data/raw etc. are missing).
# Run from the project root:  powershell -ExecutionPolicy Bypass -File scripts/run_phase1.ps1
$ErrorActionPreference = "Stop"
$d = "src/data_pipeline"
python $d/01_ourairports.py
python $d/06_make_bases.py
python $d/02_openmeteo.py --mode forecast --days 3 --use-bases --limit 60
python $d/03_opensky.py --snapshots 3 --interval 30
python $d/05_ucdp.py --countries "India,Pakistan,China" --start 2018-01-01 --end 2024-12-31
python $d/07_synthetic.py --max-bases 4 --missions 20
python $d/10_download_cmapss.py
python $d/08_data_dictionary.py
python $d/09_validate_data.py
Write-Host "Phase 1 rebuilt. Do NOT run 11_freeze_data.py again: data/frozen_v1 already exists."
