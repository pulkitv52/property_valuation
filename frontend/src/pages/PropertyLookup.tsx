import React from 'react';
import ExplanationPanel from '../components/ExplanationPanel';
import KeyValueGrid from '../components/KeyValueGrid';
import PropertySearch from '../components/PropertySearch';
import type { PropertyExplanation, PropertyRecordResponse, PropertySearchRecord } from '../types/api';
import { formatNumber } from '../utils/format';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

type PropertyLookupProps = {
  properties: PropertySearchRecord[];
  selectedPropertyId: string;
  onSelect: (propertyId: string) => void;
  propertyRecord: PropertyRecordResponse | null;
  explanation: PropertyExplanation | null;
  districtFilter: string;
  mouzaFilter: string;
  onDistrictChange: (value: string) => void;
  onMouzaChange: (value: string) => void;
  onApplyFilters: () => void;
};

export default function PropertyLookup({
  properties,
  selectedPropertyId,
  onSelect,
  propertyRecord,
  explanation,
  districtFilter,
  mouzaFilter,
  onDistrictChange,
  onMouzaChange,
  onApplyFilters,
}: PropertyLookupProps) {
  const payload = propertyRecord?.payload ?? {};

  return (
    <div className="flex flex-col lg:flex-row gap-6">
      <div className="w-full lg:w-80 flex-shrink-0">
        <PropertySearch
          properties={properties}
          selectedPropertyId={selectedPropertyId}
          onSelect={onSelect}
          districtFilter={districtFilter}
          mouzaFilter={mouzaFilter}
          onDistrictChange={onDistrictChange}
          onMouzaChange={onMouzaChange}
          onApplyFilters={onApplyFilters}
        />
      </div>
      
      <div className="flex-1 flex flex-col gap-6">
        <Card className="glass-panel overflow-hidden border-primary/20">
          <CardHeader className="bg-primary/5 border-b border-primary/10 pb-4">
            <CardTitle className="text-xl">Property Details</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="p-4 rounded-xl bg-muted/30 border border-border/40 text-center">
                <span className="block text-xs uppercase tracking-widest text-muted-foreground mb-1.5">Pred Value / Sq Ft</span>
                <strong className="text-lg text-primary">{formatNumber(payload.predicted_value_per_sqft)} <span className="text-xs font-normal text-muted-foreground">₹/sqft</span></strong>
              </div>
              <div className="p-4 rounded-xl bg-muted/30 border border-border/40 text-center">
                <span className="block text-xs uppercase tracking-widest text-muted-foreground mb-1.5">Act Value / Sq Ft</span>
                <strong className="text-lg text-foreground">{formatNumber(payload.actual_value_per_sqft)} <span className="text-xs font-normal text-muted-foreground">₹/sqft</span></strong>
              </div>
              <div className="p-4 rounded-xl bg-muted/30 border border-border/40 text-center">
                <span className="block text-xs uppercase tracking-widest text-muted-foreground mb-1.5">Market Value</span>
                <strong className="text-lg text-foreground">{formatNumber(payload.predicted_market_value)}</strong>
              </div>
              <div className="p-4 rounded-xl bg-muted/30 border border-border/40 text-center">
                <span className="block text-xs uppercase tracking-widest text-muted-foreground mb-1.5">Area Unit</span>
                <strong className="text-lg text-foreground">{String(payload.area_measurement_label ?? 'NA')}</strong>
              </div>
            </div>
            
            <KeyValueGrid
              payload={payload}
              keys={[
                'property_id',
                'property_district_Name',
                'PS_Name',
                'Mouza_Name',
                'Road_Name',
                'Zone_no',
                'Flat_or_Land',
                'Area',
                'area_sqft',
                'absolute_error_value_per_sqft',
                'absolute_error_market_value',
              ]}
            />
          </CardContent>
        </Card>

        <Card className="glass-panel">
          <CardHeader>
            <CardTitle className="text-xl">Valuation Explanation</CardTitle>
          </CardHeader>
          <CardContent>
            <ExplanationPanel explanation={explanation} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
