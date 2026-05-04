from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)

DEFAULT_JOIN_COLUMNS = [
    'query_year',
    'query_no',
    'Deed_No',
    'Deed_Year',
    'sl_no_Property',
    'property_district_Name',
    'ps_code',
    'mouza_code',
    'plot_no',
    'bata_plot_no',
]

EXPECTED_MVDB_VALUE_COLUMNS = [
    'mvdb_value',
    'circle_rate_value',
    'guideline_value',
    'government_valuation',
]


@dataclass(frozen=True)
class MVDBComparisonSummary:
    status: str
    mvdb_data_available: bool
    mvdb_path: str | None
    expected_join_columns: list[str]
    expected_value_columns: list[str]
    comparison_row_count: int
    matched_mvdb_rows: int
    ai_mae_market_value: float | None
    mvdb_mae_market_value: float | None
    ai_mape_market_value: float | None
    mvdb_mape_market_value: float | None
    better_system_by_mae: str | None
    notes: list[str]


def build_mvdb_placeholder_summary(mvdb_path: Path | None) -> MVDBComparisonSummary:
    notes = [
        'MVDB or circle-rate data is not currently available in the data folder.',
        'Provide a CSV, Excel, or Parquet file and set MVDB_FILE in .env to activate Phase 10 comparison.',
        'The comparison utility expects a government valuation column plus stable join identifiers.',
    ]
    return MVDBComparisonSummary(
        status='waiting_for_mvdb_data',
        mvdb_data_available=False,
        mvdb_path=str(mvdb_path) if mvdb_path is not None else None,
        expected_join_columns=DEFAULT_JOIN_COLUMNS,
        expected_value_columns=EXPECTED_MVDB_VALUE_COLUMNS,
        comparison_row_count=0,
        matched_mvdb_rows=0,
        ai_mae_market_value=None,
        mvdb_mae_market_value=None,
        ai_mape_market_value=None,
        mvdb_mape_market_value=None,
        better_system_by_mae=None,
        notes=notes,
    )


def load_mvdb_dataset(mvdb_path: Path) -> pd.DataFrame:
    suffix = mvdb_path.suffix.lower()
    if suffix == '.csv':
        return pd.read_csv(mvdb_path)
    if suffix in {'.xlsx', '.xls'}:
        return pd.read_excel(mvdb_path)
    if suffix == '.parquet':
        return pd.read_parquet(mvdb_path)
    raise ValueError(f'Unsupported MVDB file format: {mvdb_path.suffix}')


def infer_mvdb_value_column(mvdb_df: pd.DataFrame) -> str:
    for column in EXPECTED_MVDB_VALUE_COLUMNS:
        if column in mvdb_df.columns:
            return column
    raise ValueError(
        'MVDB dataset is missing a recognizable valuation column. '
        f'Expected one of: {EXPECTED_MVDB_VALUE_COLUMNS}'
    )


def resolve_join_columns(predictions_df: pd.DataFrame, mvdb_df: pd.DataFrame) -> list[str]:
    join_columns = [column for column in DEFAULT_JOIN_COLUMNS if column in predictions_df.columns and column in mvdb_df.columns]
    if not join_columns:
        raise ValueError(
            'No common join columns were found between valuation predictions and MVDB data. '
            f'Expected overlap on identifiers such as: {DEFAULT_JOIN_COLUMNS}'
        )
    return join_columns


def create_mvdb_comparison_dataset(
    predictions_df: pd.DataFrame,
    mvdb_df: pd.DataFrame,
    join_columns: list[str] | None = None,
    mvdb_value_column: str | None = None,
) -> tuple[pd.DataFrame, str, list[str]]:
    resolved_mvdb_value_column = mvdb_value_column or infer_mvdb_value_column(mvdb_df)
    resolved_join_columns = join_columns or resolve_join_columns(predictions_df, mvdb_df)

    left_df = predictions_df.copy()
    right_df = mvdb_df.copy()

    right_df = right_df.drop_duplicates(subset=resolved_join_columns, keep='first').copy()
    comparison_df = left_df.merge(
        right_df[resolved_join_columns + [resolved_mvdb_value_column]],
        on=resolved_join_columns,
        how='left',
    )
    comparison_df['mvdb_market_value'] = pd.to_numeric(comparison_df[resolved_mvdb_value_column], errors='coerce')
    comparison_df['mvdb_absolute_error_market_value'] = (
        comparison_df['actual_market_value_from_target'] - comparison_df['mvdb_market_value']
    ).abs()
    comparison_df['ai_absolute_error_market_value'] = (
        comparison_df['actual_market_value_from_target'] - comparison_df['predicted_market_value']
    ).abs()
    comparison_df['mvdb_absolute_percentage_error_market_value'] = np.where(
        comparison_df['actual_market_value_from_target'] != 0,
        comparison_df['mvdb_absolute_error_market_value'] / comparison_df['actual_market_value_from_target'] * 100,
        pd.NA,
    )
    comparison_df['ai_absolute_percentage_error_market_value'] = np.where(
        comparison_df['actual_market_value_from_target'] != 0,
        comparison_df['ai_absolute_error_market_value'] / comparison_df['actual_market_value_from_target'] * 100,
        pd.NA,
    )
    return comparison_df, resolved_mvdb_value_column, resolved_join_columns


def _safe_mean(series: pd.Series) -> float | None:
    numeric = pd.to_numeric(series, errors='coerce').dropna()
    if numeric.empty:
        return None
    return float(numeric.mean())


def summarize_mvdb_vs_ai(
    comparison_df: pd.DataFrame,
    mvdb_path: Path,
    join_columns: list[str],
    mvdb_value_column: str,
) -> MVDBComparisonSummary:
    matched_mask = comparison_df['mvdb_market_value'].notna()
    matched_rows = comparison_df.loc[matched_mask].copy()

    ai_mae = _safe_mean(matched_rows['ai_absolute_error_market_value'])
    mvdb_mae = _safe_mean(matched_rows['mvdb_absolute_error_market_value'])
    ai_mape = _safe_mean(matched_rows['ai_absolute_percentage_error_market_value'])
    mvdb_mape = _safe_mean(matched_rows['mvdb_absolute_percentage_error_market_value'])

    better_system = None
    if ai_mae is not None and mvdb_mae is not None:
        better_system = 'ai_model' if ai_mae < mvdb_mae else 'mvdb' if mvdb_mae < ai_mae else 'tie'

    notes = [
        f'Comparison used join columns: {join_columns}',
        f'MVDB value column used: {mvdb_value_column}',
    ]
    if matched_rows.empty:
        notes.append('MVDB file was loaded, but no comparable matched rows were found after joining.')

    return MVDBComparisonSummary(
        status='completed' if not matched_rows.empty else 'loaded_but_unmatched',
        mvdb_data_available=True,
        mvdb_path=str(mvdb_path),
        expected_join_columns=join_columns,
        expected_value_columns=[mvdb_value_column],
        comparison_row_count=int(len(comparison_df)),
        matched_mvdb_rows=int(len(matched_rows)),
        ai_mae_market_value=ai_mae,
        mvdb_mae_market_value=mvdb_mae,
        ai_mape_market_value=ai_mape,
        mvdb_mape_market_value=mvdb_mape,
        better_system_by_mae=better_system,
        notes=notes,
    )


def save_mvdb_outputs(
    summary: MVDBComparisonSummary,
    reports_dir: Path,
    comparison_df: pd.DataFrame | None = None,
) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = reports_dir / 'mvdb_comparison.csv'
    summary_path = reports_dir / 'mvdb_vs_ai_summary.json'

    if comparison_df is not None:
        comparison_df.to_csv(comparison_path, index=False)

    summary_path.write_text(json.dumps(asdict(summary), indent=2), encoding='utf-8')
    LOGGER.info('Saved MVDB summary to %s', summary_path)
    if comparison_df is not None:
        LOGGER.info('Saved MVDB comparison rows to %s', comparison_path)
    return comparison_path, summary_path


def save_mvdb_data_requirements(reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    requirements_path = reports_dir / 'mvdb_data_requirements.json'
    payload: dict[str, Any] = {
        'expected_join_columns': DEFAULT_JOIN_COLUMNS,
        'expected_value_columns': EXPECTED_MVDB_VALUE_COLUMNS,
        'supported_formats': ['.csv', '.xlsx', '.xls', '.parquet'],
        'description': 'Provide a government valuation dataset with one valuation column and stable join identifiers so AI predictions can be compared against MVDB or circle-rate values.',
    }
    requirements_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    LOGGER.info('Saved MVDB data requirements to %s', requirements_path)
    return requirements_path
