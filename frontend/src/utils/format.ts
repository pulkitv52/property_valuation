export function formatNumber(value: unknown, maximumFractionDigits = 0): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return 'NA';
  return value.toLocaleString(undefined, { maximumFractionDigits });
}

export function formatPercent(value: unknown, maximumFractionDigits = 2): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return 'NA';
  return `${value.toFixed(maximumFractionDigits)}%`;
}

export function formatRatio(value: unknown, maximumFractionDigits = 3): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return 'NA';
  return value.toFixed(maximumFractionDigits);
}

export function formatLabel(label: string): string {
  return label
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

export function formatValueByKey(key: string, value: unknown): string {
  if (value === null || value === undefined || value === '') return 'NA';
  if (typeof value === 'number') {
    if (key.toLowerCase().includes('share') || key.toLowerCase().includes('mape')) {
      return formatPercent(value);
    }
    if (key.toLowerCase().includes('r2')) {
      return formatRatio(value);
    }
    return formatNumber(value);
  }
  return String(value);
}
