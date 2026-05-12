from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backend.src.services.artifact_service import load_model, load_zone_assignments
from backend.src.utils.area_units import area_to_sqft
from backend.src.zone_clustering import ZONE_LABELS

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class InferenceSummary:
    input_row_count: int
    output_row_count: int
    model_path: str
    zone_assignment_mode: str
    rows_with_zone_assignment: int


def _required_input_columns(model: Any) -> list[str]:
    columns: list[str] = []
    if hasattr(model, "fallback_feature_inputs_"):
        columns.extend(getattr(model, "fallback_feature_inputs_"))
    if hasattr(model, "segment_feature_inputs_"):
        for segment_columns in getattr(model, "segment_feature_inputs_").values():
            columns.extend(segment_columns)
    unique_columns = list(dict.fromkeys(columns))
    return unique_columns


def _coerce_area_numeric(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    if "Area" in working.columns:
        working["Area"] = pd.to_numeric(working["Area"], errors="coerce")
    return working


def _prepare_model_inputs(raw_df: pd.DataFrame, model: Any) -> pd.DataFrame:
    required_columns = _required_input_columns(model)
    if not required_columns:
        raise ValueError("Could not infer required model input columns from model artifact")

    model_input = raw_df.copy()
    for column in required_columns:
        if column not in model_input.columns:
            model_input[column] = np.nan
    return model_input[required_columns].copy()


def _nearest_zone_for_rows(df: pd.DataFrame) -> pd.DataFrame:
    if "latitude" not in df.columns or "longitude" not in df.columns:
        result = df.copy()
        result["ai_zone"] = None
        result["ai_zone_name"] = None
        result["ai_zone_description"] = None
        return result

    zone_df = load_zone_assignments().copy()
    if "latitude" not in zone_df.columns or "longitude" not in zone_df.columns:
        result = df.copy()
        result["ai_zone"] = None
        result["ai_zone_name"] = None
        result["ai_zone_description"] = None
        return result

    zone_points = zone_df[["ai_zone", "latitude", "longitude"]].copy()
    zone_points["latitude"] = pd.to_numeric(zone_points["latitude"], errors="coerce")
    zone_points["longitude"] = pd.to_numeric(zone_points["longitude"], errors="coerce")
    zone_points = zone_points.dropna(subset=["latitude", "longitude", "ai_zone"])
    if zone_points.empty:
        result = df.copy()
        result["ai_zone"] = None
        result["ai_zone_name"] = None
        result["ai_zone_description"] = None
        return result

    unique_points = zone_points.groupby("ai_zone", as_index=False)[["latitude", "longitude"]].median()
    zone_ids = unique_points["ai_zone"].to_numpy()
    zone_lat = unique_points["latitude"].to_numpy(dtype=float)
    zone_lon = unique_points["longitude"].to_numpy(dtype=float)

    result = df.copy()
    row_lat = pd.to_numeric(result["latitude"], errors="coerce").to_numpy(dtype=float)
    row_lon = pd.to_numeric(result["longitude"], errors="coerce").to_numpy(dtype=float)
    nearest_zone: list[str | None] = []

    for lat, lon in zip(row_lat, row_lon, strict=False):
        if np.isnan(lat) or np.isnan(lon):
            nearest_zone.append(None)
            continue
        dist = np.sqrt((zone_lat - lat) ** 2 + (zone_lon - lon) ** 2)
        idx = int(np.argmin(dist))
        nearest_zone.append(str(zone_ids[idx]))

    result["ai_zone"] = nearest_zone
    result["ai_zone_name"] = result["ai_zone"].map(lambda value: ZONE_LABELS.get(value, (None, None))[0])
    result["ai_zone_description"] = result["ai_zone"].map(lambda value: ZONE_LABELS.get(value, (None, None))[1])
    return result


def run_inference(input_df: pd.DataFrame) -> tuple[pd.DataFrame, InferenceSummary]:
    if input_df.empty:
        raise ValueError("Input dataframe is empty")

    model = load_model()
    working = _coerce_area_numeric(input_df)
    model_input = _prepare_model_inputs(working, model)

    pred_log = model.predict(model_input)
    pred_value_per_area = np.expm1(pred_log)
    output = working.copy()
    output["predicted_value_per_area"] = pred_value_per_area

    if "Types of area Measurement" in output.columns and "Area" in output.columns:
        output["area_sqft"] = output.apply(
            lambda row: area_to_sqft(row.get("Area"), row.get("Types of area Measurement")),
            axis=1,
        )
        output["predicted_market_value"] = output["predicted_value_per_area"] * pd.to_numeric(
            output["area_sqft"], errors="coerce"
        )
    elif "Area" in output.columns:
        output["area_sqft"] = pd.to_numeric(output["Area"], errors="coerce")
        output["predicted_market_value"] = output["predicted_value_per_area"] * output["area_sqft"]
    else:
        output["area_sqft"] = np.nan
        output["predicted_market_value"] = np.nan

    output = _nearest_zone_for_rows(output)
    rows_with_zone_assignment = int(output["ai_zone"].notna().sum()) if "ai_zone" in output.columns else 0
    summary = InferenceSummary(
        input_row_count=int(len(input_df)),
        output_row_count=int(len(output)),
        model_path=str(Path("models") / "valuation_model.pkl"),
        zone_assignment_mode="nearest_zone_median_latlon",
        rows_with_zone_assignment=rows_with_zone_assignment,
    )
    LOGGER.info(
        "Inference complete: input_rows=%s output_rows=%s zone_assigned=%s",
        summary.input_row_count,
        summary.output_row_count,
        summary.rows_with_zone_assignment,
    )
    return output, summary

