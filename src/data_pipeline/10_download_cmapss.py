"""
Phase 1.9: get NASA C-MAPSS turbofan engine degradation data (for the ML model).

Tries to download automatically. If that fails (links change), do it by hand:
  Option A: NASA Prognostics Data Repository -> "Turbofan Engine Degradation
            Simulation Data Set" (search for it on nasa.gov, PCoE data repository)
  Option B: Kaggle "NASA C-MAPSS" (needs a free Kaggle account)
Put the .txt files (train_FD001.txt, test_FD001.txt, RUL_FD001.txt, and the
FD002-FD004 ones) or the .zip inside data/raw/cmapss/ and run this script again.

Output: data/raw/cmapss/*.txt (original) and
        data/processed/cmapss/*.csv (same data with column names added)
"""
import io, shutil, sys, zipfile
from pathlib import Path
import pandas as pd
from common import RAW, PROC, session

DEST = RAW / "cmapss"
OUT = PROC / "cmapss"
URLS = [  # tried in order; links may change over time
    "https://phm-datasets.s3.amazonaws.com/NASA/6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip",
    "https://data.nasa.gov/docs/legacy/CMAPSSData.zip",
]
COLS = ["unit", "cycle", "op1", "op2", "op3"] + [f"s{i}" for i in range(1, 22)]
SETS = ["FD001", "FD002", "FD003", "FD004"]


def extract_all(zf: zipfile.ZipFile, dest: Path):
    """Extract a zip; open nested zips too."""
    for name in zf.namelist():
        if name.endswith("/"):
            continue
        data = zf.read(name)
        if name.lower().endswith(".zip"):
            extract_all(zipfile.ZipFile(io.BytesIO(data)), dest)
        elif name.lower().endswith(".txt"):
            (dest / Path(name).name).write_bytes(data)


def download():
    s = session()
    for url in URLS:
        try:
            print(f"Trying {url} ...")
            r = s.get(url, timeout=300)
            if r.status_code == 200 and r.content[:2] == b"PK":
                print(f"Downloaded {len(r.content) / 1e6:.1f} MB")
                extract_all(zipfile.ZipFile(io.BytesIO(r.content)), DEST)
                return True
            print(f"  not available (HTTP {r.status_code})")
        except Exception as e:
            print(f"  failed: {e}")
    return False


def have_files():
    return all((DEST / f"train_{x}.txt").exists() for x in SETS)


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for z in DEST.glob("*.zip"):  # manually placed zip
        extract_all(zipfile.ZipFile(z), DEST)
    if not have_files():
        print("C-MAPSS files not found locally. Trying to download...")
        if not download() or not have_files():
            sys.exit("\nAutomatic download failed. Follow the manual steps at the top of this file,\n"
                     f"put the files in {DEST} and run again.")
    print(f"Found raw files in {DEST}")

    summary = []
    for x in SETS:
        for kind in ("train", "test"):
            df = pd.read_csv(DEST / f"{kind}_{x}.txt", sep=r"\s+", header=None)
            if df.shape[1] != 26:
                sys.exit(f"{kind}_{x}.txt has {df.shape[1]} columns, expected 26. File may be damaged.")
            df.columns = COLS
            df.to_csv(OUT / f"{kind}_{x}.csv", index=False)
            summary.append((x, kind, len(df), df.unit.nunique(), int(df.groupby("unit").cycle.max().max())))
        rul = pd.read_csv(DEST / f"RUL_{x}.txt", header=None, names=["rul_at_last_cycle"])
        rul.insert(0, "unit", range(1, len(rul) + 1))
        rul.to_csv(OUT / f"RUL_{x}.csv", index=False)
    print("\nset    kind   rows   engines  longest_run(cycles)")
    for x, k, n, u, c in summary:
        print(f"{x}  {k:5s} {n:7,d} {u:7d} {c:10d}")
    f1 = [r for r in summary if r[0] == "FD001" and r[1] == "train"][0]
    if (f1[2], f1[3]) != (20631, 100):
        print(f"\nNOTE: FD001 train has {f1[2]} rows / {f1[3]} engines; the published description "
              "lists 20,631 rows / 100 engines. Check the file is the original.")
    print(f"\nSaved labelled CSVs to {OUT}")


if __name__ == "__main__":
    main()
