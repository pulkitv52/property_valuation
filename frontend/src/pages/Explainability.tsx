import React from 'react';
import HorizontalBarList from '../components/HorizontalBarList';
import type { FeatureImportanceRecord, PropertyExplanation } from '../types/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

type ExplainabilityProps = {
  featureImportance: FeatureImportanceRecord[];
  sampleExplanations: PropertyExplanation[];
};

export default function Explainability({ featureImportance, sampleExplanations }: ExplainabilityProps) {
  const topItems = featureImportance.slice(0, 15).map((item) => ({
    label: item.base_feature,
    value: item.importance,
    subtitle: item.segment_value,
  }));

  return (
    <div className="flex flex-col gap-8">
      <Card className="glass-panel">
        <CardHeader>
          <CardTitle className="text-xl">What Drives Property Prices in General?</CardTitle>
        </CardHeader>
        <CardContent>
          <HorizontalBarList items={topItems} color="hsl(var(--primary))" valueFormatter={(value) => value.toFixed(4)} />
        </CardContent>
      </Card>
      
      <Card className="glass-panel">
        <CardHeader>
          <CardTitle className="text-xl">Why Did the AI Choose These Prices? (Examples)</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {sampleExplanations.slice(0, 3).map((item, index) => (
            <div className="p-6 rounded-2xl bg-muted/20 border border-border/50 flex flex-col gap-3 hover:bg-muted/30 transition-colors" key={index}>
              <h4 className="font-bold text-lg text-primary">{String(item.identifiers?.property_id ?? item.segment_value)}</h4>
              <p className="text-xs font-semibold tracking-wider uppercase text-muted-foreground">
                Segment: <span className="text-foreground/80">{item.segment_value}</span> | Method: <span className="text-foreground/80">{item.explanation_method}</span>
              </p>
              <p className="text-sm leading-relaxed text-foreground/90 mt-2">{item.plain_language_summary}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
