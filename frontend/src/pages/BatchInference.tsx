import React from 'react';
import * as XLSX from 'xlsx';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { api } from '../services/api';
import { formatNumber } from '../utils/format';

type BatchPredictionRow = Record<string, unknown>;

function toWorksheetRows(file: File, data: ArrayBuffer): BatchPredictionRow[] {
  const workbook = XLSX.read(data, { type: 'array' });
  const firstSheetName = workbook.SheetNames[0];
  if (!firstSheetName) return [];
  const worksheet = workbook.Sheets[firstSheetName];
  return XLSX.utils.sheet_to_json<BatchPredictionRow>(worksheet, { defval: null });
}

export default function BatchInference() {
  const [fileName, setFileName] = React.useState('');
  const [inputRows, setInputRows] = React.useState<BatchPredictionRow[]>([]);
  const [results, setResults] = React.useState<BatchPredictionRow[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [summary, setSummary] = React.useState<Record<string, unknown> | null>(null);

  async function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const lowerName = file.name.toLowerCase();
    if (!lowerName.endsWith('.csv') && !lowerName.endsWith('.xlsx') && !lowerName.endsWith('.xls')) {
      setError('Please upload only CSV or Excel (.xlsx/.xls) files.');
      setInputRows([]);
      setResults([]);
      setSummary(null);
      return;
    }
    try {
      setError('');
      setFileName(file.name);
      const data = await file.arrayBuffer();
      const rows = toWorksheetRows(file, data);
      setInputRows(rows);
      setResults([]);
      setSummary(null);
      if (!rows.length) setError('No rows detected in uploaded file.');
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : 'Failed to parse uploaded file.');
      setInputRows([]);
      setResults([]);
      setSummary(null);
    }
  }

  async function runBatchInference() {
    if (!inputRows.length) {
      setError('Upload a CSV/Excel file with at least one row.');
      return;
    }
    try {
      setLoading(true);
      setError('');
      const response = await api.predict({ records: inputRows });
      setResults(response.results);
      setSummary(response.summary);
    } catch (predictError) {
      setError(predictError instanceof Error ? predictError.message : 'Batch inference failed.');
      setResults([]);
      setSummary(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card className="glass-panel border-primary/20">
        <CardHeader className="bg-primary/5 border-b border-primary/10">
          <CardTitle className="text-xl">Batch CSV/Excel Inference</CardTitle>
        </CardHeader>
        <CardContent className="p-6 space-y-4">
          <p className="text-sm text-muted-foreground">
            Upload transaction/property records as CSV or Excel. The system will predict value per sqft, market value, and AI zone.
          </p>
          <input type="file" accept=".csv,.xlsx,.xls" onChange={handleFileChange} />
          {fileName ? <p className="text-sm">Loaded file: <strong>{fileName}</strong> ({inputRows.length.toLocaleString()} rows)</p> : null}
          <Button onClick={runBatchInference} disabled={loading || inputRows.length === 0}>
            {loading ? 'Running Inference...' : 'Run Batch Inference'}
          </Button>
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
          {summary ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 rounded-lg border border-border bg-muted/20">
              <div><div className="text-xs text-muted-foreground">Input Rows</div><div className="font-semibold">{formatNumber(summary.input_row_count)}</div></div>
              <div><div className="text-xs text-muted-foreground">Output Rows</div><div className="font-semibold">{formatNumber(summary.output_row_count)}</div></div>
              <div><div className="text-xs text-muted-foreground">Zone Assigned</div><div className="font-semibold">{formatNumber(summary.rows_with_zone_assignment)}</div></div>
              <div><div className="text-xs text-muted-foreground">Mode</div><div className="font-semibold">{String(summary.zone_assignment_mode ?? 'NA')}</div></div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card className="glass-panel">
        <CardHeader>
          <CardTitle className="text-xl">Prediction Preview</CardTitle>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-muted/40 border-b border-border">
                <th className="text-left p-3">#</th>
                <th className="text-left p-3">Predicted ₹/sqft</th>
                <th className="text-left p-3">Predicted Market Value</th>
                <th className="text-left p-3">Zone</th>
              </tr>
            </thead>
            <tbody>
              {results.slice(0, 100).map((row, index) => (
                <tr key={index} className="border-b border-border/50">
                  <td className="p-3">{index + 1}</td>
                  <td className="p-3">{formatNumber(row.predicted_value_per_area)}</td>
                  <td className="p-3">{formatNumber(row.predicted_market_value)}</td>
                  <td className="p-3">{String(row.ai_zone_name ?? row.ai_zone ?? 'NA')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
