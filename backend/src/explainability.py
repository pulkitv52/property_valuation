from __future__ import annotations

import json
import logging
import pickle
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy import sparse
from xgboost import DMatrix

from backend.src.model_training import SegmentedModelPipeline

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


@dataclass(frozen=True)
class ExplainabilitySummary:
    model_type: str
    segment_values: list[str]
    total_training_rows: int
    sampled_explanations_count: int
    feature_importance_rows: int
    top_global_feature: str | None


def load_trained_model(model_path: Path) -> SegmentedModelPipeline:
    with model_path.open('rb') as file_obj:
        model = pickle.load(file_obj)
    if not isinstance(model, SegmentedModelPipeline):
        raise TypeError(f'Expected SegmentedModelPipeline, found {type(model)!r}')
    return model


def _map_transformed_features_to_base(preprocessor, categorical_features: list[str]) -> list[str]:
    feature_names = preprocessor.get_feature_names_out()
    base_names: list[str] = []
    for name in feature_names:
        if name.startswith('num__'):
            base_names.append(name.removeprefix('num__'))
            continue
        if name.startswith('cat__'):
            encoded_name = name.removeprefix('cat__')
            matched = None
            for column in categorical_features:
                prefix = f'{column}_'
                if encoded_name == column or encoded_name.startswith(prefix):
                    matched = column
                    break
            base_names.append(matched or encoded_name)
            continue
        base_names.append(name)
    return base_names


def _aggregate_importance(feature_names: list[str], values: np.ndarray) -> pd.DataFrame:
    importance_df = pd.DataFrame({'transformed_feature': feature_names, 'importance': values})
    importance_df['base_feature'] = importance_df['transformed_feature']
    importance_df['base_feature'] = importance_df['base_feature'].str.replace(r'^(num__|cat__)', '', regex=True)
    aggregated = (
        importance_df.groupby('base_feature', as_index=False)['importance']
        .sum()
        .sort_values('importance', ascending=False)
        .reset_index(drop=True)
    )
    return aggregated


def get_feature_importance(model: SegmentedModelPipeline) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for segment_value, pipeline in model.segment_models_.items():
        preprocessor = pipeline.named_steps['preprocessor']
        estimator = pipeline.named_steps['model']
        categorical_features = model.segment_feature_summaries_[segment_value]['categorical_features']
        base_names = _map_transformed_features_to_base(preprocessor, categorical_features)
        importance_values = np.asarray(estimator.feature_importances_, dtype=float)
        transformed_names = list(preprocessor.get_feature_names_out())
        segment_df = pd.DataFrame(
            {
                'segment_value': segment_value,
                'transformed_feature': transformed_names,
                'base_feature': base_names,
                'importance': importance_values,
            }
        )
        frames.append(segment_df)

    all_segments_df = pd.concat(frames, ignore_index=True)
    global_df = (
        all_segments_df.groupby('base_feature', as_index=False)['importance']
        .mean()
        .sort_values('importance', ascending=False)
        .reset_index(drop=True)
    )
    global_df.insert(0, 'segment_value', 'GLOBAL')
    global_df.insert(1, 'transformed_feature', global_df['base_feature'])
    combined = pd.concat([global_df, all_segments_df.sort_values(['segment_value', 'importance'], ascending=[True, False])], ignore_index=True)
    return combined


def _prepare_single_row_inputs(model: SegmentedModelPipeline, property_record: pd.Series) -> tuple[str, pd.DataFrame, pd.DataFrame, list[str]]:
    segment_value = str(pd.Series([property_record.get(model.segment_column)]).astype('string').fillna('Missing').iloc[0])
    if segment_value not in model.segment_models_:
        raise ValueError(f'No fitted segment model found for segment {segment_value!r}')

    required_inputs = model.segment_feature_inputs_[segment_value]
    row_df = pd.DataFrame([{column: property_record.get(column, np.nan) for column in required_inputs}])
    pipeline = model.segment_models_[segment_value]
    encoder = pipeline.named_steps['locality_target_encoder']
    preprocessor = pipeline.named_steps['preprocessor']
    encoded_df = encoder.transform(row_df)
    numeric_features = model.segment_feature_summaries_[segment_value]['numeric_features']
    categorical_features = model.segment_feature_summaries_[segment_value]['categorical_features']
    for column in encoded_df.columns:
        if column in numeric_features or column.endswith('_target_mean'):
            encoded_df[column] = pd.to_numeric(encoded_df[column], errors='coerce').astype(float)
        else:
            encoded_df[column] = encoded_df[column].astype(object)
            encoded_df[column] = encoded_df[column].where(pd.notna(encoded_df[column]), np.nan)
    transformed = preprocessor.transform(encoded_df)
    base_names = _map_transformed_features_to_base(preprocessor, categorical_features)
    return segment_value, row_df, transformed, base_names


def _compute_contributions(model: SegmentedModelPipeline, property_record: pd.Series) -> tuple[str, pd.DataFrame, float]:
    segment_value, _, transformed, base_names = _prepare_single_row_inputs(model, property_record)
    pipeline = model.segment_models_[segment_value]
    estimator = pipeline.named_steps['model']
    transformed_dense = transformed.toarray() if sparse.issparse(transformed) else np.asarray(transformed)
    dmatrix = DMatrix(transformed_dense)
    contribs = estimator.get_booster().predict(dmatrix, pred_contribs=True)[0]
    bias = float(contribs[-1])
    contrib_df = pd.DataFrame({'base_feature': base_names, 'contribution_log_target': contribs[:-1]})
    contrib_df = (
        contrib_df.groupby('base_feature', as_index=False)['contribution_log_target']
        .sum()
        .sort_values('contribution_log_target', ascending=False)
        .reset_index(drop=True)
    )
    return segment_value, contrib_df, bias


def _factor_reason(feature_name: str, property_record: pd.Series) -> str:
    value = property_record.get(feature_name, None)
    templates = {
        'Mouza_Name': f"local mouza context ({value})",
        'Road_Name': f"road-level locality context ({value})",
        'Road_code': f"road-code locality context ({value})",
        'PS_Name': f"police-station locality context ({value})",
        'GP': f"gram panchayat context ({value})",
        'Urban_flag': 'urban classification',
        'Rural_flag': 'rural classification',
        'Area': f"property area ({value})",
        'distance_to_nearest_road': 'distance to nearest road',
        'distance_to_nearest_facility': 'distance to nearest facility',
        'facility_count_1km': 'facility density within 1 km',
        'nearest_road_width': 'nearest road width',
        'Nature_Land_use_Code': f"current land-use code ({value})",
        'Proposed_Land_use_Code': f"proposed land-use code ({value})",
        'Flat_or_Land': f"property type ({value})",
        'Is_Property_on_Road': f"property road-frontage flag ({value})",
        'Adjacent_to_Metal_Road': f"metal-road adjacency ({value})",
        'property_district_Name_target_mean': f"district pricing context ({property_record.get('property_district_Name')})",
        'PS_Name_target_mean': f"PS-level pricing context ({property_record.get('PS_Name')})",
        'Mouza_Name_target_mean': f"mouza pricing context ({property_record.get('Mouza_Name')})",
        'Road_Name_target_mean': f"road-level pricing context ({property_record.get('Road_Name')})",
        'Road_code_target_mean': f"road-code pricing context ({property_record.get('Road_code')})",
        'GP_target_mean': f"GP-level pricing context ({property_record.get('GP')})",
        'Zone_no_target_mean': f"existing zone pricing context ({property_record.get('Zone_no')})",
    }
    return templates.get(feature_name, f'{feature_name}={value}')


def generate_property_explanation(
    property_record: pd.Series,
    prediction: float,
    feature_importance: pd.DataFrame,
    model: SegmentedModelPipeline,
    actual_value_per_area: float | None = None,
) -> dict[str, Any]:
    segment_value = str(pd.Series([property_record.get(model.segment_column)]).astype('string').fillna('Missing').iloc[0])
    explanation_method = 'xgboost_pred_contrib'
    try:
        segment_value, contribution_df, bias = _compute_contributions(model, property_record)
        top_positive = contribution_df.head(5).copy()
        top_negative = contribution_df.sort_values('contribution_log_target', ascending=True).head(5).copy()

        top_positive['reason'] = top_positive['base_feature'].map(lambda feature: _factor_reason(feature, property_record))
        top_negative['reason'] = top_negative['base_feature'].map(lambda feature: _factor_reason(feature, property_record))
    except Exception as exc:  # pragma: no cover - defensive fallback for segment-specific encoder edge cases
        LOGGER.warning('Falling back to heuristic local explanation for segment %s due to: %s', segment_value, exc)
        bias = float('nan')
        explanation_method = 'heuristic_global_feature_fallback'
        global_segment = feature_importance.loc[feature_importance['segment_value'] == 'GLOBAL', ['base_feature', 'importance']].head(10).copy()
        global_segment['reason'] = global_segment['base_feature'].map(lambda feature: _factor_reason(feature, property_record))
        top_positive = global_segment.head(5).rename(columns={'importance': 'contribution_log_target'})
        top_negative = pd.DataFrame(columns=['base_feature', 'contribution_log_target', 'reason'])

    global_segment = feature_importance.loc[feature_importance['segment_value'] == 'GLOBAL', ['base_feature', 'importance']].head(10)
    identifier_payload = {column: property_record.get(column) for column in IDENTIFIER_COLUMNS if column in property_record.index}

    explanation = {
        'identifiers': identifier_payload,
        'segment_value': segment_value,
        'explanation_method': explanation_method,
        'predicted_value_per_area': float(prediction),
        'actual_value_per_area': float(actual_value_per_area) if actual_value_per_area is not None and pd.notna(actual_value_per_area) else None,
        'prediction_bias_log_target': bias,
        'top_positive_factors': top_positive.to_dict(orient='records'),
        'top_negative_factors': top_negative.to_dict(orient='records'),
        'global_top_features': global_segment.to_dict(orient='records'),
        'plain_language_summary': (
            'Predicted value is influenced mainly by '
            + ', '.join(top_positive['reason'].head(3).tolist())
            + '. Downward pressure comes from '
            + ', '.join(top_negative['reason'].head(2).tolist())
            + '.'
        ),
    }
    return explanation


def _choose_sample_rows(predictions_df: pd.DataFrame, sample_size: int = 5) -> pd.DataFrame:
    ordered = predictions_df.sort_values(['absolute_error_value_per_area', 'predicted_value_per_area'], ascending=[False, False]).copy()
    high_error = ordered.head(min(2, len(ordered)))
    low_error = ordered.tail(min(2, len(ordered)))
    median_idx = len(ordered) // 2
    median_sample = ordered.iloc[[median_idx]] if len(ordered) else ordered.head(0)
    sample_df = pd.concat([high_error, low_error, median_sample], ignore_index=False).drop_duplicates()
    return sample_df.head(sample_size)


def run_explainability(
    model: SegmentedModelPipeline,
    training_gdf: gpd.GeoDataFrame,
    predictions_df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]], ExplainabilitySummary]:
    feature_importance_df = get_feature_importance(model)
    sample_rows = _choose_sample_rows(predictions_df, sample_size=5)
    sample_explanations: list[dict[str, Any]] = []
    for _, row in sample_rows.iterrows():
        sample_explanations.append(
            generate_property_explanation(
                row,
                prediction=float(row['predicted_value_per_area']),
                actual_value_per_area=float(row['actual_value_per_area']),
                feature_importance=feature_importance_df,
                model=model,
            )
        )

    global_top_feature = None
    global_rows = feature_importance_df.loc[feature_importance_df['segment_value'] == 'GLOBAL']
    if not global_rows.empty:
        global_top_feature = str(global_rows.iloc[0]['base_feature'])

    summary = ExplainabilitySummary(
        model_type=type(model).__name__,
        segment_values=sorted(list(model.segment_models_.keys())),
        total_training_rows=int(len(training_gdf)),
        sampled_explanations_count=int(len(sample_explanations)),
        feature_importance_rows=int(len(feature_importance_df)),
        top_global_feature=global_top_feature,
    )
    return feature_importance_df, sample_explanations, summary


def save_explainability_outputs(
    feature_importance_df: pd.DataFrame,
    sample_explanations: list[dict[str, Any]],
    summary: ExplainabilitySummary,
    reports_dir: Path,
) -> tuple[Path, Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    feature_importance_path = reports_dir / 'feature_importance.csv'
    sample_explanations_path = reports_dir / 'sample_property_explanations.json'
    summary_path = reports_dir / 'explainability_summary.json'

    feature_importance_df.to_csv(feature_importance_path, index=False)
    sample_explanations_path.write_text(json.dumps(sample_explanations, indent=2, default=str), encoding='utf-8')
    summary_path.write_text(json.dumps(asdict(summary), indent=2), encoding='utf-8')

    LOGGER.info('Saved feature importance to %s', feature_importance_path)
    LOGGER.info('Saved sample property explanations to %s', sample_explanations_path)
    LOGGER.info('Saved explainability summary to %s', summary_path)
    return feature_importance_path, sample_explanations_path, summary_path
