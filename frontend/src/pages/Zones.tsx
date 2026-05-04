import React from 'react';
import DataTable from '../components/DataTable';
import HorizontalBarList from '../components/HorizontalBarList';
import ZoneMap from '../components/ZoneMap';
import type { GeoJsonFeatureCollection, ZoneSummaryRecord } from '../types/api';
import { formatNumber, formatPercent } from '../utils/format';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

type ZonesProps = {
  zones: ZoneSummaryRecord[];
  zoneGeoJson: GeoJsonFeatureCollection | null;
};

export default function Zones({ zones, zoneGeoJson }: ZonesProps) {
  const topZoneItems = zones.map((zone) => ({
    label: zone.ai_zone_name,
    value: (zone.median_value_per_sqft ?? zone.median_value_per_area) as number,
    subtitle: zone.ai_zone_description,
  }));

  return (
    <div className="flex flex-col gap-8">
      <div className="rounded-2xl overflow-hidden border border-border/50 shadow-xl">
        <ZoneMap zoneGeoJson={zoneGeoJson} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="glass-panel h-fit">
          <CardHeader>
            <CardTitle className="text-xl">How We Group Neighborhoods</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-foreground/80 leading-relaxed">
              Instead of using arbitrary government borders, our AI automatically discovers "Market Zones" based on similar property values, road access, and local amenities.
            </p>
            <ul className="space-y-3 text-sm text-muted-foreground list-disc pl-5 marker:text-primary">
              <li className="pl-1 leading-relaxed">Zones are given stakeholder-friendly names based on their characteristics (e.g., "High-Value Commercial").</li>
              <li className="pl-1 leading-relaxed">The AI naturally separates apartment-heavy areas from raw land markets.</li>
              <li className="pl-1 leading-relaxed">You can click on the map to see the typical property value for that specific neighborhood.</li>
            </ul>
          </CardContent>
        </Card>

        <Card className="glass-panel">
          <CardHeader>
            <CardTitle className="text-xl">Typical Property Value by Zone</CardTitle>
          </CardHeader>
          <CardContent>
            <HorizontalBarList items={topZoneItems} color="hsl(var(--primary))" valueFormatter={(value) => `${formatNumber(value)} ₹/sqft`} />
          </CardContent>
        </Card>
      </div>

      <div className="mt-4">
        <h3 className="text-xl font-bold mb-4">Zone Data Export</h3>
        <DataTable
          columns={[
            'ai_zone_name',
            'property_count',
            'median_value_per_sqft',
            'dominant_district',
            'dominant_mouza',
            'urban_share',
            'flat_share',
          ]}
          rows={zones.map((zone) => ({
            ...zone,
            urban_share: formatPercent(zone.urban_share),
            flat_share: formatPercent(zone.flat_share),
          }))}
        />
      </div>
    </div>
  );
}
