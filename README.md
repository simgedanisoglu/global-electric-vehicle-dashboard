# Global Electric Vehicle Dashboard

A collaborative Streamlit dashboard for exploring global electric vehicle data.

## Project structure

- `app.py`: shared Streamlit entry point (pre-existing).
- `data/`: source, analysis and future model datasets (pre-existing).
- `pages/`: dataset explorer and research insights pages.
- `src/charts/`: one Python module per visualization.
- `src/data/`: data loading, checks and reusable calculations.
- `src/ui/`: shared presentation helpers.
- `assets/`: static assets.
- `tests/`: tests.

## Setup

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

## Collaboration

Work on individual chart modules in `simge`, `halil`, and `rabia` branches.
Merge reviewed changes to `main`. Coordinate edits to `app.py` and `pages/`
to avoid conflicts. Chart modules start as placeholders; actual chart code must be
implemented and connected to Streamlit pages.