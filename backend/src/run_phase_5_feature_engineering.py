from __future__ import annotations

import logging

import geopandas as gpd

from backend.src.config import configure_logging, ensure_directories, settings
from backend.src.feature_engineering import build_model_training_dataset, save_model_training_dataset

LOGGER = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    ensure_directories()

    merged_gdf = gpd.read_parquet(settings.interim_data_dir / 'transactions_property_merged.parquet')
    roads_gdf = gpd.read_parquet(settings.interim_data_dir / 'roads_gis.parquet')
    facilities_gdf = gpd.read_parquet(settings.interim_data_dir / 'facilities_gis.parquet')

    training_gdf, summary = build_model_training_dataset(merged_gdf, roads_gdf, facilities_gdf)
    dataset_path, summary_path = save_model_training_dataset(
        training_gdf,
        summary,
        settings.processed_data_dir,
        settings.reports_dir,
    )
    LOGGER.info('Phase 5 complete. Training dataset: %s | Summary: %s', dataset_path, summary_path)


if __name__ == '__main__':
    main()
