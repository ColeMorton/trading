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
  SortingState,
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
const ResultsTable: React.FC<ResultsTableProps> = React.memo(
  ({ results, isLoading, error }) => {
    const [sorting, setSorting] = useState<SortingState>([]);
    const [globalFilter, setGlobalFilter] = useState('');
    const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

    // Debug: Log received results
    React.useEffect(() => {
      if (results && results.length > 0) {
        console.log('Frontend received results:', results);
        console.log('First result metric_type:', results[0].metric_type);
        console.log('First result keys:', Object.keys(results[0]));
        console.log(
          'Raw first result object:',
          JSON.stringify(results[0], null, 2)
        );

        // Check for any field with 'metric' in the name
        const metricFields = Object.keys(results[0]).filter((key) =>
          key.toLowerCase().includes('metric')
        );
        console.log('Fields containing "metric":', metricFields);
      }
    }, [results]);

    const columnHelper = createColumnHelper<AnalysisResult>();

    const toggleRowExpansion = (rowId: string) => {
      setExpandedRows((prev) => {
        const newSet = new Set(prev);
        if (newSet.has(rowId)) {
          newSet.delete(rowId);
        } else {
          newSet.add(rowId);
        }
        return newSet;
      });
    };

    const renderMetricTypes = (metricType: string) => {
      if (!metricType || metricType.trim() === '') {
        return (
          <dl className="row mb-0">
            <dt className="col-sm-3">Metric Type:</dt>
            <dd className="col-sm-9">
              <span className="text-muted">No metric type data available</span>
            </dd>
          </dl>
        );
      }

      const metrics = metricType
        .split(',')
        .map((m) => m.trim())
        .filter((m) => m);
      if (metrics.length === 0) {
        return (
          <dl className="row mb-0">
            <dt className="col-sm-3">Metric Type:</dt>
            <dd className="col-sm-9">
              <span className="text-muted">No metric classifications</span>
            </dd>
          </dl>
        );
      }

      return (
        <dl className="row mb-0">
          <dt className="col-sm-3">Metric Type:</dt>
          <dd className="col-sm-9">
            <div className="d-flex flex-wrap gap-1">
              {metrics.map((metric, index) => (
                <span key={index} className="badge bg-primary text-white">
                  {metric}
                </span>
              ))}
            </div>
          </dd>
        </dl>
      );
    };

    // Define columns with proper formatting for each metric
    const columns = useMemo(() => {
      return [
        columnHelper.display({
          id: 'expand',
          header: '',
          cell: ({ row }) => (
            <button
              onClick={() => toggleRowExpansion(row.id)}
              className="btn btn-sm btn-outline-secondary border-0"
              title={
                expandedRows.has(row.id) ? 'Collapse details' : 'Expand details'
              }
            >
              <Icon
                icon={
                  expandedRows.has(row.id)
                    ? icons.chevronDown
                    : icons.chevronRight
                }
                size="sm"
              />
            </button>
          ),
          size: 40,
        }),
        columnHelper.accessor('ticker', {
          header: 'Ticker',
          cell: (info) => info.getValue(),
        }),
        columnHelper.accessor('strategy_type', {
          header: 'Strategy',
          cell: (info) => info.getValue(),
        }),
        columnHelper.accessor('short_window', {
          header: 'Short Window',
          cell: (info) => info.getValue(),
        }),
        columnHelper.accessor('long_window', {
          header: 'Long Window',
          cell: (info) => info.getValue(),
        }),
        columnHelper.accessor('signal_window', {
          header: 'Signal Window',
          cell: (info) => {
            const value = info.getValue();
            const strategyType = info.row.original.strategy_type;
            // Only show signal window for MACD strategies
            if (strategyType === 'MACD') {
              return value || 'N/A';
            }
            return '-';
          },
        }),
        columnHelper.accessor('total_trades', {
          header: 'Trades',
          cell: (info) => info.getValue().toLocaleString(),
        }),
        columnHelper.accessor('score', {
          header: 'Score',
          cell: (info) => info.getValue()?.toFixed(2) || 'N/A',
        }),
        columnHelper.accessor('win_rate', {
          header: 'Win Rate %',
          cell: (info) => (info.getValue() * 100).toFixed(2) + '%',
        }),
        columnHelper.accessor('profit_factor', {
          header: 'Profit Factor',
          cell: (info) => info.getValue().toFixed(2),
        }),
        columnHelper.accessor('expectancy_per_trade', {
          header: 'Expectancy (per trade)',
          cell: (info) => info.getValue().toFixed(2),
        }),
        columnHelper.accessor('sortino_ratio', {
          header: 'Sortino Ratio',
          cell: (info) => info.getValue().toFixed(2),
        }),
        columnHelper.accessor('avg_trade_duration', {
          header: 'Avg Trade Duration',
          cell: (info) => info.getValue() || 'N/A',
        }),
        columnHelper.accessor('beats_bnh', {
          header: 'Beats BNH [%]',
          cell: (info) => {
            const value = info.getValue();
            return value !== undefined && value !== null
              ? (value * 100).toFixed(2) + '%'
              : 'N/A';
          },
        }),
      ] as ColumnDef<AnalysisResult>[];
    }, [columnHelper, expandedRows]);

    const table = useReactTable({
      data: results,
      columns,
      state: {
        sorting,
        globalFilter,
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
          pageIndex: 0,
        },
        sorting: [
          {
            id: 'score',
            desc: true,
          },
        ],
      },
    });

    // Export to CSV functionality (local download)
    const exportToCSV = () => {
      const headers = columns
        .filter((col) => col.id !== 'expand')
        .map((col) => col.header as string)
        .join(',');
      const rows = results.map((row) => {
        return [
          row.ticker,
          row.strategy_type,
          row.short_window,
          row.long_window,
          row.strategy_type === 'MACD' ? row.signal_window || 'N/A' : '-',
          row.total_trades,
          row.score?.toFixed(2) || 'N/A',
          (row.win_rate * 100).toFixed(2),
          row.profit_factor.toFixed(2),
          row.expectancy_per_trade.toFixed(2),
          row.sortino_ratio.toFixed(2),
          row.avg_trade_duration || 'N/A',
          row.beats_bnh !== undefined && row.beats_bnh !== null
            ? (row.beats_bnh * 100).toFixed(2)
            : 'N/A',
        ].join(',');
      });

      const csv = [headers, ...rows].join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `parameter_testing_results_${
        new Date().toISOString().split('T')[0]
      }.csv`;
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
            <p className="text-muted">
              No results to display. Run an analysis to see results.
            </p>
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
          <div className="d-flex gap-2">
            <button
              onClick={exportToCSV}
              className="btn btn-sm btn-outline-primary"
              title="Export to CSV (download)"
            >
              <Icon icon={icons.download} className="me-1" />
              Download CSV
            </button>
          </div>
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
                  onChange={(e) => setGlobalFilter(e.target.value)}
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
              <span className="text-muted small ms-2">
                ({table.getFilteredRowModel().rows.length} total results)
              </span>
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
                        style={{ cursor: 'pointer', userSelect: 'none' }}
                        title="Click to sort"
                      >
                        <div className="d-flex align-items-center">
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
                              <Icon
                                icon={icons.sort}
                                className="text-muted opacity-50"
                              />
                            )}
                          </span>
                        </div>
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => (
                  <React.Fragment key={row.id}>
                    <tr>
                      {row.getVisibleCells().map((cell) => (
                        <td key={cell.id}>
                          {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext()
                          )}
                        </td>
                      ))}
                    </tr>
                    {expandedRows.has(row.id) && (
                      <tr className="expanded-row">
                        <td colSpan={row.getVisibleCells().length}>
                          <div className="expanded-row-content">
                            {renderMetricTypes(row.original.metric_type || '')}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
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
                </strong>{' '}
                ({table.getRowModel().rows.length} of{' '}
                {table.getFilteredRowModel().rows.length} entries)
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }
);

export default ResultsTable;
