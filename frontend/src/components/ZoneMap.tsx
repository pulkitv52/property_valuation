import React, { useMemo, useState } from 'react';
import { GeoJSON, MapContainer, TileLayer, useMap } from 'react-leaflet';
import type { Layer } from 'leaflet';
import type { GeoJsonFeatureCollection } from '../types/api';
import 'leaflet/dist/leaflet.css';

type ZoneMapProps = {
  zoneGeoJson: GeoJsonFeatureCollection | null;
};

type ZoneProperties = {
  ai_zone?: string;
  ai_zone_name?: string;
  ai_zone_description?: string;
  property_count?: number;
  flat_share?: number;
  rural_share?: number;
  urban_share?: number;
  median_value_per_area?: number;
  median_value_per_sqft?: number;
};

const zoneDisplayNames: Record<string, string> = {
  AI_ZONE_01: 'Z-01 | Premium Urban Market',
  AI_ZONE_02: 'Z-02 | Growth Corridor',
  AI_ZONE_03: 'Z-03 | Accessible Mid-Market',
  AI_ZONE_04: 'Z-04 | Mixed Residential Belt',
  AI_ZONE_05: 'Z-05 | Emerging Urban Fringe',
  AI_ZONE_06: 'Z-06 | Affordable Expansion Zone',
  AI_ZONE_07: 'Z-07 | Outer Value Market',
};

const zonePalette = [
  '#0b6e4f', // AI_ZONE_01 - deep teal
  '#2563eb', // AI_ZONE_02 - blue
  '#000000', // AI_ZONE_03 - black
  '#7c3aed', // AI_ZONE_04 - violet
  '#16a34a', // AI_ZONE_05 - green
  '#db2777', // AI_ZONE_06 - pink
  '#dc2626', // AI_ZONE_07 - red
];

function formatNumber(value: unknown) {
  if (typeof value !== 'number') return 'NA';
  return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function formatPercent(value: unknown) {
  if (typeof value !== 'number') return 'NA';
  return `${value.toFixed(1)}%`;
}

function resolveZoneLabel(zone: ZoneProperties | null | undefined) {
  if (!zone?.ai_zone) return zone?.ai_zone_name ?? 'Zone Profile';
  return zoneDisplayNames[zone.ai_zone] ?? zone.ai_zone_name ?? zone.ai_zone;
}

export default function ZoneMap({ zoneGeoJson }: ZoneMapProps) {
  const [activeZone, setActiveZone] = useState<ZoneProperties | null>(null);

  const bounds = useMemo(() => {
    if (!zoneGeoJson) return null;
    const coords: Array<[number, number]> = [];
    for (const feature of zoneGeoJson.features) {
      const geometry = feature.geometry as { type?: string; coordinates?: unknown };
      if (!geometry?.coordinates) continue;
      const stack = [geometry.coordinates as unknown];
      while (stack.length) {
        const current = stack.pop();
        if (!Array.isArray(current)) continue;
        if (typeof current[0] === 'number' && typeof current[1] === 'number') {
          coords.push([current[1] as number, current[0] as number]);
        } else {
          for (const item of current) stack.push(item);
        }
      }
    }
    if (!coords.length) return null;
    return coords;
  }, [zoneGeoJson]);

  if (!zoneGeoJson) {
    return <div className="p-10 text-center text-muted-foreground">Loading zone map...</div>;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] overflow-hidden bg-card rounded-2xl shadow-sm border border-border/50">
      <div className="min-h-[440px] h-full w-full">
        <MapContainer className="h-full w-full min-h-[440px]" center={[23.45, 87.65]} zoom={9} scrollWheelZoom={true}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <GeoJSON
            data={zoneGeoJson as never}
            onEachFeature={(feature, layer) => {
              const props = feature.properties as ZoneProperties;
              const zoneIndex = Number(String(props.ai_zone ?? '0').replace(/\D/g, '')) - 1;
              const color = zonePalette[(zoneIndex + zonePalette.length) % zonePalette.length];
              const styledLayer = layer as Layer & {
                setStyle?: (style: Record<string, unknown>) => void;
                bindPopup: (content: string) => void;
                openPopup: () => void;
                closePopup: () => void;
                bringToFront?: () => void;
                on: (event: string, handler: () => void) => void;
              };
              const propertyCount = typeof props.property_count === 'number' ? props.property_count : NaN;
              const flatShare = typeof props.flat_share === 'number' ? props.flat_share : NaN;
              const flatCount = Number.isFinite(propertyCount) && Number.isFinite(flatShare)
                ? Math.round(propertyCount * flatShare)
                : NaN;
              const landCount = Number.isFinite(propertyCount) && Number.isFinite(flatCount)
                ? Math.max(0, propertyCount - flatCount)
                : NaN;
              styledLayer.setStyle?.({ color, weight: 1.5, fillColor: color, fillOpacity: 0.34 });
              styledLayer.bindPopup(`
                <strong>${resolveZoneLabel(props)}</strong><br/>
                Properties: ${formatNumber(props.property_count)}<br/>
                Land: ${formatNumber(landCount)} | Flat: ${formatNumber(flatCount)}<br/>
                Median value/sq ft: ${formatNumber(props.median_value_per_sqft ?? props.median_value_per_area)} ₹/sqft
              `);
              styledLayer.on('mouseover', () => {
                setActiveZone(props);
                styledLayer.bringToFront?.();
                styledLayer.openPopup();
              });
              styledLayer.on('mouseout', () => {
                styledLayer.closePopup();
              });
            }}
          />
          {bounds ? <MapBoundsSetter bounds={bounds} /> : null}
        </MapContainer>
      </div>
      <div className="p-6 bg-gradient-to-b from-primary/5 to-transparent border-t lg:border-t-0 lg:border-l border-border/50 flex flex-col gap-4">
        <div>
          <h3 className="font-bold text-xl mb-2">{resolveZoneLabel(activeZone)}</h3>
          <p className="text-muted-foreground text-sm leading-relaxed">Hover over a zone to inspect its property count, Land/Flat mix, and typical value level.</p>
        </div>
        <dl className="flex flex-col gap-3 mt-4">
          <div className="pb-3 border-b border-border/50">
            <dt className="text-[11px] uppercase tracking-widest text-muted-foreground font-semibold mb-1">Zone ID</dt>
            <dd className="font-bold text-lg">{activeZone?.ai_zone ?? 'NA'}</dd>
          </div>
          <div className="pb-3 border-b border-border/50">
            <dt className="text-[11px] uppercase tracking-widest text-muted-foreground font-semibold mb-1">Properties</dt>
            <dd className="font-bold text-lg">{formatNumber(activeZone?.property_count)}</dd>
          </div>
          <div className="pb-3 border-b border-border/50">
            <dt className="text-[11px] uppercase tracking-widest text-muted-foreground font-semibold mb-1">Land / Flat Count</dt>
            <dd className="font-bold text-lg">
              {typeof activeZone?.property_count === 'number' && typeof activeZone?.flat_share === 'number'
                ? `${formatNumber(Math.max(0, activeZone.property_count - Math.round(activeZone.property_count * activeZone.flat_share)))} / ${formatNumber(Math.round(activeZone.property_count * activeZone.flat_share))}`
                : 'NA'}
            </dd>
          </div>
          <div className="pb-3 border-b border-border/50">
            <dt className="text-[11px] uppercase tracking-widest text-muted-foreground font-semibold mb-1">Land / Flat Share</dt>
            <dd className="font-bold text-lg">
              {typeof activeZone?.flat_share === 'number'
                ? `${formatPercent((1 - activeZone.flat_share) * 100)} / ${formatPercent(activeZone.flat_share * 100)}`
                : 'NA'}
            </dd>
          </div>
          <div className="pb-3 border-b border-border/50 border-b-transparent">
            <dt className="text-[11px] uppercase tracking-widest text-muted-foreground font-semibold mb-1">Median Value / Sq Ft</dt>
            <dd className="font-bold text-lg text-primary">{formatNumber(activeZone?.median_value_per_sqft ?? activeZone?.median_value_per_area)} <span className="text-xs font-normal text-muted-foreground">₹/sqft</span></dd>
          </div>
        </dl>
      </div>
    </div>
  );
}

function MapBoundsSetter({ bounds }: { bounds: Array<[number, number]> }) {
  const mapBounds = useMemo(() => bounds, [bounds]);
  const map = useMap();
  React.useEffect(() => {
    map.fitBounds(mapBounds, { padding: [24, 24] });
  }, [map, mapBounds]);
  return null;
}
