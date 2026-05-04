import React from 'react';
import HorizontalBarList from '../components/HorizontalBarList';
import MetricCard from '../components/MetricCard';
import DataTable from '../components/DataTable';
import type { DashboardSummary, FeatureImportanceRecord, PropertyTypeAnalysisRecord } from '../types/api';
import { formatNumber, formatPercent, formatRatio } from '../utils/format';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

type ModelPerformanceProps = {
  summary: DashboardSummary | null;
  featureImportance: FeatureImportanceRecord[];
};

export default function ModelPerformance({ summary, featureImportance }: ModelPerformanceProps) {
  if (!summary) return <div className="p-8 text-center text-muted-foreground bg-muted/20 rounded-xl border border-dashed border-border">Loading model performance...</div>;
  const metrics = summary.metrics as Record<string, number>;
  const propertyTypeRows = (summary.property_type_analysis ?? []) as PropertyTypeAnalysisRecord[];
  const topFeatures = featureImportance.slice(0, 10).map((item) => ({
    label: item.base_feature,
    value: item.importance,
    subtitle: item.segment_value,
  }));
  return (
    <div className="flex flex-col gap-8">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <MetricCard label="Average Price Difference (MAE)" value={formatNumber(metrics.mae)} tooltip="The average raw difference between our estimate and the actual price." />
        <MetricCard label="Maximum Expected Error (RMSE)" value={formatNumber(metrics.rmse)} tooltip="A stricter measure of error that heavily penalizes large mistakes in prediction." />
        <MetricCard label="Average Error Margin (MAPE)" value={formatPercent(metrics.mape)} tone="accent" tooltip="On average, our AI's price estimate is within this percentage of the true market price." />
        <MetricCard label="Accuracy Score (R²)" value={formatRatio(metrics.r2)} tone="accent" tooltip="A score out of 1.0 showing how well our AI understands the market dynamics. Higher is better." />
        <MetricCard label="Market Value Error (MAE)" value={formatNumber(metrics.mae_market_value)} tooltip="The average error when comparing against standard market valuation rates." />
        <MetricCard label="Market Value Max Error (RMSE)" value={formatNumber(metrics.rmse_market_value)} tooltip="The strictest error measure against standard market valuation rates." />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="glass-panel">
          <CardHeader>
            <CardTitle className="text-xl">Key Price Drivers (Global)</CardTitle>
          </CardHeader>
          <CardContent>
            <HorizontalBarList
              items={topFeatures}
              valueFormatter={(value) => value.toFixed(4)}
            />
          </CardContent>
        </Card>
        
        <Card className="glass-panel h-fit">
          <CardHeader>
            <CardTitle className="text-xl">Performance Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-4 text-foreground/80 list-disc pl-5 marker:text-primary">
              <li className="pl-1 leading-relaxed"><strong>Average Error Margin (MAPE)</strong> is the primary business-facing metric. It tells us how far off we are on a typical property.</li>
              <li className="pl-1 leading-relaxed">The current Smart Valuation Engine automatically splits the market into 'Land' and 'Flat' to improve accuracy.</li>
              <li className="pl-1 leading-relaxed">Market-value error metrics are also exposed here to help bridge our engine's output with stakeholder expectations and official rates.</li>
            </ul>
          </CardContent>
        </Card>
      </div>

      <Card className="glass-panel">
        <CardHeader>
          <CardTitle className="text-xl">Land vs Flat Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={[
              'group_name',
              'count',
              'mape',
              'mae',
              'rmse',
              'mean_actual_value_per_area',
              'mean_predicted_value_per_area',
            ]}
            rows={propertyTypeRows.map((row) => ({
              ...row,
              mape: `${row.mape.toFixed(2)}%`,
              mae: row.mae.toFixed(2),
              rmse: row.rmse.toFixed(2),
              mean_actual_value_per_area: row.mean_actual_value_per_area.toFixed(2),
              mean_predicted_value_per_area: row.mean_predicted_value_per_area.toFixed(2),
            }))}
          />
        </CardContent>
      </Card>
    </div>
  );
}
