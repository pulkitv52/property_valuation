from __future__ import annotations

import json
import logging
import os
import pickle
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, train_test_split
from sklearn.pipeline import Pipeline

from backend.src.model_training import (
    DEFAULT_RANDOM_STATE,
    TARGET_COLUMN,
    TARGET_LOG_COLUMN,
    SubsetMode,
    prepare_model_inputs,
)

LOGGER = logging.getLogger(__name__)
os.environ.setdefault('MPLCONFIGDIR', '/tmp/matplotlib')


@dataclass(frozen=True)
class EvaluationSummary:
    evaluation_row_count: int
    subset_mode: str
    segment_column: str | None
    segment_value: str | None
    mae: float
    rmse: float
    mape: float
    r2: float
    mae_market_value: float
    rmse_market_value: float
    mape_market_value: float
    random_state: int
    test_size: float
    evaluation_model_source: str


@dataclass(frozen=True)
class KFoldCVSummary:
    n_splits: int
    subset_mode: str
    segment_column: str | None
    segment_value: str | None
    cv_r2_mean: float
    cv_r2_std: float
    cv_mape_mean: float
    cv_mape_std: float
    cv_mae_mean: float
    cv_mae_std: float
    cv_r2_scores: list[float]
    cv_mape_scores: list[float]
    cv_mae_scores: list[float]



def mean_absolute_percentage_error(y_true: pd.Series | np.ndarray, y_pred: pd.Series | np.ndarray) -> float:
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)
    mask = y_true_arr != 0
    if not mask.any():
        return float('nan')
    return float(np.mean(np.abs((y_true_arr[mask] - y_pred_arr[mask]) / y_true_arr[mask])) * 100)



def load_trained_model(model_path: Path) -> Pipeline:
    with model_path.open('rb') as file_obj:
        return pickle.load(file_obj)



def build_test_split(
    training_gdf: gpd.GeoDataFrame,
    subset_mode: SubsetMode = 'full',
    segment_column: str | None = None,
    segment_value: str | None = None,
    test_size: float = 0.2,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.DataFrame]:
    X, y, _, _, _, usable_df = prepare_model_inputs(
        training_gdf,
        subset_mode=subset_mode,
        segment_column=segment_column,
        segment_value=segment_value,
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
    )
    evaluation_df = usable_df.loc[X_test.index].copy()
    return X_train, X_test, y_train, y_test, evaluation_df



def evaluate_model(
    model: Pipeline,
    training_gdf: gpd.GeoDataFrame,
    subset_mode: SubsetMode = 'full',
    segment_column: str | None = None,
    segment_value: str | None = None,
    test_size: float = 0.2,
    random_state: int = DEFAULT_RANDOM_STATE,
    evaluation_model_source: str = 'loaded_pickle',
) -> tuple[EvaluationSummary, pd.DataFrame]:
    _, X_test, _, y_test, evaluation_df = build_test_split(
        training_gdf,
        subset_mode=subset_mode,
        segment_column=segment_column,
        segment_value=segment_value,
        test_size=test_size,
        random_state=random_state,
    )

    pred_log = model.predict(X_test)
    pred_value_per_area = np.expm1(pred_log)
    actual_value_per_area = np.expm1(y_test.to_numpy())

    area = pd.to_numeric(evaluation_df['Area'], errors='coerce').to_numpy(dtype=float)
    predicted_market_value = pred_value_per_area * area
    actual_market_value = actual_value_per_area * area

    summary = EvaluationSummary(
        evaluation_row_count=int(len(X_test)),
        subset_mode=subset_mode,
        segment_column=segment_column,
        segment_value=segment_value,
        mae=float(mean_absolute_error(actual_value_per_area, pred_value_per_area)),
        rmse=float(np.sqrt(mean_squared_error(actual_value_per_area, pred_value_per_area))),
        mape=float(mean_absolute_percentage_error(actual_value_per_area, pred_value_per_area)),
        r2=float(r2_score(actual_value_per_area, pred_value_per_area)),
        mae_market_value=float(mean_absolute_error(actual_market_value, predicted_market_value)),
        rmse_market_value=float(np.sqrt(mean_squared_error(actual_market_value, predicted_market_value))),
        mape_market_value=float(mean_absolute_percentage_error(actual_market_value, predicted_market_value)),
        random_state=random_state,
        test_size=test_size,
        evaluation_model_source=evaluation_model_source,
    )

    predictions_df = evaluation_df.copy()
    predictions_df['actual_value_per_area'] = actual_value_per_area
    predictions_df['predicted_value_per_area'] = pred_value_per_area
    predictions_df['actual_market_value_from_target'] = actual_market_value
    predictions_df['predicted_market_value'] = predicted_market_value
    predictions_df['absolute_error_value_per_area'] = np.abs(
        predictions_df['actual_value_per_area'] - predictions_df['predicted_value_per_area']
    )
    predictions_df['absolute_error_market_value'] = np.abs(
        predictions_df['actual_market_value_from_target'] - predictions_df['predicted_market_value']
    )
    return summary, predictions_df



def cross_validate_model(
    training_gdf: gpd.GeoDataFrame,
    candidate_name: str,
    subset_mode: SubsetMode = 'full',
    segment_column: str | None = None,
    segment_value: str | None = None,
    n_splits: int = 5,
    max_training_sample_size: int | None = 30000,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> KFoldCVSummary:
    """Run K-Fold cross-validation and return aggregated metric statistics."""
    from backend.src.model_training import build_candidate_pipeline

    X, y, numeric_features, categorical_features, _, _ = prepare_model_inputs(
        training_gdf,
        subset_mode=subset_mode,
        segment_column=segment_column,
        segment_value=segment_value,
    )

    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    r2_scores, mape_scores, mae_scores = [], [], []

    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train_fold, X_test_fold = X.iloc[train_idx], X.iloc[test_idx]
        y_train_fold, y_test_fold = y.iloc[train_idx], y.iloc[test_idx]

        # Optionally sample within fold to keep training fast
        if max_training_sample_size and len(X_train_fold) > max_training_sample_size:
            sample_idx = X_train_fold.sample(n=max_training_sample_size, random_state=random_state).index
            X_train_fold = X_train_fold.loc[sample_idx]
            y_train_fold = y_train_fold.loc[sample_idx]

        pipeline, _, _, _ = build_candidate_pipeline(
            candidate_name, numeric_features, categorical_features, random_state=random_state
        )
        pipeline.fit(X_train_fold, y_train_fold)
        pred_log = pipeline.predict(X_test_fold)

        pred = np.expm1(pred_log)
        actual = np.expm1(y_test_fold.to_numpy())

        r2_scores.append(float(r2_score(actual, pred)))
        mae_scores.append(float(mean_absolute_error(actual, pred)))
        mask = actual != 0
        mape_scores.append(float(np.mean(np.abs((actual[mask] - pred[mask]) / actual[mask])) * 100))
        LOGGER.info('CV Fold %d/%d — R²: %.4f  MAPE: %.2f%%', fold_idx + 1, n_splits, r2_scores[-1], mape_scores[-1])

    return KFoldCVSummary(
        n_splits=n_splits,
        subset_mode=subset_mode,
        segment_column=segment_column,
        segment_value=segment_value,
        cv_r2_mean=float(np.mean(r2_scores)),
        cv_r2_std=float(np.std(r2_scores)),
        cv_mape_mean=float(np.mean(mape_scores)),
        cv_mape_std=float(np.std(mape_scores)),
        cv_mae_mean=float(np.mean(mae_scores)),
        cv_mae_std=float(np.std(mae_scores)),
        cv_r2_scores=r2_scores,
        cv_mape_scores=mape_scores,
        cv_mae_scores=mae_scores,
    )



def build_error_analysis(predictions_df: pd.DataFrame) -> pd.DataFrame:
    group_specs = [
        ('district', 'property_district_Name'),
        ('mouza', 'Mouza_Name'),
        ('property_type', 'Flat_or_Land'),
    ]
    frames: list[pd.DataFrame] = []

    for level_name, column in group_specs:
        if column not in predictions_df.columns:
            continue
        working = predictions_df[[column, 'actual_value_per_area', 'predicted_value_per_area']].copy()
        working[column] = working[column].fillna('Missing')
        grouped = working.groupby(column, dropna=False)
        rows = []
        for group_name, group_df in grouped:
            actual = group_df['actual_value_per_area'].to_numpy(dtype=float)
            predicted = group_df['predicted_value_per_area'].to_numpy(dtype=float)
            rows.append(
                {
                    'level': level_name,
                    'group_name': group_name,
                    'count': int(len(group_df)),
                    'mae': float(mean_absolute_error(actual, predicted)),
                    'rmse': float(np.sqrt(mean_squared_error(actual, predicted))),
                    'mape': float(mean_absolute_percentage_error(actual, predicted)),
                    'mean_actual_value_per_area': float(np.mean(actual)),
                    'mean_predicted_value_per_area': float(np.mean(predicted)),
                }
            )
        frames.append(pd.DataFrame(rows))

    if not frames:
        return pd.DataFrame(
            columns=['level', 'group_name', 'count', 'mae', 'rmse', 'mape', 'mean_actual_value_per_area', 'mean_predicted_value_per_area']
        )
    return pd.concat(frames, ignore_index=True)



def save_predicted_vs_actual_plot(predictions_df: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sample_df = predictions_df[['actual_value_per_area', 'predicted_value_per_area']].sample(
        n=min(5000, len(predictions_df)),
        random_state=DEFAULT_RANDOM_STATE,
    )

    plt.figure(figsize=(8, 6))
    plt.scatter(sample_df['actual_value_per_area'], sample_df['predicted_value_per_area'], alpha=0.25, s=10)
    max_val = float(max(sample_df['actual_value_per_area'].max(), sample_df['predicted_value_per_area'].max()))
    plt.plot([0, max_val], [0, max_val], linestyle='--')
    plt.xlabel('Actual Value Per Area')
    plt.ylabel('Predicted Value Per Area')
    plt.title('Predicted vs Actual Value Per Area')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    LOGGER.info('Saved predicted vs actual plot to %s', output_path)
    return output_path



def save_evaluation_outputs(
    summary: EvaluationSummary,
    predictions_df: pd.DataFrame,
    error_analysis_df: pd.DataFrame,
    reports_dir: Path,
    processed_dir: Path,
) -> tuple[Path, Path, Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = reports_dir / 'model_metrics.json'
    error_analysis_path = reports_dir / 'error_analysis.csv'
    plot_path = reports_dir / 'predicted_vs_actual.png'
    predictions_path = processed_dir / 'valuation_predictions.parquet'

    metrics_path.write_text(json.dumps(asdict(summary), indent=2), encoding='utf-8')
    error_analysis_df.to_csv(error_analysis_path, index=False)
    predictions_df.to_parquet(predictions_path, index=False)
    save_predicted_vs_actual_plot(predictions_df, plot_path)

    LOGGER.info('Saved model metrics to %s', metrics_path)
    LOGGER.info('Saved error analysis to %s', error_analysis_path)
    LOGGER.info('Saved valuation predictions to %s', predictions_path)
    return metrics_path, error_analysis_path, plot_path, predictions_path
