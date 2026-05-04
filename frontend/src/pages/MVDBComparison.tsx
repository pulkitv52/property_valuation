import React from 'react';
import { formatLabel } from '../utils/format';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

type MVDBComparisonProps = {
  mvdbStatus: Record<string, unknown> | null;
};

export default function MVDBComparison({ mvdbStatus }: MVDBComparisonProps) {
  const rows = Object.entries(mvdbStatus ?? {});
  return (
    <div className="flex flex-col gap-8">
      <Card className="glass-panel border-primary/20 bg-primary/5">
        <CardHeader>
          <CardTitle className="text-xl text-primary">Government Circle Rate Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-foreground/80 leading-relaxed text-lg">
            This module will automatically cross-check our AI's price estimates against the official government circle rates.
            It is currently waiting for the official valuation dataset to be uploaded by the administration.
          </p>
        </CardContent>
      </Card>

      <Card className="glass-panel">
        <CardHeader>
          <CardTitle className="text-xl">Integration Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {rows.map(([key, value]) => (
              <div className="p-5 rounded-xl bg-muted/30 border border-border/50 hover:bg-muted/50 transition-colors" key={key}>
                <span className="block text-[11px] uppercase tracking-widest text-muted-foreground font-semibold mb-2">{formatLabel(key)}</span>
                <strong className="text-lg font-bold">{Array.isArray(value) ? value.join(', ') : String(value)}</strong>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
