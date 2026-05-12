from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

LOGGER = logging.getLogger(__name__)

ZONE_LABELS = {
    "AI_ZONE_01": ("Z-01 | Premium Urban Market", "High-value core market cluster with strong access to roads and nearby facilities."),
    "AI_ZONE_02": ("Z-02 | Growth Corridor", "Fast-moving market corridor with strong pricing and expansion potential."),
    "AI_ZONE_03": ("Z-03 | Accessible Mid-Market", "Well-connected mid-market zone with balanced value and service access."),
    "AI_ZONE_04": ("Z-04 | Mixed Residential Belt", "Broad residential market belt with mixed price points and moderate accessibility."),
    "AI_ZONE_05": ("Z-05 | Emerging Urban Fringe", "Outer urban market showing active development and rising accessibility."),
    "AI_ZONE_06": ("Z-06 | Affordable Expansion Zone", "Value-oriented expansion market with lower price levels and developing infrastructure."),
    "AI_ZONE_07": ("Z-07 | Outer Value Market", "Lower-priced outer-market cluster with sparse amenities and longer access distances."),
    "AI_ZONE_08": ("Peripheral Opportunity Zone", "Peripheral market pocket with selective growth opportunities."),
    "AI_ZONE_09": ("Transitional Growth Zone", "Transition market zone showing improving value and access conditions."),
    "AI_ZONE_10": ("Remote Market Cluster", "Low-density remote market area far from major urban centres."),
    "AI_ZONE_11": ("Mixed Access Corridor", "Mixed-use access corridor with diverse property patterns and moderate connectivity."),
    "AI_ZONE_12": ("Special Market Cluster", "Distinct market cluster with atypical pricing or spatial behaviour."),
}

BASE_ZONE_FEATURES = [
    "centroid_x",
    "centroid_y",
    "log_value_per_area",
    "log_distance_to_nearest_road",
    "log_distance_to_nearest_facility",
    "facility_count_1km",
    "nearest_road_width",
    "Urban_flag",
    "Rural_flag",
    "flat_flag",
    "nature_land_use_freq",
    "proposed_land_use_freq",
    "nearest_road_category_freq",
]

REQUIRED_SOURCE_COLUMNS = [
    "value_per_area",
    "distance_to_nearest_road",
    "distance_to_nearest_facility",
    "facility_count_1km",
    "nearest_road_width",
    "Urban_flag",
    "Rural_flag",
    "Flat_or_Land",
    "Nature_Land_use_Code",
    "Proposed_Land_use_Code",
    "nearest_road_category",
]


@dataclass(frozen=True)
class ZoneClusteringSummary:
    input_row_count: int
    rows_with_geometry: int
    rows_used_for_clustering: int
    projected_crs: str
    selected_cluster_count: int
    candidate_cluster_range: list[int]
    silhouette_score: float | None
    feature_columns: list[str]
    output_assignment_rows: int
    output_zone_rows: int


@dataclass(frozen=True)
class ZoneClusteringArtifacts:
    assignments_gdf: gpd.GeoDataFrame
    zone_polygons_gdf: gpd.GeoDataFrame
    zone_summary_df: pd.DataFrame
    summary: ZoneClusteringSummary


def _ensure_projected_crs(gdf: gpd.GeoDataFrame, dataset_name: str) -> None:
    if gdf.crs is None:
        raise ValueError(f"{dataset_name} has no CRS")
    if not gdf.crs.is_projected:
        raise ValueError(f"{dataset_name} must use a projected CRS for zone clustering")


def _mode_value(series: pd.Series) -> str | None:
    non_missing = series.dropna()
    if non_missing.empty:
        return None
    mode = non_missing.mode(dropna=True)
    if mode.empty:
        return None
    return str(mode.iloc[0])


def _frequency_encode(series: pd.Series) -> pd.Series:
    normalized = series.astype("string").fillna("Missing")
    freq_map = normalized.value_counts(normalize=True, dropna=False).to_dict()
    return normalized.astype(str).map(freq_map).astype(float)


def _prepare_zone_dataframe(df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    _ensure_projected_crs(df, "training_gdf")
    working = df.copy()
    centroid = working.geometry.centroid
    working["centroid_x"] = centroid.x.astype(float)
    working["centroid_y"] = centroid.y.astype(float)
    working["log_value_per_area"] = np.log1p(pd.to_numeric(working["value_per_area"], errors="coerce"))
    working["log_distance_to_nearest_road"] = np.log1p(pd.to_numeric(working["distance_to_nearest_road"], errors="coerce"))
    working["log_distance_to_nearest_facility"] = np.log1p(pd.to_numeric(working["distance_to_nearest_facility"], errors="coerce"))
    working["flat_flag"] = working.get("Flat_or_Land", pd.Series(index=working.index, dtype="string")).astype("string").str.upper().eq("FLAT").astype("Int64")
    working["nature_land_use_freq"] = _frequency_encode(working.get("Nature_Land_use_Code", pd.Series(index=working.index, dtype="string")))
    working["proposed_land_use_freq"] = _frequency_encode(working.get("Proposed_Land_use_Code", pd.Series(index=working.index, dtype="string")))
    working["nearest_road_category_freq"] = _frequency_encode(working.get("nearest_road_category", pd.Series(index=working.index, dtype="string")))

    for column in [
        "facility_count_1km",
        "nearest_road_width",
        "Urban_flag",
        "Rural_flag",
        "flat_flag",
    ]:
        if column in working.columns:
            working[column] = pd.to_numeric(working[column], errors="coerce")

    required_columns = ["geometry", *REQUIRED_SOURCE_COLUMNS, *BASE_ZONE_FEATURES]
    zone_df = working.dropna(subset=[column for column in required_columns if column in working.columns]).copy()
    zone_df = zone_df.loc[zone_df.geometry.notna() & ~zone_df.geometry.is_empty].copy()
    return zone_df


def _select_cluster_count(
    X_scaled: np.ndarray,
    cluster_options: list[int],
    random_state: int,
    sample_size: int = 20000,
) -> tuple[int, float | None]:
    if len(X_scaled) < 3:
        return max(1, min(cluster_options, default=2)), None

    sample_indices = np.arange(len(X_scaled))
    if len(sample_indices) > sample_size:
        rng = np.random.default_rng(random_state)
        sample_indices = rng.choice(sample_indices, size=sample_size, replace=False)
    X_sample = X_scaled[sample_indices]

    scored_options: list[tuple[int, float]] = []
    for n_clusters in cluster_options:
        if n_clusters >= len(X_sample):
            continue
        model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init="auto")
        labels = model.fit_predict(X_sample)
        if len(np.unique(labels)) < 2:
            continue
        score = float(silhouette_score(X_sample, labels))
        scored_options.append((n_clusters, score))

    if not scored_options:
        fallback = cluster_options[0] if cluster_options else 8
        return fallback, None

    best_clusters, best_score = max(scored_options, key=lambda item: item[1])
    return best_clusters, best_score


def _relabel_zones_by_value(zone_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    ranking = (
        zone_df.groupby("ai_zone_raw", dropna=False)["value_per_area"]
        .median()
        .sort_values(ascending=False)
        .reset_index()
    )
    ranking["ai_zone"] = [f"AI_ZONE_{idx:02d}" for idx in range(1, len(ranking) + 1)]
    mapping = dict(zip(ranking["ai_zone_raw"], ranking["ai_zone"]))
    relabeled = zone_df.copy()
    relabeled["ai_zone"] = relabeled["ai_zone_raw"].map(mapping)
    relabeled["ai_zone_name"] = relabeled["ai_zone"].map(lambda value: ZONE_LABELS.get(value, (value, ""))[0])
    relabeled["ai_zone_description"] = relabeled["ai_zone"].map(lambda value: ZONE_LABELS.get(value, (value, ""))[1])
    return relabeled


def create_ai_zones(
    df: gpd.GeoDataFrame,
    n_clusters: int | None = None,
    random_state: int = 42,
    cluster_range: tuple[int, int] = (6, 12),
) -> ZoneClusteringArtifacts:
    zone_df = _prepare_zone_dataframe(df)
    if zone_df.empty:
        raise ValueError("No usable rows are available for zone clustering")

    feature_columns = [column for column in BASE_ZONE_FEATURES if column in zone_df.columns]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(zone_df[feature_columns])

    candidate_cluster_range = list(range(cluster_range[0], cluster_range[1] + 1))
    selected_clusters = n_clusters
    selected_silhouette: float | None = None
    if selected_clusters is None:
        selected_clusters, selected_silhouette = _select_cluster_count(
            X_scaled,
            candidate_cluster_range,
            random_state=random_state,
        )

    model = KMeans(n_clusters=selected_clusters, random_state=random_state, n_init="auto")
    zone_df = zone_df.copy()
    zone_df["ai_zone_raw"] = model.fit_predict(X_scaled)
    zone_df = _relabel_zones_by_value(zone_df)

    zone_summary_df = generate_zone_summary(zone_df)
    zone_polygons_gdf = build_zone_polygons(zone_df, zone_summary_df)
    summary = ZoneClusteringSummary(
        input_row_count=int(len(df)),
        rows_with_geometry=int(df.geometry.notna().sum()),
        rows_used_for_clustering=int(len(zone_df)),
        projected_crs=str(df.crs),
        selected_cluster_count=int(selected_clusters),
        candidate_cluster_range=candidate_cluster_range,
        silhouette_score=selected_silhouette,
        feature_columns=feature_columns,
        output_assignment_rows=int(len(zone_df)),
        output_zone_rows=int(len(zone_polygons_gdf)),
    )
    return ZoneClusteringArtifacts(
        assignments_gdf=zone_df,
        zone_polygons_gdf=zone_polygons_gdf,
        zone_summary_df=zone_summary_df,
        summary=summary,
    )


def generate_zone_summary(df: gpd.GeoDataFrame) -> pd.DataFrame:
    grouped = df.groupby("ai_zone", dropna=False)
    summary = grouped.agg(
        property_count=("value_per_area", "count"),
        avg_value_per_area=("value_per_area", "mean"),
        median_value_per_area=("value_per_area", "median"),
        avg_market_value=("market_value", "mean"),
        median_market_value=("market_value", "median"),
        avg_distance_to_nearest_road=("distance_to_nearest_road", "mean"),
        avg_distance_to_nearest_facility=("distance_to_nearest_facility", "mean"),
        avg_facility_count_1km=("facility_count_1km", "mean"),
        avg_nearest_road_width=("nearest_road_width", "mean"),
        urban_share=("Urban_flag", "mean"),
        rural_share=("Rural_flag", "mean"),
        flat_share=("flat_flag", "mean"),
    ).reset_index()

    summary["dominant_district"] = grouped["property_district_Name"].agg(_mode_value).values
    summary["dominant_mouza"] = grouped["Mouza_Name"].agg(_mode_value).values
    summary["dominant_transaction_type"] = grouped["Transaction_Name"].agg(_mode_value).values
    summary["dominant_land_use"] = grouped["Nature_Land_use_Name"].agg(_mode_value).values
    summary["dominant_existing_zone_no"] = grouped["Zone_no"].agg(_mode_value).values
    summary["ai_zone_name"] = summary["ai_zone"].map(lambda value: ZONE_LABELS.get(value, (value, ""))[0])
    summary["ai_zone_description"] = summary["ai_zone"].map(lambda value: ZONE_LABELS.get(value, (value, ""))[1])
    summary = summary.sort_values("median_value_per_area", ascending=False).reset_index(drop=True)
    return summary


def build_zone_polygons(assignments_gdf: gpd.GeoDataFrame, zone_summary_df: pd.DataFrame) -> gpd.GeoDataFrame:
    zone_polygons = assignments_gdf[["ai_zone", assignments_gdf.geometry.name]].dissolve(by="ai_zone", as_index=False)
    zone_polygons = zone_polygons.merge(zone_summary_df, on="ai_zone", how="left")
    return zone_polygons


def save_zone_outputs(
    artifacts: ZoneClusteringArtifacts,
    processed_dir: Path,
    reports_dir: Path,
) -> tuple[Path, Path, Path, Path]:
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    assignments_path = processed_dir / "ai_zone_assignments.parquet"
    zones_path = processed_dir / "ai_zones.geojson"
    summary_csv_path = reports_dir / "zone_summary.csv"
    summary_json_path = reports_dir / "zone_clustering_summary.json"

    artifacts.assignments_gdf.to_parquet(assignments_path, index=False)
    artifacts.zone_polygons_gdf.to_file(zones_path, driver="GeoJSON")
    artifacts.zone_summary_df.to_csv(summary_csv_path, index=False)
    summary_json_path.write_text(json.dumps(asdict(artifacts.summary), indent=2), encoding="utf-8")

    LOGGER.info("Saved AI zone assignments to %s", assignments_path)
    LOGGER.info("Saved AI zones GeoJSON to %s", zones_path)
    LOGGER.info("Saved zone summary CSV to %s", summary_csv_path)
    LOGGER.info("Saved zone clustering summary to %s", summary_json_path)
    return assignments_path, zones_path, summary_csv_path, summary_json_path
