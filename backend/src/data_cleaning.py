from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)

NUMERIC_COLUMNS = [
    "market_value",
    "setforth_value",
    "Area",
    "Approach_Road_Width",
]
CATEGORICAL_COLUMNS = [
    "Road_Name",
    "Zone_no",
    "Urban",
    "Rural",
    "Proposed_Land_use_Name",
    "Nature_Land_use_Name",
    "Flat_or_Land",
    "Road_Category",
    "Is_Property_on_Road",
    "Adjacent_to_Metal_Road",
    "Area_type",
    "Types of area Measurement",
]

# Conversion factors from various units → Square Feet (West Bengal standards)
AREA_TO_SQFT: dict[str, float] = {
    "decimal":   435.6,    # 1 Decimal = 435.6 Sq Ft  (WB standard)
    "sq ft":     1.0,
    "sq. ft":    1.0,
    "sqft":      1.0,
    "sq ft.":    1.0,
    "sq. ft.":   1.0,
    "sq m":      10.7639,  # 1 Sq Metre = 10.7639 Sq Ft
    "sq. m":     10.7639,
    "sq meter":  10.7639,
    "sq metre":  10.7639,
    "sq. meter": 10.7639,
    "sq mt":     10.7639,
    "sq yd":     9.0,      # 1 Sq Yard = 9 Sq Ft
    "sq yard":   9.0,
    "sq. yard":  9.0,
    "sq. yd":    9.0,
    "katha":     720.0,    # 1 Katha (WB) = 720 Sq Ft
    "cottah":    720.0,
    "bigha":     14400.0,  # 1 Bigha (WB) = 20 Katha = 14400 Sq Ft
    "acre":      43560.0,
    "hectare":   107639.0,
}


@dataclass(frozen=True)
class CleaningSummary:
    input_row_count: int
    duplicate_rows_removed: int
    invalid_market_value_rows_removed: int
    invalid_area_rows_removed: int
    outliers_removed: int
    rows_with_value_per_area: int
    output_row_count: int
    missing_after_cleaning: dict[str, int]


def _coerce_numeric_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    cleaned = (
        series.astype("string")
        .str.replace(",", "", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    cleaned = cleaned.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "NULL": pd.NA})
    return pd.to_numeric(cleaned, errors="coerce")


def _standardize_categorical_series(series: pd.Series) -> pd.Series:
    standardized = series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    return standardized.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "NULL": pd.NA})


def clean_transaction_data(transactions: pd.DataFrame) -> tuple[pd.DataFrame, CleaningSummary]:
    cleaned = transactions.copy()
    input_row_count = int(len(cleaned))

    duplicate_rows_removed = int(cleaned.duplicated().sum())
    if duplicate_rows_removed:
        cleaned = cleaned.drop_duplicates().copy()

    for column in NUMERIC_COLUMNS:
        if column in cleaned.columns:
            cleaned[column] = _coerce_numeric_series(cleaned[column])
        else:
            LOGGER.warning("Expected numeric column '%s' was not found in the transaction data", column)

    for column in CATEGORICAL_COLUMNS:
        if column in cleaned.columns:
            cleaned[column] = _standardize_categorical_series(cleaned[column])

    invalid_market_mask = cleaned["market_value"].isna() | (cleaned["market_value"] <= 0)
    invalid_market_value_rows_removed = int(invalid_market_mask.sum())
    cleaned = cleaned.loc[~invalid_market_mask].copy()

    invalid_area_mask = cleaned["Area"].isna() | (cleaned["Area"] <= 0)
    invalid_area_rows_removed = int(invalid_area_mask.sum())
    cleaned = cleaned.loc[~invalid_area_mask].copy()

    # Standardize Area → Square Feet using the 'Types of area Measurement' column.
    # This ensures value_per_area is universally ₹/sqft for all property types.
    if "Types of area Measurement" in cleaned.columns:
        unit_col = cleaned["Types of area Measurement"].astype(str).str.strip().str.lower()
        conversion_factors = unit_col.map(AREA_TO_SQFT).fillna(1.0)
        unrecognised = unit_col[~unit_col.isin(AREA_TO_SQFT)].value_counts()
        if not unrecognised.empty:
            LOGGER.warning("Unrecognised area units (defaulting to no conversion): %s", unrecognised.to_dict())
        cleaned = cleaned.copy()
        cleaned["Area"] = cleaned["Area"] * conversion_factors
        LOGGER.info(
            "Area standardized to Sq Ft. Unit breakdown: %s",
            dict(unit_col.value_counts()),
        )
    else:
        LOGGER.warning("'Types of area Measurement' column not found — Area units NOT standardized to Sq Ft")

    cleaned["value_per_area"] = cleaned["market_value"] / cleaned["Area"]
    cleaned = cleaned.replace([np.inf, -np.inf], pd.NA).dropna(subset=["value_per_area"])

    # Outlier Trimming: Remove top 1% and bottom 1% per Flat_or_Land segment
    # (1% trim tested to be better than 2% in notebooks/09_trim_tuning_and_cross_validation.ipynb)
    trimmed_dfs = []
    outliers_removed = 0
    for segment in cleaned["Flat_or_Land"].fillna("Missing").unique():
        segment_mask = cleaned["Flat_or_Land"].fillna("Missing") == segment
        segment_df = cleaned[segment_mask]

        lower_bound = segment_df["value_per_area"].quantile(0.01)
        upper_bound = segment_df["value_per_area"].quantile(0.99)

        valid_mask = (segment_df["value_per_area"] >= lower_bound) & (segment_df["value_per_area"] <= upper_bound)
        trimmed_dfs.append(segment_df[valid_mask])
        outliers_removed += int((~valid_mask).sum())

    cleaned = pd.concat(trimmed_dfs)

    cleaned["log_value_per_area"] = np.log1p(cleaned["value_per_area"])
    cleaned = cleaned.convert_dtypes()

    summary = CleaningSummary(
        input_row_count=input_row_count,
        duplicate_rows_removed=duplicate_rows_removed,
        invalid_market_value_rows_removed=invalid_market_value_rows_removed,
        invalid_area_rows_removed=invalid_area_rows_removed,
        outliers_removed=outliers_removed,
        rows_with_value_per_area=int(cleaned["value_per_area"].notna().sum()),
        output_row_count=int(len(cleaned)),
        missing_after_cleaning={column: int(value) for column, value in cleaned.isna().sum().items() if int(value) > 0},
    )
    return cleaned, summary


def save_cleaned_transactions(
    cleaned_transactions: pd.DataFrame,
    summary: CleaningSummary,
    interim_dir: Path,
    reports_dir: Path,
) -> tuple[Path, Path]:
    interim_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = interim_dir / "cleaned_transactions.parquet"
    summary_path = reports_dir / "phase_2_transaction_cleaning_summary.json"

    cleaned_transactions.to_parquet(parquet_path, index=False)
    summary_path.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")

    LOGGER.info("Saved cleaned transactions to %s", parquet_path)
    LOGGER.info("Saved cleaning summary to %s", summary_path)
    return parquet_path, summary_path
