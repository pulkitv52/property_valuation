import React from 'react';
import { formatNumber } from '../utils/format';
import { cn } from '@/lib/utils';

type HorizontalBarListProps = {
  items: Array<{
    label: string;
    value: number;
    subtitle?: string;
  }>;
  color?: string;
  valueFormatter?: (value: number) => string;
};

export default function HorizontalBarList({
  items,
  color = 'hsl(var(--primary))',
  valueFormatter = (value) => formatNumber(value),
}: HorizontalBarListProps) {
  const maxValue = Math.max(...items.map((item) => item.value), 0);

  return (
    <div className="flex flex-col gap-4">
      {items.map((item) => {
        const width = maxValue > 0 ? `${(item.value / maxValue) * 100}%` : '0%';
        return (
          <div className="flex flex-col gap-2 group" key={`${item.label}-${item.value}`}>
            <div className="flex justify-between gap-3 items-end">
              <div>
                <div className="font-semibold text-sm group-hover:text-primary transition-colors">{item.label}</div>
                {item.subtitle ? <div className="text-xs text-muted-foreground mt-0.5">{item.subtitle}</div> : null}
              </div>
              <strong className="text-sm font-bold">{valueFormatter(item.value)}</strong>
            </div>
            <div className="w-full h-2.5 rounded-full bg-secondary overflow-hidden">
              <div 
                className="h-full rounded-full transition-all duration-500 ease-out" 
                style={{ width, background: color }} 
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
