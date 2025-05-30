import React, { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper,
  ColumnDef,
  SortingState
} from '@tanstack/react-table';
import { AnalysisResult } from '../types';
import Icon from './Icon';
import { icons } from '../utils/icons';

interface ResultsTableProps {
  results: AnalysisResult[];
  isLoading?: boolean;
  error?: string | null;
}

/**
 * Component to display parameter testing analysis results in an interactive table
 */
const ResultsTable: React.FC<ResultsTableProps> = React.memo(({ results, isLoading, error }) => {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState('');
  
  const columnHelper = createColumnHelper<AnalysisResult>();
  
  // Define columns with proper formatting for each metric
  const columns = useMemo(() => {
    return [
      columnHelper.accessor('ticker', {
        header: 'Ticker',
        cell: info => info.getValue()
      }),
      columnHelper.accessor('strategy_type', {
        header: 'Strategy',
        cell: info => info.getValue()
      }),
      columnHelper.accessor('short_window', {
        header: 'Short Win',
        cell: info => info.getValue()
      }),
      columnHelper.accessor('long_window', {
        header: 'Long Win',
        cell: info => info.getValue()
      }),
      columnHelper.accessor('signal_window', {
        header: 'Signal Win',
        cell: info => info.getValue()
      }),
      columnHelper.accessor('direction', {
        header: 'Direction',
        cell: info => info.getValue()
      }),
      columnHelper.accessor('timeframe', {
        header: 'Timeframe',
        cell: info => info.getValue()
      }),
      columnHelper.accessor('total_trades', {
        header: 'Trades',
        cell: info => info.getValue().toLocaleString()
      }),
      columnHelper.accessor('win_rate', {
        header: 'Win Rate %',
        cell: info => (info.getValue() * 100).toFixed(2) + '%'
      }),
      columnHelper.accessor('profit_factor', {
        header: 'Profit Factor',
        cell: info => info.getValue().toFixed(2)
      }),
      columnHelper.accessor('expectancy_per_trade', {
        header: 'Expectancy %',
        cell: info => (info.getValue() * 100).toFixed(2) + '%'
      }),
      columnHelper.accessor('sortino_ratio', {
        header: 'Sortino Ratio',
        cell: info => info.getValue().toFixed(2)
      }),
      columnHelper.accessor('max_drawdown', {
        header: 'Max DD %',
        cell: info => (info.getValue() * 100).toFixed(2) + '%'
      }),
      columnHelper.accessor('total_return', {
        header: 'Total Return %',
        cell: info => (info.getValue() * 100).toFixed(2) + '%'
      })
    ] as ColumnDef<AnalysisResult>[];
  }, []);
  
  const table = useReactTable({
    data: results,
    columns,
    state: {
      sorting,
      globalFilter
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize: 25,
        pageIndex: 0
      },
      sorting: [
        {
          id: 'sortino_ratio',
          desc: true
        }
      ]
    }
  });
  
  // Export to CSV functionality
  const exportToCSV = () => {
    const headers = columns.map(col => col.header as string).join(',');
    const rows = results.map(row => {
      return [
        row.ticker,
        row.strategy_type,
        row.short_window,
        row.long_window,
        row.signal_window,
        row.direction,
        row.timeframe,
        row.total_trades,
        (row.win_rate * 100).toFixed(2),
        row.profit_factor.toFixed(2),
        (row.expectancy_per_trade * 100).toFixed(2),
        row.sortino_ratio.toFixed(2),
        (row.max_drawdown * 100).toFixed(2),
        (row.total_return * 100).toFixed(2)
      ].join(',');
    });
    
    const csv = [headers, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `parameter_testing_results_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  if (isLoading) {
    return (
      <div className="card mb-4">
        <div className="card-body text-center py-5">
          <div className="spinner-border text-primary mb-3" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="text-muted">Loading results...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="card mb-4">
        <div className="card-body">
          <div className="alert alert-danger mb-0" role="alert">
            <Icon icon={icons.warning} className="me-2" />
            <strong>Error:</strong> {error}
          </div>
        </div>
      </div>
    );
  }
  
  if (results.length === 0) {
    return (
      <div className="card mb-4">
        <div className="card-body text-center py-5">
          <Icon icon={icons.brand} className="text-muted mb-3" size="3x" />
          <p className="text-muted">No results to display. Run an analysis to see results.</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="card mb-4">
      <div className="card-header d-flex align-items-center justify-content-between">
        <div className="d-flex align-items-center">
          <Icon icon={icons.table} className="me-2" />
          <h5 className="card-title mb-0">Analysis Results</h5>
        </div>
        <button
          onClick={exportToCSV}
          className="btn btn-sm btn-outline-primary"
          title="Export to CSV"
        >
          <Icon icon={icons.download} className="me-1" />
          Export CSV
        </button>
      </div>
      <div className="card-body">
        <div className="row mb-3 align-items-center">
          <div className="col-md-6">
            <div className="input-group">
              <span className="input-group-text">
                <Icon icon={icons.search} />
              </span>
              <input
                value={globalFilter || ''}
                onChange={e => setGlobalFilter(e.target.value)}
                placeholder="Filter results..."
                className="form-control"
              />
            </div>
          </div>
          <div className="col-md-6 d-flex align-items-center justify-content-end gap-2">
            <span className="text-muted small">Show</span>
            <select
              value={table.getState().pagination.pageSize}
              onChange={e => table.setPageSize(Number(e.target.value))}
              className="form-select form-select-sm"
              style={{ width: 'auto' }}
            >
              {[10, 25, 50, 100].map(size => (
                <option key={size} value={size}>
                  {size} entries
                </option>
              ))}
            </select>
            <span className="text-muted small ms-2">
              ({table.getFilteredRowModel().rows.length} total results)
            </span>
          </div>
        </div>
      
        <div className="table-responsive">
          <table className="react-table">
            <thead>
              {table.getHeaderGroups().map(headerGroup => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map(header => (
                    <th
                      key={header.id}
                      onClick={header.column.getToggleSortingHandler()}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      title="Click to sort"
                    >
                      <div className="d-flex align-items-center">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        <span className="ms-1">
                          {header.column.getIsSorted() === 'asc' && <Icon icon={icons.sortUp} />}
                          {header.column.getIsSorted() === 'desc' && <Icon icon={icons.sortDown} />}
                          {!header.column.getIsSorted() && <Icon icon={icons.sort} className="text-muted opacity-50" />}
                        </span>
                      </div>
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map(row => (
                <tr key={row.id}>
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
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
                {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
              </strong>
              {' '}
              ({table.getRowModel().rows.length} of {table.getFilteredRowModel().rows.length} entries)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
});

export default ResultsTable;