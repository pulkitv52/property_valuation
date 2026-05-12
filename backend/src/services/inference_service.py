from __future__ import annotations

from dataclasses import asdict
from typing import Any

import pandas as pd

from backend.src.inference import run_inference
from backend.src.services.artifact_service import normalize_for_json


def predict_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not records:
        raise ValueError("Prediction request must include at least one record")

    input_df = pd.DataFrame(records)
    predictions_df, summary = run_inference(input_df)
    payload_rows = [normalize_for_json(row) for row in predictions_df.to_dict(orient="records")]
    return payload_rows, normalize_for_json(asdict(summary))

