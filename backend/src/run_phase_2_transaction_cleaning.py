from __future__ import annotations

import logging

from backend.src.config import configure_logging, ensure_directories, settings
from backend.src.data_cleaning import clean_transaction_data, save_cleaned_transactions
from backend.src.data_loader import load_transaction_data

LOGGER = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    ensure_directories()

    transactions = load_transaction_data()
    cleaned_transactions, summary = clean_transaction_data(transactions)
    parquet_path, summary_path = save_cleaned_transactions(
        cleaned_transactions,
        summary,
        settings.interim_data_dir,
        settings.reports_dir,
    )
    LOGGER.info("Phase 2 complete. Cleaned data: %s | Summary: %s", parquet_path, summary_path)


if __name__ == "__main__":
    main()
