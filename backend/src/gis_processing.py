from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.validation import make_valid

LOGGER = logging.getLogger(__name__)
DEFAULT_PROJECTED_EPSG = 32645


@dataclass(frozen=True)
class LayerProcessingSummary:
    layer_name: str
    input_row_count: int
    output_row_count: int
    input_crs: str | None
    output_crs: str
    invalid_geometry_count_before: int
    invalid_geometry_count_after: int
    null_geometry_count_after: int
    geometry_types_after: dict[str, int]


@dataclass(frozen=True)
class GISProcessingSummary:
    target_crs: str
    property_layer: LayerProcessingSummary
    road_layer: LayerProcessingSummary
    facilities_layer: LayerProcessingSummary



def _resolve_target_crs(road_gdf: gpd.GeoDataFrame) -> str:
    if road_gdf.crs is not None and road_gdf.crs.is_projected:
        return str(road_gdf.crs)
    return f"EPSG:{DEFAULT_PROJECTED_EPSG}"



def _fix_invalid_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    fixed = gdf.copy()
    invalid_mask = ~fixed.geometry.is_valid
    if invalid_mask.any():
        fixed.loc[invalid_mask, fixed.geometry.name] = fixed.loc[invalid_mask, fixed.geometry.name].apply(make_valid)
    return fixed



def _drop_empty_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    mask = gdf.geometry.notna() & ~gdf.geometry.is_empty
    return gdf.loc[mask].copy()



def process_gis_layer(gdf: gpd.GeoDataFrame, layer_name: str, target_crs: str) -> tuple[gpd.GeoDataFrame, LayerProcessingSummary]:
    working = gdf.copy()
    input_row_count = int(len(working))
    input_crs = str(working.crs) if working.crs is not None else None
    invalid_before = int((~working.geometry.is_valid).sum()) if len(working) else 0

    working = _fix_invalid_geometries(working)
    if working.crs is None:
        raise ValueError(f"Layer '{layer_name}' does not have a CRS defined")
    working = working.to_crs(target_crs)
    working = _drop_empty_geometries(working)

    invalid_after = int((~working.geometry.is_valid).sum()) if len(working) else 0
    null_geometry_count_after = int(working.geometry.isna().sum()) if len(working) else 0
    geometry_types_after = {
        str(geometry_type): int(count)
        for geometry_type, count in working.geometry.geom_type.value_counts(dropna=False).items()
    }

    summary = LayerProcessingSummary(
        layer_name=layer_name,
        input_row_count=input_row_count,
        output_row_count=int(len(working)),
        input_crs=input_crs,
        output_crs=str(working.crs),
        invalid_geometry_count_before=invalid_before,
        invalid_geometry_count_after=invalid_after,
        null_geometry_count_after=null_geometry_count_after,
        geometry_types_after=geometry_types_after,
    )
    return working, summary



def process_all_gis_layers(
    property_gdf: gpd.GeoDataFrame,
    roads_gdf: gpd.GeoDataFrame,
    facilities_gdf: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame, GISProcessingSummary]:
    target_crs = _resolve_target_crs(roads_gdf)
    processed_property, property_summary = process_gis_layer(property_gdf, "property_layer", target_crs)
    processed_roads, road_summary = process_gis_layer(roads_gdf, "road_layer", target_crs)
    processed_facilities, facilities_summary = process_gis_layer(facilities_gdf, "facilities_layer", target_crs)

    summary = GISProcessingSummary(
        target_crs=target_crs,
        property_layer=property_summary,
        road_layer=road_summary,
        facilities_layer=facilities_summary,
    )
    return processed_property, processed_roads, processed_facilities, summary



def save_processed_gis_layers(
    property_gdf: gpd.GeoDataFrame,
    roads_gdf: gpd.GeoDataFrame,
    facilities_gdf: gpd.GeoDataFrame,
    summary: GISProcessingSummary,
    interim_dir: Path,
    reports_dir: Path,
) -> tuple[Path, Path, Path, Path]:
    interim_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    property_path = interim_dir / "property_gis.parquet"
    roads_path = interim_dir / "roads_gis.parquet"
    facilities_path = interim_dir / "facilities_gis.parquet"
    summary_path = reports_dir / "phase_3_gis_processing_summary.json"

    property_gdf.to_parquet(property_path, index=False)
    roads_gdf.to_parquet(roads_path, index=False)
    facilities_gdf.to_parquet(facilities_path, index=False)
    summary_path.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")

    LOGGER.info("Saved processed property layer to %s", property_path)
    LOGGER.info("Saved processed road layer to %s", roads_path)
    LOGGER.info("Saved processed facilities layer to %s", facilities_path)
    LOGGER.info("Saved GIS processing summary to %s", summary_path)
    return property_path, roads_path, facilities_path, summary_path
