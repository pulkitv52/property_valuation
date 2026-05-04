# Use Case 1: AI-Based Property Valuation PoC — Implementation Plan

## 1. Objective

Build a Proof of Concept (PoC) for an AI-based property valuation system that can:

1. Predict property market value.
2. Identify AI-driven valuation zones.
3. Explain factors affecting valuation.
4. Compare AI predictions with actual transaction values and existing MVDB/circle rates, if available.

The system will use transaction data, GIS property data, road network data, and facilities/amenities data.

---

## 2. Available Data

### 2.1 Transaction Dataset

Expected file:

```text
tran_data.xlsx / tran_data.csv
```

Important columns include:

```text
query_year, query_no, book, Deed_No, Deed_Year,
Registration_district_code, Registration_district_Name,
Registration_RO_code, Registration_Office_Name,
Transaction_code, Transaction_Name,
Date_of_presentation, Date_of_Registration, Time_of_Presentation,
sl_no_Property, property_district_code, property_district_Name,
Property_Office_code, property_Office_Name,
ps_code, PS_Name, mouza_code, Mouza_Name,
plot_code_type, plot_no, bata_plot_no, premises,
Urban, Rural, Road_code, Road_Name, Zone_no,
Special_project_Name, Is_Property_on_Road,
Approach_Road_Width, Adjacent_to_Metal_Road,
Proposed_Land_use_Code, Proposed_Land_use_Name,
Nature_Land_use_Code, Nature_Land_use_Name,
Proposed_Apartment_use_Name, Nature_Apartment_use_name,
Litigated_Property, bargadar, whether_tenant_purchaser,
Area_type, Area, Types of area Measurement,
setforth_value, market_value, is_bargadar_purchaser,
Mouza_Type, Road_Category, Flat_or_Land
```

Key fields:

| Column | Purpose |
|---|---|
| `market_value` | Main target variable |
| `setforth_value` | Declared value / comparison value |
| `Area` | Property area |
| `property_district_Name` | Location feature |
| `Mouza_Name` | Location feature |
| `Road_Name` | Connectivity/location feature |
| `Zone_no` | Existing zone reference |
| `Approach_Road_Width` | Road accessibility feature |
| `Road_Category` | Road quality/connectivity feature |
| `Proposed_Land_use_Name` | Land use feature |
| `Nature_Land_use_Name` | Actual land use feature |
| `Urban`, `Rural` | Urban/rural classification |
| `Flat_or_Land` | Property type |

---

### 2.2 GIS Property Dataset

Expected files:

```text
ai_usecase_data240326.shp
ai_usecase_data240326.dbf
ai_usecase_data240326.shx
ai_usecase_data240326.prj
```

Purpose:

- Property spatial layer.
- Used for mapping, spatial joins, and zone creation.

---

### 2.3 Road Network Dataset

Expected files:

```text
ai_usecase_road240326.shp
ai_usecase_road240326.dbf
ai_usecase_road240326.shx
ai_usecase_road240326.prj
```

Purpose:

- Road network analysis.
- Used to generate features such as:
  - Distance to nearest road.
  - Connectivity score.
  - Road category influence.

---

### 2.4 Facilities / Amenities Dataset

Expected files:

```text
ai_usecase_facilities240326.shp
ai_usecase_facilities240326.dbf
ai_usecase_facilities240326.shx
ai_usecase_facilities240326.prj
```

Purpose:

- Facility/amenity proximity analysis.
- Used to generate features such as:
  - Distance to nearest facility.
  - Number of facilities within 500m / 1km.
  - Amenity density.

---

## 3. Recommended Project Structure

```text
valuation_poc/
│
├── data/
│   ├── raw/
│   │   ├── tran_data.xlsx
│   │   ├── ai_usecase_data240326.*
│   │   ├── ai_usecase_road240326.*
│   │   └── ai_usecase_facilities240326.*
│   │
│   ├── interim/
│   │   ├── cleaned_transactions.parquet
│   │   ├── property_gis.parquet
│   │   ├── roads_gis.parquet
│   │   └── facilities_gis.parquet
│   │
│   └── processed/
│       ├── model_training_dataset.parquet
│       ├── valuation_predictions.parquet
│       └── ai_zones.geojson
│
├── notebooks/
│   ├── 01_data_understanding.ipynb
│   ├── 02_gis_processing.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_model_training.ipynb
│   └── 05_zone_clustering.ipynb
│
├── src/
│   ├── config.py
│   ├── data_loader.py
│   ├── data_cleaning.py
│   ├── gis_processing.py
│   ├── feature_engineering.py
│   ├── model_training.py
│   ├── zone_clustering.py
│   ├── explainability.py
│   ├── evaluation.py
│   └── api.py
│
├── frontend/
│   └── app.py
│
├── models/
│   ├── valuation_model.pkl
│   ├── encoder.pkl
│   └── scaler.pkl
│
├── reports/
│   ├── data_profile_report.html
│   ├── model_metrics.json
│   └── final_poc_report.md
│
├── requirements.txt
└── README.md
```

---

## 4. Phase 1 — Data Understanding

### Goal

Understand the size, structure, quality, and usability of all datasets.

### Tasks

1. Load transaction data.
2. Load all shapefiles.
3. Check record counts.
4. Check column names and data types.
5. Check missing values.
6. Check duplicate records.
7. Identify keys for joining transaction and GIS data.
8. Identify outliers in `market_value`, `setforth_value`, and `Area`.

### Code Skeleton

```python
import pandas as pd
import geopandas as gpd

tran_df = pd.read_excel("data/raw/tran_data.xlsx")

property_gdf = gpd.read_file("data/raw/ai_usecase_data240326.shp")
road_gdf = gpd.read_file("data/raw/ai_usecase_road240326.shp")
facilities_gdf = gpd.read_file("data/raw/ai_usecase_facilities240326.shp")

print(tran_df.shape)
print(property_gdf.shape)
print(road_gdf.shape)
print(facilities_gdf.shape)

print(tran_df.info())
print(tran_df.isnull().sum().sort_values(ascending=False).head(30))
```

### Expected Output

- Data summary report.
- List of usable columns.
- List of missing/dirty columns.
- Candidate join keys.

---

## 5. Phase 2 — Transaction Data Cleaning

### Goal

Prepare the transaction dataset for model building.

### Tasks

1. Convert numeric columns:
   - `market_value`
   - `setforth_value`
   - `Area`
   - `Approach_Road_Width`
2. Remove records with missing or invalid `market_value`.
3. Remove records with missing or invalid `Area`.
4. Create `value_per_area`.
5. Standardize categorical columns.
6. Handle missing values.
7. Remove extreme outliers.

### Code Skeleton

```python
import numpy as np
import pandas as pd

def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    numeric_cols = [
        "market_value",
        "setforth_value",
        "Area",
        "Approach_Road_Width"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["market_value", "Area"])
    df = df[(df["market_value"] > 0) & (df["Area"] > 0)]

    df["value_per_area"] = df["market_value"] / df["Area"]

    text_cols = df.select_dtypes(include=["object"]).columns
    for col in text_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({"NAN": np.nan, "NONE": np.nan})
        )

    lower = df["value_per_area"].quantile(0.01)
    upper = df["value_per_area"].quantile(0.99)
    df = df[(df["value_per_area"] >= lower) & (df["value_per_area"] <= upper)]

    return df
```

### Expected Output

```text
data/interim/cleaned_transactions.parquet
```

---

## 6. Phase 3 — GIS Processing

### Goal

Prepare property, road, and facilities GIS layers for spatial analysis.

### Tasks

1. Load shapefiles.
2. Check coordinate reference system.
3. Convert all layers to a common projected CRS.
4. Validate geometry.
5. Fix invalid geometries.
6. Save cleaned GIS layers.

### Notes

Use a projected CRS for distance calculation. For India, choose a suitable UTM zone depending on the dataset location. If unsure, start with EPSG:32645 or EPSG:32646 and confirm with the GIS team/SPOC.

### Code Skeleton

```python
import geopandas as gpd

TARGET_CRS = "EPSG:32645"

def clean_gis_layer(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()

    if gdf.crs is None:
        raise ValueError("CRS is missing. Please confirm projection from SPOC/GIS team.")

    gdf = gdf.to_crs(TARGET_CRS)

    gdf["geometry"] = gdf["geometry"].buffer(0)

    gdf = gdf[~gdf.geometry.is_empty]
    gdf = gdf[gdf.geometry.notnull()]

    return gdf
```

### Expected Output

```text
data/interim/property_gis.parquet
data/interim/roads_gis.parquet
data/interim/facilities_gis.parquet
```

---

## 7. Phase 4 — Join Transaction Data with Property GIS

### Goal

Create a combined dataset containing transaction attributes and property geometry.

### Possible Join Keys

Try combinations of:

```text
mouza_code
plot_no
Road_code
Zone_no
property_district_code
Property_Office_code
```

### Tasks

1. Check common columns between transaction and property GIS layer.
2. Standardize join key formats.
3. Perform exact join.
4. Check join success rate.
5. If join rate is poor, use alternate keys or spatial join.

### Code Skeleton

```python
def standardize_key(series):
    return series.astype(str).str.strip().str.upper()

join_keys = ["mouza_code", "plot_no"]

for key in join_keys:
    tran_df[key] = standardize_key(tran_df[key])
    property_gdf[key] = standardize_key(property_gdf[key])

merged_gdf = property_gdf.merge(
    tran_df,
    on=join_keys,
    how="inner"
)

join_rate = len(merged_gdf) / len(tran_df)
print(f"Join rate: {join_rate:.2%}")
```

### Expected Output

```text
data/interim/merged_property_transactions.parquet
```

---

## 8. Phase 5 — Feature Engineering

### Goal

Create meaningful model features from transaction and GIS data.

### 8.1 Basic Property Features

Use:

```text
Area
Flat_or_Land
Urban
Rural
Proposed_Land_use_Name
Nature_Land_use_Name
Area_type
Mouza_Type
Road_Category
Litigated_Property
bargadar
whether_tenant_purchaser
```

### 8.2 Road Features

Create:

1. Distance to nearest road.
2. Road connectivity score.
3. Road category.
4. Approach road width.
5. Whether property is on road.
6. Adjacent to metal road.

```python
def add_nearest_road_distance(property_gdf, road_gdf):
    property_gdf = property_gdf.copy()
    road_union = road_gdf.geometry.union_all()
    property_gdf["distance_to_nearest_road"] = property_gdf.geometry.distance(road_union)
    return property_gdf
```

### 8.3 Facility Features

Create:

1. Distance to nearest facility.
2. Facility count within 500 meters.
3. Facility count within 1 km.
4. Facility density.

```python
def add_facility_features(property_gdf, facilities_gdf):
    property_gdf = property_gdf.copy()
    facility_union = facilities_gdf.geometry.union_all()
    property_gdf["distance_to_nearest_facility"] = property_gdf.geometry.distance(facility_union)

    property_gdf["facility_count_500m"] = property_gdf.geometry.apply(
        lambda geom: facilities_gdf[facilities_gdf.geometry.distance(geom) <= 500].shape[0]
    )

    property_gdf["facility_count_1km"] = property_gdf.geometry.apply(
        lambda geom: facilities_gdf[facilities_gdf.geometry.distance(geom) <= 1000].shape[0]
    )

    return property_gdf
```

### 8.4 Location Features

Create:

```text
district
registration office
property office
police station
mouza
zone
road name
latitude
longitude
```

```python
merged_gdf["centroid"] = merged_gdf.geometry.centroid
merged_gdf["latitude"] = merged_gdf["centroid"].y
merged_gdf["longitude"] = merged_gdf["centroid"].x
```

### Expected Output

```text
data/processed/model_training_dataset.parquet
```

---

## 9. Phase 6 — Model Training

### Goal

Train a valuation prediction model.

### Recommended Target

Use:

```text
value_per_area = market_value / Area
```

Then calculate:

```text
predicted_market_value = predicted_value_per_area * Area
```

### Recommended Models

Start with:

1. Linear Regression — baseline.
2. Random Forest — non-linear baseline.
3. XGBoost / LightGBM — recommended final model.

### Feature Groups

Numerical:

```text
Area
Approach_Road_Width
distance_to_nearest_road
distance_to_nearest_facility
facility_count_500m
facility_count_1km
latitude
longitude
```

Categorical:

```text
property_district_Name
PS_Name
Mouza_Name
Road_Name
Zone_no
Proposed_Land_use_Name
Nature_Land_use_Name
Urban
Rural
Road_Category
Flat_or_Land
Litigated_Property
```

### Code Skeleton

```python
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
import numpy as np

target_col = "value_per_area"

numeric_features = [
    "Area",
    "Approach_Road_Width",
    "distance_to_nearest_road",
    "distance_to_nearest_facility",
    "facility_count_500m",
    "facility_count_1km",
    "latitude",
    "longitude"
]

categorical_features = [
    "property_district_Name",
    "PS_Name",
    "Mouza_Name",
    "Road_Name",
    "Zone_no",
    "Proposed_Land_use_Name",
    "Nature_Land_use_Name",
    "Urban",
    "Rural",
    "Road_Category",
    "Flat_or_Land",
    "Litigated_Property"
]

feature_cols = numeric_features + categorical_features

df_model = df.dropna(subset=[target_col])
X = df_model[feature_cols]
y = np.log1p(df_model[target_col])

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

preprocessor = ColumnTransformer(
    transformers=[
        ("num", "passthrough", numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
    ]
)

model = RandomForestRegressor(
    n_estimators=300,
    random_state=42,
    n_jobs=-1
)

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)

pipeline.fit(X_train, y_train)

pred_log = pipeline.predict(X_test)
pred_value_per_area = np.expm1(pred_log)
actual_value_per_area = np.expm1(y_test)

mae = mean_absolute_error(actual_value_per_area, pred_value_per_area)
rmse = mean_squared_error(actual_value_per_area, pred_value_per_area, squared=False)
r2 = r2_score(actual_value_per_area, pred_value_per_area)

print("MAE:", mae)
print("RMSE:", rmse)
print("R2:", r2)
```

### Expected Output

```text
models/valuation_model.pkl
reports/model_metrics.json
```

---

## 10. Phase 7 — Model Evaluation

### Goal

Measure model accuracy and explain performance.

### Metrics

| Metric | Meaning |
|---|---|
| MAE | Average absolute valuation error |
| RMSE | Penalizes large errors |
| MAPE | Average percentage error |
| R² Score | Overall model fit |

### Add MAPE

```python
def mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
```

### Evaluation Outputs

Generate:

1. Predicted vs actual chart.
2. Error distribution.
3. District-wise error.
4. Mouza-wise error.
5. Property-type-wise error.

### Expected Output

```text
reports/model_metrics.json
reports/error_analysis.csv
reports/predicted_vs_actual.png
```

---

## 11. Phase 8 — AI-Based Zone Identification

### Goal

Create AI-generated valuation zones based on spatial and price similarity.

### Inputs

Use:

```text
latitude
longitude
value_per_area
distance_to_nearest_road
distance_to_nearest_facility
facility_count_1km
Urban/Rural
Land use
Road category
```

### Recommended Algorithms

Start with:

1. KMeans
2. DBSCAN
3. HDBSCAN, if available

### Code Skeleton

```python
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

zone_features = [
    "latitude",
    "longitude",
    "value_per_area",
    "distance_to_nearest_road",
    "distance_to_nearest_facility",
    "facility_count_1km"
]

zone_df = df.dropna(subset=zone_features).copy()

scaler = StandardScaler()
X_zone = scaler.fit_transform(zone_df[zone_features])

kmeans = KMeans(n_clusters=10, random_state=42, n_init="auto")
zone_df["ai_zone"] = kmeans.fit_predict(X_zone)

zone_summary = zone_df.groupby("ai_zone").agg(
    avg_value_per_area=("value_per_area", "mean"),
    median_value_per_area=("value_per_area", "median"),
    property_count=("value_per_area", "count")
).reset_index()
```

### Expected Output

```text
data/processed/ai_zones.geojson
reports/zone_summary.csv
```

---

## 12. Phase 9 — Explainability

### Goal

Explain why a property receives a particular valuation.

### Recommended Methods

1. Feature importance from tree-based models.
2. SHAP values for detailed explainability.

### Example Explanation

```text
Predicted value is high because:
- Property is in an urban area.
- It is close to a major road.
- It has high facility density nearby.
- Similar properties in the same mouza show high transaction value.
```

### Expected Output

```text
reports/feature_importance.csv
reports/sample_property_explanations.json
```

---

## 13. Phase 10 — MVDB / Circle Rate Comparison

### Goal

Compare AI-based valuation with current government valuation, if MVDB/circle rate data is available.

### Required Data

```text
MVDB / circle rate dataset
```

### Comparison Table

| Property | Existing MVDB Value | Actual Market Value | AI Predicted Value | AI Error % | MVDB Error % |
|---|---:|---:|---:|---:|---:|

### Outcome

Show whether AI valuation is closer to actual transaction value than existing MVDB value.

### Expected Output

```text
reports/mvdb_comparison.csv
reports/mvdb_vs_ai_summary.json
```

---

## 14. Phase 11 — Dashboard

### Goal

Build a simple PoC dashboard for officials.

### Recommended Tool

```text
Streamlit
```

### Dashboard Pages

1. Data Overview
2. Map View
3. Property Valuation Prediction
4. AI Zones
5. Model Performance
6. Explainability
7. MVDB Comparison, if available

### Minimum Dashboard Features

- Upload/select property.
- Show predicted market value.
- Show actual market value.
- Show prediction error.
- Show AI zone.
- Show nearby roads/facilities.
- Show top valuation factors.
- Show map visualization.

---

## 15. Phase 12 — APIs

### Goal

Expose valuation model through APIs.

### Recommended Framework

```text
FastAPI
```

### APIs

```text
POST /predict-value
GET /zone/{property_id}
GET /valuation-explanation/{property_id}
GET /dashboard-summary
GET /health
```

### Example Input

```json
{
  "district": "Kolkata",
  "mouza_code": "123",
  "area": 500,
  "road_width": 20,
  "land_use": "Residential",
  "flat_or_land": "Land"
}
```

### Example Output

```json
{
  "predicted_market_value": 4500000,
  "predicted_value_per_area": 9000,
  "ai_zone": "AI_ZONE_12",
  "confidence": 0.87,
  "top_factors": [
    "Urban location",
    "Near major road",
    "High-value mouza"
  ]
}
```

---

## 16. Phase 13 — Final Reporting

### Goal

Create an official PoC report.

### Report Sections

1. Executive Summary
2. Data Understanding
3. Data Quality Findings
4. Feature Engineering
5. Model Development
6. Model Accuracy
7. AI Zone Creation
8. Explainability
9. MVDB Comparison
10. Risks and Limitations
11. Recommendations
12. Next Steps

---

## 17. Success Criteria for PoC

The PoC should be considered successful if it demonstrates:

1. Transaction and GIS data can be integrated.
2. AI model can predict property value using available features.
3. AI-generated zones can be visualized on map.
4. Model performance can be measured using actual `market_value`.
5. Key valuation factors can be explained.
6. Output can be shown through a frontend/API.

---

## 18. Key Blockers / Clarifications Required from SPOC

### Data

1. Confirm if `market_value` is the correct target variable.
2. Confirm meaning of `setforth_value`.
3. Provide MVDB / circle rate data for comparison.
4. Confirm if transaction data covers multiple years.
5. Confirm whether data contains all property types or selected categories.

### GIS

1. Confirm CRS/projection of shapefiles.
2. Confirm relationship between transaction records and GIS property records.
3. Confirm join keys between transaction and property GIS data.
4. Confirm whether facilities include category/type fields.
5. Confirm whether road data includes width/category attributes.

### Scope

1. Confirm PoC geography.
2. Confirm property types to include.
3. Confirm whether valuation should be total value or value per unit area.
4. Confirm expected accuracy benchmark.
5. Confirm whether dashboard or API is mandatory for PoC.

### Policy

1. Confirm business rules that must be followed.
2. Confirm if any AI output requires manual approval.
3. Confirm data hosting preference.
4. Confirm data privacy/security requirements.

---

## 19. Recommended PoC Scope

For faster and stronger delivery, start with:

1. One selected district.
2. One or two property types.
3. Clean transaction records with valid `market_value` and `Area`.
4. GIS integration for roads and facilities.
5. Baseline ML model.
6. AI zone clustering.
7. Streamlit dashboard.
8. Final report with metrics.

---

## 20. Codex Task List

### Task 1: Create project structure

Create folders:

```text
data/raw
data/interim
data/processed
notebooks
src
dashboard
models
reports
```

### Task 2: Implement data loader

Create:

```text
src/data_loader.py
```

Functions:

```python
load_transaction_data(path: str) -> pd.DataFrame
load_gis_layer(path: str) -> gpd.GeoDataFrame
```

### Task 3: Implement transaction cleaning

Create:

```text
src/data_cleaning.py
```

Functions:

```python
clean_transactions(df: pd.DataFrame) -> pd.DataFrame
create_value_per_area(df: pd.DataFrame) -> pd.DataFrame
remove_outliers(df: pd.DataFrame, column: str) -> pd.DataFrame
```

### Task 4: Implement GIS processing

Create:

```text
src/gis_processing.py
```

Functions:

```python
validate_crs(gdf: gpd.GeoDataFrame) -> None
convert_crs(gdf: gpd.GeoDataFrame, target_crs: str) -> gpd.GeoDataFrame
fix_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame
```

### Task 5: Implement data merge

Create:

```text
src/feature_engineering.py
```

Functions:

```python
merge_transaction_with_property_gis(
    tran_df: pd.DataFrame,
    property_gdf: gpd.GeoDataFrame,
    join_keys: list[str]
) -> gpd.GeoDataFrame
```

### Task 6: Implement spatial features

Add functions:

```python
add_nearest_road_distance(property_gdf, road_gdf)
add_nearest_facility_distance(property_gdf, facilities_gdf)
add_facility_counts(property_gdf, facilities_gdf, radius_meters)
add_centroid_lat_long(property_gdf)
```

### Task 7: Implement model training

Create:

```text
src/model_training.py
```

Functions:

```python
prepare_features(df: pd.DataFrame)
train_baseline_model(df: pd.DataFrame)
evaluate_model(model, X_test, y_test)
save_model(model, path: str)
```

### Task 8: Implement zone clustering

Create:

```text
src/zone_clustering.py
```

Functions:

```python
create_ai_zones(df: pd.DataFrame, n_clusters: int)
generate_zone_summary(df: pd.DataFrame)
```

### Task 9: Implement explainability

Create:

```text
src/explainability.py
```

Functions:

```python
get_feature_importance(model)
generate_property_explanation(property_record, prediction, feature_importance)
```

### Task 10: Implement dashboard

Create:

```text
frontend/app.py
```

Include:

1. Dataset overview.
2. Map visualization.
3. Prediction result.
4. AI zones.
5. Feature importance.
6. Model metrics.

### Task 11: Implement API

Create:

```text
src/api.py
```

Use FastAPI.

Endpoints:

```text
GET /health
POST /predict-value
GET /dashboard-summary
```

### Task 12: Generate final report

Create:

```text
reports/final_poc_report.md
```

Include:

1. Data summary.
2. Cleaning summary.
3. Features used.
4. Model metrics.
5. Zone summary.
6. Limitations.
7. Next steps.

---

## 21. Suggested Requirements

```text
pandas
numpy
geopandas
shapely
pyproj
fiona
openpyxl
scikit-learn
xgboost
lightgbm
joblib
matplotlib
plotly
streamlit
fastapi
uvicorn
shap
```

---

## 22. Initial Command Flow

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt

python src/data_loader.py
python src/data_cleaning.py
python src/gis_processing.py
python src/feature_engineering.py
python src/model_training.py
python src/zone_clustering.py

streamlit run frontend/app.py

uvicorn backend.src.api:app --reload
```

---

## 23. Final Output Expected from PoC

The final PoC should produce:

1. Cleaned dataset.
2. Feature-engineered model dataset.
3. Trained valuation prediction model.
4. Model accuracy report.
5. AI-generated valuation zones.
6. Feature importance report.
7. Dashboard for visualization.
8. API for prediction.
9. Final PoC report.

---

## 24. Final Summary

This PoC solves the valuation problem by combining:

1. Transaction-level property data.
2. GIS-based spatial property data.
3. Road connectivity data.
4. Facilities/amenities data.
5. Machine learning valuation model.
6. AI-based zoning.
7. Explainability and validation.

The recommended first implementation should focus on predicting `value_per_area`, generating AI zones, and demonstrating results through a simple dashboard.
