from __future__ import annotations

import logging

import geopandas as gpd

from backend.src.config import configure_logging, ensure_directories, settings
from backend.src.zone_clustering import create_ai_zones, save_zone_outputs

LOGGER = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    ensure_directories()

    training_gdf = gpd.read_parquet(settings.processed_data_dir / 'model_training_dataset.parquet')
    artifacts = create_ai_zones(training_gdf)
    assignments_path, zones_path, summary_csv_path, summary_json_path = save_zone_outputs(
        artifacts,
        settings.processed_data_dir,
        settings.reports_dir,
    )
    LOGGER.info(
        'Phase 8 complete. Assignments: %s | Zones: %s | Summary CSV: %s | Summary JSON: %s',
        assignments_path,
        zones_path,
        summary_csv_path,
        summary_json_path,
    )


if __name__ == '__main__':
    main()
