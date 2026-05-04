import React from 'react';
import type { PropertyExplanation } from '../types/api';
import { formatNumber } from '../utils/format';
import { Card, CardContent } from './ui/card';

type ExplanationPanelProps = {
  explanation: PropertyExplanation | null;
};

export default function ExplanationPanel({ explanation }: ExplanationPanelProps) {
  if (!explanation) {
    return <div className="p-8 text-center text-muted-foreground bg-muted/20 rounded-xl border border-dashed border-border">Select a property to see explanation details.</div>;
  }

  return (
    <div className="flex flex-col gap-6">
      <p className="text-base text-foreground/90 leading-relaxed font-medium">
        {explanation.plain_language_summary}
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="bg-muted/30 border-border/50">
          <CardContent className="p-4 flex flex-col gap-1">
            <span className="text-xs uppercase tracking-widest text-muted-foreground font-semibold">Predicted Value / Sq Ft</span>
            <strong className="text-lg">{formatNumber(explanation.predicted_value_per_sqft)} <span className="text-xs font-normal text-muted-foreground">₹/sqft</span></strong>
          </CardContent>
        </Card>
        <Card className="bg-muted/30 border-border/50">
          <CardContent className="p-4 flex flex-col gap-1">
            <span className="text-xs uppercase tracking-widest text-muted-foreground font-semibold">Actual Value / Sq Ft</span>
            <strong className="text-lg">{formatNumber(explanation.actual_value_per_sqft)} <span className="text-xs font-normal text-muted-foreground">₹/sqft</span></strong>
          </CardContent>
        </Card>
        <Card className="bg-muted/30 border-border/50">
          <CardContent className="p-4 flex flex-col gap-1">
            <span className="text-xs uppercase tracking-widest text-muted-foreground font-semibold">Area Unit</span>
            <strong className="text-lg">{explanation.area_measurement_label ?? 'NA'}</strong>
          </CardContent>
        </Card>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-5 rounded-xl border border-primary/20 bg-primary/5">
          <h4 className="font-semibold text-primary mb-3">Top Positive Factors</h4>
          <ul className="list-disc pl-5 space-y-2 text-sm text-foreground/80 marker:text-primary">
            {explanation.top_positive_factors.map((factor, index) => (
              <li key={index}>{String(factor.reason ?? factor.base_feature)}</li>
            ))}
          </ul>
        </div>
        <div className="p-5 rounded-xl border border-destructive/20 bg-destructive/5">
          <h4 className="font-semibold text-destructive mb-3">Top Negative Factors</h4>
          <ul className="list-disc pl-5 space-y-2 text-sm text-foreground/80 marker:text-destructive">
            {explanation.top_negative_factors.map((factor, index) => (
              <li key={index}>{String(factor.reason ?? factor.base_feature)}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
