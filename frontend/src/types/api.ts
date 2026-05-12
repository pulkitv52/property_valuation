export type DashboardSummary = {
  property_count: number;
  best_candidate_name: string;
  metrics: Record<string, number | string>;
  zones: Record<string, number | string>;
  explainability: Record<string, number | string>;
  property_type_analysis: PropertyTypeAnalysisRecord[];
  zone_property_type_analysis?: ZonePropertyTypeRecord[];
  mvdb_status: string;
};

export type PropertyTypeAnalysisRecord = {
  level: string;
  group_name: string;
  count: number;
  mae: number;
  rmse: number;
  mape: number;
  mean_actual_value_per_area: number;
  mean_predicted_value_per_area: number;
};

export type ZonePropertyTypeRecord = {
  zone_id: string;
  zone_name: string;
  zone_label?: string;
  property_type: string;
  count: number;
  mape: number;
  mean_actual: number;
  mean_predicted: number;
  flat_share?: number;
  land_share?: number;
};

export type ZoneSummaryRecord = {
  ai_zone: string;
  ai_zone_name: string;
  ai_zone_description: string;
  property_count: number;
  median_value_per_area: number;
  median_value_per_sqft?: number | null;
  avg_distance_to_nearest_road: number;
  avg_distance_to_nearest_facility: number;
  urban_share: number;
  rural_share: number;
  flat_share: number;
  dominant_district: string | null;
  dominant_mouza: string | null;
};

export type PropertySearchRecord = {
  property_id: string;
  property_district_Name?: string;
  Mouza_Name?: string;
  Flat_or_Land?: string;
  Area?: number;
  area_sqft?: number;
  area_measurement_label?: string;
  predicted_value_per_area?: number;
  actual_value_per_area?: number;
  predicted_value_per_sqft?: number;
  actual_value_per_sqft?: number;
  ai_zone?: string;
  ai_zone_name?: string;
};

export type PropertyRecordResponse = {
  property_id: string;
  payload: Record<string, unknown>;
};

export type PropertyExplanation = {
  identifiers: Record<string, unknown>;
  segment_value: string;
  explanation_method: string;
  predicted_value_per_area: number;
  actual_value_per_area: number | null;
  predicted_value_per_sqft?: number | null;
  actual_value_per_sqft?: number | null;
  area_measurement_label?: string | null;
  plain_language_summary: string;
  top_positive_factors: Array<Record<string, unknown>>;
  top_negative_factors: Array<Record<string, unknown>>;
  global_top_features: Array<Record<string, unknown>>;
};

export type FeatureImportanceRecord = {
  segment_value: string;
  base_feature: string;
  importance: number;
};

export type GeoJsonFeatureCollection = {
  type: 'FeatureCollection';
  features: Array<{
    type: 'Feature';
    properties: Record<string, unknown>;
    geometry: Record<string, unknown>;
  }>;
};

export type PredictionRequest = {
  records: Array<Record<string, unknown>>;
};

export type PredictionResponse = {
  results: Array<Record<string, unknown>>;
  summary: Record<string, unknown>;
};
