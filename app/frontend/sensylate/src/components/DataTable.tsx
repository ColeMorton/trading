import React, { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper,
  ColumnDef,
} from '@tanstack/react-table';
import { useAppContext } from '../context/AppContext';
import { cleanData, formatValue } from '../utils/csvUtils';
import Icon from './Icon';
import { icons } from '../utils/icons';

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

    return csvData.columns.map((column) => {
      const cleanKey = column.replace(/[\[\]%]/g, '_');

      return columnHelper.accessor(cleanKey, {
        header: column,
        cell: (info) => formatValue(info.getValue(), column),
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
        pageIndex: 0,
      },
    },
  });

  if (viewMode !== 'table' || !csvData) {
    return null;
  }

  return (
    <div className="card mb-4">
      <div className="card-header d-flex align-items-center">
        <Icon icon={icons.table} className="me-2" />
        <h5 className="card-title mb-0">Results</h5>
      </div>
      <div className="card-body">
        <div className="row mb-3 align-items-center">
          <div className="col-md-6">
            <div className="input-group">
              <span className="input-group-text">
                <Icon icon={icons.search} />
              </span>
              <input
                value={table.getState().globalFilter || ''}
                onChange={(e) => table.setGlobalFilter(e.target.value)}
                placeholder="Filter results..."
                className="form-control"
              />
            </div>
          </div>
          <div className="col-md-6 d-flex align-items-center justify-content-end gap-2">
            <span className="text-muted small">Show</span>
            <select
              value={table.getState().pagination.pageSize}
              onChange={(e) => table.setPageSize(Number(e.target.value))}
              className="form-select form-select-sm"
              style={{ width: 'auto' }}
            >
              {[10, 25, 50, 100].map((size) => (
                <option key={size} value={size}>
                  {size} entries
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="table-responsive">
          <table className="react-table">
            <thead>
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      onClick={header.column.getToggleSortingHandler()}
                      style={{ cursor: 'pointer' }}
                    >
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                      <span className="ms-1">
                        {header.column.getIsSorted() === 'asc' && (
                          <Icon icon={icons.sortUp} />
                        )}
                        {header.column.getIsSorted() === 'desc' && (
                          <Icon icon={icons.sortDown} />
                        )}
                        {!header.column.getIsSorted() && (
                          <Icon icon={icons.sort} className="text-muted" />
                        )}
                      </span>
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row) => (
                <tr key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="row mt-3 align-items-center">
          <div className="col-auto">
            <div className="btn-group" role="group">
              <button
                onClick={() => table.setPageIndex(0)}
                disabled={!table.getCanPreviousPage()}
                className="btn btn-outline-secondary btn-sm"
                title="First page"
              >
                <Icon icon={icons.chevronLeft} />
                <Icon icon={icons.chevronLeft} />
              </button>
              <button
                onClick={() => table.previousPage()}
                disabled={!table.getCanPreviousPage()}
                className="btn btn-outline-secondary btn-sm"
                title="Previous page"
              >
                <Icon icon={icons.chevronLeft} />
              </button>
              <button
                onClick={() => table.nextPage()}
                disabled={!table.getCanNextPage()}
                className="btn btn-outline-secondary btn-sm"
                title="Next page"
              >
                <Icon icon={icons.chevronRight} />
              </button>
              <button
                onClick={() => table.setPageIndex(table.getPageCount() - 1)}
                disabled={!table.getCanNextPage()}
                className="btn btn-outline-secondary btn-sm"
                title="Last page"
              >
                <Icon icon={icons.chevronRight} />
                <Icon icon={icons.chevronRight} />
              </button>
            </div>
          </div>
          <div className="col-auto ms-auto">
            <span className="text-muted small">
              Page{' '}
              <strong>
                {table.getState().pagination.pageIndex + 1} of{' '}
                {table.getPageCount()}
              </strong>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataTable;
