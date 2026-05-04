import React from 'react';
import { Card, CardContent } from './ui/card';
import { cn } from '@/lib/utils';
import { Info } from 'lucide-react';

type MetricCardProps = {
  label: string;
  value: string;
  tone?: 'default' | 'accent' | 'muted';
  tooltip?: string;
};

export default function MetricCard({ label, value, tone = 'default', tooltip }: MetricCardProps) {
  return (
    <Card 
      className={cn(
        "transition-all duration-200 hover:scale-[1.02] border-border/40 backdrop-blur-sm relative overflow-visible",
        tone === 'default' && "bg-card shadow-lg",
        tone === 'accent' && "bg-primary text-primary-foreground shadow-primary/20 shadow-xl border-primary/50",
        tone === 'muted' && "bg-muted/50 text-muted-foreground shadow-md"
      )}
    >
      <CardContent className="p-6 flex flex-col gap-2 relative">
        <div className="flex items-center gap-1.5 z-10 group">
          <span className="text-[11px] sm:text-xs uppercase tracking-widest opacity-80 font-semibold">{label}</span>
          {tooltip && (
            <div className="relative flex items-center">
              <Info className="w-3.5 h-3.5 opacity-60 hover:opacity-100 transition-opacity cursor-help" />
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-foreground text-background text-xs rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 pointer-events-none z-50 text-center leading-relaxed">
                {tooltip}
                <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-foreground"></div>
              </div>
            </div>
          )}
        </div>
        <span className="text-2xl sm:text-3xl font-bold tracking-tight">{value}</span>
      </CardContent>
    </Card>
  );
}
