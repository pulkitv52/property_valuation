from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class FeatureImportanceResponse(BaseModel):
    results: list[dict[str, Any]]


class SampleExplanationsResponse(BaseModel):
    results: list[dict[str, Any]]


class PropertyExplanationResponse(BaseModel):
    payload: dict[str, Any]
