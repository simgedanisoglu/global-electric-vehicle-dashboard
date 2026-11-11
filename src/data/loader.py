"""Central place for data-loading helpers."""
from pathlib import Path
import pandas as pd


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV; use paths from src.config when possible."""
    return pd.read_csv(path)


def load_excel(path: str | Path, **kwargs) -> pd.DataFrame:
    """Load an Excel sheet; pass sheet_name via keyword arguments."""
    return pd.read_excel(path, **kwargs)