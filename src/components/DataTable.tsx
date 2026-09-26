import React from 'react';

export interface Column<T> {
  header: string;
  accessor?: keyof T;
  render?: (item: T) => React.ReactNode;
  align?: 'left' | 'center' | 'right';
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string;
  className?: string;
  emptyMessage?: string;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  className = '',
  emptyMessage = 'No records found in this view.',
}: DataTableProps<T>) {
  return (
    <div
      className={`w-full overflow-x-auto bg-surface-container-lowest border border-hairline rounded ${className}`}
    >
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-surface-container border-b-2 border-primary/20 font-label-caps text-label-caps uppercase text-secondary">
            {columns.map((col, idx) => (
              <th
                key={idx}
                className={`py-3 px-4 font-bold ${
                  col.align === 'right'
                    ? 'text-right'
                    : col.align === 'center'
                      ? 'text-center'
                      : 'text-left'
                } ${col.className || ''}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-hairline">
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="py-8 px-4 text-center text-secondary font-body-md"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((item) => (
              <tr
                key={keyExtractor(item)}
                className="hover:bg-surface-container-low transition-colors"
              >
                {columns.map((col, idx) => (
                  <td
                    key={idx}
                    className={`py-3 px-4 font-body-sm ${
                      col.align === 'right'
                        ? 'text-right font-code-tabular'
                        : col.align === 'center'
                          ? 'text-center'
                          : 'text-left'
                    } ${col.className || ''}`}
                  >
                    {col.render
                      ? col.render(item)
                      : col.accessor
                        ? (item[col.accessor] as React.ReactNode)
                        : null}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
