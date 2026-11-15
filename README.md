# Global Electric Vehicle Dashboard

**CEN445 – Introduction to Data Visualization**

|                       |                                                                                                                                                                                          |
| :-------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Live Dashboard**    | [https://global-electric-vehicle-dashboard-7dktbb3dxpiah6gcc3erqo.streamlit.app/](https://global-electric-vehicle-dashboard-7dktbb3dxpiah6gcc3erqo.streamlit.app/)                       |
| **GitHub Repository** | [https://github.com/simgedanisoglu/global-electric-vehicle-dashboard](https://github.com/simgedanisoglu/global-electric-vehicle-dashboard)                                               |

## Project Overview

An interactive Streamlit dashboard has been developed using the IEA *Global EV Outlook 2026* dataset to investigate the transition to electric vehicles (EVs). Differences among countries, public charging infrastructure, vehicle prices, energy impacts, and 2035 scenario projections are examined. Nine visualization techniques are included, while K-Means clustering and next-year regression analyses are presented on a separate page.

| Page                | Content                                                                                              |
| :------------------ | :--------------------------------------------------------------------------------------------------- |
| Dataset Explorer    | Sunburst view of how the dataset is organized                                                        |
| Research & Insights | Eight visualizations in five tabs: Market & Adoption, Charging, Prices, Energy & Impact, Future 2035 |
| ML Insights         | K-Means clustering and regression error analysis                                                     |

## Dataset Description

- **Source:** International Energy Agency (IEA), *Global EV Outlook 2026* – [https://www.iea.org/reports/global-ev-outlook-2026](https://www.iea.org/reports/global-ev-outlook-2026). The citation and second-version update date (26 May 2026) are documented in the Excel file's `Notes` sheet.
- **Raw file:** `data/EV data by country 2026.xlsx` (sheet `GEVO_EV_2026`, 49,375 rows × 9 columns, plus documentation sheets such as `Notes` and `Definitions`)
- **Cleaned file:** `data/analysisdataset/global_ev_cleaned.csv` (48,277 rows × 9 columns, no missing values)
- **Scenario file:** `data/analysisdataset/ev_2035_scenario_comparison.csv` (620 rows × 10 columns; matched STEPS/CPS pairs in 2035). The absolute STEPS − CPS difference is stored in the CSV `difference` column, whereas a relative percentage is calculated for the heatmap.
- **ML files:** `data/modeldataset/clustering/` and `data/modeldataset/regression/` (feature sets, results, notebooks, saved models)

### Variables (cleaned file)

Each row is used to represent **one measurement associated with a specific geography, year, indicator, and vehicle or charging category**. The meaning of the columns is explained below.

| Column | Data type | What it means in this dataset |
| :--- | :--- | :--- |
| `region_country` | string | **Where** the measurement applies: a country such as China, a region, or the World (72 distinct geographic labels). |
| `category` | string | **Whether an observation or a projection is recorded**: past data are labeled `Historical`; two 2035 scenarios are labeled `Projection-STEPS` and `Projection-CPS`. |
| `parameter` | string | **What is being measured**: for example, number of EVs sold, percentage of new cars that are electric, vehicles in use, charging stations, energy demand or car prices (19 indicators). |
| `mode` | string | **Which vehicle or product segment** the number describes: cars, buses, trucks, vans, two/three-wheelers, charging equipment (`EVSE`) or a particular car-size segment. |
| `powertrain` | string | **Which propulsion or charging technology** is counted: battery electric (`BEV`), plug-in hybrid (`PHEV`), conventional combustion engine (`ICEV`), or, for charging records, charger speed/type. |
| `year` | integer | **When** the value refers to: a year between 2010 and 2035. |
| `unit` | string | **How the value is expressed**: e.g., vehicles, percentage, charging points, GWh or constant 2025 USD. Ten unit spellings are represented in the file. |
| `value` | float | **The numeric result**: e.g., `150000` vehicles or `25` percent, interpreted together with `parameter` and `unit`. |
| `Aggregate group` | string | **The geographic level assigned to the row**: a country, the World, a regional aggregate or a scenario-specific group; used to distinguish totals from individual-country observations. |

**Historical vs. projection data.** A total of 47,016 `Historical` records are provided for 2010–2025. `Projection-STEPS` (640 rows) and `Projection-CPS` (621 rows) are provided for 2035 and are treated as scenario outcomes rather than observations. In the scenario comparison file, 620 STEPS/CPS pairs are matched; the remaining 21 unmatched records are excluded from paired comparisons.

## Data Preprocessing

The original Excel file was examined and cleaned to improve comparability. The steps are documented in `data/DataVisulationProject.ipynb`. The row count is reconciled as **49,375 − 1,078 − 15 − 5 = 48,277**.

| Step | Finding and decision |
| :--- | :--- |
| Missing countries | **1,078 price records** did not identify any country. Because their geographic origin was unknown, they could not be used in country comparisons and were excluded. |
| Duplicate rows | **15 identical records** were removed so the same measurement would not be counted twice; one copy was kept. |
| Missing price units | **22,582 price records** lacked a unit. The unit was filled as **2025 USD**, consistent with the price-indicator names. |
| Impossible percentages | Five UAE **van EV sales-share** values for 2021–2025 were **200–310%**. Values above 100% were deemed invalid as shares, so the five records were removed; the valid 2020 value (5.6%) was retained. |
| Units and values | Original unit spellings were retained; indicators are interpreted together with their units. Invalid percentages were checked, and **18 fractional count values** were reviewed and retained rather than automatically rounded. |
| Missing combinations | Missing country–year–indicator combinations are **not filled with zero**; available comparable records are used in each chart. |
| World and regional totals | Country records are kept separate from World, regional, and EU totals to prevent double counting or misleading rankings. |

### Outlier Detection

In the notebook's *Outlier Detection & Analysis* section, **Tukey's interquartile-range (IQR) rule** was applied. Values below Q1 − 1.5 × IQR or above Q3 + 1.5 × IQR are flagged for review. Only country-level observations were compared, with separate evaluation **by indicator, vehicle type, technology, unit, year, and historical/projection category**. Groups were evaluated only when at least eight countries and a non-zero IQR were available.

| Result | Value |
| :--- | :--- |
| Country-level records considered | 40,477 |
| Comparable groups / groups eligible for testing | 3,170 / 2,189 |
| Records in eligible groups | 36,722 |
| Records flagged by the IQR rule | **3,235 (8.8%)** |

| Indicator family | Flagged / evaluated | Flagged share |
| :--- | :--- | :--- |
| Vehicle counts (sales, stock and chargers) | 1,558 / 11,231 | 13.9% |
| Ratios (EVs per charging point) | 40 / 444 | 9.0% |
| Percentage shares | 339 / 3,921 | 8.6% |
| Charging power capacity | 60 / 889 | 6.7% |
| Prices (2025 USD) | 1,238 / 20,237 | 6.1% |

**Scope and interpretation.** The four energy indicators and the 2035 projections had too few countries per comparable group to meet the test threshold; the reported flags concern **historical** data only. Many large observations reflect genuinely uneven markets, such as China's EV volumes, rather than incorrect records. The USA's **5,000,000 USD** maximum price (`price_p100_2025USD`, 2025, large ICEV car) lies roughly 6% above its IQR upper fence but is plausible as an exceptional high-end maximum. The violin plot uses median prices (`price_p50_2025USD`), not this maximum. In contrast, five UAE van sales shares above 100% violate the meaning of a percentage; their removal was justified by that rule, not by IQR alone.

**Decision:** Statistical outliers were **identified and documented, not automatically removed**. The IQR analysis did not modify the cleaned data. The five logically invalid UAE values had already been excluded during data cleaning. Some indicators represent related/overlapping measures, so the count of flagged records should not be treated as independent events.

## Dashboard Visualizations

**Nine distinct visualization techniques** are employed in the dashboard. The research questions, measured values and supported interactions are summarized below. The term *metric* refers to a measured quantity, such as sales count, sales share or charging-point count.

| # | Method | Research question | What the chart shows | Main interactions |
| :-- | :--- | :--- | :--- | :--- |
| 01 | **Sunburst** (Dataset Explorer) | How is the EV dataset organized? | Counts of the distinct **indicator → vehicle category → technology** combinations represented in the data; a combination is counted once even if it appears in multiple rows. | Indicator selector, click to explore nested categories, hover |
| 02 | **Connected Scatterplot** | How did global electric-car sales and the proportion of BEVs change together? | Annual World EV car sales alongside **BEV sales as a share of BEV + PHEV sales**. | Hover, zoom and pan |
| 03 | **Rank Comparison Dumbbell** | Do countries leading in EV sales numbers also lead in sales percentage? | Each country's position in **sales-volume ranking versus EV sales-share ranking** (countries in the top 12 of either list). | Year selector, hover |
| 04 | **Scatterplot Matrix (SPLOM)** | Are larger EV fleets associated with better public charging availability? | Four country-level measures: EV stock and public charger counts (both on log10 scales), **EV cars per charging point**, and EV sales share; 33 matched countries in 2025, plus Spearman correlation. | Box/lasso selection and linked highlighting, hover, zoom/pan |
| 05 | **Violin Plot** | How do electric and conventional car prices compare? | The **percentage difference between BEV and ICEV median car prices** by country and car-size segment, using 2025-USD values. | Segment multiselect, hover, zoom/pan |
| 06 | **Treemap** | Which vehicle types contribute most to energy-related impacts? | The contribution of five vehicle types to a selected metric: **oil displacement, battery deployment or electricity demand** (World, 2025). | Metric selector, hover, click to drill down |
| 07 | **Sankey Diagram** | How did countries shift between low, medium and high electricity demand per EV from 2020 to 2025? | **Numbers of countries** moving between three demand-per-EV levels, based on five matched countries; the flows represent countries, **not units of energy**. | Hover, drag nodes |
| 08 | **Parallel Coordinates Plot** | Which vehicle types increased their EV sales share most between 2020 and 2025? | Each vehicle type's **percentage of new sales that were electric**, shown across successive years at World level. | Drag to select axis ranges, hover |
| 09 | **Diverging Heatmap** | Where do the two 2035 scenarios differ most? | **Relative percentage difference** between STEPS and CPS for each geography and indicator: 100 × (STEPS − CPS) / abs(CPS). A signed-log transform is used for **colors only**; tooltips retain the actual numbers. | Hover to inspect both scenario values, percentages and units |

For the purposes of this project, **seven techniques have been classified as advanced**: Sunburst, SPLOM, Violin Plot, Treemap, Sankey Diagram, Parallel Coordinates and Diverging Heatmap. **Two techniques have been classified as intermediate**: Connected Scatterplot and Rank Comparison Dumbbell. This categorization is used as a project-level assessment of complexity and is not presented as an official course designation.

A research question, a data-derived *Key Insight*, coverage information, and a *Methodology & Limitations* explanation are provided for each chart.

## Machine Learning Insights

In addition to visualizing historical EV market patterns, two complementary machine learning tasks were selected: **clustering** to identify countries with similar EV adoption profiles without predefined labels, and **regression** to estimate next-year EV sales shares from past observations. The methods were chosen to support both descriptive comparisons and predictive evaluation.

### K-Means Clustering: EV Adoption Profiles

**Rationale.** As similar adoption and charging-infrastructure characteristics may be observed in countries with different market sizes, profiles were developed using multiple indicators rather than rankings based on a single sales percentage.

- **Dataset construction:** Historical records for 2020–2025 were matched by **country and year**. Observations with the required EV adoption and charging measures were retained, yielding **185 country–year records across 33 countries**.
- **Features:** **EV sales share, EV stock share, EV stock size**, and densities of **slow, fast and ultra-fast public charging points per 1,000 EVs** were included. Charging densities were used to improve comparability between markets of different sizes.
- **Transformations:** A **`log1p` transformation** was applied to skewed EV stock and charger-density features. The features were subsequently **standardized** so that differences in units and scales would not dominate distance calculations.
- **Model comparison:** Feature Sets **A and B** and K-Means solutions for **k = 2–8** were evaluated using silhouette scores and inertia. **Agglomerative Clustering and DBSCAN** were also assessed. **K-Means with Feature Set B and k = 3** was selected to provide three interpretable profiles. Scores of **silhouette 0.290**, **Davies–Bouldin 1.261**, and **Calinski–Harabasz 72.448** were obtained.
- **Cluster interpretation:** The three resulting groups were labeled **Early EV Adoption**, **Intermediate EV Adoption**, and **Advanced EV Adoption** after model fitting. These labels are used as interpretations rather than ground-truth classes, and overlapping EV sales-share ranges may be observed. A country-holdout stability study yielded a mean **ARI of 0.956**, which was interpreted as a measure of grouping consistency rather than classification accuracy.
- **Dashboard presentation:** EV sales share is displayed for each country–year record in a cluster-colored **strip plot**. Comparisons can be made using **year, country and cluster filters** and the per-cluster summary table.

### Regression: Predicting Next-Year EV Sales Share

**Rationale.** Regression was selected to examine whether next-year EV sales share could be predicted using current-year adoption and sales indicators. Several models were evaluated against a simple baseline so that any benefits of increased model complexity could be assessed.

- **Dataset construction:** Historical data were reorganized into **country–year records**. **EV sales share, total EV sales, and BEV car sales** for year *t* were selected as inputs, while the same country's **EV sales share in year t+1** was defined as the target. A dataset of **687 matched observations from 61 countries** was obtained.
- **Temporal evaluation:** A **chronological split** was applied instead of a random split to preserve the forecasting setting: training targets through **2022 (507 rows)**, validation in **2023–2024 (120 rows)**, and a held-out **2025 test set (60 countries)**. Final models were refitted on **627 training and validation observations**, with 2025 target values excluded from training.
- **Compared models:** In the **Persistence Baseline**, next-year sales share is assumed to equal the current share. Linear relationships were modeled using **Linear Regression**, while nonlinear relationships were modeled using **Random Forest** and **XGBoost**. Model complexity was evaluated relative to the baseline.
- **Evaluation:** **Mean absolute error (MAE)**, median error, and maximum error were used for comparison. Errors are expressed in **percentage points (pp)**; lower values indicate better predictions.

| Model | MAE (pp) | Median error (pp) | Maximum error (pp) |
| :--- | ---: | ---: | ---: |
| Persistence Baseline | 5.521 | 4.900 | 21.000 |
| Linear Regression | **4.114** | 3.447 | 17.859 |
| XGBoost | 4.222 | **2.895** | 16.203 |
| Random Forest | 4.319 | 3.107 | **16.015** |

**Results and model choice.** On the **2025 test set**, the lowest **mean** error was achieved by Linear Regression, the lowest **median** error by XGBoost, and the lowest **maximum** error by Random Forest. Lower test MAE values than the Persistence Baseline were obtained with all three ML models. However, the lowest **2023–2024 validation MAE (4.06 pp)** was achieved by the baseline, and no clear superiority among the ML models was established by the bootstrap comparisons. Consequently, **all four methods are presented side by side**, without claiming a universally superior model.

**Dashboard presentation.** Absolute prediction errors, country-level results, and extreme cases are visualized in an interactive **box plot**. Model and country filters, a summary table, and bootstrap comparisons are provided to support examination of model differences across countries.

**Limitations.** Only three input variables and one held-out test year were used. Predictions were not constrained to the valid 0–100% range; for example, a prediction of 101.94% was produced for Norway by Linear Regression. The results are interpreted as predictive associations, not evidence of causality.

## Key Insights and Findings

All numerical findings were calculated from the project datasets using the dashboard's visualization code.

- World electric car sales were observed to increase from 7,400 (2010) to 21,000,000 (2025). The BEV share of BEV/PHEV sales was calculated as 94.0% in 2010 and 66.0% in 2025.
- Across 33 matched countries in 2025, EV car stock and public charging points have a Spearman rank correlation of 0.93. This is an association, not causation.
- In 2025, China was ranked first in EV car sales volume and eighth in EV sales share.
- Lower BEV than ICEV median prices were identified in 7 of 50 country–segment pairs (10 countries, 2025); a median gap of +27.2% was calculated.
- Among vehicle types with complete data, cars show the largest EV sales-share change from 2020 to 2025 (+20.6 percentage points).
- Among 5 countries with matched 2020 and 2025 electricity-demand-per-EV data, 2 were observed to remain in the same category.
- On the 2025 test set, an MAE reduction of approximately 1.2–1.4 percentage points relative to the Persistence Baseline was obtained with the three regression models.

## Interactivity and User Experience

| Feature                                          | Where it is available                                                                                                                                    |
| :----------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hover tooltips with original values              | All charts                                                                                                                                               |
| Zoom, pan and the Plotly toolbar                 | Plotly charts (toolbar enabled for all cards)                                                                                                            |
| Dropdown / multiselect filters                   | Sunburst (parameter group), Dumbbell (year), Violin (segments), Treemap (metric), ML Clustering (year, country, cluster), ML Regression (model, country) |
| Click-to-drill-down                              | Sunburst, Treemap                                                                                                                                        |
| Box and lasso selection with linked highlighting | SPLOM                                                                                                                                                    |
| Axis brushing                                    | Parallel Coordinates                                                                                                                                     |
| Draggable nodes                                  | Sankey                                                                                                                                                   |
| Light / Dark theme                               | Theme selector on every page                                                                                                                             |
| Tab and top navigation                           | Research & Insights tabs, ML Insights tabs, page navigation                                                                                              |

## Technology Stack

| Area                      | Technologies and tools                                                                  |
| :------------------------ | :-------------------------------------------------------------------------------------- |
| Language                  | Python                                                                                  |
| Dashboard                 | Streamlit (multipage app, top navigation, `st.cache_data`)                              |
| Interactive visualization | Plotly (`graph_objects`, `express`)                                                     |
| Data processing           | pandas, NumPy, openpyxl                                                                 |
| ML workflows              | scikit-learn, XGBoost; SciPy where used in notebooks                                    |
| Notebooks                 | Jupyter / Google Colab, Matplotlib                                                      |
| Version control           | Git, GitHub, branches and pull requests                                                 |
| Testing                   | Python `unittest`; pytest-compatible tests                                              |
| Deployment                | Streamlit Community Cloud                                                               |
| AI-assisted development   | AI coding assistants were used for development and review, with human review of changes |

The `streamlit`, `pandas`, `numpy`, `plotly`, and `openpyxl` dependencies are listed in `requirements.txt` and can be used to run the dashboard. Additional packages, including `scikit-learn`, `xgboost`, and `matplotlib`, and a notebook environment are required to rerun the analyses.

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

On the current `main` branch, **63 passing tests** and **43 sub-tests** were reported for this command.

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

The project was developed through collaborative planning and evaluation by three team members. Dataset exploration, data-cleaning decisions, research question formulation, and visualization technique selection were carried out collaboratively. During the development phase, responsibility for the nine core visualizations was distributed equally among the team members.

### 1. Data Preprocessing

The raw dataset was jointly examined by all team members. Missing values, duplicate records, invalid measurements, and statistical outliers were evaluated, and data-cleaning decisions were made collaboratively. The exploratory preprocessing and IQR outlier-detection notebook (`data/DataVisulationProject.ipynb`) was implemented and documented by Rabia based on these shared decisions.

### 2. Visualization Design

Research questions, visualization techniques, and key metrics were jointly determined by **Simge, Halil, and Rabia**. The visualizations were designed to explore different aspects of the dataset and to incorporate varied visualization techniques.

Following these collaborative design decisions, each team member was assigned responsibility for the technical design and implementation of three visualizations.

### 3. Interaction Implementation

- **Simge:** Interactive features were implemented for the Connected Scatterplot, Treemap, and Diverging Heatmap, including metric selection, hover tooltips, and chart navigation.
- **Halil:** Interactive features were implemented for the Sunburst, Rank Comparison Dumbbell, and Sankey Diagram, including hierarchical drill-down, year selection, hover tooltips, and draggable Sankey nodes.
- **Rabia:** Interactive features were implemented for the Scatterplot Matrix (SPLOM), Violin Plot, and Parallel Coordinates Plot, including linked box/lasso selection, segment filtering, axis brushing, and hover tooltips.

### 4. Individual Visualization Development

| Team Member | Developed Visualizations |
|---|---|
| **Simge Danışoğlu** (`simgedanisoglu`) | Connected Scatterplot, Treemap, Diverging Heatmap |
| **Halil Keremoğlu** (`halilkrm`) | Sunburst, Rank Comparison Dumbbell, Sankey Diagram |
| **Rabia Avcı** (`rabiaavc`) | Scatterplot Matrix (SPLOM), Violin Plot, Parallel Coordinates Plot |

The data preparation, visualization implementation, and associated testing required for each chart were carried out by the responsible team member.

**Halil** developed the Streamlit dashboard interface, integrated the visualization charts into the application pages, and deployed the dashboard to **Streamlit Community Cloud**, making it publicly accessible. **Simge** contributed to theme customization, reviewed and tested the visualizations, and added the Methodology & Limitations sections.

The **K-Means clustering, regression analysis, and ML Insights page** were developed by **Rabia**. The clustering strip plot, regression error box plot, filters, summary tables, and bootstrap comparisons were also implemented and tested by Rabia.

### 5. Report Writing

The one-page English project results report was prepared by Simge Danışoğlu. The report summarizes the project objectives, visualization techniques, key findings, machine learning results, data preprocessing, and individual team contributions.

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
- **Association vs. causation:** Correlations and temporal patterns presented in the dashboard are not interpreted as evidence of causation.
- **Data reuse:** The IEA source is cited below; dataset-specific redistribution and licensing conditions should be verified with the data provider.

## References

- IEA (2026), *Global EV Outlook 2026*, [https://www.iea.org/reports/global-ev-outlook-2026](https://www.iea.org/reports/global-ev-outlook-2026) (citation given in the Excel `Notes` sheet; second version, updated 26 May 2026).
- Streamlit documentation – [https://docs.streamlit.io](https://docs.streamlit.io/)
- Plotly Python documentation – [https://plotly.com/python/](https://plotly.com/python/)
- pandas documentation – [https://pandas.pydata.org/docs/](https://pandas.pydata.org/docs/)
- scikit-learn documentation – [https://scikit-learn.org/stable/](https://scikit-learn.org/stable/)
- XGBoost documentation – [https://xgboost.readthedocs.io](https://xgboost.readthedocs.io/)
