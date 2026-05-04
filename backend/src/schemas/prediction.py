from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PropertyRecordResponse(BaseModel):
    property_id: str
    payload: dict[str, Any]


class PropertySearchResponse(BaseModel):
    results: list[dict[str, Any]]
