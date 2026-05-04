import React from 'react';
import MetricCard from '../components/MetricCard';
import type { DashboardSummary, PropertyTypeAnalysisRecord } from '../types/api';
import { formatPercent, formatRatio } from '../utils/format';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';

type OverviewProps = {
  summary: DashboardSummary | null;
};

export default function Overview({ summary }: OverviewProps) {
  if (!summary) return <div className="p-8 text-center text-muted-foreground bg-muted/20 rounded-xl border border-dashed border-border">Loading overview...</div>;
  const metrics = summary.metrics as Record<string, number>;
  const zones = summary.zones as Record<string, number>;
  const propertyTypeRows = summary.property_type_analysis ?? [];
  const land = propertyTypeRows.find((row: PropertyTypeAnalysisRecord) => row.group_name === 'Land');
  const flat = propertyTypeRows.find((row: PropertyTypeAnalysisRecord) => row.group_name === 'Flat');
  return (
    <div className="flex flex-col gap-8">
      <Card className="overflow-hidden border-primary/30 shadow-primary/5 bg-gradient-to-br from-card to-primary/5">
        <CardContent className="p-8 flex flex-col md:flex-row gap-8 items-start md:items-end justify-between">
          <div className="flex-1 max-w-3xl">
            <Badge variant="outline" className="mb-4 bg-background/50 backdrop-blur-md border-primary/50 text-primary">System Ready</Badge>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4 leading-tight">
              Our AI accurately estimates property prices and clusters distinct market zones.
            </h2>
            <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl">
              This dashboard uses our Smart Valuation Engine to instantly estimate property values, group similar neighborhoods, and explain exactly why a property is priced the way it is.
            </p>
          </div>
          <div className="bg-primary/10 border border-primary/20 p-6 rounded-2xl min-w-[280px]">
            <span className="block text-xs uppercase tracking-widest text-primary font-semibold mb-2">Smart Engine Version</span>
            <strong className="text-2xl tracking-tight font-bold">{summary.best_candidate_name.replace(/_/g, ' ')}</strong>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard label="Tested Properties" value={String(summary.property_count)} tone="accent" tooltip="The number of historical properties we used to test the AI's accuracy." />
        <MetricCard label="Average Error Margin (MAPE)" value={formatPercent(metrics.mape)} tooltip="On average, our AI's price estimate is within this percentage of the true market price." />
        <MetricCard label="Accuracy Score (R²)" value={formatRatio(metrics.r2)} tooltip="A score out of 1.0 showing how well our AI understands the market dynamics. Higher is better." />
        <MetricCard label="AI Zones Created" value={String(zones.output_zone_rows ?? '-')} tooltip="The number of distinct, algorithmically discovered market regions." />
        <MetricCard label="Clustering Samples" value={String(zones.rows_used_for_clustering ?? '-')} tooltip="How many properties were analyzed to draw the zone boundaries." />
        <MetricCard label="Gov Valuation Compare" value={summary.mvdb_status} tone="muted" tooltip="Status of our integration with official government circle rates." />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="glass-panel">
          <CardContent className="p-8">
            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
              <span className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm">1</span>
              Why this system is valuable today
            </h3>
            <ul className="space-y-4 text-foreground/80 list-disc pl-5 marker:text-primary">
              <li className="pl-1 leading-relaxed">It delivers instant, objective property valuations based on real historical data.</li>
              <li className="pl-1 leading-relaxed">It automatically discovers local market zones based on infrastructure and sales, rather than arbitrary borders.</li>
              <li className="pl-1 leading-relaxed">It is fully integrated and ready to connect with external government portals for automated auditing.</li>
            </ul>
          </CardContent>
        </Card>
        
        <Card className="glass-panel">
          <CardContent className="p-8">
            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
              <span className="w-8 h-8 rounded-full bg-accent/20 text-accent flex items-center justify-center text-sm">2</span>
              Key findings from the data
            </h3>
            <ul className="space-y-4 text-foreground/80 list-disc pl-5 marker:text-accent">
              <li className="pl-1 leading-relaxed">Location and road access are the strongest drivers of property value.</li>
              <li className="pl-1 leading-relaxed">The AI has naturally separated high-density apartment areas from raw land plots into different zones.</li>
              <li className="pl-1 leading-relaxed">The engine is primed and waiting for official government rates to begin automated cross-checking.</li>
            </ul>
          </CardContent>
        </Card>
      </div>

      <Card className="glass-panel">
        <CardContent className="p-8">
          <h3 className="text-xl font-bold mb-6">Separate Analysis: Land vs Flat</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="rounded-2xl border border-border/50 bg-muted/20 p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-semibold">Land</h4>
                <Badge variant="outline">{land?.count ?? '-'} records</Badge>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <MetricCard label="MAPE" value={formatPercent(land?.mape)} />
                <MetricCard label="Avg Predicted" value={String(land?.mean_predicted_value_per_area?.toFixed?.(2) ?? 'NA')} />
                <MetricCard label="MAE" value={String(land?.mae?.toFixed?.(2) ?? 'NA')} />
                <MetricCard label="Avg Actual" value={String(land?.mean_actual_value_per_area?.toFixed?.(2) ?? 'NA')} />
              </div>
            </div>
            <div className="rounded-2xl border border-border/50 bg-muted/20 p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-semibold">Flat</h4>
                <Badge variant="outline">{flat?.count ?? '-'} records</Badge>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <MetricCard label="MAPE" value={formatPercent(flat?.mape)} />
                <MetricCard label="Avg Predicted" value={String(flat?.mean_predicted_value_per_area?.toFixed?.(2) ?? 'NA')} />
                <MetricCard label="MAE" value={String(flat?.mae?.toFixed?.(2) ?? 'NA')} />
                <MetricCard label="Avg Actual" value={String(flat?.mean_actual_value_per_area?.toFixed?.(2) ?? 'NA')} />
              </div>
            </div>
          </div>
          <p className="mt-5 text-sm text-muted-foreground leading-relaxed">
            We now evaluate Land and Flat separately because they behave like different markets. Flat predictions are usually tighter in percentage terms, while Land values tend to span a wider range and need stronger locality context.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
