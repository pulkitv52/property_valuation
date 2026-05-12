from __future__ import annotations

import json
import importlib
import logging
import pickle
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd

from backend.src.config import settings
from backend.src.zone_clustering import ZONE_LABELS

LOGGER = logging.getLogger(__name__)
IDENTIFIER_COLUMNS = [
    'query_year',
    'query_no',
    'Deed_No',
    'Deed_Year',
    'sl_no_Property',
    'property_district_Name',
    'ps_code',
    'mouza_code',
    'plot_no',
    'bata_plot_no',
]


def build_property_id(record: pd.Series | dict[str, Any]) -> str:
    getter = record.get if isinstance(record, dict) else record.get
    query_year = getter('query_year', 'na')
    query_no = getter('query_no', 'na')
    sl_no_property = getter('sl_no_Property', 'na')
    district = str(getter('property_district_Name', 'na')).replace(' ', '_')
    return f'{query_year}-{query_no}-{sl_no_property}-{district}'


def normalize_for_json(value: Any) -> Any:
    if value is None or value is pd.NA:
        return None
    if isinstance(value, np.ndarray):
        return [normalize_for_json(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return normalize_for_json(value.item())
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and np.isnan(value):
        return None
    try:
        missing = pd.isna(value)
        if isinstance(missing, (bool, np.bool_)) and missing:
            return None
    except TypeError:
        pass
    if isinstance(value, dict):
        return {str(key): normalize_for_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [normalize_for_json(item) for item in value]
    return value


def required_artifact_paths() -> dict[str, Path]:
    return {
        'model': settings.models_dir / 'valuation_model.pkl',
        'model_metrics': settings.reports_dir / 'model_metrics.json',
        'model_comparison': settings.reports_dir / 'model_comparison.json',
        'predictions': settings.processed_data_dir / 'valuation_predictions.parquet',
        'zone_summary': settings.reports_dir / 'zone_summary.csv',
        'zone_polygons': settings.processed_data_dir / 'ai_zones.geojson',
        'zone_assignments': settings.processed_data_dir / 'ai_zone_assignments.parquet',
        'feature_importance': settings.reports_dir / 'feature_importance.csv',
        'sample_property_explanations': settings.reports_dir / 'sample_property_explanations.json',
        'explainability_summary': settings.reports_dir / 'explainability_summary.json',
    }


def validate_required_artifacts() -> list[str]:
    missing = [name for name, path in required_artifact_paths().items() if not path.exists()]
    if missing:
        LOGGER.error('Missing required API artifacts: %s', ', '.join(missing))
    return missing


def warm_artifact_caches() -> None:
    LOGGER.info('Warming API artifact caches')
    load_model_metrics()
    load_model_comparison()
    load_explainability_summary()
    load_mvdb_summary()
    load_zone_clustering_summary()
    load_zone_summary()
    load_zone_polygons()
    load_zone_assignments()
    load_predictions()
    load_feature_importance()
    load_sample_property_explanations()


class _ModuleRemappingUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str) -> Any:
        remapped_module = module
        if module == 'src' or module.startswith('src.'):
            remapped_module = module.replace('src', 'backend.src', 1)
        return super().find_class(remapped_module, name)


def _prepare_legacy_module_aliases() -> None:
    backend_src = importlib.import_module('backend.src')
    sys.modules.setdefault('src', backend_src)

    alias_pairs = {
        'src.config': 'backend.src.config',
        'src.model_training': 'backend.src.model_training',
        'src.explainability': 'backend.src.explainability',
        'src.services': 'backend.src.services',
        'src.schemas': 'backend.src.schemas',
    }
    for legacy_name, new_name in alias_pairs.items():
        sys.modules.setdefault(legacy_name, importlib.import_module(new_name))


@lru_cache(maxsize=1)
def load_model() -> Any:
    model_path = settings.models_dir / 'valuation_model.pkl'
    LOGGER.info('Loading model artifact from %s', model_path)
    _prepare_legacy_module_aliases()
    with model_path.open('rb') as file_obj:
        return _ModuleRemappingUnpickler(file_obj).load()


@lru_cache(maxsize=1)
def load_model_metrics() -> dict[str, Any]:
    return json.loads((settings.reports_dir / 'model_metrics.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def load_model_comparison() -> dict[str, Any]:
    return json.loads((settings.reports_dir / 'model_comparison.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def load_explainability_summary() -> dict[str, Any]:
    return json.loads((settings.reports_dir / 'explainability_summary.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def load_mvdb_summary() -> dict[str, Any]:
    path = settings.reports_dir / 'mvdb_vs_ai_summary.json'
    if not path.exists():
        return {'status': 'not_run'}
    return json.loads(path.read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def load_zone_clustering_summary() -> dict[str, Any]:
    return json.loads((settings.reports_dir / 'zone_clustering_summary.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def load_zone_summary() -> pd.DataFrame:
    df = pd.read_csv(settings.reports_dir / 'zone_summary.csv')
    if 'ai_zone' in df.columns:
        df = df.copy()
        df['ai_zone_name'] = df['ai_zone'].map(lambda value: ZONE_LABELS.get(value, (value, ''))[0])
        df['ai_zone_description'] = df['ai_zone'].map(lambda value: ZONE_LABELS.get(value, (value, ''))[1])
    return df


@lru_cache(maxsize=1)
def load_zone_polygons() -> gpd.GeoDataFrame:
    return gpd.read_file(settings.processed_data_dir / 'ai_zones.geojson')


@lru_cache(maxsize=1)
def load_zone_assignments() -> pd.DataFrame:
    df = pd.read_parquet(settings.processed_data_dir / 'ai_zone_assignments.parquet')
    if 'ai_zone' in df.columns:
        df = df.copy()
        # Normalize to canonical labels in case persisted artifacts were generated
        # before the latest naming scheme was introduced.
        df['ai_zone_name'] = df['ai_zone'].map(lambda value: ZONE_LABELS.get(value, (value, ''))[0])
        df['ai_zone_description'] = df['ai_zone'].map(lambda value: ZONE_LABELS.get(value, (value, ''))[1])
    if 'property_id' not in df.columns:
        df = df.copy()
        df['property_id'] = df.apply(build_property_id, axis=1)
    if 'Types of area Measurement' not in df.columns:
        unit_df = load_transaction_units()
        df = df.merge(unit_df, on='property_id', how='left')
    return df


@lru_cache(maxsize=1)
def load_predictions() -> pd.DataFrame:
    df = pd.read_parquet(settings.processed_data_dir / 'valuation_predictions.parquet')
    if 'property_id' not in df.columns:
        df = df.copy()
        df['property_id'] = df.apply(build_property_id, axis=1)
    if 'Types of area Measurement' not in df.columns:
        unit_df = load_transaction_units()
        df = df.merge(unit_df, on='property_id', how='left')
    return df


@lru_cache(maxsize=1)
def load_transaction_units() -> pd.DataFrame:
    merged_df = pd.read_parquet(settings.interim_data_dir / 'transactions_property_merged.parquet')
    if 'property_id' not in merged_df.columns:
        merged_df = merged_df.copy()
        merged_df['property_id'] = merged_df.apply(build_property_id, axis=1)
    columns = ['property_id', 'Types of area Measurement']
    available_columns = [column for column in columns if column in merged_df.columns]
    unit_df = merged_df[available_columns].drop_duplicates(subset=['property_id'])
    return unit_df


@lru_cache(maxsize=1)
def load_feature_importance() -> pd.DataFrame:
    return pd.read_csv(settings.reports_dir / 'feature_importance.csv')


@lru_cache(maxsize=1)
def load_sample_property_explanations() -> list[dict[str, Any]]:
    return json.loads((settings.reports_dir / 'sample_property_explanations.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def load_error_analysis() -> pd.DataFrame:
    return pd.read_csv(settings.reports_dir / 'error_analysis.csv')
