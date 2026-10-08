"""Shared helpers: project folders + a requests session with retries.
The project root is found automatically (the folder that contains requirements.txt),
so these scripts work from any folder depth."""
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _find_root() -> Path:
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "requirements.txt").exists():
            return p
    raise RuntimeError("Project root not found (no requirements.txt above this file).")


ROOT = _find_root()
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
SYN = ROOT / "data" / "synthetic"
for _d in (RAW, PROC, SYN):
    _d.mkdir(parents=True, exist_ok=True)


def session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=5, backoff_factor=1.5,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET", "POST"])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = "airpower-hackathon-research/1.0"
    return s
