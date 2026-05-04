from __future__ import annotations

import logging

import geopandas as gpd
import pandas as pd

from backend.src.config import configure_logging, ensure_directories, settings
from backend.src.data_merge import merge_transactions_with_property, save_merged_dataset

LOGGER = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    ensure_directories()

    transactions = pd.read_parquet(settings.interim_data_dir / "cleaned_transactions.parquet")
    property_gdf = gpd.read_parquet(settings.interim_data_dir / "property_gis.parquet")

    merged_gdf, summary = merge_transactions_with_property(transactions, property_gdf)
    merged_path, summary_path = save_merged_dataset(
        merged_gdf,
        summary,
        settings.interim_data_dir,
        settings.reports_dir,
    )
    LOGGER.info("Phase 4 complete. Merged data: %s | Summary: %s", merged_path, summary_path)


if __name__ == "__main__":
    main()
