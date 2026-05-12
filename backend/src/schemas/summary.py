from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class DashboardSummaryResponse(BaseModel):
    property_count: int
    best_candidate_name: str
    metrics: dict[str, Any]
    zones: dict[str, Any]
    explainability: dict[str, Any]
    property_type_analysis: list[dict[str, Any]]
    zone_property_type_analysis: list[dict[str, Any]] | None = None
    mvdb_status: str


class MVDBStatusResponse(BaseModel):
    status: str
    mvdb_data_available: bool | None = None
    notes: list[str] | None = None
