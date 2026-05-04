# XGBoost Feature Importance Audit

Date: 2026-04-29

Model: `XGBRegressor`

Total transformed features: `434`

## Top Features

1. `Proposed_Land_use_Code_   ` | importance `0.532501` | group `transaction_context`
2. `Nature_Land_use_Code_   ` | importance `0.281217` | group `transaction_context`
3. `Adjacent_to_Metal_Road_Missing` | importance `0.143661` | group `road_access`
4. `Rural_flag` | importance `0.007314` | group `other`
5. `Road_Name_Missing` | importance `0.006070` | group `road_access`
6. `PS_Name_Panchla` | importance `0.002917` | group `other`
7. `Urban_flag` | importance `0.002686` | group `other`
8. `Nature_Land_use_Name_Industrial Use` | importance `0.001615` | group `transaction_context`
9. `Zone_no_0` | importance `0.001204` | group `other`
10. `PS_Name_Kanksa` | importance `0.001162` | group `other`
11. `Adjacent_to_Metal_Road_flag` | importance `0.000976` | group `road_access`
12. `Proposed_Land_use_Name_Shali` | importance `0.000959` | group `transaction_context`
13. `Road_Name_Unassessed Road (Fuljhore)` | importance `0.000732` | group `road_access`
14. `Adjacent_to_Metal_Road_N` | importance `0.000649` | group `road_access`
15. `GP_target_mean` | importance `0.000586` | group `locality_target_encoding`
16. `Transaction_code_307` | importance `0.000525` | group `transaction_context`
17. `Mouza_Name_Jangalpur` | importance `0.000497` | group `other`
18. `property_district_Name_target_mean` | importance `0.000449` | group `locality_target_encoding`
19. `Proposed_Land_use_Code_003` | importance `0.000447` | group `transaction_context`
20. `Proposed_Land_use_Code_021` | importance `0.000390` | group `transaction_context`

## Importance by Feature Group

- `transaction_context`: `0.823677`
- `road_access`: `0.154270`
- `other`: `0.019246`
- `locality_target_encoding`: `0.001665`
- `facility_proximity`: `0.000470`
- `geometry_location`: `0.000394`
- `transaction_time`: `0.000228`
- `property_core`: `0.000050`

## Interpretation

- This ranking is based on the fitted tuned XGBoost model currently saved in `models/valuation_model.pkl`.
- One-hot encoded categorical features and locality target-encoded features are both included in the transformed feature space.
- Higher importance indicates greater contribution to tree splits, but it does not by itself prove causal influence.

## Suggested Next Improvements

- If locality target-encoding dominates, the next gain may come from richer train-only locality aggregates beyond mean encoding.
- If road/facility features are weak, we should expand road-network density and exact facility-type features.
- If time features are strong, adding time-windowed locality pricing trends may help further.
- If transaction context is strong, segment-specific models by transaction or property type may help.