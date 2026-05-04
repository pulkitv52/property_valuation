from __future__ import annotations

import logging

from backend.src.config import configure_logging, ensure_directories, settings
from backend.src.data_loader import load_all_phase_1_datasets
from backend.src.reporting import profile_geospatial_dataset, profile_tabular_dataset, write_profiles

LOGGER = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    ensure_directories()

    datasets = load_all_phase_1_datasets()
    profiles = [
        profile_tabular_dataset(datasets.transactions, "transactions"),
        profile_geospatial_dataset(datasets.property_gdf, "property_layer"),
        profile_geospatial_dataset(datasets.roads_gdf, "road_layer"),
        profile_geospatial_dataset(datasets.facilities_gdf, "facilities_layer"),
    ]
    json_path, md_path = write_profiles(profiles, settings.reports_dir)
    LOGGER.info("Phase 1 complete. Reports created at %s and %s", json_path, md_path)


if __name__ == "__main__":
    main()
