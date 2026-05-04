import type {
  DashboardSummary,
  FeatureImportanceRecord,
  GeoJsonFeatureCollection,
  PropertyExplanation,
  PropertyRecordResponse,
  PropertySearchRecord,
  ZoneSummaryRecord,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed for ${path}: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  getSummary: () => request<DashboardSummary>('/summary'),
  getZones: async () => (await request<{ results: ZoneSummaryRecord[] }>('/zones')).results,
  getZonesGeoJson: () => request<GeoJsonFeatureCollection>('/zones/geojson'),
  getGlobalFeatureImportance: async () => (await request<{ results: FeatureImportanceRecord[] }>('/explanations/global?limit=20')).results,
  getSampleExplanations: async () => (await request<{ results: PropertyExplanation[] }>('/explanations/samples')).results,
  getProperties: async (district?: string, mouza?: string, limit = 50) => {
    const params = new URLSearchParams();
    params.set('limit', String(limit));
    if (district) params.set('district', district);
    if (mouza) params.set('mouza', mouza);
    return (await request<{ results: PropertySearchRecord[] }>(`/properties?${params.toString()}`)).results;
  },
  getProperty: (propertyId: string) => request<PropertyRecordResponse>(`/property/${propertyId}`),
  getPropertyExplanation: async (propertyId: string) => (await request<{ payload: PropertyExplanation }>(`/valuation-explanation/${propertyId}`)).payload,
  getMvdbStatus: () => request<Record<string, unknown>>('/mvdb-status'),
};
