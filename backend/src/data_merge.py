from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

import geopandas as gpd
import pandas as pd

LOGGER = logging.getLogger(__name__)
MERGE_KEY_COLUMNS = ["district_name_norm", "ps_code_norm", "mouza_code_norm", "plot_no_norm"]


@dataclass(frozen=True)
class MergeSummary:
    transaction_input_rows: int
    property_input_rows: int
    property_unique_merge_keys: int
    property_duplicate_merge_key_rows: int
    matched_transaction_rows: int
    unmatched_transaction_rows: int
    match_coverage_percent: float
    output_rows: int
    merge_key_columns: list[str]



def _normalize_text(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().str.replace(r"\s+", " ", regex=True)



def _normalize_code(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype("Int64").astype("string")



def prepare_transaction_merge_keys(transactions: pd.DataFrame) -> pd.DataFrame:
    keyed = transactions.copy()
    keyed["district_name_norm"] = _normalize_text(keyed["property_district_Name"])
    keyed["ps_code_norm"] = _normalize_code(keyed["ps_code"])
    keyed["mouza_code_norm"] = _normalize_code(keyed["mouza_code"])
    keyed["plot_no_norm"] = _normalize_code(keyed["plot_no"])
    return keyed



def prepare_property_merge_keys(property_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    keyed = property_gdf.copy()
    keyed["district_name_norm"] = _normalize_text(keyed["Dist_name"])
    keyed["ps_code_norm"] = _normalize_code(keyed["PS_CODE"])
    keyed["mouza_code_norm"] = _normalize_code(keyed["moucode"])
    keyed["plot_no_norm"] = _normalize_code(keyed["plot_no"])
    return keyed



def aggregate_property_layer_for_merge(property_gdf: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, int]:
    keyed = prepare_property_merge_keys(property_gdf)
    valid_key_mask = keyed[MERGE_KEY_COLUMNS].notna().all(axis=1)
    keyed = keyed.loc[valid_key_mask].copy()

    duplicate_merge_key_rows = int(keyed.duplicated(subset=MERGE_KEY_COLUMNS, keep=False).sum())
    keyed["property_record_count"] = 1

    aggregated = keyed.dissolve(
        by=MERGE_KEY_COLUMNS,
        aggfunc={
            "property_record_count": "sum",
            "BLOCK_CODE": "first",
            "BLOCK": "first",
            "PS_CODE": "first",
            "ps_name": "first",
            "moucode": "first",
            "ENG_MOUNAM": "first",
            "mouza_type": "first",
            "Dist_name": "first",
            "dist_code": "first",
            "Ward_No": "first",
            "GP": "first",
            "Municipali": "first",
            "SHAPE_Area": "first",
            "SHAPE_Leng": "first",
            "plot_no": "first",
            "bata_no": "first",
        },
        as_index=False,
    )
    return aggregated, duplicate_merge_key_rows



def merge_transactions_with_property(
    cleaned_transactions: pd.DataFrame,
    property_gdf: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, MergeSummary]:
    transaction_keyed = prepare_transaction_merge_keys(cleaned_transactions)
    property_aggregated, duplicate_merge_key_rows = aggregate_property_layer_for_merge(property_gdf)

    merged = transaction_keyed.merge(
        property_aggregated,
        on=MERGE_KEY_COLUMNS,
        how="left",
        indicator=True,
        suffixes=("", "_property"),
    )
    merged["property_match_found"] = merged["_merge"].eq("both")
    matched_rows = int(merged["property_match_found"].sum())
    unmatched_rows = int(len(merged) - matched_rows)
    coverage = round((matched_rows / len(merged)) * 100, 2) if len(merged) else 0.0

    merged_gdf = gpd.GeoDataFrame(merged.drop(columns=["_merge"]), geometry="geometry", crs=property_gdf.crs)
    summary = MergeSummary(
        transaction_input_rows=int(len(cleaned_transactions)),
        property_input_rows=int(len(property_gdf)),
        property_unique_merge_keys=int(len(property_aggregated)),
        property_duplicate_merge_key_rows=duplicate_merge_key_rows,
        matched_transaction_rows=matched_rows,
        unmatched_transaction_rows=unmatched_rows,
        match_coverage_percent=coverage,
        output_rows=int(len(merged_gdf)),
        merge_key_columns=MERGE_KEY_COLUMNS,
    )
    return merged_gdf, summary



def save_merged_dataset(
    merged_gdf: gpd.GeoDataFrame,
    summary: MergeSummary,
    interim_dir: Path,
    reports_dir: Path,
) -> tuple[Path, Path]:
    interim_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    merged_path = interim_dir / "transactions_property_merged.parquet"
    summary_path = reports_dir / "phase_4_data_merge_summary.json"

    merged_gdf.to_parquet(merged_path, index=False)
    summary_path.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")

    LOGGER.info("Saved merged transaction-property dataset to %s", merged_path)
    LOGGER.info("Saved data merge summary to %s", summary_path)
    return merged_path, summary_path
