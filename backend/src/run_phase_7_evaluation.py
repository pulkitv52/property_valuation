from __future__ import annotations

import json
import logging
from pathlib import Path

import geopandas as gpd

from backend.src.config import configure_logging, ensure_directories, settings
from backend.src.evaluation import build_error_analysis, cross_validate_model, evaluate_model, save_evaluation_outputs
from backend.src.model_training import parse_candidate_label, train_model_candidate

LOGGER = logging.getLogger(__name__)



def _resolve_selected_candidate(reports_dir: Path) -> tuple[str, str, str | None, str | None, int | None]:
    comparison_path = reports_dir / 'model_comparison.json'
    if comparison_path.exists():
        comparison = json.loads(comparison_path.read_text(encoding='utf-8'))
        best_candidate_name = comparison['best_candidate_name']
        candidate_metadata = {
            candidate['candidate_name']: (
                candidate.get('segment_column'),
                candidate.get('segment_value'),
                candidate.get('max_training_sample_size'),
            )
            for candidate in comparison.get('candidates', [])
        }
        candidate_name, subset_mode, segment_column, segment_value = parse_candidate_label(best_candidate_name)
        stored_segment_column, stored_segment_value, max_training_sample_size = candidate_metadata.get(
            best_candidate_name,
            (segment_column, segment_value, None),
        )
        return (
            candidate_name,
            subset_mode,
            stored_segment_column if stored_segment_column is not None else segment_column,
            stored_segment_value if stored_segment_value is not None else segment_value,
            max_training_sample_size,
        )

    summary_path = reports_dir / 'model_training_summary.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    model_name = summary['model_name']
    subset_mode = summary.get('subset_mode', 'full')

    model_lookup = {
        'RandomForestRegressor': 'random_forest',
        'ExtraTreesRegressor': 'extra_trees',
        'HistGradientBoostingRegressor': 'hist_gradient_boosting',
        'XGBRegressor': 'xgboost_deep',
        'LGBMRegressor': 'lightgbm',
        'SegmentedXGBRegressor': 'xgboost_deep_segmented',
    }
    if model_name not in model_lookup:
        raise ValueError(f'Unsupported model_name in summary: {model_name}')
    return (
        model_lookup[model_name],
        subset_mode,
        summary.get('segment_column'),
        summary.get('segment_value'),
        summary.get('max_training_sample_size'),
    )



def main() -> None:
    configure_logging()
    ensure_directories()

    training_gdf = gpd.read_parquet(settings.processed_data_dir / 'model_training_dataset.parquet')
    candidate_name, subset_mode, segment_column, segment_value, max_training_sample_size = _resolve_selected_candidate(settings.reports_dir)
    LOGGER.info(
        'Evaluating selected candidate %s on subset %s segment %s=%s',
        candidate_name,
        subset_mode,
        segment_column,
        segment_value,
    )

    artifacts = train_model_candidate(
        training_gdf,
        candidate_name=candidate_name,
        subset_mode=subset_mode,
        segment_column=segment_column,
        segment_value=segment_value,
        max_training_sample_size=max_training_sample_size,
    )
    summary, predictions_df = evaluate_model(
        artifacts.pipeline,
        training_gdf,
        subset_mode=subset_mode,
        segment_column=segment_column,
        segment_value=segment_value,
        evaluation_model_source=f'retrained_in_environment:{candidate_name}:{subset_mode}:{segment_column}:{segment_value}',
    )
    error_analysis_df = build_error_analysis(predictions_df)
    metrics_path, error_analysis_path, plot_path, predictions_path = save_evaluation_outputs(
        summary,
        predictions_df,
        error_analysis_df,
        settings.reports_dir,
        settings.processed_data_dir,
    )

    # --- K-Fold Cross-Validation ---
    LOGGER.info('Running 5-Fold Cross-Validation on best candidate...')
    cv_summary = cross_validate_model(
        training_gdf,
        candidate_name=candidate_name,
        subset_mode=subset_mode,
        segment_column=segment_column,
        segment_value=segment_value,
        n_splits=5,
        max_training_sample_size=30000,
    )
    cv_path = settings.reports_dir / 'cross_validation_report.json'
    cv_path.write_text(
        __import__('json').dumps(__import__('dataclasses').asdict(cv_summary), indent=2),
        encoding='utf-8'
    )
    LOGGER.info(
        'CV complete. R²: %.4f (±%.4f)  MAPE: %.2f%% (±%.2f%%). Saved to %s',
        cv_summary.cv_r2_mean, cv_summary.cv_r2_std,
        cv_summary.cv_mape_mean, cv_summary.cv_mape_std,
        cv_path,
    )
    LOGGER.info(
        'Phase 7 complete. Metrics: %s | Error analysis: %s | Plot: %s | Predictions: %s',
        metrics_path,
        error_analysis_path,
        plot_path,
        predictions_path,
    )


if __name__ == '__main__':
    main()
