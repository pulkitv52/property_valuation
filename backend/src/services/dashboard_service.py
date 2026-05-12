from __future__ import annotations

from typing import Any

from backend.src.services.artifact_service import (
    load_error_analysis,
    load_explainability_summary,
    load_model_comparison,
    load_model_metrics,
    load_mvdb_summary,
    load_predictions,
    load_zone_assignments,
    load_zone_clustering_summary,
    load_zone_summary,
    normalize_for_json,
)


import numpy as np


def _build_property_type_analysis() -> list[dict[str, Any]]:
    error_df = load_error_analysis()
    property_type_df = error_df.loc[error_df['level'] == 'property_type'].copy()
    if property_type_df.empty:
        return []
    property_type_df = property_type_df.sort_values('group_name').reset_index(drop=True)
    return property_type_df.to_dict(orient='records')


def _resolve_zone_names(predictions_df):
    df = predictions_df.copy()

    zone_summary_df = load_zone_summary().copy()

    if 'property_id' in df.columns:
        zone_assignments_df = load_zone_assignments()
        zone_assignment_columns = [column for column in ['property_id', 'ai_zone', 'ai_zone_name'] if column in zone_assignments_df.columns]
        if 'property_id' in zone_assignment_columns and len(zone_assignment_columns) > 1:
            zone_lookup = zone_assignments_df[zone_assignment_columns].drop_duplicates(subset=['property_id'])
            merged = df.merge(zone_lookup, on='property_id', how='left', suffixes=('', '_from_assignment'))
            if 'ai_zone_from_assignment' in merged.columns:
                if 'ai_zone' in merged.columns:
                    merged['ai_zone'] = merged['ai_zone'].fillna(merged['ai_zone_from_assignment'])
                else:
                    merged['ai_zone'] = merged['ai_zone_from_assignment']
                merged = merged.drop(columns=['ai_zone_from_assignment'])
            if 'ai_zone_name_from_assignment' in merged.columns:
                if 'ai_zone_name' in merged.columns:
                    merged['ai_zone_name'] = merged['ai_zone_name'].fillna(merged['ai_zone_name_from_assignment'])
                else:
                    merged['ai_zone_name'] = merged['ai_zone_name_from_assignment']
                merged = merged.drop(columns=['ai_zone_name_from_assignment'])
            df = merged

    if ('ai_zone_name' not in df.columns or not df['ai_zone_name'].notna().any()) and 'ai_zone' in df.columns:
        if {'ai_zone', 'ai_zone_name'}.issubset(zone_summary_df.columns):
            zone_lookup = zone_summary_df[['ai_zone', 'ai_zone_name']].drop_duplicates(subset=['ai_zone'])
            merged = df.merge(zone_lookup, on='ai_zone', how='left', suffixes=('', '_from_zone'))
            if 'ai_zone_name_from_zone' in merged.columns:
                if 'ai_zone_name' in merged.columns:
                    merged['ai_zone_name'] = merged['ai_zone_name'].fillna(merged['ai_zone_name_from_zone'])
                else:
                    merged['ai_zone_name'] = merged['ai_zone_name_from_zone']
                merged = merged.drop(columns=['ai_zone_name_from_zone'])
            df = merged

    if ('ai_zone' not in df.columns or not df['ai_zone'].notna().any()) and 'ai_zone_name' in df.columns:
        if {'ai_zone', 'ai_zone_name'}.issubset(zone_summary_df.columns):
            zone_lookup = zone_summary_df[['ai_zone_name', 'ai_zone']].drop_duplicates(subset=['ai_zone_name'])
            merged = df.merge(zone_lookup, on='ai_zone_name', how='left', suffixes=('', '_from_zone_name'))
            if 'ai_zone_from_zone_name' in merged.columns:
                if 'ai_zone' in merged.columns:
                    merged['ai_zone'] = merged['ai_zone'].fillna(merged['ai_zone_from_zone_name'])
                else:
                    merged['ai_zone'] = merged['ai_zone_from_zone_name']
                merged = merged.drop(columns=['ai_zone_from_zone_name'])
            df = merged

    return df


def _build_zone_property_type_analysis() -> list[dict[str, Any]]:
    predictions_df = load_predictions()
    df = _resolve_zone_names(predictions_df)
    zone_summary_df = load_zone_summary().copy()
    zone_mix_lookup: dict[str, dict[str, Any]] = {}
    if 'ai_zone' in zone_summary_df.columns:
        for record in zone_summary_df.to_dict(orient='records'):
            zone_id = record.get('ai_zone')
            if zone_id is None:
                continue
            flat_share = record.get('flat_share')
            flat_share_value = float(flat_share) if flat_share is not None else np.nan
            land_share_value = float(1.0 - flat_share_value) if not np.isnan(flat_share_value) else np.nan
            zone_mix_lookup[str(zone_id)] = {
                'zone_label': record.get('ai_zone_name'),
                'flat_share': flat_share_value,
                'land_share': land_share_value,
            }

    # Filter out missing data
    df = df.dropna(subset=['ai_zone', 'ai_zone_name', 'Flat_or_Land', 'actual_value_per_area', 'predicted_value_per_area'])

    # Group and aggregate
    grouped = df.groupby(['ai_zone', 'ai_zone_name', 'Flat_or_Land'])

    results = []
    for (zone_id, zone_name, prop_type), group in grouped:
        actual = group['actual_value_per_area'].to_numpy(dtype=float)
        predicted = group['predicted_value_per_area'].to_numpy(dtype=float)

        # Calculate MAPE (Avg. Deviation)
        mask = actual != 0
        mape = float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100) if mask.any() else 0
        zone_meta = zone_mix_lookup.get(str(zone_id), {})

        results.append({
            'zone_id': zone_id,
            'zone_name': zone_name,
            'zone_label': zone_meta.get('zone_label', zone_name),
            'property_type': prop_type,
            'count': int(len(group)),
            'mape': mape,
            'mean_actual': float(np.mean(actual)),
            'mean_predicted': float(np.mean(predicted)),
            'flat_share': zone_meta.get('flat_share'),
            'land_share': zone_meta.get('land_share'),
        })

    sorted_results = sorted(results, key=lambda x: (x['zone_id'], x['property_type']))
    return normalize_for_json(sorted_results)


def get_dashboard_summary() -> dict[str, Any]:
    predictions_df = load_predictions()
    metrics = load_model_metrics()
    comparison = load_model_comparison()
    explainability = load_explainability_summary()
    zones = load_zone_clustering_summary()
    mvdb = load_mvdb_summary()
    return {
        'property_count': int(len(predictions_df)),
        'best_candidate_name': comparison['best_candidate_name'],
        'metrics': metrics,
        'zones': zones,
        'explainability': explainability,
        'property_type_analysis': _build_property_type_analysis(),
        'zone_property_type_analysis': _build_zone_property_type_analysis(),
        'mvdb_status': mvdb.get('status', 'not_run'),
    }
