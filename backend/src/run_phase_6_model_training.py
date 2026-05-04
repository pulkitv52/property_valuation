from __future__ import annotations

import logging

import geopandas as gpd

from backend.src.config import configure_logging, ensure_directories, settings
from backend.src.model_training import compare_model_candidates, save_model_artifacts

LOGGER = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    ensure_directories()

    training_gdf = gpd.read_parquet(settings.processed_data_dir / 'model_training_dataset.parquet')
    best_artifacts, comparison = compare_model_candidates(training_gdf)
    model_path, summary_path, comparison_path = save_model_artifacts(best_artifacts, settings.models_dir, settings.reports_dir, comparison)
    LOGGER.info('Phase 6 complete. Model: %s | Summary: %s | Comparison: %s', model_path, summary_path, comparison_path)


if __name__ == '__main__':
    main()
