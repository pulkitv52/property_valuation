from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.src.config import settings
from backend.src.schemas.explanation import (
    FeatureImportanceResponse,
    PropertyExplanationResponse,
    SampleExplanationsResponse,
)
from backend.src.schemas.prediction import PropertyRecordResponse, PropertySearchResponse
from backend.src.schemas.summary import DashboardSummaryResponse, HealthResponse, MVDBStatusResponse
from backend.src.schemas.zone import ZoneDetailResponse, ZoneGeoJSONResponse, ZoneSummaryListResponse
from backend.src.services.dashboard_service import get_dashboard_summary
from backend.src.services.explanation_service import (
    get_global_feature_importance,
    get_property_explanation,
    get_sample_explanations,
)
from backend.src.services.prediction_service import get_property_by_id, list_properties
from backend.src.services.zone_service import get_zone_by_id, get_zone_geojson, get_zone_summary_records
from backend.src.services.artifact_service import load_mvdb_summary, validate_required_artifacts, warm_artifact_caches

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    missing_artifacts = validate_required_artifacts()
    if missing_artifacts:
        raise RuntimeError(f'Missing required API artifacts: {", ".join(missing_artifacts)}')
    warm_artifact_caches()
    LOGGER.info(
        'API startup complete on %s:%s with allowed origins: %s',
        settings.api_host,
        settings.api_port,
        settings.cors_allowed_origins_list,
    )
    yield

app = FastAPI(
    title='AI Property Valuation PoC API',
    version='0.1.0',
    description='Artifact-driven API for valuation metrics, AI zones, property lookup, and explainability.',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health', response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status='ok')


@app.get('/summary', response_model=DashboardSummaryResponse)
def summary() -> DashboardSummaryResponse:
    return DashboardSummaryResponse(**get_dashboard_summary())


@app.get('/properties', response_model=PropertySearchResponse)
def properties(
    limit: int = Query(default=25, ge=1, le=200),
    district: str | None = None,
    mouza: str | None = None,
) -> PropertySearchResponse:
    return PropertySearchResponse(results=list_properties(limit=limit, district=district, mouza=mouza))


@app.get('/property/{property_id}', response_model=PropertyRecordResponse)
def property_detail(property_id: str) -> PropertyRecordResponse:
    try:
        payload = get_property_by_id(property_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f'Property {property_id} not found') from exc
    return PropertyRecordResponse(property_id=property_id, payload=payload)


@app.get('/zones', response_model=ZoneSummaryListResponse)
def zones() -> ZoneSummaryListResponse:
    return ZoneSummaryListResponse(results=get_zone_summary_records())


@app.get('/zones/geojson', response_model=ZoneGeoJSONResponse)
def zones_geojson() -> ZoneGeoJSONResponse:
    payload = get_zone_geojson()
    return ZoneGeoJSONResponse(**payload)


@app.get('/zones/{zone_id}', response_model=ZoneDetailResponse)
def zone_detail(zone_id: str) -> ZoneDetailResponse:
    try:
        payload = get_zone_by_id(zone_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f'Zone {zone_id} not found') from exc
    return ZoneDetailResponse(payload=payload)


@app.get('/explanations/global', response_model=FeatureImportanceResponse)
def explanations_global(limit: int = Query(default=25, ge=1, le=200)) -> FeatureImportanceResponse:
    return FeatureImportanceResponse(results=get_global_feature_importance(limit=limit))


@app.get('/explanations/samples', response_model=SampleExplanationsResponse)
def explanations_samples() -> SampleExplanationsResponse:
    return SampleExplanationsResponse(results=get_sample_explanations())


@app.get('/valuation-explanation/{property_id}', response_model=PropertyExplanationResponse)
def valuation_explanation(property_id: str) -> PropertyExplanationResponse:
    try:
        payload = get_property_explanation(property_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f'Property {property_id} not found') from exc
    return PropertyExplanationResponse(payload=payload)


@app.get('/mvdb-status', response_model=MVDBStatusResponse)
def mvdb_status() -> MVDBStatusResponse:
    payload = load_mvdb_summary()
    return MVDBStatusResponse(**payload)
