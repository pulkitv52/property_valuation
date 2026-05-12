from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from backend.src.config import configure_logging, ensure_directories
from backend.src.inference import run_inference


def _read_input(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported input format: {suffix}. Use csv/xlsx/parquet")


def _write_output(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df.to_csv(path, index=False)
        return
    if suffix == ".parquet":
        df.to_parquet(path, index=False)
        return
    raise ValueError(f"Unsupported output format: {suffix}. Use csv/parquet")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run valuation model inference on single/batch input.")
    parser.add_argument("--input", required=True, help="Input file path (.csv/.xlsx/.parquet)")
    parser.add_argument(
        "--output",
        default="data/processed/inference_predictions.csv",
        help="Output file path (.csv/.parquet)",
    )
    parser.add_argument(
        "--summary-output",
        default="reports/inference_summary.json",
        help="Inference summary JSON output path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_directories()
    configure_logging()

    input_path = Path(args.input)
    output_path = Path(args.output)
    summary_path = Path(args.summary_output)

    input_df = _read_input(input_path)
    predictions_df, summary = run_inference(input_df)

    _write_output(predictions_df, output_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")

    print(f"Inference input: {input_path}")
    print(f"Predictions saved: {output_path}")
    print(f"Summary saved: {summary_path}")


if __name__ == "__main__":
    main()

