import React, { useEffect, useMemo, useState } from 'react';
import { NavLink, Route, Routes } from 'react-router-dom';
import Explainability from './pages/Explainability';
import BatchInference from './pages/BatchInference';
import ModelPerformance from './pages/ModelPerformance';
import MVDBComparison from './pages/MVDBComparison';
import Overview from './pages/Overview';
import PropertyLookup from './pages/PropertyLookup';
import Zones from './pages/Zones';
import { api } from './services/api';
import type {
  DashboardSummary,
  FeatureImportanceRecord,
  GeoJsonFeatureCollection,
  PropertyExplanation,
  PropertyRecordResponse,
  PropertySearchRecord,
  ZoneSummaryRecord,
} from './types/api';
import { cn } from './lib/utils';
import { Activity } from 'lucide-react';

const navItems = [
  ['/', 'Overview'],
  ['/zones', 'Market Zones'],
  ['/properties', 'Property Lookup'],
  ['/batch-inference', 'Batch Inference'],
  ['/explainability', 'Why This Price?'],
  ['/mvdb', 'Gov Rate Compare'],
] as const;

export default function App() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [zones, setZones] = useState<ZoneSummaryRecord[]>([]);
  const [zoneGeoJson, setZoneGeoJson] = useState<GeoJsonFeatureCollection | null>(null);
  const [featureImportance, setFeatureImportance] = useState<FeatureImportanceRecord[]>([]);
  const [properties, setProperties] = useState<PropertySearchRecord[]>([]);
  const [selectedPropertyId, setSelectedPropertyId] = useState<string>('');
  const [propertyRecord, setPropertyRecord] = useState<PropertyRecordResponse | null>(null);
  const [propertyExplanation, setPropertyExplanation] = useState<PropertyExplanation | null>(null);
  const [sampleExplanations, setSampleExplanations] = useState<PropertyExplanation[]>([]);
  const [mvdbStatus, setMvdbStatus] = useState<Record<string, unknown> | null>(null);
  const [districtFilter, setDistrictFilter] = useState<string>('');
  const [mouzaFilter, setMouzaFilter] = useState<string>('');
  const [error, setError] = useState<string>('');

  async function loadProperties(district?: string, mouza?: string) {
    const propertyRows = await api.getProperties(district, mouza, 75);
    setProperties(propertyRows);
    setSelectedPropertyId((current) => {
      if (propertyRows.some((item) => item.property_id === current)) return current;
      return propertyRows[0]?.property_id ?? '';
    });
  }

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [summaryPayload, zoneRows, zoneGeoJsonPayload, featureRows, sampleRows, mvdbPayload] = await Promise.all([
          api.getSummary(),
          api.getZones(),
          api.getZonesGeoJson(),
          api.getGlobalFeatureImportance(),
          api.getSampleExplanations(),
          api.getMvdbStatus(),
        ]);
        setSummary(summaryPayload);
        setZones(zoneRows);
        setZoneGeoJson(zoneGeoJsonPayload);
        setFeatureImportance(featureRows);
        setSampleExplanations(sampleRows);
        setMvdbStatus(mvdbPayload);
        await loadProperties();
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Unknown dashboard loading error');
      }
    }
    void loadDashboard();
  }, []);

  useEffect(() => {
    async function loadPropertyState() {
      if (!selectedPropertyId) return;
      try {
        const [record, explanation] = await Promise.all([
          api.getProperty(selectedPropertyId),
          api.getPropertyExplanation(selectedPropertyId),
        ]);
        setPropertyRecord(record);
        setPropertyExplanation(explanation);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Unknown property loading error');
      }
    }
    void loadPropertyState();
  }, [selectedPropertyId]);

  async function handleApplyPropertyFilters() {
    try {
      setError('');
      await loadProperties(districtFilter || undefined, mouzaFilter || undefined);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unknown property filtering error');
    }
  }

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div>
          <img src="/kpmg_logo.png" alt="KPMG Logo" className="h-10 w-auto mb-6 object-contain" />
          <div className="text-[11px] font-bold tracking-[0.2em] uppercase text-primary mb-2 flex items-center gap-2">
            <Activity className="w-4 h-4" />
            AI Property Valuation
          </div>

        </div>
        <nav className="flex flex-col gap-2 flex-1">
          {navItems.map(([path, label]) => (
            <NavLink 
              key={path} 
              to={path} 
              className={({ isActive }) => cn(
                "px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 border border-transparent hover:translate-x-1",
                isActive 
                  ? "bg-primary text-primary-foreground shadow-md shadow-primary/20 border-primary/20" 
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/40 hover:border-border/50"
              )}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="app-main">
        <div className="max-w-[1400px] mx-auto">
          {error ? (
            <div className="mb-6 p-4 rounded-xl bg-destructive/10 border border-destructive text-destructive shadow-sm">
              {error}
            </div>
          ) : null}
          <Routes>
            <Route path="/" element={<Overview summary={summary} />} />
            <Route path="/zones" element={<Zones zones={zones} zoneGeoJson={zoneGeoJson} />} />
            <Route
              path="/properties"
              element={
                <PropertyLookup
                  properties={properties}
                  selectedPropertyId={selectedPropertyId}
                  onSelect={setSelectedPropertyId}
                  propertyRecord={propertyRecord}
                  explanation={propertyExplanation}
                  districtFilter={districtFilter}
                  mouzaFilter={mouzaFilter}
                  onDistrictChange={setDistrictFilter}
                  onMouzaChange={setMouzaFilter}
                  onApplyFilters={handleApplyPropertyFilters}
                />
              }
            />
            <Route path="/batch-inference" element={<BatchInference />} />
            <Route path="/explainability" element={<Explainability featureImportance={featureImportance} sampleExplanations={sampleExplanations} />} />
            <Route path="/mvdb" element={<MVDBComparison mvdbStatus={mvdbStatus} />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
