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
    subtitle: `Land ${formatPercent((1 - zone.flat_share) * 100)} | Flat ${formatPercent(zone.flat_share * 100)}`,
  }));

  return (
    <div className="flex flex-col gap-8">
      <div className="rounded-2xl overflow-hidden border border-border/50 shadow-xl">
        <ZoneMap zoneGeoJson={zoneGeoJson} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
            'property_count',
            'ai_zone_name',
            'median_value_per_sqft',
            'dominant_district',
            'dominant_mouza',
            'urban_share',
            'rural_share',
            'flat_share',
          ]}
          rows={zones.map((zone) => ({
            ...zone,
            urban_share: formatPercent(zone.urban_share * 100),
            rural_share: formatPercent(zone.rural_share * 100),
            flat_share: formatPercent(zone.flat_share * 100),
          }))}
        />
      </div>
    </div>
  );
}
