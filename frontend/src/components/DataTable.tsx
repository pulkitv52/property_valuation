import React from 'react';
import { formatLabel, formatValueByKey } from '../utils/format';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Card } from './ui/card';

type DataTableProps = {
  columns: string[];
  rows: Array<Record<string, unknown>>;
};

export default function DataTable({ columns, rows }: DataTableProps) {
  return (
    <Card className="overflow-hidden glass">
      <Table>
        <TableHeader className="bg-muted/50">
          <TableRow>
            {columns.map((column) => (
              <TableHead key={column} className="font-semibold text-xs uppercase tracking-wider">
                {formatLabel(column)}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, index) => (
            <TableRow key={index} className="hover:bg-muted/30 transition-colors">
              {columns.map((column) => (
                <TableCell key={column} className="py-3">
                  {formatValueByKey(column, row[column])}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  );
}
