import * as React from "react";

import { EmptyState } from "@/components/ui-kit/empty-state";
import { cn } from "@/lib/utils";

export type DataTableColumn<T> = {
  key: string;
  header: React.ReactNode;
  cell: (row: T) => React.ReactNode;
  className?: string;
};

export interface DataTableProps<T> {
  rows: T[];
  columns: Array<DataTableColumn<T>>;
  getRowKey: (row: T) => string | number;
  emptyTitle?: string;
  emptyDescription?: string;
  className?: string;
}

export function DataTable<T>({ rows, columns, getRowKey, emptyTitle = "No records", emptyDescription = "Records will appear here after activity starts.", className }: DataTableProps<T>) {
  if (!rows.length) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <div className={cn("overflow-x-auto rounded-xl border border-shb-border bg-white/[0.035]", className)}>
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead className="sticky top-0 bg-shb-bg-soft text-xs uppercase tracking-[0.14em] text-shb-muted backdrop-blur">
          <tr>
            {columns.map((column) => (
              <th key={column.key} className={cn("px-4 py-3 font-bold", column.className)}>
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={getRowKey(row)} className="border-t border-white/10 transition hover:bg-white/[0.045]">
              {columns.map((column) => (
                <td key={column.key} className={cn("px-4 py-3 align-middle text-slate-200", column.className)}>
                  {column.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
