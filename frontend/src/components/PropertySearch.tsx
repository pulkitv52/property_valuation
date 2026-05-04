import React from 'react';
import type { PropertySearchRecord } from '../types/api';
import { formatNumber } from '../utils/format';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Button } from './ui/button';
import { cn } from '@/lib/utils';

type PropertySearchProps = {
  properties: PropertySearchRecord[];
  selectedPropertyId: string;
  onSelect: (propertyId: string) => void;
  districtFilter: string;
  mouzaFilter: string;
  onDistrictChange: (value: string) => void;
  onMouzaChange: (value: string) => void;
  onApplyFilters: () => void;
};

export default function PropertySearch({
  properties,
  selectedPropertyId,
  onSelect,
  districtFilter,
  mouzaFilter,
  onDistrictChange,
  onMouzaChange,
  onApplyFilters,
}: PropertySearchProps) {
  return (
    <div className="flex flex-col gap-3 p-4 bg-card/40 backdrop-blur-md rounded-2xl border border-border/40 shadow-lg h-[calc(100vh-120px)]">
      <div className="flex flex-col gap-4 pb-4 border-b border-border/50">
        <h3 className="font-semibold text-lg">Property Search</h3>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>District</Label>
            <Input 
              value={districtFilter} 
              onChange={(event) => onDistrictChange(event.target.value)} 
              placeholder="Purba Bardhaman" 
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Mouza</Label>
            <Input 
              value={mouzaFilter} 
              onChange={(event) => onMouzaChange(event.target.value)} 
              placeholder="Burdwan" 
            />
          </div>
        </div>
        <Button onClick={onApplyFilters} className="w-full">
          Refresh List
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto pr-2 flex flex-col gap-2">
        {properties.map((property) => {
          const isActive = selectedPropertyId === property.property_id;
          return (
            <button
              key={property.property_id}
              onClick={() => onSelect(property.property_id)}
              type="button"
              className={cn(
                "text-left p-4 rounded-xl transition-all duration-200 border",
                isActive 
                  ? "bg-primary/10 border-primary shadow-sm shadow-primary/10" 
                  : "bg-background border-transparent hover:border-border hover:bg-muted/40"
              )}
            >
              <div className={cn("font-bold mb-1.5", isActive ? "text-primary" : "text-foreground")}>
                {property.property_id}
              </div>
              <div className="text-xs text-muted-foreground flex flex-col gap-1">
                <span className="font-medium text-foreground/70">{property.property_district_Name} / {property.Mouza_Name}</span>
                <span>
                  Predicted Value/Sq Ft:{' '}
                  <strong className="text-foreground/80">
                    {formatNumber(property.predicted_value_per_sqft)} <span className="text-muted-foreground font-normal">₹/sqft</span>
                  </strong>
                </span>
                <span>Original Area Unit: {property.area_measurement_label ?? 'NA'}</span>
                <span>AI Zone: {property.ai_zone_name ?? property.ai_zone ?? 'NA'}</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
