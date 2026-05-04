from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

LOGGER = logging.getLogger(__name__)

FACILITY_GROUP_PATTERNS = {
    "education": ["educational institute", "university", "school", "college"],
    "health": ["health facility", "hospital", "phc"],
    "transport": ["railway station", "bus stop", "highway", "transport"],
    "market": ["market", "business hub", "fair price shop"],
    "recreation": ["recreational"],
    "religious_tourism": ["religious", "tourist attraction"],
}

PRESERVED_TRANSACTION_FEATURES = [
    "Area",
    "Area_original",
    "Area_sqft",
    "Sq ft",
    "Types of area Measurement",
    "Market value per sq ft",
    "Approach_Road_Width",
    "Urban",
    "Rural",
    "Road_Category",
    "Flat_or_Land",
    "Zone_no",
    "Mouza_Name",
    "PS_Name",
    "Road_Name",
    "Proposed_Land_use_Name",
    "Nature_Land_use_Name",
    "Litigated_Property",
    "value_per_area",
    "value_per_sqft",
    "log_value_per_area",
    "market_value",
    "setforth_value",
    "property_match_found",
    "property_record_count",
    "Transaction_code",
    "Transaction_Name",
    "Road_code",
    "Is_Property_on_Road",
    "Adjacent_to_Metal_Road",
    "GP",
    "Nature_Land_use_Code",
    "Proposed_Land_use_Code",
]
IDENTIFIER_COLUMNS = [
    "query_year",
    "query_no",
    "Deed_No",
    "Deed_Year",
    "sl_no_Property",
    "property_district_Name",
    "ps_code",
    "mouza_code",
    "plot_no",
    "bata_plot_no",
]


@dataclass(frozen=True)
class FeatureSummary:
    input_row_count: int
    output_row_count: int
    projected_crs: str
    rows_with_geometry: int
    distance_to_nearest_road_missing: int
    distance_to_nearest_facility_missing: int
    facility_count_500m_nonzero: int
    facility_count_1km_nonzero: int
    preserved_features: list[str]
    final_columns: list[str]



def _ensure_projected_crs(gdf: gpd.GeoDataFrame, dataset_name: str) -> None:
    if gdf.crs is None:
        raise ValueError(f"{dataset_name} has no CRS")
    if not gdf.crs.is_projected:
        raise ValueError(f"{dataset_name} must be in a projected CRS for spatial distance calculations")



def _centroid_points(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    centroid_geometry = gdf.geometry.centroid
    return gpd.GeoDataFrame(gdf.drop(columns=gdf.geometry.name), geometry=centroid_geometry, crs=gdf.crs)



def _safe_feature_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")



def _label_facility_groups(facilities_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    labeled = facilities_gdf.copy()
    source = labeled["Facility_T"].astype("string").str.lower().fillna("")
    labeled["facility_group"] = pd.Series("other", index=labeled.index, dtype="string")
    for group_name, patterns in FACILITY_GROUP_PATTERNS.items():
        mask = source.str.contains("|".join(re.escape(pattern) for pattern in patterns), regex=True)
        labeled.loc[mask, "facility_group"] = group_name
    return labeled



def add_nearest_road_distance(property_gdf: gpd.GeoDataFrame, road_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    _ensure_projected_crs(property_gdf, "property_gdf")
    _ensure_projected_crs(road_gdf, "road_gdf")

    result = property_gdf.copy()
    centroid_gdf = _centroid_points(result[[result.geometry.name]].copy())
    valid_mask = centroid_gdf.geometry.notna() & ~centroid_gdf.geometry.is_empty
    result["distance_to_nearest_road"] = np.nan
    result["nearest_road_width"] = np.nan
    result["nearest_road_category"] = pd.Series(pd.NA, index=result.index, dtype="string")
    result["nearest_road_surface"] = pd.Series(pd.NA, index=result.index, dtype="string")

    if valid_mask.any():
        nearest = gpd.sjoin_nearest(
            centroid_gdf.loc[valid_mask],
            road_gdf[["R_WIDTH", "R_CATG", "R_TOP_MAT", road_gdf.geometry.name]],
            how="left",
            distance_col="distance_to_nearest_road",
        )
        result.loc[nearest.index, "distance_to_nearest_road"] = nearest["distance_to_nearest_road"].astype(float)
        result.loc[nearest.index, "nearest_road_width"] = pd.to_numeric(nearest["R_WIDTH"], errors="coerce").astype(float)
        result.loc[nearest.index, "nearest_road_category"] = nearest["R_CATG"].astype("string")
        result.loc[nearest.index, "nearest_road_surface"] = nearest["R_TOP_MAT"].astype("string")

    result["distance_to_nearest_road_missing_flag"] = result["distance_to_nearest_road"].isna().astype("Int64")
    result["log_distance_to_nearest_road"] = np.log1p(result["distance_to_nearest_road"])
    return result



def add_nearest_facility_distance(property_gdf: gpd.GeoDataFrame, facilities_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    _ensure_projected_crs(property_gdf, "property_gdf")
    _ensure_projected_crs(facilities_gdf, "facilities_gdf")

    labeled_facilities = _label_facility_groups(facilities_gdf)
    result = property_gdf.copy()
    centroid_gdf = _centroid_points(result[[result.geometry.name]].copy())
    valid_mask = centroid_gdf.geometry.notna() & ~centroid_gdf.geometry.is_empty
    result["distance_to_nearest_facility"] = np.nan
    result["nearest_facility_group"] = pd.Series(pd.NA, index=result.index, dtype="string")

    if valid_mask.any():
        nearest = gpd.sjoin_nearest(
            centroid_gdf.loc[valid_mask],
            labeled_facilities[["facility_group", labeled_facilities.geometry.name]],
            how="left",
            distance_col="distance_to_nearest_facility",
        )
        result.loc[nearest.index, "distance_to_nearest_facility"] = nearest["distance_to_nearest_facility"].astype(float)
        result.loc[nearest.index, "nearest_facility_group"] = nearest["facility_group"].astype("string")

    result["distance_to_nearest_facility_missing_flag"] = result["distance_to_nearest_facility"].isna().astype("Int64")
    result["log_distance_to_nearest_facility"] = np.log1p(result["distance_to_nearest_facility"])
    return result



def add_facility_counts(property_gdf: gpd.GeoDataFrame, facilities_gdf: gpd.GeoDataFrame, radius_meters: float) -> pd.Series:
    _ensure_projected_crs(property_gdf, "property_gdf")
    _ensure_projected_crs(facilities_gdf, "facilities_gdf")

    centroid_gdf = _centroid_points(property_gdf[[property_gdf.geometry.name]].copy())
    valid_mask = centroid_gdf.geometry.notna() & ~centroid_gdf.geometry.is_empty
    counts = pd.Series(0, index=property_gdf.index, dtype="Int64")

    if not valid_mask.any() or facilities_gdf.empty:
        return counts

    property_coords = np.column_stack((centroid_gdf.loc[valid_mask].geometry.x, centroid_gdf.loc[valid_mask].geometry.y))
    facility_coords = np.column_stack((facilities_gdf.geometry.x, facilities_gdf.geometry.y))
    facility_tree = cKDTree(facility_coords)
    neighbor_lists = facility_tree.query_ball_point(property_coords, r=radius_meters)
    counts.loc[centroid_gdf.loc[valid_mask].index] = [len(neighbors) for neighbors in neighbor_lists]
    return counts



def add_grouped_facility_counts(property_gdf: gpd.GeoDataFrame, facilities_gdf: gpd.GeoDataFrame, radius_meters: float = 1000.0) -> gpd.GeoDataFrame:
    _ensure_projected_crs(property_gdf, "property_gdf")
    _ensure_projected_crs(facilities_gdf, "facilities_gdf")

    result = property_gdf.copy()
    labeled_facilities = _label_facility_groups(facilities_gdf)
    for group_name in sorted(set(labeled_facilities["facility_group"].dropna().astype(str))):
        group_facilities = labeled_facilities.loc[labeled_facilities["facility_group"] == group_name].copy()
        col_name = f"facility_group_{_safe_feature_name(group_name)}_count_1km"
        result[col_name] = add_facility_counts(result, group_facilities, radius_meters)
    return result



def add_centroid_lat_long(property_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    _ensure_projected_crs(property_gdf, "property_gdf")

    result = property_gdf.copy()
    centroid_gdf = _centroid_points(result[[result.geometry.name]].copy())
    centroid_wgs84 = centroid_gdf.to_crs("EPSG:4326")
    result["longitude"] = centroid_wgs84.geometry.x.astype(float)
    result["latitude"] = centroid_wgs84.geometry.y.astype(float)
    result["geometry_missing_flag"] = result.geometry.isna().astype("Int64")
    result["spatial_features_available"] = result.geometry.notna().astype("Int64")
    return result



def add_property_geometry_features(property_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    _ensure_projected_crs(property_gdf, "property_gdf")

    result = property_gdf.copy()
    result["property_geometry_area"] = result.geometry.area.astype(float)
    result["property_geometry_perimeter"] = result.geometry.length.astype(float)
    result["property_shape_compactness"] = (4 * np.pi * result["property_geometry_area"]) / np.square(result["property_geometry_perimeter"]).replace(0, np.nan)
    return result


def add_transaction_context_features(property_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    result = property_gdf.copy()

    for column in ("Date_of_Registration", "Date_of_presentation"):
        if column in result.columns:
            parsed = pd.to_datetime(result[column], errors="coerce")
            prefix = "registration" if column == "Date_of_Registration" else "presentation"
            result[f"{prefix}_year"] = parsed.dt.year.astype("Int64")
            result[f"{prefix}_month"] = parsed.dt.month.astype("Int64")
            result[f"{prefix}_quarter"] = parsed.dt.quarter.astype("Int64")
            result[f"{prefix}_dayofweek"] = parsed.dt.dayofweek.astype("Int64")

    if {"Date_of_Registration", "Date_of_presentation"}.issubset(result.columns):
        registration_dt = pd.to_datetime(result["Date_of_Registration"], errors="coerce")
        presentation_dt = pd.to_datetime(result["Date_of_presentation"], errors="coerce")
        result["registration_presentation_gap_days"] = (registration_dt - presentation_dt).dt.total_seconds() / 86400.0

    if "Time_of_Presentation" in result.columns:
        time_series = result["Time_of_Presentation"].astype("string").str.extract(r"(?P<hour>\d{1,2})")
        result["presentation_hour"] = pd.to_numeric(time_series["hour"], errors="coerce").astype("Int64")
        result["presentation_is_afternoon"] = result["presentation_hour"].ge(12).astype("Int64")

    binary_like_columns = [
        "Is_Property_on_Road",
        "Adjacent_to_Metal_Road",
        "Urban",
        "Rural",
        "Litigated_Property",
    ]
    for column in binary_like_columns:
        if column not in result.columns:
            continue
        normalized = result[column].astype("string").str.strip().str.upper()
        result[f"{column}_flag"] = normalized.map(
            {
                "Y": 1,
                "YES": 1,
                "TRUE": 1,
                "N": 0,
                "NO": 0,
                "FALSE": 0,
            }
        ).astype("Float64")

    return result



def build_model_training_dataset(
    merged_property_gdf: gpd.GeoDataFrame,
    road_gdf: gpd.GeoDataFrame,
    facilities_gdf: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, FeatureSummary]:
    _ensure_projected_crs(merged_property_gdf, "merged_property_gdf")
    _ensure_projected_crs(road_gdf, "road_gdf")
    _ensure_projected_crs(facilities_gdf, "facilities_gdf")

    featured = merged_property_gdf.copy()
    featured = add_transaction_context_features(featured)
    featured = add_property_geometry_features(featured)
    featured = add_nearest_road_distance(featured, road_gdf)
    featured = add_nearest_facility_distance(featured, facilities_gdf)
    featured["facility_count_500m"] = add_facility_counts(featured, facilities_gdf, 500.0)
    featured["facility_count_1km"] = add_facility_counts(featured, facilities_gdf, 1000.0)
    featured = add_grouped_facility_counts(featured, facilities_gdf, 1000.0)
    featured = add_centroid_lat_long(featured)

    grouped_facility_columns = sorted([column for column in featured.columns if column.startswith("facility_group_")])
    final_columns = [column for column in IDENTIFIER_COLUMNS if column in featured.columns]
    final_columns += [column for column in PRESERVED_TRANSACTION_FEATURES if column in featured.columns]
    final_columns += [
        "property_geometry_area",
        "property_geometry_perimeter",
        "property_shape_compactness",
        "registration_year",
        "registration_month",
        "registration_quarter",
        "registration_dayofweek",
        "presentation_year",
        "presentation_month",
        "presentation_quarter",
        "presentation_dayofweek",
        "registration_presentation_gap_days",
        "presentation_hour",
        "presentation_is_afternoon",
        "Is_Property_on_Road_flag",
        "Adjacent_to_Metal_Road_flag",
        "Urban_flag",
        "Rural_flag",
        "Litigated_Property_flag",
        "distance_to_nearest_road",
        "distance_to_nearest_road_missing_flag",
        "log_distance_to_nearest_road",
        "nearest_road_width",
        "nearest_road_category",
        "nearest_road_surface",
        "distance_to_nearest_facility",
        "distance_to_nearest_facility_missing_flag",
        "log_distance_to_nearest_facility",
        "nearest_facility_group",
        "facility_count_500m",
        "facility_count_1km",
        *grouped_facility_columns,
        "spatial_features_available",
        "geometry_missing_flag",
        "latitude",
        "longitude",
        featured.geometry.name,
    ]
    final_columns = [column for column in final_columns if column in featured.columns]
    final_columns = list(dict.fromkeys(final_columns))

    training_gdf = featured[final_columns].copy()
    rows_with_geometry = int(training_gdf.geometry.notna().sum())
    summary = FeatureSummary(
        input_row_count=int(len(merged_property_gdf)),
        output_row_count=int(len(training_gdf)),
        projected_crs=str(training_gdf.crs),
        rows_with_geometry=rows_with_geometry,
        distance_to_nearest_road_missing=int(training_gdf["distance_to_nearest_road"].isna().sum()),
        distance_to_nearest_facility_missing=int(training_gdf["distance_to_nearest_facility"].isna().sum()),
        facility_count_500m_nonzero=int((training_gdf["facility_count_500m"].fillna(0) > 0).sum()),
        facility_count_1km_nonzero=int((training_gdf["facility_count_1km"].fillna(0) > 0).sum()),
        preserved_features=[column for column in PRESERVED_TRANSACTION_FEATURES if column in training_gdf.columns],
        final_columns=final_columns,
    )
    return training_gdf, summary



def save_model_training_dataset(
    training_gdf: gpd.GeoDataFrame,
    summary: FeatureSummary,
    processed_dir: Path,
    reports_dir: Path,
) -> tuple[Path, Path]:
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = processed_dir / "model_training_dataset.parquet"
    summary_path = reports_dir / "feature_summary.json"

    training_gdf.to_parquet(dataset_path, index=False)
    summary_path.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")

    LOGGER.info("Saved model training dataset to %s", dataset_path)
    LOGGER.info("Saved feature summary to %s", summary_path)
    return dataset_path, summary_path
