from __future__ import annotations

import json
import logging
import pickle
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

try:
    from xgboost import XGBRegressor
except ImportError:  # pragma: no cover
    XGBRegressor = None

try:
    from lightgbm import LGBMRegressor
except ImportError:  # pragma: no cover
    LGBMRegressor = None

LOGGER = logging.getLogger(__name__)
TARGET_COLUMN = "value_per_area"
TARGET_LOG_COLUMN = "log_value_per_area"
DEFAULT_RANDOM_STATE = 42
LOCALITY_TARGET_COLUMNS = [
    "property_district_Name",
    "PS_Name",
    "Mouza_Name",
    "Zone_no",
    "Road_Name",
    "Road_code",
    "GP",
]
LOCALITY_TARGET_OUTPUT_COLUMNS = [f"{column}_target_mean" for column in LOCALITY_TARGET_COLUMNS]

NUMERIC_FEATURES = [
    "Area",
    "Approach_Road_Width",
    "distance_to_nearest_road",
    "distance_to_nearest_road_missing_flag",
    "distance_to_nearest_facility",
    "distance_to_nearest_facility_missing_flag",
    "facility_count_500m",
    "facility_count_1km",
    "latitude",
    "longitude",
    "property_match_found",
    "property_record_count",
    "spatial_features_available",
    "geometry_missing_flag",
    "property_geometry_area",
    "property_geometry_perimeter",
    "property_shape_compactness",
    "registration_year",
    "registration_month",
    "registration_quarter",
    "registration_dayofweek",
    "presentation_year",
    "presentation_month",
    "presentation_quarter",
    "presentation_dayofweek",
    "registration_presentation_gap_days",
    "presentation_hour",
    "presentation_is_afternoon",
    "Is_Property_on_Road_flag",
    "Adjacent_to_Metal_Road_flag",
    "Urban_flag",
    "Rural_flag",
    "Litigated_Property_flag",
    "log_distance_to_nearest_road",
    "nearest_road_width",
    "log_distance_to_nearest_facility",
    "facility_group_education_count_1km",
    "facility_group_health_count_1km",
    "facility_group_market_count_1km",
    "facility_group_other_count_1km",
    "facility_group_recreation_count_1km",
    "facility_group_religious_tourism_count_1km",
    "facility_group_transport_count_1km",
    *LOCALITY_TARGET_OUTPUT_COLUMNS,
]
CATEGORICAL_FEATURES = [
    "property_district_Name",
    "PS_Name",
    "Mouza_Name",
    "Road_Name",
    "Road_code",
    "Transaction_code",
    "Transaction_Name",
    "GP",
    "Nature_Land_use_Code",
    "Proposed_Land_use_Code",
    "Is_Property_on_Road",
    "Adjacent_to_Metal_Road",
    "Zone_no",
    "Proposed_Land_use_Name",
    "Nature_Land_use_Name",
    "Urban",
    "Rural",
    "Road_Category",
    "Flat_or_Land",
    "Litigated_Property",
    "nearest_road_category",
    "nearest_road_surface",
    "nearest_facility_group",
]

SubsetMode = Literal["full", "matched_only"]
SegmentColumn = Literal["Flat_or_Land"]


@dataclass(frozen=True)
class ModelTrainingSummary:
    input_row_count: int
    rows_used_for_training: int
    subset_mode: str
    train_row_count: int
    test_row_count: int
    train_row_count_after_sampling: int
    target_column: str
    target_transform: str
    model_name: str
    numeric_features: list[str]
    categorical_features: list[str]
    dropped_categorical_features: list[str]
    preprocessing_kind: str
    random_state: int
    test_size: float
    model_params: dict[str, int | float | str | None]
    max_training_sample_size: int | None
    segment_column: str | None = None
    segment_value: str | None = None


@dataclass(frozen=True)
class TrainedModelArtifacts:
    pipeline: Pipeline
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    summary: ModelTrainingSummary


@dataclass(frozen=True)
class CandidateResult:
    candidate_name: str
    subset_mode: str
    model_name: str
    preprocessing_kind: str
    train_rows_after_sampling: int
    test_row_count: int
    mae: float
    rmse: float
    mape: float
    r2: float
    max_training_sample_size: int | None
    segment_column: str | None = None
    segment_value: str | None = None


@dataclass(frozen=True)
class ModelComparisonResult:
    best_candidate_name: str
    selection_metric: str
    candidates: list[CandidateResult]


class LocalityTargetEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, columns: list[str], smoothing: float = 50.0) -> None:
        self.columns = columns
        self.smoothing = smoothing

    def fit(self, X: pd.DataFrame, y: pd.Series | np.ndarray) -> "LocalityTargetEncoder":
        X_df = pd.DataFrame(X).copy()
        y_series = pd.Series(y, index=X_df.index, dtype=float)
        self.global_mean_ = float(y_series.mean())
        self.available_columns_ = [column for column in self.columns if column in X_df.columns]
        self.mapping_: dict[str, dict[str, float]] = {}

        for column in self.available_columns_:
            working = pd.DataFrame(
                {
                    "category": X_df[column].astype("string").fillna("Missing"),
                    "target": y_series,
                }
            )
            grouped = working.groupby("category", dropna=False)["target"].agg(["mean", "count"]).reset_index()
            grouped["smoothed_mean"] = (
                grouped["count"] * grouped["mean"] + self.smoothing * self.global_mean_
            ) / (grouped["count"] + self.smoothing)
            self.mapping_[column] = dict(zip(grouped["category"].astype(str), grouped["smoothed_mean"].astype(float)))
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_df = pd.DataFrame(X).copy()
        for column in self.columns:
            output_column = f"{column}_target_mean"
            if column not in X_df.columns or column not in getattr(self, "mapping_", {}):
                X_df[output_column] = float(getattr(self, "global_mean_", np.nan))
                continue
            category_series = X_df[column].astype("string").fillna("Missing")
            X_df[output_column] = (
                category_series.astype(str).map(self.mapping_[column]).fillna(self.global_mean_).astype(float)
            )
        return X_df


class SegmentedModelPipeline(BaseEstimator):
    def __init__(
        self,
        base_candidate_name: str,
        segment_column: str,
        segment_values: list[str],
        numeric_features: list[str],
        categorical_features: list[str],
        random_state: int = DEFAULT_RANDOM_STATE,
        prune_features_by_segment: bool = False,
    ) -> None:
        self.base_candidate_name = base_candidate_name
        self.segment_column = segment_column
        self.segment_values = segment_values
        self.numeric_features = numeric_features
        self.categorical_features = categorical_features
        self.random_state = random_state
        self.prune_features_by_segment = prune_features_by_segment

    def _select_segment_features(self, X_segment: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
        target_encoded_numeric = set(LOCALITY_TARGET_OUTPUT_COLUMNS)
        if not self.prune_features_by_segment:
            required_inputs = list(
                dict.fromkeys(
                    [column for column in self.numeric_features if column not in target_encoded_numeric]
                    + self.categorical_features
                    + LOCALITY_TARGET_COLUMNS
                )
            )
            return self.numeric_features, self.categorical_features, required_inputs

        usable_numeric: list[str] = []
        for column in self.numeric_features:
            if column in target_encoded_numeric:
                usable_numeric.append(column)
                continue
            if column not in X_segment.columns:
                continue
            non_missing = pd.to_numeric(X_segment[column], errors="coerce").dropna()
            if len(non_missing) == 0 or non_missing.nunique() <= 1:
                continue
            usable_numeric.append(column)

        categorical_candidates = [column for column in self.categorical_features if column in X_segment.columns]
        usable_categorical, _ = _filter_usable_categorical_features(X_segment, categorical_candidates)
        required_inputs = list(
            dict.fromkeys(usable_numeric + usable_categorical + [c for c in LOCALITY_TARGET_COLUMNS if c in X_segment.columns])
        )
        required_inputs = [column for column in required_inputs if column not in target_encoded_numeric]
        return usable_numeric, usable_categorical, required_inputs

    def fit(self, X: pd.DataFrame, y: pd.Series | np.ndarray) -> "SegmentedModelPipeline":
        X_df = pd.DataFrame(X).copy()
        y_series = pd.Series(y, index=X_df.index, dtype=float)
        self.segment_models_: dict[str, Pipeline] = {}
        self.segment_feature_inputs_: dict[str, list[str]] = {}
        self.segment_feature_summaries_: dict[str, dict[str, list[str] | int]] = {}
        for segment_value in self.segment_values:
            mask = X_df[self.segment_column].astype("string").fillna("Missing") == segment_value
            if not mask.any():
                continue
            X_segment = X_df.loc[mask].copy()
            segment_numeric_features, segment_categorical_features, required_inputs = self._select_segment_features(X_segment)
            segment_pipeline, _, _, _ = build_candidate_pipeline(
                self.base_candidate_name,
                segment_numeric_features,
                segment_categorical_features,
                random_state=self.random_state,
            )
            segment_pipeline.fit(X_segment[required_inputs], y_series.loc[mask])
            self.segment_models_[segment_value] = segment_pipeline
            self.segment_feature_inputs_[segment_value] = required_inputs
            self.segment_feature_summaries_[segment_value] = {
                "numeric_features": segment_numeric_features,
                "categorical_features": segment_categorical_features,
                "input_feature_count": len(required_inputs),
            }

        fallback_numeric_features, fallback_categorical_features, fallback_inputs = self._select_segment_features(X_df)
        self.fallback_pipeline_, _, _, _ = build_candidate_pipeline(
            self.base_candidate_name,
            fallback_numeric_features,
            fallback_categorical_features,
            random_state=self.random_state,
        )
        self.fallback_pipeline_.fit(X_df[fallback_inputs], y_series)
        self.fallback_feature_inputs_ = fallback_inputs
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_df = pd.DataFrame(X).copy()
        predictions = np.full(shape=len(X_df), fill_value=np.nan, dtype=float)
        for segment_value, segment_model in getattr(self, "segment_models_", {}).items():
            mask = X_df[self.segment_column].astype("string").fillna("Missing") == segment_value
            if mask.any():
                required_inputs = self.segment_feature_inputs_[segment_value]
                predictions[mask.to_numpy()] = segment_model.predict(X_df.loc[mask, required_inputs])

        missing_mask = np.isnan(predictions)
        if missing_mask.any():
            fallback_pred = self.fallback_pipeline_.predict(X_df.loc[missing_mask, self.fallback_feature_inputs_])
            predictions[missing_mask] = fallback_pred
        return predictions



def mean_absolute_percentage_error(y_true: pd.Series | np.ndarray, y_pred: pd.Series | np.ndarray) -> float:
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)
    mask = y_true_arr != 0
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((y_true_arr[mask] - y_pred_arr[mask]) / y_true_arr[mask])) * 100)



def _available_columns(df: pd.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column in df.columns]



def _coerce_for_sklearn(X: pd.DataFrame, numeric_features: list[str], categorical_features: list[str]) -> pd.DataFrame:
    X_clean = X.copy()
    for column in numeric_features:
        if column not in X_clean.columns:
            continue
        X_clean[column] = pd.to_numeric(X_clean[column], errors="coerce").astype(float)
    for column in categorical_features:
        if column not in X_clean.columns:
            continue
        X_clean[column] = X_clean[column].astype(object)
        X_clean[column] = X_clean[column].where(pd.notna(X_clean[column]), np.nan)
    return X_clean



def _filter_usable_categorical_features(df: pd.DataFrame, categorical_features: list[str]) -> tuple[list[str], list[str]]:
    usable: list[str] = []
    dropped: list[str] = []
    for column in categorical_features:
        non_missing = df[column].dropna()
        if non_missing.empty or non_missing.nunique() <= 1:
            dropped.append(column)
        else:
            usable.append(column)
    return usable, dropped



def _sample_training_rows(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    max_training_sample_size: int | None,
    random_state: int,
) -> tuple[pd.DataFrame, pd.Series]:
    if max_training_sample_size is None or len(X_train) <= max_training_sample_size:
        return X_train, y_train
    stratify_bins = pd.qcut(y_train, q=min(10, y_train.nunique()), duplicates="drop")
    grouped = X_train.groupby(stratify_bins, observed=False)
    sampled_indices: list[pd.Index] = []
    for _, group in grouped:
        frac = len(group) / len(X_train)
        n_group = max(1, int(round(frac * max_training_sample_size)))
        n_group = min(n_group, len(group))
        sampled_indices.append(group.sample(n=n_group, random_state=random_state).index)
    sampled_index = pd.Index(np.concatenate([idx.to_numpy() for idx in sampled_indices]))
    if len(sampled_index) > max_training_sample_size:
        sampled_index = sampled_index.to_series().sample(n=max_training_sample_size, random_state=random_state).index
    sampled_X = X_train.loc[sampled_index].copy()
    sampled_y = y_train.loc[sampled_index].copy()
    return sampled_X, sampled_y



def prepare_model_inputs(
    training_gdf: gpd.GeoDataFrame,
    subset_mode: SubsetMode = "full",
    segment_column: SegmentColumn | None = None,
    segment_value: str | None = None,
) -> tuple[pd.DataFrame, pd.Series, list[str], list[str], list[str], pd.DataFrame]:
    df = pd.DataFrame(training_gdf.drop(columns=training_gdf.geometry.name, errors="ignore")).copy()
    if subset_mode == "matched_only" and "spatial_features_available" in df.columns:
        df = df.loc[df["spatial_features_available"] == 1].copy()
    if segment_column is not None and segment_value is not None:
        if segment_column not in df.columns:
            raise ValueError(f"Segment column {segment_column} is not available in training data")
        df = df.loc[df[segment_column].astype("string").fillna("Missing") == segment_value].copy()
    usable_df = df.dropna(subset=[TARGET_COLUMN, TARGET_LOG_COLUMN]).copy()

    numeric_features = _available_columns(usable_df, NUMERIC_FEATURES)
    categorical_features = _available_columns(usable_df, CATEGORICAL_FEATURES)
    categorical_features, dropped_categorical_features = _filter_usable_categorical_features(usable_df, categorical_features)
    locality_output_features = [
        f"{column}_target_mean"
        for column in LOCALITY_TARGET_COLUMNS
        if column in usable_df.columns
    ]
    numeric_features = list(dict.fromkeys(numeric_features + locality_output_features))
    feature_columns = list(dict.fromkeys(_available_columns(usable_df, CATEGORICAL_FEATURES + NUMERIC_FEATURES) + categorical_features))
    if not feature_columns:
        raise ValueError("No model feature columns are available in the training dataset")

    X = usable_df[feature_columns].copy()
    X = _coerce_for_sklearn(X, numeric_features, categorical_features)
    y = usable_df[TARGET_LOG_COLUMN].astype(float)
    return X, y, numeric_features, categorical_features, dropped_categorical_features, usable_df



def _build_one_hot_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))])
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="Missing")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", min_frequency=100)),
        ]
    )
    transformers = [("num", numeric_pipeline, numeric_features)]
    if categorical_features:
        transformers.append(("cat", categorical_pipeline, categorical_features))
    return ColumnTransformer(transformers=transformers)



def _build_ordinal_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))])
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="Missing")),
            ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
        ]
    )
    transformers = [("num", numeric_pipeline, numeric_features)]
    if categorical_features:
        transformers.append(("cat", categorical_pipeline, categorical_features))
    return ColumnTransformer(transformers=transformers)



def _wrap_with_locality_encoder(
    preprocessor: ColumnTransformer,
    model: object,
) -> Pipeline:
    return Pipeline(
        [
            ("locality_target_encoder", LocalityTargetEncoder(columns=LOCALITY_TARGET_COLUMNS, smoothing=75.0)),
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )



def build_candidate_pipeline(
    candidate_name: str,
    numeric_features: list[str],
    categorical_features: list[str],
    random_state: int = DEFAULT_RANDOM_STATE,
) -> tuple[Pipeline, str, str, dict[str, int | float | str | None]]:
    if candidate_name == "random_forest":
        params = {"n_estimators": 80, "max_depth": 18, "min_samples_leaf": 10}
        return (
            _wrap_with_locality_encoder(
                _build_one_hot_preprocessor(numeric_features, categorical_features),
                RandomForestRegressor(random_state=random_state, n_jobs=-1, **params),
            ),
            "RandomForestRegressor",
            "one_hot",
            params,
        )
    if candidate_name == "extra_trees":
        params = {"n_estimators": 120, "max_depth": None, "min_samples_leaf": 5}
        return (
            _wrap_with_locality_encoder(
                _build_one_hot_preprocessor(numeric_features, categorical_features),
                ExtraTreesRegressor(random_state=random_state, n_jobs=-1, **params),
            ),
            "ExtraTreesRegressor",
            "one_hot",
            params,
        )
    if candidate_name == "extra_trees_large":
        params = {
            "n_estimators": 240,
            "max_depth": None,
            "min_samples_leaf": 2,
            "max_features": "sqrt",
        }
        return (
            _wrap_with_locality_encoder(
                _build_one_hot_preprocessor(numeric_features, categorical_features),
                ExtraTreesRegressor(random_state=random_state, n_jobs=-1, **params),
            ),
            "ExtraTreesRegressor",
            "one_hot",
            params,
        )
    if candidate_name == "hist_gradient_boosting":
        params = {"max_iter": 250, "max_depth": 10, "learning_rate": 0.05, "min_samples_leaf": 20}
        return (
            _wrap_with_locality_encoder(
                _build_ordinal_preprocessor(numeric_features, categorical_features),
                HistGradientBoostingRegressor(random_state=random_state, **params),
            ),
            "HistGradientBoostingRegressor",
            "ordinal",
            params,
        )
    if candidate_name == "xgboost":
        if XGBRegressor is None:
            raise ValueError("XGBoost is not installed in the current environment")
        params = {
            "n_estimators": 300,
            "max_depth": 8,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_weight": 5,
            "reg_lambda": 1.0,
        }
        return (
            _wrap_with_locality_encoder(
                _build_one_hot_preprocessor(numeric_features, categorical_features),
                XGBRegressor(
                    random_state=random_state,
                    n_jobs=-1,
                    objective="reg:squarederror",
                    tree_method="hist",
                    **params,
                ),
            ),
            "XGBRegressor",
            "one_hot",
            params,
        )
    if candidate_name == "xgboost_deep":
        if XGBRegressor is None:
            raise ValueError("XGBoost is not installed in the current environment")
        params = {
            "n_estimators": 500,
            "max_depth": 10,
            "learning_rate": 0.04,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "min_child_weight": 3,
            "reg_lambda": 2.0,
            "gamma": 0.1,
        }
        return (
            _wrap_with_locality_encoder(
                _build_one_hot_preprocessor(numeric_features, categorical_features),
                XGBRegressor(
                    random_state=random_state,
                    n_jobs=-1,
                    objective="reg:squarederror",
                    tree_method="hist",
                    **params,
                ),
            ),
            "XGBRegressor",
            "one_hot",
            params,
        )
    if candidate_name == "xgboost_deep_segmented":
        params = {
            "base_candidate_name": "xgboost_deep",
            "segment_column": "Flat_or_Land",
            "segment_values": ["Land", "Flat"],
            "prune_features_by_segment": False,
        }
        return (
            SegmentedModelPipeline(
                base_candidate_name="xgboost_deep",
                segment_column="Flat_or_Land",
                segment_values=["Land", "Flat"],
                numeric_features=numeric_features,
                categorical_features=categorical_features,
                random_state=random_state,
                prune_features_by_segment=False,
            ),
            "SegmentedXGBRegressor",
            "one_hot",
            params,
        )
    if candidate_name == "xgboost_deep_segmented_pruned":
        params = {
            "base_candidate_name": "xgboost_deep",
            "segment_column": "Flat_or_Land",
            "segment_values": ["Land", "Flat"],
            "prune_features_by_segment": True,
        }
        return (
            SegmentedModelPipeline(
                base_candidate_name="xgboost_deep",
                segment_column="Flat_or_Land",
                segment_values=["Land", "Flat"],
                numeric_features=numeric_features,
                categorical_features=categorical_features,
                random_state=random_state,
                prune_features_by_segment=True,
            ),
            "SegmentedXGBRegressor",
            "one_hot",
            params,
        )
    if candidate_name == "xgboost_regularized":
        if XGBRegressor is None:
            raise ValueError("XGBoost is not installed in the current environment")
        params = {
            "n_estimators": 450,
            "max_depth": 8,
            "learning_rate": 0.04,
            "subsample": 0.8,
            "colsample_bytree": 0.7,
            "min_child_weight": 6,
            "reg_lambda": 3.0,
            "reg_alpha": 0.1,
            "gamma": 0.2,
        }
        return (
            _wrap_with_locality_encoder(
                _build_one_hot_preprocessor(numeric_features, categorical_features),
                XGBRegressor(
                    random_state=random_state,
                    n_jobs=-1,
                    objective="reg:squarederror",
                    tree_method="hist",
                    **params,
                ),
            ),
            "XGBRegressor",
            "one_hot",
            params,
        )
    if candidate_name == "xgboost_wide":
        if XGBRegressor is None:
            raise ValueError("XGBoost is not installed in the current environment")
        params = {
            "n_estimators": 700,
            "max_depth": 6,
            "learning_rate": 0.03,
            "subsample": 0.9,
            "colsample_bytree": 0.9,
            "min_child_weight": 8,
            "reg_lambda": 2.0,
            "reg_alpha": 0.05,
        }
        return (
            _wrap_with_locality_encoder(
                _build_one_hot_preprocessor(numeric_features, categorical_features),
                XGBRegressor(
                    random_state=random_state,
                    n_jobs=-1,
                    objective="reg:squarederror",
                    tree_method="hist",
                    **params,
                ),
            ),
            "XGBRegressor",
            "one_hot",
            params,
        )
    if candidate_name == "lightgbm":
        if LGBMRegressor is None:
            raise ValueError("LightGBM is not installed in the current environment")
        params = {
            "n_estimators": 300,
            "learning_rate": 0.05,
            "num_leaves": 63,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_samples": 30,
            "reg_lambda": 1.0,
        }
        return (
            _wrap_with_locality_encoder(
                _build_one_hot_preprocessor(numeric_features, categorical_features),
                LGBMRegressor(
                    random_state=random_state,
                    objective="regression",
                    n_jobs=-1,
                    verbosity=-1,
                    **params,
                ),
            ),
            "LGBMRegressor",
            "one_hot",
            params,
        )
    raise ValueError(f"Unsupported candidate_name: {candidate_name}")



def _evaluate_predictions(y_test_log: pd.Series, pred_log: np.ndarray) -> tuple[float, float, float, float]:
    pred = np.expm1(pred_log)
    actual = np.expm1(y_test_log.to_numpy())
    mae = float(np.mean(np.abs(actual - pred)))
    rmse = float(np.sqrt(np.mean(np.square(actual - pred))))
    mape = mean_absolute_percentage_error(actual, pred)
    ss_res = float(np.sum(np.square(actual - pred)))
    ss_tot = float(np.sum(np.square(actual - np.mean(actual))))
    r2 = float(1 - ss_res / ss_tot) if ss_tot else float("nan")
    return mae, rmse, mape, r2



def train_model_candidate(
    training_gdf: gpd.GeoDataFrame,
    candidate_name: str,
    subset_mode: SubsetMode = "full",
    segment_column: SegmentColumn | None = None,
    segment_value: str | None = None,
    test_size: float = 0.2,
    random_state: int = DEFAULT_RANDOM_STATE,
    max_training_sample_size: int | None = 30000,
) -> TrainedModelArtifacts:
    X, y, numeric_features, categorical_features, dropped_categorical_features, usable_df = prepare_model_inputs(
        training_gdf,
        subset_mode=subset_mode,
        segment_column=segment_column,
        segment_value=segment_value,
    )
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
    full_train_row_count = int(len(X_train))
    X_train, y_train = _sample_training_rows(X_train, y_train, max_training_sample_size, random_state)

    pipeline, model_name, preprocessing_kind, model_params = build_candidate_pipeline(
        candidate_name,
        numeric_features,
        categorical_features,
        random_state=random_state,
    )
    pipeline.fit(X_train, y_train)

    summary = ModelTrainingSummary(
        input_row_count=int(len(training_gdf)),
        rows_used_for_training=int(len(usable_df)),
        subset_mode=subset_mode,
        train_row_count=full_train_row_count,
        test_row_count=int(len(X_test)),
        train_row_count_after_sampling=int(len(X_train)),
        target_column=TARGET_COLUMN,
        target_transform="log1p(value_per_area)",
        model_name=model_name,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        dropped_categorical_features=dropped_categorical_features,
        preprocessing_kind=preprocessing_kind,
        random_state=random_state,
        test_size=test_size,
        model_params=model_params,
        max_training_sample_size=max_training_sample_size,
        segment_column=segment_column,
        segment_value=segment_value,
    )
    return TrainedModelArtifacts(pipeline, X_train, X_test, y_train, y_test, summary)



def train_random_forest_model(
    training_gdf: gpd.GeoDataFrame,
    test_size: float = 0.2,
    random_state: int = DEFAULT_RANDOM_STATE,
    n_estimators: int = 80,
    max_depth: int | None = 18,
    min_samples_leaf: int = 10,
    max_training_sample_size: int | None = 30000,
) -> TrainedModelArtifacts:
    artifacts = train_model_candidate(
        training_gdf,
        candidate_name="random_forest",
        subset_mode="full",
        test_size=test_size,
        random_state=random_state,
        max_training_sample_size=max_training_sample_size,
    )
    return artifacts



def compare_model_candidates(
    training_gdf: gpd.GeoDataFrame,
    test_size: float = 0.2,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> tuple[TrainedModelArtifacts, ModelComparisonResult]:
    candidate_specs = [
        ("xgboost", "full", 60000, None, None),
        ("xgboost_deep", "full", 80000, None, None),
        ("xgboost_deep_segmented", "full", 80000, None, None),
        ("xgboost_deep_segmented_pruned", "full", 80000, None, None),
        ("xgboost_regularized", "full", 80000, None, None),
        ("xgboost_wide", "full", 80000, None, None),
        ("lightgbm", "full", 60000, None, None),
    ]
    results: list[CandidateResult] = []
    artifacts_by_name: dict[str, TrainedModelArtifacts] = {}

    for candidate_name, subset_mode, max_sample, segment_column, segment_value in candidate_specs:
        label = build_candidate_label(candidate_name, subset_mode, segment_column=segment_column, segment_value=segment_value)
        LOGGER.info("Training candidate %s", label)
        artifacts = train_model_candidate(
            training_gdf,
            candidate_name=candidate_name,
            subset_mode=subset_mode,
            segment_column=segment_column,
            segment_value=segment_value,
            test_size=test_size,
            random_state=random_state,
            max_training_sample_size=max_sample,
        )
        pred_log = artifacts.pipeline.predict(artifacts.X_test)
        mae, rmse, mape, r2 = _evaluate_predictions(artifacts.y_test, pred_log)
        results.append(
            CandidateResult(
                candidate_name=label,
                subset_mode=subset_mode,
                model_name=artifacts.summary.model_name,
                preprocessing_kind=artifacts.summary.preprocessing_kind,
                train_rows_after_sampling=artifacts.summary.train_row_count_after_sampling,
                test_row_count=artifacts.summary.test_row_count,
                mae=mae,
                rmse=rmse,
                mape=mape,
                r2=r2,
                max_training_sample_size=max_sample,
                segment_column=segment_column,
                segment_value=segment_value,
            )
        )
        artifacts_by_name[label] = artifacts

    ranked = sorted(results, key=lambda item: (item.mape, item.rmse, -item.r2))
    best = ranked[0]
    comparison = ModelComparisonResult(best_candidate_name=best.candidate_name, selection_metric="mape_then_rmse_then_r2", candidates=results)
    return artifacts_by_name[best.candidate_name], comparison


def build_candidate_label(
    candidate_name: str,
    subset_mode: str,
    segment_column: str | None = None,
    segment_value: str | None = None,
) -> str:
    label = f"{candidate_name}__{subset_mode}"
    if segment_column is not None and segment_value is not None:
        safe_value = segment_value.lower().replace(" ", "_")
        label = f"{label}__{segment_column.lower()}_{safe_value}"
    return label


def parse_candidate_label(label: str) -> tuple[str, str, str | None, str | None]:
    parts = label.split("__")
    if len(parts) < 2:
        raise ValueError(f"Invalid candidate label: {label}")
    candidate_name = parts[0]
    subset_mode = parts[1]
    segment_column: str | None = None
    segment_value: str | None = None
    if len(parts) >= 3 and parts[2].startswith("flat_or_land_"):
        segment_column = "Flat_or_Land"
        segment_value = parts[2].removeprefix("flat_or_land_").replace("_", " ").title()
    return candidate_name, subset_mode, segment_column, segment_value



def save_model_artifacts(
    artifacts: TrainedModelArtifacts,
    models_dir: Path,
    reports_dir: Path,
    comparison: ModelComparisonResult | None = None,
) -> tuple[Path, Path, Path | None]:
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / "valuation_model.pkl"
    summary_path = reports_dir / "model_training_summary.json"
    comparison_path = reports_dir / "model_comparison.json" if comparison is not None else None

    with model_path.open("wb") as file_obj:
        pickle.dump(artifacts.pipeline, file_obj)
    summary_path.write_text(json.dumps(asdict(artifacts.summary), indent=2), encoding="utf-8")
    if comparison_path is not None:
        comparison_path.write_text(json.dumps(asdict(comparison), indent=2), encoding="utf-8")

    LOGGER.info("Saved trained model to %s", model_path)
    LOGGER.info("Saved training summary to %s", summary_path)
    if comparison_path is not None:
        LOGGER.info("Saved model comparison to %s", comparison_path)
    return model_path, summary_path, comparison_path
