from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

from backend.src.config import settings

LOGGER = logging.getLogger(__name__)

EXCEL_EXTENSIONS = {".xls", ".xlsx", ".xlsm", ".xlsb", ".ods"}
CSV_EXTENSIONS = {".csv", ".txt"}


@dataclass(frozen=True)
class DatasetBundle:
    transactions: pd.DataFrame
    property_gdf: gpd.GeoDataFrame
    roads_gdf: gpd.GeoDataFrame
    facilities_gdf: gpd.GeoDataFrame


def _validate_file(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required dataset not found: {path}")
    return path


def load_transaction_data(path: Path | None = None, **kwargs: Any) -> pd.DataFrame:
    transaction_path = _validate_file(path or settings.transaction_path)
    suffix = transaction_path.suffix.lower()
    LOGGER.info("Loading transaction data from %s", transaction_path)

    if suffix in EXCEL_EXTENSIONS:
        return pd.read_excel(transaction_path, **kwargs)
    if suffix in CSV_EXTENSIONS:
        return pd.read_csv(transaction_path, **kwargs)

    raise ValueError(
        f"Unsupported transaction file format '{suffix}'. Supported formats: "
        f"{sorted(EXCEL_EXTENSIONS | CSV_EXTENSIONS)}"
    )


def load_shapefile(path: Path, **kwargs: Any) -> gpd.GeoDataFrame:
    shapefile_path = _validate_file(path)
    LOGGER.info("Loading shapefile from %s", shapefile_path)
    return gpd.read_file(shapefile_path, **kwargs)


def load_property_layer(path: Path | None = None, **kwargs: Any) -> gpd.GeoDataFrame:
    return load_shapefile(path or settings.property_path, **kwargs)


def load_road_layer(path: Path | None = None, **kwargs: Any) -> gpd.GeoDataFrame:
    return load_shapefile(path or settings.road_path, **kwargs)


def load_facility_layer(path: Path | None = None, **kwargs: Any) -> gpd.GeoDataFrame:
    return load_shapefile(path or settings.facility_path, **kwargs)


def load_all_phase_1_datasets() -> DatasetBundle:
    return DatasetBundle(
        transactions=load_transaction_data(),
        property_gdf=load_property_layer(),
        roads_gdf=load_road_layer(),
        facilities_gdf=load_facility_layer(),
    )
