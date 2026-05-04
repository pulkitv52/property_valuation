from __future__ import annotations

import logging
import pandas as pd
import geopandas as gpd

from backend.src.config import configure_logging, ensure_directories, settings
from backend.src.explainability import (
    load_trained_model,
    run_explainability,
    save_explainability_outputs,
)

LOGGER = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    ensure_directories()

    model = load_trained_model(settings.models_dir / 'valuation_model.pkl')
    training_gdf = gpd.read_parquet(settings.processed_data_dir / 'model_training_dataset.parquet')
    predictions_df = pd.read_parquet(settings.processed_data_dir / 'valuation_predictions.parquet')

    feature_importance_df, sample_explanations, summary = run_explainability(
        model,
        training_gdf,
        predictions_df,
    )
    feature_importance_path, sample_explanations_path, summary_path = save_explainability_outputs(
        feature_importance_df,
        sample_explanations,
        summary,
        settings.reports_dir,
    )
    LOGGER.info(
        'Phase 9 complete. Feature importance: %s | Sample explanations: %s | Summary: %s',
        feature_importance_path,
        sample_explanations_path,
        summary_path,
    )


if __name__ == '__main__':
    main()
