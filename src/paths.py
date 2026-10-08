"""Single place for project folders. Use this in Phase 2 onward.

At the top of any script in src/ml, src/optimiser or src/dashboard:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from paths import FROZEN, OUTPUTS, MODELS, DOCS

Read inputs ONLY from FROZEN. Write results ONLY to OUTPUTS or MODELS.
"""
from pathlib import Path


def _find_root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "requirements.txt").exists():
            return p
    raise RuntimeError("Project root not found.")


ROOT = _find_root()
DATA = ROOT / "data"
FROZEN = DATA / "frozen_v1"      # read-only, never edit
OUTPUTS = DATA / "outputs"       # results of ML / optimiser (see file contracts)
MODELS = ROOT / "models"
DOCS = ROOT / "docs"
OUTPUTS.mkdir(parents=True, exist_ok=True)
MODELS.mkdir(parents=True, exist_ok=True)
