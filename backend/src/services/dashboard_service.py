from __future__ import annotations

from typing import Any

from backend.src.services.artifact_service import (
    load_error_analysis,
    load_explainability_summary,
    load_model_comparison,
    load_model_metrics,
    load_mvdb_summary,
    load_predictions,
    load_zone_clustering_summary,
)


def _build_property_type_analysis() -> list[dict[str, Any]]:
    error_df = load_error_analysis()
    property_type_df = error_df.loc[error_df['level'] == 'property_type'].copy()
    if property_type_df.empty:
        return []
    property_type_df = property_type_df.sort_values('group_name').reset_index(drop=True)
    return property_type_df.to_dict(orient='records')


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
        'mvdb_status': mvdb.get('status', 'not_run'),
    }
