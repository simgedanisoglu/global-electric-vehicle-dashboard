"""Project-wide paths for local data access."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ANALYSIS_DATA_DIR = DATA_DIR / "analysisdataset"
MODEL_DATA_DIR = DATA_DIR / "modeldataset"