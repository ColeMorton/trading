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
    <div className="overflow-x-auto bg-white rounded-lg shadow-lg p-4">
      <div className="mb-4 flex justify-between items-center">
        <div>
          <input
            value={table.getState().globalFilter || ''}
            onChange={e => table.setGlobalFilter(e.target.value)}
            placeholder="Search..."
            className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <div>
          <select
            value={table.getState().pagination.pageSize}
            onChange={e => table.setPageSize(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          >
            {[10, 25, 50, 100].map(size => (
              <option key={size} value={size}>
                Show {size}
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
        <div>
          <button
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
            className="px-2 py-1 mr-1 border border-gray-300 rounded-md disabled:opacity-50"
          >
            {'<<'}
          </button>
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="px-2 py-1 mr-1 border border-gray-300 rounded-md disabled:opacity-50"
          >
            {'<'}
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="px-2 py-1 mr-1 border border-gray-300 rounded-md disabled:opacity-50"
          >
            {'>'}
          </button>
          <button
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage()}
            className="px-2 py-1 border border-gray-300 rounded-md disabled:opacity-50"
          >
            {'>>'}
          </button>
        </div>
        <div>
          <span>
            Page{' '}
            <strong>
              {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
            </strong>
          </span>
        </div>
      </div>
    </div>
  );
};

export default DataTable;