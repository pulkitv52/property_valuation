from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ZoneSummaryListResponse(BaseModel):
    results: list[dict[str, Any]]


class ZoneGeoJSONResponse(BaseModel):
    type: str
    features: list[dict[str, Any]]


class ZoneDetailResponse(BaseModel):
    payload: dict[str, Any]
