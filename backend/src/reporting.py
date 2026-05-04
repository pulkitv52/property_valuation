from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from pandas.api.types import is_numeric_dtype

LOGGER = logging.getLogger(__name__)
NUMERIC_OUTLIER_COLUMNS = ["market_value", "setforth_value", "Area"]
POTENTIAL_JOIN_KEY_PATTERNS = (
    "district",
    "office",
    "road",
    "zone",
    "mouza",
    "plot",
    "property",
    "premises",
    "deed",
    "code",
    "name",
)


@dataclass(frozen=True)
class DatasetProfile:
    dataset_name: str
    dataset_type: str
    row_count: int
    column_count: int
    columns: list[str]
    dtypes: dict[str, str]
    missing_values: dict[str, int]
    missing_percent: dict[str, float]
    duplicate_row_count: int
    candidate_join_keys: list[str]
    numeric_summary: dict[str, dict[str, float | None]]
    outlier_summary: dict[str, dict[str, float | int | None]]
    crs: str | None = None
    geometry_type_counts: dict[str, int] | None = None
    invalid_geometry_count: int | None = None
    bounds: dict[str, float] | None = None


def _serialise_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _normalise_numeric_series(series: pd.Series) -> pd.Series:
    if is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    cleaned = series.astype(str).str.replace(",", "", regex=False).str.strip()
    return pd.to_numeric(cleaned, errors="coerce")


def _build_numeric_summary(df: pd.DataFrame) -> dict[str, dict[str, float | None]]:
    summary: dict[str, dict[str, float | None]] = {}
    for column in df.columns:
        numeric_series = _normalise_numeric_series(df[column])
        if numeric_series.notna().sum() == 0:
            continue
        summary[column] = {
            "count": float(numeric_series.count()),
            "mean": _serialise_value(numeric_series.mean()),
            "median": _serialise_value(numeric_series.median()),
            "min": _serialise_value(numeric_series.min()),
            "max": _serialise_value(numeric_series.max()),
            "std": _serialise_value(numeric_series.std()),
        }
    return summary


def _build_outlier_summary(df: pd.DataFrame, columns: list[str]) -> dict[str, dict[str, float | int | None]]:
    outliers: dict[str, dict[str, float | int | None]] = {}
    for column in columns:
        if column not in df.columns:
            continue
        numeric_series = _normalise_numeric_series(df[column]).dropna()
        if numeric_series.empty:
            continue
        q1 = numeric_series.quantile(0.25)
        q3 = numeric_series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_count = int(((numeric_series < lower) | (numeric_series > upper)).sum())
        outliers[column] = {
            "q1": _serialise_value(q1),
            "q3": _serialise_value(q3),
            "iqr": _serialise_value(iqr),
            "lower_bound": _serialise_value(lower),
            "upper_bound": _serialise_value(upper),
            "outlier_count": outlier_count,
        }
    return outliers


def _candidate_join_keys(columns: list[str]) -> list[str]:
    return [
        column
        for column in columns
        if any(pattern in column.lower() for pattern in POTENTIAL_JOIN_KEY_PATTERNS)
    ]


def profile_tabular_dataset(df: pd.DataFrame, dataset_name: str) -> DatasetProfile:
    missing = df.isna().sum().sort_values(ascending=False)
    missing_pct = ((missing / max(len(df), 1)) * 100).round(2)
    duplicate_count = int(df.duplicated().sum())
    numeric_columns = [column for column in df.columns if _normalise_numeric_series(df[column]).notna().sum() > 0]

    return DatasetProfile(
        dataset_name=dataset_name,
        dataset_type="tabular",
        row_count=int(len(df)),
        column_count=int(len(df.columns)),
        columns=[str(column) for column in df.columns],
        dtypes={str(column): str(dtype) for column, dtype in df.dtypes.items()},
        missing_values={str(column): int(value) for column, value in missing.items() if int(value) > 0},
        missing_percent={str(column): float(missing_pct[column]) for column in missing.index if int(missing[column]) > 0},
        duplicate_row_count=duplicate_count,
        candidate_join_keys=_candidate_join_keys([str(column) for column in df.columns]),
        numeric_summary={column: values for column, values in _build_numeric_summary(df[numeric_columns]).items()},
        outlier_summary=_build_outlier_summary(df, NUMERIC_OUTLIER_COLUMNS),
    )


def profile_geospatial_dataset(gdf: gpd.GeoDataFrame, dataset_name: str) -> DatasetProfile:
    base_df = pd.DataFrame(gdf.drop(columns=gdf.geometry.name))
    tabular_profile = profile_tabular_dataset(base_df, dataset_name)

    geometry_type_counts = {
        str(geometry_type): int(count)
        for geometry_type, count in gdf.geometry.geom_type.value_counts(dropna=False).items()
    }
    invalid_geometry_count = int((~gdf.geometry.is_valid).sum()) if len(gdf) else 0
    bounds = None
    if len(gdf):
        minx, miny, maxx, maxy = gdf.total_bounds.tolist()
        bounds = {"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy}

    return DatasetProfile(
        dataset_name=dataset_name,
        dataset_type="geospatial",
        row_count=tabular_profile.row_count,
        column_count=tabular_profile.column_count + 1,
        columns=tabular_profile.columns + [gdf.geometry.name],
        dtypes={**tabular_profile.dtypes, gdf.geometry.name: str(gdf.geometry.dtype)},
        missing_values=tabular_profile.missing_values,
        missing_percent=tabular_profile.missing_percent,
        duplicate_row_count=tabular_profile.duplicate_row_count,
        candidate_join_keys=tabular_profile.candidate_join_keys,
        numeric_summary=tabular_profile.numeric_summary,
        outlier_summary=tabular_profile.outlier_summary,
        crs=str(gdf.crs) if gdf.crs is not None else None,
        geometry_type_counts=geometry_type_counts,
        invalid_geometry_count=invalid_geometry_count,
        bounds=bounds,
    )


def write_profiles(profiles: list[DatasetProfile], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "phase_1_data_summary.json"
    md_path = output_dir / "phase_1_data_summary.md"

    payload = {profile.dataset_name: asdict(profile) for profile in profiles}
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown_report(profiles), encoding="utf-8")
    LOGGER.info("Saved Phase 1 reports to %s and %s", json_path, md_path)
    return json_path, md_path


def _render_markdown_report(profiles: list[DatasetProfile]) -> str:
    lines = [
        "# Phase 1 Data Understanding Report",
        "",
        "This report summarizes the transaction and GIS datasets required for Use Case 1.",
        "",
    ]

    for profile in profiles:
        lines.extend(
            [
                f"## {profile.dataset_name}",
                "",
                f"- Type: {profile.dataset_type}",
                f"- Rows: {profile.row_count}",
                f"- Columns: {profile.column_count}",
                f"- Duplicate rows: {profile.duplicate_row_count}",
                f"- Candidate join keys: {', '.join(profile.candidate_join_keys) if profile.candidate_join_keys else 'None detected'}",
            ]
        )

        if profile.crs:
            lines.append(f"- CRS: {profile.crs}")
        if profile.geometry_type_counts is not None:
            lines.append(f"- Geometry types: {json.dumps(profile.geometry_type_counts)}")
        if profile.invalid_geometry_count is not None:
            lines.append(f"- Invalid geometries: {profile.invalid_geometry_count}")
        if profile.bounds is not None:
            lines.append(f"- Bounds: {json.dumps(profile.bounds)}")

        lines.extend(["", "### Top Missing Columns", ""])
        if profile.missing_values:
            for column, count in list(profile.missing_values.items())[:15]:
                percent = profile.missing_percent.get(column, 0.0)
                lines.append(f"- {column}: {count} missing ({percent}%)")
        else:
            lines.append("- No missing values detected")

        lines.extend(["", "### Outlier Summary", ""])
        if profile.outlier_summary:
            for column, summary in profile.outlier_summary.items():
                lines.append(
                    f"- {column}: {summary['outlier_count']} outliers, "
                    f"bounds=({summary['lower_bound']}, {summary['upper_bound']})"
                )
        else:
            lines.append("- No configured outlier columns available in this dataset")

        lines.extend(["", "### Schema", ""])
        for column, dtype in profile.dtypes.items():
            lines.append(f"- {column}: {dtype}")
        lines.append("")

    return "\n".join(lines)
