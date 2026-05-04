from __future__ import annotations

from typing import Any

DECIMAL_TO_SQFT = 435.6


def normalize_area_measurement(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text or text == 'nan':
        return None
    if text in {'sq ft', 'sqft', 'square feet', 'square foot', 'sft', 'ft2'}:
        return 'sqft'
    if text in {'decimal', 'dec'}:
        return 'decimal'
    return text


def area_to_sqft(area: float | int | None, measurement: Any) -> float | None:
    if area is None:
        return None
    unit = normalize_area_measurement(measurement)
    area_value = float(area)
    if unit == 'decimal':
        return area_value * DECIMAL_TO_SQFT
    if unit == 'sqft':
        return area_value
    return None


def value_per_area_to_sqft(value_per_area: float | int | None, measurement: Any) -> float | None:
    if value_per_area is None:
        return None
    unit = normalize_area_measurement(measurement)
    value = float(value_per_area)
    if unit == 'decimal':
        return value / DECIMAL_TO_SQFT
    if unit == 'sqft':
        return value
    return None


def area_unit_label(measurement: Any) -> str:
    unit = normalize_area_measurement(measurement)
    if unit == 'decimal':
        return 'Decimal'
    if unit == 'sqft':
        return 'Sq ft'
    return 'Unknown'
