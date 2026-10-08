"""Fails if anyone changed a frozen file. Run: pytest"""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_matches_manifest():
    mf = ROOT / "data" / "frozen_v1" / "MANIFEST.json"
    assert mf.exists(), "data/frozen_v1/MANIFEST.json is missing"
    files = json.loads(mf.read_text())["files"]
    assert files, "manifest is empty"
    for rel, info in files.items():
        data = (mf.parent / rel).read_bytes()
        assert hashlib.sha256(data).hexdigest() == info["sha256"], f"CHANGED: {rel}"
