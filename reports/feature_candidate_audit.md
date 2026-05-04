# Feature Candidate Audit

Date: 2026-04-29

## Purpose
This report documents potentially useful columns that are present in the currently loaded datasets but are not yet being used in the model training dataset. The goal is to identify high-value candidates for the next feature engineering improvement pass.

## Scope
Audited sources:
- `data/interim/transactions_property_merged.parquet`
- `data/interim/roads_gis.parquet`
- `data/interim/facilities_gis.parquet`

Current model inputs already include:
- transaction features such as `Area`, `Approach_Road_Width`, `Urban`, `Rural`, `Flat_or_Land`, `Zone_no`, `Mouza_Name`, `PS_Name`, `Road_Name`, land-use fields, `Litigated_Property`
- property geometry features
- road proximity and nearest-road attributes
- facility proximity and grouped facility counts
- locality target-encoded features for district, PS, mouza, zone, and road

## Findings

### High-priority candidate features
These are the strongest next candidates based on domain relevance, coverage, and likely incremental signal.

1. `Date_of_Registration`
- Coverage: 100%
- Why it may help: captures time-dependent market movement.
- Recommended derived features: registration month, quarter, year-month bucket, day-of-week.

2. `Date_of_presentation`
- Coverage: 100%
- Why it may help: another time marker that may capture market timing and administrative lag.
- Recommended derived features: presentation month, quarter, lag vs registration date.

3. `Time_of_Presentation`
- Coverage: 100%
- Why it may help: probably weak by itself, but can help when combined with presentation date and registration process patterns.
- Recommended derived features: hour bucket, morning/afternoon flag.

4. `Transaction_code`
- Coverage: 100%
- Why it may help: transaction type strongly affects observed value behavior.
- Notes: likely better than raw text alone.

5. `Transaction_Name`
- Coverage: 100%
- Why it may help: human-readable transaction-type category.
- Notes: may overlap with `Transaction_code`, but useful for auditability and model comparison.

6. `Road_code`
- Coverage: ~100%
- Why it may help: strong locality identifier that may be more stable than free-text `Road_Name`.
- Notes: likely a good candidate for target encoding.

7. `Is_Property_on_Road`
- Coverage: 100%
- Why it may help: direct frontage/access signal that is highly relevant for valuation.

8. `Adjacent_to_Metal_Road`
- Coverage: 66.94%
- Why it may help: road quality/accessibility proxy, likely useful especially where transaction `Road_Category` is missing.

9. `GP`
- Coverage: 57.28%
- Why it may help: local administrative geography, useful for locality-level price variation.
- Notes: good candidate for target encoding or direct categorical use with missing handling.

10. `Nature_Land_use_Code`
- Coverage: 100%
- Why it may help: coded land-use field may be cleaner and more consistent than the name column.

11. `Proposed_Land_use_Code`
- Coverage: 100%
- Why it may help: same rationale as `Nature_Land_use_Code`.

### Medium-priority candidate features
These may help, but are less compelling than the group above.

1. `Mouza_Type`
- Coverage: 100%
- Why it may help: compact land/locality-type feature.

2. `Special_project_Name`
- Coverage: 99.29%
- Why it may help: could identify premium or special development zones.
- Risk: appears to contain placeholder-like values such as `999`; needs cleaning first.

3. `bargadar`
4. `whether_tenant_purchaser`
5. `is_bargadar_purchaser`
- Coverage: 66.94%
- Why they may help: legal/occupancy status may affect value.

6. `Ward_No`
- Coverage: 21.47%
- Why it may help: useful municipal locality signal where present.
- Risk: low coverage.

7. `BLOCK`
8. `BLOCK_CODE`
- Coverage: 72.92% / 75.82%
- Why they may help: extra administrative hierarchy.
- Risk: some overlap with existing locality features.

9. `ps_name`
10. `ENG_MOUNAM`
- Coverage: 75.82%
- Why they may help: alternate locality names from GIS/property layer.
- Risk: likely redundant with existing PS/Mouza names.

### Low-priority or not recommended
These are either helper fields, redundant, low-signal, or too sparse.

1. `plot_no_norm`
2. `mouza_code_norm`
3. `ps_code_norm`
4. `district_name_norm`
- Why not recommended: technical helper merge keys, not meaningful new valuation features.

5. `SHAPE_Area`
6. `SHAPE_Leng`
- Why not recommended: replaced by better engineered geometry features already in the model.

7. `book`
8. `Area_type`
9. `Types of area Measurement`
10. `Property_Office_code`
- Why not recommended: very low variety or weak expected signal.

11. `Municipali`
- Why not recommended: effectively one value in matched rows.

12. `premises`
- Why not recommended: extremely sparse.

## Additional road/facility opportunities

### Road layer
Unused road attribute with potential value:
- `adsr_jur`
  - Coverage: 100%
  - Why it may help: nearest-road administrative/jurisdiction context.

### Facility layer
Potential future candidates:
- `Survey_Use`
- `Office_Nam`
- `Block__ULB`
- `Police_Sta`
- `GP_Ward`
- `Brief_Desc`

These are not immediate must-haves, but could support:
- better facility grouping
- nearest-facility context
- locality-aware amenity summaries

## Recommended next feature batch
Highest-return next additions:
1. `Transaction_code` and/or `Transaction_Name`
2. temporal features from `Date_of_Registration` and `Date_of_presentation`
3. `Road_code`
4. `Is_Property_on_Road`
5. `Adjacent_to_Metal_Road`
6. `GP`
7. `Nature_Land_use_Code` and `Proposed_Land_use_Code`

## Implementation guidance
- Use leakage-safe target encoding only for locality-style identifiers such as `Road_code` or `GP` if added.
- Convert datetime strings into derived calendar features instead of using raw timestamps directly.
- For binary/legal fields, normalize values before modeling.
- Add missingness-aware handling for partial-coverage fields like `Adjacent_to_Metal_Road`, `GP`, and `Ward_No`.
- Compare performance incrementally rather than adding every candidate at once.

## Conclusion
Yes, there are still useful unused columns in the already loaded datasets. The strongest next improvement opportunity is not from unused files in `data/`, but from currently unused transaction and GIS attributes already present in the merged dataset.
