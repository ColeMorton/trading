import React, { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper,
  ColumnDef
} from '@tanstack/react-table';
import { useAppContext } from '../context/AppContext';
import { cleanData, formatValue } from '../utils/csvUtils';

/**
 * Component to display CSV data as an interactive table
 */
const DataTable: React.FC = () => {
  const { csvData, viewMode } = useAppContext();
  
  const data = useMemo(() => {
    if (!csvData) return [];
    return cleanData(csvData.data);
  }, [csvData]);
  
  const columnHelper = createColumnHelper<any>();
  
  const columns = useMemo(() => {
    if (!csvData) return [] as ColumnDef<any>[];
    
    return csvData.columns.map(column => {
      const cleanKey = column.replace(/[\[\]%]/g, '_');
      
      return columnHelper.accessor(cleanKey, {
        header: column,
        cell: info => formatValue(info.getValue(), column)
      });
    });
  }, [csvData]);
  
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize: 25,
        pageIndex: 0
      }
    }
  });
  
  if (viewMode !== 'table' || !csvData) {
    return null;
  }
  
  return (
    <div className="mb-6 rounded-lg border overflow-hidden" style={{ 
      backgroundColor: 'var(--bs-card-bg)', 
      borderColor: 'var(--bs-card-border-color)' 
    }}>
      <div className="border-b px-4 py-3" style={{ 
        backgroundColor: 'var(--bs-card-cap-bg)', 
        borderColor: 'var(--bs-card-border-color)' 
      }}>
        <h5 className="mb-0 font-bold" style={{ color: 'var(--bs-body-color)' }}>Results</h5>
      </div>
      <div className="p-4">
        <div className="mb-4 flex justify-between items-center">
          <div>
            <input
              value={table.getState().globalFilter || ''}
              onChange={e => table.setGlobalFilter(e.target.value)}
              placeholder="Filter results..."
              className="form-control"
              style={{
                backgroundColor: 'var(--bs-input-bg)',
                color: 'var(--bs-input-color)',
                border: '1px solid var(--bs-input-border-color)',
                borderRadius: '0.375rem',
                padding: '0.375rem 0.75rem'
              }}
            />
          </div>
          <div className="flex items-center gap-4">
            <span style={{ color: 'var(--bs-secondary-color)', fontSize: '0.875rem' }}>
              Show
            </span>
            <select
              value={table.getState().pagination.pageSize}
              onChange={e => table.setPageSize(Number(e.target.value))}
              className="form-control"
              style={{
                backgroundColor: 'var(--bs-input-bg)',
                color: 'var(--bs-input-color)',
                border: '1px solid var(--bs-input-border-color)',
                borderRadius: '0.375rem',
                padding: '0.375rem 0.75rem'
              }}
            >
              {[10, 25, 50, 100].map(size => (
                <option key={size} value={size}>
                  {size} entries
                </option>
              ))}
            </select>
          </div>
        </div>
      
      <div className="overflow-x-auto">
        <table className="react-table">
          <thead>
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className="p-2 text-left cursor-pointer"
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    <span>
                      {{
                        asc: ' 🔼',
                        desc: ' 🔽'
                      }[header.column.getIsSorted() as string] ?? ''}
                    </span>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map(row => (
              <tr key={row.id}>
                {row.getVisibleCells().map(cell => (
                  <td key={cell.id} className="p-2 border-b border-gray-200">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
        <div className="mt-4 flex items-center justify-between">
          <div className="flex gap-1">
            <button
              onClick={() => table.setPageIndex(0)}
              disabled={!table.getCanPreviousPage()}
              className="px-3 py-1.5 rounded border disabled:opacity-50"
              style={{
                backgroundColor: 'var(--bs-input-bg)',
                color: 'var(--bs-body-color)',
                borderColor: 'var(--bs-border-color)'
              }}
            >
              {'<<'}
            </button>
            <button
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="px-3 py-1.5 rounded border disabled:opacity-50"
              style={{
                backgroundColor: 'var(--bs-input-bg)',
                color: 'var(--bs-body-color)',
                borderColor: 'var(--bs-border-color)'
              }}
            >
              {'<'}
            </button>
            <button
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="px-3 py-1.5 rounded border disabled:opacity-50"
              style={{
                backgroundColor: 'var(--bs-input-bg)',
                color: 'var(--bs-body-color)',
                borderColor: 'var(--bs-border-color)'
              }}
            >
              {'>'}
            </button>
            <button
              onClick={() => table.setPageIndex(table.getPageCount() - 1)}
              disabled={!table.getCanNextPage()}
              className="px-3 py-1.5 rounded border disabled:opacity-50"
              style={{
                backgroundColor: 'var(--bs-input-bg)',
                color: 'var(--bs-body-color)',
                borderColor: 'var(--bs-border-color)'
              }}
            >
              {'>>'}
            </button>
          </div>
          <div>
            <span style={{ color: 'var(--bs-secondary-color)', fontSize: '0.875rem' }}>
              Page{' '}
              <strong style={{ color: 'var(--bs-body-color)' }}>
                {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
              </strong>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataTable;