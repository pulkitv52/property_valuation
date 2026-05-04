from __future__ import annotations

import logging

from backend.src.config import configure_logging, ensure_directories, settings
from backend.src.data_loader import load_facility_layer, load_property_layer, load_road_layer
from backend.src.gis_processing import process_all_gis_layers, save_processed_gis_layers

LOGGER = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    ensure_directories()

    property_gdf = load_property_layer()
    roads_gdf = load_road_layer()
    facilities_gdf = load_facility_layer()

    processed_property, processed_roads, processed_facilities, summary = process_all_gis_layers(
        property_gdf,
        roads_gdf,
        facilities_gdf,
    )
    property_path, roads_path, facilities_path, summary_path = save_processed_gis_layers(
        processed_property,
        processed_roads,
        processed_facilities,
        summary,
        settings.interim_data_dir,
        settings.reports_dir,
    )
    LOGGER.info(
        "Phase 3 complete. Property: %s | Roads: %s | Facilities: %s | Summary: %s",
        property_path,
        roads_path,
        facilities_path,
        summary_path,
    )


if __name__ == "__main__":
    main()
