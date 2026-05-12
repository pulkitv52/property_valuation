from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PropertyRecordResponse(BaseModel):
    property_id: str
    payload: dict[str, Any]


class PropertySearchResponse(BaseModel):
    results: list[dict[str, Any]]


class PredictionRequest(BaseModel):
    records: list[dict[str, Any]]


class PredictionResponse(BaseModel):
    results: list[dict[str, Any]]
    summary: dict[str, Any]
