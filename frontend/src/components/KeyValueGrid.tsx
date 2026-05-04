import React from 'react';
import { formatLabel, formatValueByKey } from '../utils/format';
import { cn } from '@/lib/utils';

type KeyValueGridProps = {
  payload: Record<string, unknown>;
  keys: string[];
};

/** Returns a colour class based on how bad an absolute error is relative to actual value. */
function errorSeverityClass(key: string, payload: Record<string, unknown>): string {
  if (!key.startsWith('absolute_error')) return '';
  const error = payload[key];
  if (typeof error !== 'number') return '';

  // For value_per_area errors, compare against the actual value_per_area
  if (key === 'absolute_error_value_per_area') {
    const actual = payload['actual_value_per_area'];
    if (typeof actual !== 'number' || actual === 0) return '';
    const ratio = error / actual;
    if (ratio > 0.5) return 'text-destructive'; // >50% error → red
    if (ratio > 0.25) return 'text-amber-500';  // 25–50% → amber
    return 'text-emerald-500';                   // <25% → green
  }

  // For market value errors, >25% of MAE threshold (₹2,00,000) → red
  if (key === 'absolute_error_market_value') {
    if (error > 500000) return 'text-destructive';
    if (error > 200000) return 'text-amber-500';
    return 'text-emerald-500';
  }

  return '';
}

export default function KeyValueGrid({ payload, keys }: KeyValueGridProps) {
  return (
    <dl className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mt-6">
      {keys.map((key) => {
        const colourClass = errorSeverityClass(key, payload);
        const rawValue = formatValueByKey(key, payload[key]);
        const unit = key.includes('value_per_sqft') ? ' ₹/sqft' : '';
        return (
          <div className="p-4 rounded-xl bg-muted/40 border border-border/50 hover:bg-muted/60 transition-colors" key={key}>
            <dt className="text-[11px] uppercase tracking-widest text-muted-foreground mb-1.5 font-semibold">
              {formatLabel(key)}
            </dt>
            <dd className={cn('m-0 font-bold', colourClass || 'text-foreground')}>
              {rawValue}{unit}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}
