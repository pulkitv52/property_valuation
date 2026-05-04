# AGENTS.md — AI Property Valuation PoC (Use Case 1)

---

# ⚠️ CORE INSTRUCTION (READ FIRST)

This project is primarily an **AI/ML + GIS system**.

> ❗ Build **data pipelines and ML models FIRST**, then APIs and UI.

---

# 🎯 OBJECTIVE

Build a PoC system that:

1. Predicts **property market value**
2. Creates **AI-based valuation zones**
3. Explains **factors affecting valuation**
4. Validates predictions using real transaction data

---

# 🧠 PROBLEM FORMULATION

We solve:

### 1. Price Prediction (Supervised ML)

```text
value_per_area = market_value / Area
```

Model learns:

```text
value_per_area = f(location + area + road + facilities + land_use)
```

---

### 2. Zone Creation (Clustering)

* Group similar valuation regions
* Based on spatial + pricing patterns

---

### 3. Explainability

* Identify why a property is priced high/low

---

# 📊 DATA CONTEXT

## Transaction Dataset (Primary)

Contains:

* `market_value` → target
* `Area`
* `Road_Name`, `Zone_no`
* `Urban/Rural`
* `Land_use`
* Legal/property attributes

---

## GIS Datasets

### Property Layer

* Geometry (polygons/points)

### Road Network

* Connectivity

### Facilities

* Schools, hospitals, amenities

---

# 🚀 EXECUTION PLAN (STRICT)

Follow **use_case_1_property_valuation_implementation_plan.md**

### Mandatory order:

1. Data Understanding
2. Data Cleaning
3. GIS Processing
4. Data Merge
5. Feature Engineering
6. Model Training
7. Evaluation
8. Zone Clustering
9. Explainability
10. API
11. Dashboard

👉 Do NOT change order
👉 Do NOT skip phases

---

# 🏗️ MODULES TO BUILD

## Data Layer

* `data_loader.py`
* `data_cleaning.py`

## GIS Layer

* `gis_processing.py`

## Feature Engineering

* `feature_engineering.py`

## ML Layer

* `model_training.py`
* `evaluation.py`

## Clustering

* `zone_clustering.py`

## Explainability

* `explainability.py`

## Interface

* `api.py`
* `frontend/app.py`

---

# ⚙️ ML REQUIREMENTS

## Target

Always use:

```text
value_per_area = market_value / Area
```

---

## Features (MANDATORY)

### Spatial Features

* distance_to_nearest_road
* distance_to_nearest_facility
* facility_count (500m / 1km)

### Property Features

* Area
* Land use
* Flat_or_Land
* Urban/Rural

### Infrastructure Features

* Road width
* Road category
* Connectivity

---

## GIS RULES

* ❗ Always use projected CRS (not lat/lon) for distance
* Use spatial joins where needed
* Fix invalid geometries

---

# 🧪 MODELING RULES

* Start with RandomForest
* Then optionally use XGBoost / LightGBM
* Use log transformation:

```text
log1p(value_per_area)
```

---

# 📊 EVALUATION METRICS

* MAE
* RMSE
* MAPE
* R²

---

# 📦 OUTPUTS REQUIRED

* Trained model
* Model metrics
* Predicted vs actual values
* AI zones
* Feature importance
* Dashboard
* API

---

# ❌ WHAT NOT TO DO

* Do NOT start frontend first
* Do NOT skip feature engineering
* Do NOT treat as CRUD system
* Do NOT ignore GIS
* Do NOT directly predict raw `market_value`

---

# 🧠 ENGINEERING STANDARDS

## General

* Use `.env`
* No hardcoded secrets
* Modular code
* Logging enabled

## Python

* Type hints
* Clean structure
* Reusable functions

## ML

* Save intermediate datasets
* Ensure reproducibility
* Handle missing values properly

---

# 🔁 WORKFLOW RULE

At every step:

1. Read implementation plan
2. Implement phase completely
3. Save outputs
4. Move to next phase

---

# 🚀 HOW TO EXECUTE

Start with:

> Phase 1: Data Loading & Understanding

Then proceed step-by-step.

---

# 🔥 FINAL RULE

> This is a **data + ML system first**, not an application.

---

# END
