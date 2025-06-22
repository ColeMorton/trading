import React, { useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  ColumnDef,
  SortingState,
} from '@tanstack/react-table';
import { InvestmentHolding } from '../../types';
import Icon from '../Icon';
import { icons } from '../../utils/icons';

interface StrategicHoldingsTableProps {
  holdings: InvestmentHolding[];
  isLoading?: boolean;
}

const StrategicHoldingsTable: React.FC<StrategicHoldingsTableProps> = ({
  holdings,
  isLoading = false,
}) => {
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'currentValue', desc: true },
  ]);
  const [globalFilter, setGlobalFilter] = useState('');

  const formatCurrency = (value: number | undefined) => {
    if (value === undefined || value === null || isNaN(value)) {
      return '$0';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value: number | undefined) => {
    if (value === undefined || value === null || isNaN(value)) {
      return '0.00%';
    }
    return `${value.toFixed(2)}%`;
  };

  const formatShares = (value: number | undefined) => {
    if (value === undefined || value === null || isNaN(value)) {
      return '0.0000';
    }
    return value.toFixed(4);
  };

  const getPnLColor = (pnl: number | undefined) => {
    if (pnl === undefined || pnl === null || isNaN(pnl)) return 'text-muted';
    if (pnl > 0) return 'text-success';
    if (pnl < 0) return 'text-danger';
    return 'text-muted';
  };

  const getPnLIcon = (pnl: number | undefined) => {
    if (pnl === undefined || pnl === null || isNaN(pnl)) return icons.remove;
    if (pnl > 0) return icons.chevronUp;
    if (pnl < 0) return icons.chevronDown;
    return icons.remove;
  };

  const columns = useMemo<ColumnDef<InvestmentHolding>[]>(
    () => [
      {
        accessorKey: 'symbol',
        header: 'Symbol',
        cell: ({ getValue }) => (
          <div className="fw-bold text-primary">{getValue() as string}</div>
        ),
      },
      {
        accessorKey: 'shares',
        header: 'Shares',
        cell: ({ getValue }) => (
          <div className="text-end">{formatShares(getValue() as number)}</div>
        ),
      },
      {
        accessorKey: 'averagePrice',
        header: 'Avg. Price',
        cell: ({ getValue }) => (
          <div className="text-end">{formatCurrency(getValue() as number)}</div>
        ),
      },
      {
        accessorKey: 'currentValue',
        header: 'Current Value',
        cell: ({ getValue }) => (
          <div className="text-end fw-bold">
            {formatCurrency(getValue() as number)}
          </div>
        ),
      },
      {
        accessorKey: 'unrealizedPnl',
        header: 'Unrealized P&L',
        cell: ({ getValue }) => {
          const pnl = getValue() as number;
          return (
            <div
              className={`text-end d-flex align-items-center justify-content-end ${getPnLColor(
                pnl
              )}`}
            >
              <Icon icon={getPnLIcon(pnl)} className="me-1" />
              {formatCurrency(Math.abs(pnl))}
            </div>
          );
        },
      },
      {
        accessorKey: 'allocationPercentage',
        header: 'Allocation %',
        cell: ({ getValue }) => {
          const percentage = getValue() as number;
          return (
            <div className="text-end">
              <span className="badge bg-info">
                {formatPercentage(percentage)}
              </span>
            </div>
          );
        },
      },
    ],
    []
  );

  const table = useReactTable({
    data: holdings,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    state: {
      sorting,
      globalFilter,
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
  });

  // Calculate totals
  const totalValue = holdings.reduce(
    (sum, holding) => sum + holding.currentValue,
    0
  );
  const totalPnL = holdings.reduce(
    (sum, holding) => sum + holding.unrealizedPnl,
    0
  );
  const totalAllocation = holdings.reduce(
    (sum, holding) => sum + holding.allocationPercentage,
    0
  );

  return (
    <div className="card">
      <div className="card-header">
        <div className="d-flex justify-content-between align-items-center">
          <div className="d-flex align-items-center">
            <Icon icon={icons.portfolio} className="me-2" />
            <h6 className="mb-0">Strategic Holdings (Investment Portfolio)</h6>
            <span className="badge bg-secondary ms-2">{holdings.length}</span>
          </div>
          <div className="d-flex align-items-center gap-2">
            <div
              className="input-group input-group-sm"
              style={{ width: '200px' }}
            >
              <span className="input-group-text">
                <Icon icon={icons.search} />
              </span>
              <input
                type="text"
                className="form-control"
                placeholder="Search holdings..."
                value={globalFilter}
                onChange={(e) => setGlobalFilter(e.target.value)}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="card-body p-0">
        {isLoading ? (
          <div className="d-flex justify-content-center align-items-center p-4">
            <Icon icon={icons.loading} className="fa-spin me-2" />
            Loading holdings...
          </div>
        ) : holdings.length === 0 ? (
          <div className="text-center p-4 text-muted">
            <Icon icon={icons.info} className="mb-2" size="2x" />
            <div>No strategic holdings found</div>
            <small>Investment portfolio holdings will appear here</small>
          </div>
        ) : (
          <>
            <div className="table-responsive">
              <table className="table table-hover table-sm mb-0">
                <thead className="table-light">
                  {table.getHeaderGroups().map((headerGroup) => (
                    <tr key={headerGroup.id}>
                      {headerGroup.headers.map((header) => (
                        <th
                          key={header.id}
                          style={{
                            cursor: header.column.getCanSort()
                              ? 'pointer'
                              : 'default',
                          }}
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          <div className="d-flex align-items-center justify-content-between">
                            {flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                            {header.column.getCanSort() && (
                              <div className="ms-1">
                                {{
                                  asc: <Icon icon={icons.sortUp} />,
                                  desc: <Icon icon={icons.sortDown} />,
                                }[header.column.getIsSorted() as string] ?? (
                                  <Icon
                                    icon={icons.sort}
                                    className="text-muted"
                                  />
                                )}
                              </div>
                            )}
                          </div>
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

            {/* Summary Footer */}
            <div className="border-top p-3 bg-light">
              <div className="row text-center">
                <div className="col-md-3">
                  <div className="text-muted small">Total Holdings</div>
                  <div className="fw-bold">{holdings.length}</div>
                </div>
                <div className="col-md-3">
                  <div className="text-muted small">Total Value</div>
                  <div className="fw-bold text-primary">
                    {formatCurrency(totalValue)}
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-muted small">Total P&L</div>
                  <div className={`fw-bold ${getPnLColor(totalPnL)}`}>
                    <Icon icon={getPnLIcon(totalPnL)} className="me-1" />
                    {formatCurrency(Math.abs(totalPnL))}
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-muted small">Total Allocation</div>
                  <div className="fw-bold">
                    {formatPercentage(totalAllocation)}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default StrategicHoldingsTable;
