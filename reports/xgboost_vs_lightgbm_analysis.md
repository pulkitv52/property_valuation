# XGBoost vs LightGBM Analysis

Date: 2026-05-07

## Scope

This note compares the saved `XGBoost` candidates against the saved `LightGBM` candidate for the property valuation PoC. The comparison is based on the persisted training artifacts in:

- `reports/model_comparison.json`
- `reports/model_metrics.json`
- `backend/src/model_training.py`

The project selection rule for model ranking is:

`mape_then_rmse_then_r2`

## Evaluation Setup

- Problem type: regression on `log1p(value_per_area)`
- Test rows: `59,488`
- Train/test split: `80/20`
- Random state: `42`
- Feature family: transaction + GIS-derived features

## Candidate Summary

| Candidate | Model | Train Sample | MAE | RMSE | MAPE | R2 |
|---|---|---:|---:|---:|---:|---:|
| `xgboost__full` | XGBRegressor | 60,000 | 184.80 | 436.81 | 16.26% | 0.9035 |
| `xgboost_deep__full` | XGBRegressor | 80,000 | 151.25 | 384.48 | 13.80% | 0.9252 |
| `xgboost_deep_segmented__full` | SegmentedXGBRegressor | 80,000 | 145.77 | 384.35 | 13.33% | 0.9253 |
| `xgboost_deep_segmented_pruned__full` | SegmentedXGBRegressor | 80,000 | 146.63 | 386.42 | 13.38% | 0.9245 |
| `xgboost_regularized__full` | XGBRegressor | 80,000 | 179.52 | 429.56 | 15.72% | 0.9067 |
| `xgboost_wide__full` | XGBRegressor | 80,000 | 214.17 | 482.79 | 18.30% | 0.8821 |
| `lightgbm__full` | LGBMRegressor | 60,000 | 199.57 | 463.94 | 16.73% | 0.8911 |

## Best Model

The best saved candidate is:

`xgboost_deep_segmented__full`

Why it won:

- Lowest `MAPE`: `13.33%`
- Lowest `RMSE`: `384.35`
- Highest `R2`: `0.9253`

Saved market-value error metrics for this selected model from `reports/model_metrics.json`:

- `MAE (market value)`: `Rs 277,877.18`
- `RMSE (market value)`: `Rs 3,363,737.16`
- `MAPE (market value)`: `13.33%`

## LightGBM vs Best XGBoost

Direct comparison between `lightgbm__full` and `xgboost_deep_segmented__full`:

| Metric | LightGBM | Best XGBoost | Absolute Gap | Relative Gap vs LightGBM |
|---|---:|---:|---:|---:|
| MAE | 199.57 | 145.77 | 53.80 lower | 26.96% better |
| RMSE | 463.94 | 384.35 | 79.59 lower | 17.15% better |
| MAPE | 16.73% | 13.33% | 3.40 pts lower | 20.30% better |
| R2 | 0.8911 | 0.9253 | 0.0341 higher | 3.83% higher |

Interpretation:

- LightGBM is clearly weaker than the best XGBoost candidate on every saved evaluation metric.
- The biggest business-facing difference is in `MAPE`: XGBoost reduces average percentage error by about `3.40` percentage points.
- In simple terms, LightGBM is roughly at `16.73%` average percentage error, while the best XGBoost is at `13.33%`.

## LightGBM vs Non-Segmented XGBoost

Even before segmentation, the stronger XGBoost variant outperformed LightGBM:

| Metric | LightGBM | `xgboost_deep__full` | Gap |
|---|---:|---:|---:|
| MAE | 199.57 | 151.25 | XGBoost better by 48.32 |
| RMSE | 463.94 | 384.48 | XGBoost better by 79.46 |
| MAPE | 16.73% | 13.80% | XGBoost better by 2.93 pts |
| R2 | 0.8911 | 0.9252 | XGBoost higher by 0.0341 |

This suggests the gain is not only from segmentation. The underlying XGBoost family is already stronger on this dataset.

## Why XGBoost Likely Won Here

Based on the saved pipeline design and candidate results, the likely reasons are:

- The feature space is wide and mixed, with many categorical locality fields plus GIS-derived numeric features.
- The segmented XGBoost setup benefits from modeling `Land` and `Flat` as different markets.
- XGBoost appears to handle the current nonlinear interactions and sparse one-hot structure better than the tested LightGBM setup.

This is an inference from the saved results, not a separate causal experiment.

## Recommendation

For this PoC, use `xgboost_deep_segmented__full` as the production candidate.

Reasons:

- Best overall score by the project selection rule
- Best `MAPE`, which is the lead metric for business interpretability
- Better `RMSE` and `R2` than LightGBM
- Supports the observed market split between `Flat` and `Land`

## Next Analysis Ideas

If we want a more complete XGBoost vs LightGBM study later, the next useful checks would be:

1. Train segmented LightGBM with the same `Flat_or_Land` split.
2. Compare training time and inference time in addition to accuracy.
3. Generate per-segment metrics for LightGBM, not just aggregate metrics.
4. Evaluate rupee-denominated error for LightGBM using the same market-value reconstruction flow.
