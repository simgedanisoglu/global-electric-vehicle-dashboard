# Global Electric Vehicle Dashboard

**CEN445 – Introduction to Data Visualization**

| | |
|---|---|
| **Live dashboard** | https://global-electric-vehicle-dashboard-7dktbb3dxpiah6gcc3erqo.streamlit.app/ |
| **ML Insights page** | https://global-electric-vehicle-dashboard-7dktbb3dxpiah6gcc3erqo.streamlit.app/ML_Insights |
| **GitHub repository** | https://github.com/simgedanisoglu/global-electric-vehicle-dashboard |

## Project Overview

This project is an interactive Streamlit dashboard that uses the IEA *Global EV Outlook 2026* data to study
the transition to electric vehicles (EVs). It addresses differences between countries, public charging
infrastructure, vehicle prices, energy impacts, and 2035 scenario projections. Nine visualization methods
form the core of the dashboard; two additional machine learning analyses (K-Means clustering and
next-year regression) are presented on a separate page.

| Page | Content |
|---|---|
| Dataset Explorer | Sunburst view of how the dataset is organized |
| Research & Insights | Eight visualizations in five tabs: Market & Adoption, Charging, Prices, Energy & Impact, Future 2035 |
| ML Insights | K-Means clustering and regression error analysis |

## Dataset Description

- **Source:** International Energy Agency (IEA), *Global EV Outlook 2026* – https://www.iea.org/reports/global-ev-outlook-2026. The `Notes` sheet of the Excel file gives the citation and identifies this as the second version, updated 26 May 2026.
- **Raw file:** `data/EV data by country 2026.xlsx` (sheet `GEVO_EV_2026`, 49,375 rows × 9 columns, plus documentation sheets such as `Notes` and `Definitions`)
- **Cleaned file:** `data/analysisdataset/global_ev_cleaned.csv` (48,277 rows × 9 columns, no missing values)
- **Scenario file:** `data/analysisdataset/ev_2035_scenario_comparison.csv` (620 rows × 10 columns; matched STEPS/CPS pairs in 2035). The CSV `difference` column stores the absolute STEPS − CPS difference, whereas the heatmap calculates a relative percentage.
- **ML files:** `data/modeldataset/clustering/` and `data/modeldataset/regression/` (feature sets, results, notebooks, saved models)

### Variables (cleaned file)

| Column | Type | Description |
|---|---|---|
| `region_country` | string | Country, region or World (72 distinct values) |
| `category` | string | `Historical`, `Projection-STEPS` or `Projection-CPS` |
| `parameter` | string | 19 indicators, e.g. EV sales, EV sales share, EV stock, EV charging points, electricity demand, price percentiles |
| `mode` | string | 13 values, e.g. Cars, Buses, Trucks, Vans, 2 and 3 wheelers, EVSE, price segments |
| `powertrain` | string | 10 values, e.g. BEV, PHEV, EV, ICEV, FCEV, public charger types |
| `year` | integer | 2010–2035 |
| `unit` | string | 10 unit spellings, e.g. Vehicles, percent, GWh, charging points, 2025 USD |
| `value` | float | Observation |
| `Aggregate group` | string | Geography grouping (e.g. `Other`, `_World`, `European Union`, `Projection_country`) |

**Historical vs. projection data.** `Historical` rows cover 2010–2025 (47,016 rows). `Projection-STEPS`
(640 rows) and `Projection-CPS` (621 rows) exist only for 2035; they are scenario outcomes, not observations.
The scenario comparison file contains 620 matched STEPS/CPS pairs; 21 unmatched projection records are not part of those paired comparisons.

## Data Preprocessing

Data exploration and cleaning are documented in `data/DataVisulationProject.ipynb`. The cleaning decisions below reproduce the cleaned file exactly (verified against the raw Excel sheet): **49,375 − 1,078 − 15 − 5 = 48,277 rows**.

| Step | Finding and treatment |
|---|---|
| Missing geography | 1,078 rows have no `region_country`; all are price records (7 price statistics × 154 rows). They cannot be assigned to a country and were removed. |
| Duplicate records | 15 fully duplicated rows were removed (first occurrence kept). After cleaning, no measurement key (`region_country`, `category`, `parameter`, `mode`, `powertrain`, `year`) is repeated and no conflicting values or units remain. |
| Missing units | 22,582 price records have no unit in the raw file; the unit was set to `2025 USD`, which the parameter names state. |
| Invalid shares | Five *United Arab Emirates / Vans / EV sales share* records (2021–2025; 200%, 280%, 310%, 290%, 210%) exceed the 0–100% range of a share and were removed. The 2020 value (5.6%) was kept. |
| Unit spellings | Original spellings are retained (e.g. lowercase `vehicles` for *Electric LDVs per charging point*); every parameter has exactly one unit, so analyses use `parameter` together with `unit`. |
| Value checks | The cleaned file has no negative or zero values and no percentage above 100. A small number of non-integer count values (18 records, e.g. 0.001 buses) were inspected and kept. |
| Missing combinations | Missing country–year–indicator combinations are not imputed as zero; each chart filters to comparable available records. |
| Aggregates | World, regional and EU rows are retained but are never added to country values and are excluded from country rankings. |

### Outlier Detection

Statistical outliers were **detected and documented, not removed**. The notebook section *Outlier Detection & Analysis* applies Tukey's IQR rule (outside Q1 − 1.5·IQR … Q3 + 1.5·IQR) separately within comparable groups defined by `category × parameter × mode × powertrain × unit × year`, using country-level rows only. Price statistics, percentages, vehicle counts and other indicators are therefore never pooled. A group must contain at least 8 countries and a non-zero IQR to be evaluated. The analysis is read-only and does not change any dataset.

| Result | Value |
|---|---|
| Country-level rows compared (aggregates excluded) | 40,477 |
| Comparable groups / evaluated groups | 3,170 / 2,189 |
| Rows in evaluated groups | 36,722 |
| Rows flagged as IQR outliers | **3,235 (8.8%)** |

| Indicator family | Flagged / evaluated rows | Share |
|---|---|---|
| Vehicle counts (sales, stock, charging points) | 1,558 / 11,231 | 13.9% |
| Ratios (EVs per charging point) | 40 / 444 | 9.0% |
| Percentages (sales and stock shares) | 339 / 3,921 | 8.6% |
| Power capacity | 60 / 889 | 6.7% |
| Prices (2025 USD, each statistic evaluated separately) | 1,238 / 20,237 | 6.1% |

**Scope.** The four energy indicators and all 2035 projection rows have no group with at least 8 countries and were not evaluated, so the results describe historical indicators only.

**Interpretation and decisions.**
- Most flags in count indicators reflect strongly right-skewed distributions: large markets such as China are legitimately far larger than most countries. Statistically extreme values are therefore not deleted automatically.
- A record is removed only when it is *invalid by definition* (missing country, exact duplicate, share above 100%).
- The 5,000,000 USD `price_p100` value (USA, 2025, Large car, ICEV) is flagged only marginally (about 6% above the IQR fence; the next-highest country value is 3,000,000 USD). The maximum observed price naturally reflects niche luxury models, so the value was kept. The violin plot uses only median prices (`price_p50_2025USD`), so it is not affected.
- The five UAE Vans share records lie above the IQR fence in each of 2021–2025, but the removal rests on the domain rule (a share cannot exceed 100%); the largest Vans share reported by any other country is 84%.
- Related rows overlap (for example `All cars` and the `ALL` powertrain), so flagged counts are indicative rather than independent events.

## Dashboard Visualizations

The nine core visualization methods (the numbers below are for this table only; the card titles on the dashboard use their own numbering):

| # | Method | Research question | Key metrics | Main interactions |
|---|---|---|---|---|
| 01 | **Sunburst** (Dataset Explorer) | How are EV indicators organized across parameters, vehicle modes and powertrains? | Count of unique parameter → mode → powertrain combinations | Parameter-group selector, click to drill down, hover |
| 02 | **Connected Scatterplot** | How did global EV sales and the BEV share of BEV/PHEV sales evolve together? | World car EV sales; BEV/(BEV+PHEV) (%) | Hover, zoom/pan |
| 03 | **Rank Comparison Dumbbell** | Do countries leading in EV sales volume also lead in EV sales share? | Sales-volume rank vs. sales-share rank (top 12 in either ranking) | Historical-year selector, hover |
| 04 | **Scatterplot Matrix (SPLOM)** | Are larger electric car fleets associated with more public charging points? | Four panels: log10 EV stock, log10 public charging points, EV cars per public point, EV sales share (2025, 33 matched countries); Spearman correlation | Box/lasso selection with linked highlighting across panels, hover, zoom/pan |
| 05 | **Violin Plot** | How does the BEV–ICEV median price gap vary across segments and countries? | Price gap (%) per country–segment pair from 2025 USD medians | Segment multiselect, hover on country points, zoom/pan |
| 06 | **Treemap** | Which vehicle types contribute most to oil displacement, battery deployment and electricity demand? | One selected energy metric across five vehicle types (World, 2025) | Metric selector, hover, click to drill down |
| 07 | **Sankey Diagram** | How did countries move between electricity-demand-per-EV levels from 2020 to 2025? | **Country counts** (not energy flows) between Low/Medium/High levels (pooled terciles); five matched countries | Hover, drag nodes |
| 08 | **Parallel Coordinates Plot** | Did different vehicle types electrify at the same pace between 2020 and 2025? | World EV sales share by year, per vehicle type | Axis brushing (drag a range), hover |
| 09 | **Diverging Heatmap** | Where are the largest relative STEPS–CPS differences across indicators and geographies in 2035? | 100 × (STEPS − CPS)/abs(CPS); symmetric signed-log color mapping only, real percentages on the colorbar | Hover (original CPS/STEPS values, percentages and units) |

Each chart is presented with a title and research question, an interactive figure, and a result card with a data-derived Key Insight, scope information and Methodology & Limitations text. The assignment asks for at least six advanced visualizations; which of the methods above the course formally counts as advanced has not been confirmed, so no claim is made here.

## Machine Learning Insights

The two ML analyses support the dashboard and are **not** counted among the nine core visualizations. The workflows are in `data/modeldataset/clustering/clustering.ipynb` and `data/modeldataset/regression/regression.ipynb` (notebook text is in Turkish). The dashboard reads only the precomputed result CSVs; it does not retrain models or load the saved model files.

### K-Means Clustering

- **Objective:** Group countries by similarity in EV adoption and charging infrastructure.
- **Data:** 185 country–year rows (33 countries, 2020–2025) built from the cleaned dataset; countries need complete values for the selected indicators.
- **Features (Feature Set B):** EV sales share, EV stock share, `log1p`(EV stock), and `log1p` of slow, fast and ultra-fast public chargers per 1,000 EVs.
- **Preprocessing:** `log1p` transform for skewed counts and densities, then standardization.
- **Method:** K-Means with k = 3, chosen after comparing Feature Sets A and B for k = 2–8 by silhouette score and inertia. Agglomerative clustering and DBSCAN were also evaluated.
- **Metrics (Feature Set B, k = 3):** silhouette 0.290; Davies–Bouldin 1.261; Calinski–Harabasz 72.448 (notebook outputs).
- **Dashboard:** a strip plot of EV sales share by cluster (*Early*, *Intermediate*, *Advanced EV Adoption*) with Year, Country and Cluster filters and a per-cluster summary table.
- **Interpretation:** The silhouette score indicates weak-to-moderate structure. Cluster names were assigned after clustering, and clusters also reflect stock and charging density, so sales-share ranges overlap. A country-holdout stability study in the notebook reports a mean ARI of 0.956 for Feature Set B; this measures consistency with the full-data grouping, not classification accuracy.

### Regression: Next-Year EV Sales Share

- **Target:** a country's EV car sales share (%) in year *t+1*.
- **Inputs (year *t*):** EV sales share, EV sales, BEV sales (cars).
- **Dataset:** 687 country-year observations across 61 countries, historical records only.
- **Models:** Persistence Baseline (next year = this year), Linear Regression, Random Forest, XGBoost.
- **Split (chronological, by target year):** train ≤ 2022 (507 rows), validation 2023–2024 (120 rows), test 2025 (60 countries). Final models were refitted on the combined 627 training and validation rows before testing.

| Model | MAE (pp) | Median error | Max error |
|---|---|---|---|
| Persistence Baseline | 5.521 | 4.900 | 21.000 |
| Linear Regression | 4.114 | 3.447 | 17.859 |
| XGBoost | 4.222 | 2.895 | 16.203 |
| Random Forest | 4.319 | 3.107 | 16.015 |

- **Interpretation:** All three ML models improve on the Persistence Baseline on the 2025 test set. Linear Regression has the lowest observed MAE and XGBoost the lowest median error, but a bootstrap of country-level MAE differences (shown on the page) does not clearly separate the ML models. On the 2023–2024 validation set the Persistence Baseline was best (MAE 4.06).
- **Limitations:** Only three inputs and a single test year with 60 countries; predictions are not clipped and can fall outside 0–100% (e.g. Linear Regression predicts 101.94% for Norway); results are not causal.
- **Dashboard:** an error box plot with individual country points, Model and Country filters, a summary table and bootstrap comparisons.

## Key Insights and Findings

All figures are computed from the project datasets by the dashboard's chart code.

- World electric car sales grew from 7,400 (2010) to 21,000,000 (2025). The BEV share of BEV/PHEV sales was 94.0% in 2010 and 66.0% in 2025.
- Across 33 matched countries in 2025, EV car stock and public charging points have a Spearman rank correlation of 0.93. This is an association, not causation.
- In 2025, China ranked first in EV car sales volume but eighth in EV sales share.
- BEV median prices are below ICEV medians in 7 of 50 country–segment pairs (10 countries, 2025); the median gap is +27.2%.
- Among vehicle types with complete data, cars show the largest EV sales-share change from 2020 to 2025 (+20.6 percentage points).
- Of 5 countries with matched 2020 and 2025 electricity demand per EV data, 2 stayed in the same demand category.
- On the 2025 test set, the three regression models reduce MAE by roughly 1.2–1.4 percentage points relative to the persistence baseline.

## Interactivity and User Experience

| Feature | Where it is available |
|---|---|
| Hover tooltips with original values | All charts |
| Zoom, pan and the Plotly toolbar | Plotly charts (toolbar enabled for all cards) |
| Dropdown / multiselect filters | Sunburst (parameter group), Dumbbell (year), Violin (segments), Treemap (metric), ML Clustering (year, country, cluster), ML Regression (model, country) |
| Click-to-drill-down | Sunburst, Treemap |
| Box and lasso selection with linked highlighting | SPLOM |
| Axis brushing | Parallel Coordinates |
| Draggable nodes | Sankey |
| Light / Dark theme | Theme selector on every page |
| Tab and top navigation | Research & Insights tabs, ML Insights tabs, page navigation |

## Technology Stack

| Area | Technologies and tools |
|---|---|
| Language | Python |
| Dashboard | Streamlit (multipage app, top navigation, `st.cache_data`) |
| Interactive visualization | Plotly (`graph_objects`, `express`) |
| Data processing | pandas, NumPy, openpyxl |
| ML workflows | scikit-learn, XGBoost; SciPy where used in notebooks |
| Notebooks | Jupyter / Google Colab, Matplotlib |
| Version control | Git, GitHub, branches and pull requests |
| Testing | Python `unittest`; pytest-compatible tests |
| Deployment | Streamlit Community Cloud |
| AI-assisted development | AI coding assistants were used for development and review, with human review of changes |

`requirements.txt` lists `streamlit`, `pandas`, `numpy`, `plotly` and `openpyxl`, which is enough to run the dashboard. Re-running the notebooks requires additional packages such as `scikit-learn`, `xgboost`, `matplotlib` and a notebook environment.

## Installation and Local Execution

```bash
git clone https://github.com/simgedanisoglu/global-electric-vehicle-dashboard.git
cd global-electric-vehicle-dashboard
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

**Tests**

```bash
python -m pip install pytest
python -m pytest -q
```

On the current `main` branch, this run reports 63 passed tests (plus 43 sub-tests).

## Project Structure

```text
.
├── app.py                      # Entry point: navigation, theme
├── requirements.txt
├── data/
│   ├── EV data by country 2026.xlsx
│   ├── DataVisulationProject.ipynb   # Exploration, cleaning and outlier analysis
│   ├── analysisdataset/        # global_ev_cleaned.csv, ev_2035_scenario_comparison.csv
│   └── modeldataset/
│       ├── clustering/         # notebook, feature sets, clustering_results.csv
│       └── regression/         # notebook, regression_results_2025.csv, saved_models/
├── pages/
│   ├── 1_Dataset_Explorer.py
│   ├── 2_Research_Insights.py
│   └── 3_ML_Insights.py
├── src/
│   ├── charts/                 # One module per visualization (incl. ml_clustering, ml_regression)
│   ├── data/                   # Data loading helpers
│   ├── ui/theme.py             # Shared theme and card components
│   └── config.py
└── tests/                      # Chart and ML tests
```

## Team Members and Individual Contributions

Each team member developed three of the nine core visualizations. Contributions below are based on the Git history (authorship of each module, page and test file) and the repository contents.

### Simge (`simgedanisoglu`)

- **Core visualizations:** Connected Scatterplot, Treemap, Diverging Heatmap, each with a dedicated test file.
- **Dashboard and UI:** Card-based Streamlit layout and the Light/Dark theme switcher (`src/ui/theme.py`, shared pages); signed-log color mapping that improves heatmap readability.
- **Project foundation:** Initialized the repository and shared Streamlit application, replaced the placeholder dataset with the IEA EV data, created the project structure (`app.py`, `pages/`, `src/charts/`, `data/`) and the analysis/model dataset folders; initial project README.

### Halil Keremoglu (`halilkrm`)

- **Core visualizations:** Sunburst, Rank Comparison Dumbbell, Sankey Diagram, with tests (`tests/test_halil_charts.py`).
- **Dashboard integration:** Integrated the nine visualizations into the Streamlit pages (Dataset Explorer and Research & Insights), applied consistent dashboard styling, fixed Sankey node and link tooltips, and fixed the Light/Dark toggle alignment.

### Rabia Avcı (`rabiaavc`)

- **Core visualizations:** Scatterplot Matrix (SPLOM), Violin Plot and Parallel Coordinates Plot, each with tests; SPLOM box and lasso selection with linked highlighting; Violin density-range accuracy fix.
- **Machine learning:** K-Means clustering and next-year regression notebooks; the ML Insights page with the clustering strip plot, regression error box plot, filters, summaries and bootstrap comparison; tests for the ML chart modules.
- **Data quality:** Data exploration, cleaning and outlier-detection notebook (`data/DataVisulationProject.ipynb`), including the IQR analysis documented above.

### Shared responsibilities

The three members share testing of their own visualizations. Data collection, exploratory analysis beyond the notebooks above, and report writing are not attributed to individuals because the repository does not show who carried them out.

## Limitations

- **Coverage:** Country coverage differs by indicator and year. Price and charging data are available for fewer countries than sales data, and incomplete records are excluded rather than imputed.
- **Units and shares:** Indicators use different units (vehicles, percent, GWh, charging points, USD) and are never added together. Sales shares describe new sales, not the vehicle fleet.
- **Aggregates:** World and regional rows are kept separate from countries and never summed with them.
- **Projections:** 2035 values come from two IEA scenarios (STEPS and CPS); they are not forecasts or observations. Relative differences can be inflated by small CPS baselines.
- **Derived categories:** Low/Medium/High electricity demand per EV levels are pooled terciles defined for this dashboard, not IEA categories.
- **Prices:** Price gaps use country-level medians, not individual car prices.
- **Outliers:** 3,235 historical records were flagged by the IQR rule but were not removed because they mostly reflect skewed, legitimate values; five invalid UAE share records were removed. Energy indicators and projection rows could not be tested because of small group sizes, and flagged counts are indicative rather than independent.
- **Clustering:** Weak-to-moderate structure (silhouette 0.290); cluster names are interpretive labels.
- **Regression:** Three input features, one test year, no clear difference between the ML models, and unclipped predictions.
- **Association vs. causation:** Correlations and temporal patterns shown in the dashboard do not establish causation.
- **Data reuse:** The IEA source is cited below; dataset-specific redistribution and licensing terms should be checked with the data provider.

## References

- IEA (2026), *Global EV Outlook 2026*, https://www.iea.org/reports/global-ev-outlook-2026 (citation given in the Excel `Notes` sheet; second version, updated 26 May 2026).
- Streamlit documentation – https://docs.streamlit.io
- Plotly Python documentation – https://plotly.com/python/
- pandas documentation – https://pandas.pydata.org/docs/
- scikit-learn documentation – https://scikit-learn.org/stable/
- XGBoost documentation – https://xgboost.readthedocs.io
