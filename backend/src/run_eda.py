from __future__ import annotations

import logging
import runpy
from pathlib import Path

import geopandas as gpd
import pandas as pd

from backend.src.config import configure_logging, ensure_directories, settings

LOGGER = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    ensure_directories()

    training_gdf = gpd.read_parquet(settings.processed_data_dir / 'model_training_dataset.parquet')
    predictions_df = pd.read_parquet(settings.processed_data_dir / 'valuation_predictions.parquet')

    module_globals = runpy.run_path('/tmp/eda_module.py')
    run_eda = module_globals['run_eda']
    save_eda_outputs = module_globals['save_eda_outputs']

    summary, tables = run_eda(training_gdf, predictions_df)
    json_path, md_path = save_eda_outputs(summary, tables, settings.reports_dir)
    LOGGER.info('EDA complete. JSON: %s | Markdown: %s', json_path, md_path)


if __name__ == '__main__':
    main()
