from __future__ import annotations

import logging

import pandas as pd

from backend.src.config import configure_logging, ensure_directories, settings
from backend.src.mvdb_comparison import (
    build_mvdb_placeholder_summary,
    create_mvdb_comparison_dataset,
    load_mvdb_dataset,
    save_mvdb_data_requirements,
    save_mvdb_outputs,
    summarize_mvdb_vs_ai,
)

LOGGER = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    ensure_directories()

    predictions_df = pd.read_parquet(settings.processed_data_dir / 'valuation_predictions.parquet')
    requirements_path = save_mvdb_data_requirements(settings.reports_dir)

    if settings.mvdb_path is None or not settings.mvdb_path.exists():
        summary = build_mvdb_placeholder_summary(settings.mvdb_path)
        comparison_path, summary_path = save_mvdb_outputs(summary, settings.reports_dir, comparison_df=None)
        LOGGER.info(
            'Phase 10 placeholder complete. Requirements: %s | Summary: %s | Comparison path reserved: %s',
            requirements_path,
            summary_path,
            comparison_path,
        )
        return

    mvdb_df = load_mvdb_dataset(settings.mvdb_path)
    comparison_df, mvdb_value_column, join_columns = create_mvdb_comparison_dataset(predictions_df, mvdb_df)
    summary = summarize_mvdb_vs_ai(
        comparison_df,
        settings.mvdb_path,
        join_columns,
        mvdb_value_column,
    )
    comparison_path, summary_path = save_mvdb_outputs(summary, settings.reports_dir, comparison_df=comparison_df)
    LOGGER.info(
        'Phase 10 complete. Requirements: %s | Summary: %s | Comparison: %s',
        requirements_path,
        summary_path,
        comparison_path,
    )


if __name__ == '__main__':
    main()
