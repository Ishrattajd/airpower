"""
Phase 1.11: freeze the data so the whole team works on identical files.

Copies the files the project uses into data/frozen_v1/ and writes
MANIFEST.json (file sizes + SHA-256 fingerprints). Refuses to run if
validation did not PASS (use --force only if you know why).

Usage:
  python 11_freeze_data.py            # create the frozen copy (once)
  python 11_freeze_data.py --verify   # later: confirm nothing was changed
"""
import argparse, hashlib, json, shutil, sys
from datetime import datetime, timezone
from common import ROOT, RAW, PROC, SYN

FROZEN = ROOT / "data" / "frozen_v1"
INCLUDE = {  # source folder -> files to freeze
    "synthetic": (SYN, None),  # all CSV + ASSUMPTIONS.txt
    "processed": (PROC, ["bases.csv"]),
    "raw": (RAW, ["weather_forecast.csv", "conflict_events.csv", "opensky_states.csv",
                  "airports_india.csv", "runways_india.csv"]),
}


def sha(p):
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def verify():
    mf = FROZEN / "MANIFEST.json"
    if not mf.exists():
        sys.exit("No frozen copy found. Run without --verify first.")
    m = json.loads(mf.read_text())
    bad = [r for r, v in m["files"].items() if not (FROZEN / r).exists() or sha(FROZEN / r) != v["sha256"]]
    if bad:
        sys.exit(f"FROZEN DATA HAS CHANGED: {bad}")
    print(f"OK: all {len(m['files'])} frozen files match the manifest (frozen {m['frozen_at_utc']}).")


def main(a):
    if a.verify:
        return verify()
    rep = ROOT / "docs" / "validation_report.md"
    if not a.force:
        if not rep.exists() or "RESULT: PASS" not in rep.read_text(encoding="utf-8"):
            sys.exit("Validation has not passed. Run 09_validate_data.py and fix FAILs first "
                     "(or use --force).")
    if (FROZEN / "MANIFEST.json").exists():
        sys.exit(f"{FROZEN} already exists. Frozen data must not be overwritten. "
                 "Delete the folder by hand only if the whole team agrees.")
    files = {}
    for sub, (src, names) in INCLUDE.items():
        (FROZEN / sub).mkdir(parents=True, exist_ok=True)
        todo = names or sorted(p.name for p in src.iterdir() if p.suffix in (".csv", ".txt"))
        for n in todo:
            if not (src / n).exists():
                print(f"  skipped (not found): {sub}/{n}")
                continue
            shutil.copy2(src / n, FROZEN / sub / n)
            files[f"{sub}/{n}"] = {"bytes": (FROZEN / sub / n).stat().st_size, "sha256": sha(FROZEN / sub / n)}
    cm = PROC / "cmapss"
    if cm.exists():
        (FROZEN / "cmapss").mkdir(exist_ok=True)
        for p in sorted(cm.glob("*.csv")):
            shutil.copy2(p, FROZEN / "cmapss" / p.name)
            files[f"cmapss/{p.name}"] = {"bytes": p.stat().st_size, "sha256": sha(p)}
    (FROZEN / "MANIFEST.json").write_text(json.dumps(
        {"frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "files": files}, indent=2))
    print(f"Froze {len(files)} files -> {FROZEN}")
    print("Next: commit data/frozen_v1 to GitHub. From now on every phase reads from it.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    p.add_argument("--force", action="store_true")
    main(p.parse_args())
