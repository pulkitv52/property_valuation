import React from 'react';
import MetricCard from '../components/MetricCard';
import type { DashboardSummary, PropertyTypeAnalysisRecord, ZonePropertyTypeRecord } from '../types/api';
import { formatNumber, formatPercent, formatRatio } from '../utils/format';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { cn } from '../lib/utils';

type OverviewProps = {
  summary: DashboardSummary | null;
};

export default function Overview({ summary }: OverviewProps) {
  if (!summary) return <div className="p-8 text-center text-muted-foreground bg-muted/20 rounded-xl border border-dashed border-border">Loading overview...</div>;
  const metrics = summary.metrics as Record<string, number>;
  const zones = summary.zones as Record<string, number>;
  const propertyTypeRows = summary.property_type_analysis ?? [];
  const zoneRows = summary.zone_property_type_analysis ?? [];
  const land = propertyTypeRows.find((row: PropertyTypeAnalysisRecord) => row.group_name === 'Land');
  const flat = propertyTypeRows.find((row: PropertyTypeAnalysisRecord) => row.group_name === 'Flat');
  const landZoneRows = zoneRows.filter((row: ZonePropertyTypeRecord) => row.property_type === 'Land');
  const flatZoneRows = zoneRows.filter((row: ZonePropertyTypeRecord) => row.property_type === 'Flat');
  const totalTestedRows = (land?.count ?? 0) + (flat?.count ?? 0);

  function renderZoneTable(rows: ZonePropertyTypeRecord[], propertyType: 'Land' | 'Flat', accentClassName: string) {
    return (
      <div className="space-y-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <Badge variant="secondary" className={accentClassName}>{propertyType}</Badge>
              <span className="text-sm text-muted-foreground">
                {formatNumber(rows.reduce((sum, row) => sum + row.count, 0))} evaluated properties across {formatNumber(rows.length)} AI zones
              </span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
              {propertyType === 'Land'
                ? 'These rows show how Land records performed inside each AI zone.'
                : 'These rows show how Flat records performed inside each AI zone.'}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 md:min-w-[340px]">
            <div className="rounded-xl border border-border/50 bg-muted/20 px-4 py-3">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Overall Avg. Deviation</div>
              <div className="mt-1 text-lg font-bold">{formatPercent(propertyType === 'Land' ? land?.mape : flat?.mape)}</div>
            </div>
            <div className="rounded-xl border border-border/50 bg-muted/20 px-4 py-3">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Mean Registered Rate</div>
              <div className="mt-1 text-lg font-bold">
                ₹{formatNumber(propertyType === 'Land' ? land?.mean_actual_value_per_area : flat?.mean_actual_value_per_area, 2)}
              </div>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto rounded-xl border border-border/50">
          <table className="w-full text-sm text-left">
            <thead className="text-[10px] uppercase tracking-wider bg-muted/40 text-muted-foreground">
              <tr>
                <th className="px-6 py-4 font-bold">Zone</th>
                <th className="px-6 py-4 font-bold">Zone Mix</th>
                <th className="px-6 py-4 font-bold">Evaluation Slice</th>
                <th className="px-6 py-4 font-bold">Sample Count</th>
                <th className="px-6 py-4 font-bold text-right">Avg. Deviation</th>
                <th className="px-6 py-4 font-bold text-right">Estimated Rate</th>
                <th className="px-6 py-4 font-bold text-right">Registered Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {rows.map((record) => (
                <tr key={`${record.zone_id}-${record.property_type}`} className="hover:bg-muted/10 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-semibold text-foreground">{record.zone_name}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-muted-foreground">
                      Land {formatPercent((record.land_share ?? 0) * 100)} | Flat {formatPercent((record.flat_share ?? 0) * 100)}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <Badge variant="secondary" className={accentClassName}>
                      {record.property_type}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 text-muted-foreground">{record.count.toLocaleString()} properties</td>
                  <td className="px-6 py-4 text-right font-bold text-primary">{formatPercent(record.mape)}</td>
                  <td className="px-6 py-4 text-right font-mono text-xs">₹{record.mean_predicted.toFixed(2)}</td>
                  <td className="px-6 py-4 text-right font-mono text-xs">₹{record.mean_actual.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <Card className="overflow-hidden border-primary/30 shadow-primary/5 bg-gradient-to-br from-card to-primary/5">
        <CardContent className="p-8 flex flex-col md:flex-row gap-8 items-start md:items-end justify-between">
          <div className="flex-1 max-w-3xl">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4 leading-tight">
              AI-Based Property Valuation and Market Zoning
            </h2>
            <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl">
              This project predicts property value per area, groups similar locations into AI-driven market zones, and helps explain the main drivers behind price variation.
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard label="Evaluation Records" value={String(totalTestedRows || summary.property_count)} tone="accent" tooltip="Historical records used to evaluate model performance." />
        <MetricCard label="Average Prediction Error" value={formatPercent(metrics.mape)} tooltip="Average percentage difference between predicted and actual value per area." />
        <MetricCard label="Model Fit Score" value={formatRatio(metrics.r2)} tooltip="R² score showing how well the model explains variation in property value." />
        <MetricCard label="AI Zones Created" value={String(zones.output_zone_rows ?? '-')} tooltip="The number of distinct, algorithmically discovered market regions." />
        <MetricCard label="Zone Clustering Records" value={String(zones.rows_used_for_clustering ?? '-')} tooltip="Records used to create AI market zones." />
        <MetricCard label="Gov Rate Comparison" value={summary.mvdb_status} tone="muted" tooltip="Status of comparison with official government valuation rates." />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="glass-panel">
          <CardContent className="p-8">
            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
              <span className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm">1</span>
              What This Project Delivers
            </h3>
            <ul className="space-y-4 text-foreground/80 list-disc pl-5 marker:text-primary">
              <li className="pl-1 leading-relaxed">Predicts market value per area from transaction and GIS signals.</li>
              <li className="pl-1 leading-relaxed">Creates AI-based market zones from location, access, and pricing patterns.</li>
              <li className="pl-1 leading-relaxed">Supports explainable valuation and future comparison with government rates.</li>
            </ul>
          </CardContent>
        </Card>
        
        <Card className="glass-panel">
          <CardContent className="p-8">
            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
              <span className="w-8 h-8 rounded-full bg-accent/20 text-accent flex items-center justify-center text-sm">2</span>
              What The Metrics Show
            </h3>
            <ul className="space-y-4 text-foreground/80 list-disc pl-5 marker:text-accent">
              <li className="pl-1 leading-relaxed">The model was evaluated on {formatNumber(totalTestedRows || summary.property_count)} records.</li>
              <li className="pl-1 leading-relaxed">Average prediction error is {formatPercent(metrics.mape)} with an R² of {formatRatio(metrics.r2)}.</li>
              <li className="pl-1 leading-relaxed">{String(zones.output_zone_rows ?? '-')} AI zones were created from {formatNumber(zones.rows_used_for_clustering ?? '-')} clustered records.</li>
            </ul>
          </CardContent>
        </Card>
      </div>

      <Card className="glass-panel">
        <CardContent className="p-8">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold">Detailed Market Analysis by Zone</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                Client showcase view based on the evaluated test set of {formatNumber(totalTestedRows || summary.property_count)} records, broken out separately for Land and Flat segments.
              </p>
            </div>
            <div className="rounded-2xl border border-primary/20 bg-primary/5 px-4 py-3">
              <div className="text-[10px] uppercase tracking-wider text-primary">Evaluation Split</div>
              <div className="mt-1 text-sm font-semibold">
                Land: {formatNumber(land?.count)} | Flat: {formatNumber(flat?.count)}
              </div>
            </div>
          </div>

          <div className="space-y-8">
            {renderZoneTable(
              landZoneRows,
              'Land',
              cn('font-medium', 'bg-amber-500/10 text-amber-600 border-amber-500/20'),
            )}
            {renderZoneTable(
              flatZoneRows,
              'Flat',
              cn('font-medium', 'bg-indigo-500/10 text-indigo-600 border-indigo-500/20'),
            )}
          </div>

          <div className="mt-6 flex items-start gap-3 p-4 rounded-xl bg-primary/5 border border-primary/10">
            <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
            <p className="text-sm text-muted-foreground leading-relaxed">
              This breakdown highlights valuation performance across different geographies in the held-out evaluation sample.
              Each AI zone is a mixed market cluster discovered by the model rather than a strict Land-only or Flat-only boundary.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
