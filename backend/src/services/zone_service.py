from __future__ import annotations

from typing import Any

from backend.src.services.artifact_service import load_zone_assignments, load_zone_polygons, load_zone_summary, normalize_for_json


def get_zone_summary_records() -> list[dict[str, Any]]:
    """Return zone summary records. value_per_area is already in ₹/sqft
    (standardized in data_cleaning.py), so no unit conversion is needed here."""
    rows = []
    for record in load_zone_summary().to_dict(orient='records'):
        # Expose median_value_per_area directly as median_value_per_sqft for
        # the frontend (already standardized to ₹/sqft by the pipeline).
        record['median_value_per_sqft'] = record.get('median_value_per_area')
        record['avg_value_per_sqft'] = record.get('avg_value_per_area')
        rows.append(normalize_for_json(record))
    return rows


def get_zone_geojson() -> dict[str, Any]:
    """Return GeoJSON with per-sqft metrics embedded in each zone polygon."""
    summary_df = load_zone_summary().set_index('ai_zone')
    polygons = load_zone_polygons().copy()

    polygons['median_value_per_sqft'] = polygons['ai_zone'].map(
        lambda z: summary_df.loc[z, 'median_value_per_area'] if z in summary_df.index else None
    )
    polygons['avg_value_per_sqft'] = polygons['ai_zone'].map(
        lambda z: summary_df.loc[z, 'avg_value_per_area'] if z in summary_df.index else None
    )
    return normalize_for_json(polygons.to_crs('EPSG:4326').__geo_interface__)


def get_zone_by_id(zone_id: str) -> dict[str, Any]:
    summary_df = load_zone_summary()
    matches = summary_df.loc[summary_df['ai_zone'] == zone_id]
    if matches.empty:
        raise KeyError(zone_id)
    summary_payload = matches.iloc[0].to_dict()
    summary_payload['median_value_per_sqft'] = summary_payload.get('median_value_per_area')
    summary_payload['avg_value_per_sqft'] = summary_payload.get('avg_value_per_area')

    assignment_df = load_zone_assignments()
    summary_payload['assignment_count'] = int((assignment_df['ai_zone'] == zone_id).sum())
    return normalize_for_json(summary_payload)
