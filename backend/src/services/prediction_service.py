from __future__ import annotations

from typing import Any

from backend.src.services.artifact_service import load_predictions, normalize_for_json
from backend.src.utils.area_units import area_to_sqft, area_unit_label, value_per_area_to_sqft

SUMMARY_COLUMNS = [
    'property_id',
    'query_year',
    'query_no',
    'Deed_No',
    'Deed_Year',
    'sl_no_Property',
    'property_district_Name',
    'PS_Name',
    'Mouza_Name',
    'Road_Name',
    'Zone_no',
    'Flat_or_Land',
    'Area',
    'Types of area Measurement',
    'actual_value_per_area',
    'predicted_value_per_area',
    'actual_market_value_from_target',
    'predicted_market_value',
    'absolute_error_value_per_area',
    'absolute_error_market_value',
    'ai_zone',
    'ai_zone_name',
]


def _replace_nan(value: Any) -> Any:
    return normalize_for_json(value)


def list_properties(limit: int = 25, district: str | None = None, mouza: str | None = None) -> list[dict[str, Any]]:
    df = load_predictions().copy()
    if district:
        df = df.loc[df['property_district_Name'].astype(str).str.lower() == district.lower()]
    if mouza:
        df = df.loc[df['Mouza_Name'].astype(str).str.lower() == mouza.lower()]
    if 'Types of area Measurement' in df.columns:
        df['predicted_value_per_sqft_display'] = df.apply(
            lambda row: value_per_area_to_sqft(row.get('predicted_value_per_area'), row.get('Types of area Measurement')),
            axis=1,
        )
        sort_column = 'predicted_value_per_sqft_display'
    else:
        sort_column = 'predicted_value_per_area'
    df = df.sort_values(sort_column, ascending=False).head(limit)
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        payload = {column: _replace_nan(row[column]) for column in SUMMARY_COLUMNS if column in row.index}
        payload.update(_build_display_metrics(payload))
        rows.append(payload)
    return rows


def get_property_by_id(property_id: str) -> dict[str, Any]:
    df = load_predictions()
    matches = df.loc[df['property_id'] == property_id]
    if matches.empty:
        raise KeyError(property_id)
    row = matches.iloc[0]
    payload = {column: _replace_nan(row[column]) for column in row.index}
    payload.update(_build_display_metrics(payload))
    return payload


def _build_display_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    measurement = payload.get('Types of area Measurement')
    area = payload.get('Area')
    predicted_value_per_area = payload.get('predicted_value_per_area')
    actual_value_per_area = payload.get('actual_value_per_area')
    absolute_error_value_per_area = payload.get('absolute_error_value_per_area')

    return {
        'area_measurement_label': area_unit_label(measurement),
        'area_sqft': normalize_for_json(area_to_sqft(area, measurement)),
        'predicted_value_per_sqft': normalize_for_json(value_per_area_to_sqft(predicted_value_per_area, measurement)),
        'actual_value_per_sqft': normalize_for_json(value_per_area_to_sqft(actual_value_per_area, measurement)),
        'absolute_error_value_per_sqft': normalize_for_json(value_per_area_to_sqft(absolute_error_value_per_area, measurement)),
    }
