from __future__ import annotations

from typing import Any

import pandas as pd

from backend.src.explainability import generate_property_explanation
from backend.src.services.artifact_service import (
    load_feature_importance,
    load_model,
    load_predictions,
    load_sample_property_explanations,
    normalize_for_json,
)
from backend.src.utils.area_units import area_unit_label, value_per_area_to_sqft


def get_global_feature_importance(limit: int = 25) -> list[dict[str, Any]]:
    df = load_feature_importance()
    global_df = df.loc[df['segment_value'] == 'GLOBAL'].head(limit)
    return [normalize_for_json(record) for record in global_df.to_dict(orient='records')]


def get_sample_explanations() -> list[dict[str, Any]]:
    return normalize_for_json(load_sample_property_explanations())


def get_property_explanation(property_id: str) -> dict[str, Any]:
    predictions_df = load_predictions()
    matches = predictions_df.loc[predictions_df['property_id'] == property_id]
    if matches.empty:
        raise KeyError(property_id)
    row = matches.iloc[0]
    model = load_model()
    feature_importance = load_feature_importance()
    measurement = row.get('Types of area Measurement')
    payload = generate_property_explanation(
        property_record=row,
        prediction=float(row['predicted_value_per_area']),
        actual_value_per_area=float(row['actual_value_per_area']) if pd.notna(row['actual_value_per_area']) else None,
        feature_importance=feature_importance,
        model=model,
    )
    payload['area_measurement_label'] = area_unit_label(measurement)
    payload['predicted_value_per_sqft'] = value_per_area_to_sqft(payload.get('predicted_value_per_area'), measurement)
    payload['actual_value_per_sqft'] = value_per_area_to_sqft(payload.get('actual_value_per_area'), measurement)
    return normalize_for_json(payload)
