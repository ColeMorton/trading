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
import { TradingPosition } from '../../types';
import Icon from '../Icon';
import { icons } from '../../utils/icons';

interface ActivePositionsTableProps {
  positions: TradingPosition[];
  isLoading?: boolean;
}

const ActivePositionsTable: React.FC<ActivePositionsTableProps> = ({
  positions,
  isLoading = false,
}) => {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString();
  };

  const getAccountTypeBadge = (accountType: string) => {
    const badges: Record<string, string> = {
      IBKR: 'bg-primary',
      Bybit: 'bg-warning',
      Cash: 'bg-success',
    };
    return badges[accountType] || 'bg-secondary';
  };

  const columns = useMemo<ColumnDef<TradingPosition>[]>(
    () => [
      {
        accessorKey: 'symbol',
        header: 'Symbol',
        cell: ({ getValue }) => (
          <div className="fw-bold text-primary">{getValue() as string}</div>
        ),
      },
      {
        accessorKey: 'positionValue',
        header: 'Position Value',
        cell: ({ getValue }) => (
          <div className="text-end">{formatCurrency(getValue() as number)}</div>
        ),
      },
      {
        accessorKey: 'currentPosition',
        header: 'Current Position',
        cell: ({ getValue }) => {
          const value = getValue() as number | undefined;
          if (value == null) return <span className="text-muted">-</span>;
          return <div className="text-end">{value.toFixed(4)}</div>;
        },
      },
      {
        accessorKey: 'maxDrawdown',
        header: 'Stop Loss %',
        cell: ({ getValue }) => {
          const value = getValue() as number | undefined;
          if (!value) return <span className="text-muted">-</span>;
          return (
            <div className="text-end">
              <span className="badge bg-danger">{formatPercentage(value)}</span>
            </div>
          );
        },
      },
      {
        accessorKey: 'riskAmount',
        header: 'Risk Amount',
        cell: ({ getValue }) => {
          const value = getValue() as number | undefined;
          if (!value) return <span className="text-muted">-</span>;
          return (
            <div className="text-end text-danger">{formatCurrency(value)}</div>
          );
        },
      },
      {
        accessorKey: 'accountType',
        header: 'Account',
        cell: ({ getValue }) => {
          const accountType = getValue() as string;
          return (
            <span className={`badge ${getAccountTypeBadge(accountType)}`}>
              {accountType}
            </span>
          );
        },
      },
      {
        accessorKey: 'entryDate',
        header: 'Entry Date',
        cell: ({ getValue }) => (
          <div className="text-muted small">
            {formatDate(getValue() as string)}
          </div>
        ),
      },
      {
        accessorKey: 'stopLossPrice',
        header: 'Stop Loss Price',
        cell: ({ getValue }) => {
          const value = getValue() as number | undefined;
          if (!value) return <span className="text-muted">-</span>;
          return <div className="text-end">{formatCurrency(value)}</div>;
        },
      },
    ],
    []
  );

  const table = useReactTable({
    data: positions,
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
  const totalValue = positions.reduce((sum, pos) => sum + pos.positionValue, 0);
  const totalRisk = positions.reduce(
    (sum, pos) => sum + (pos.riskAmount || 0),
    0
  );

  return (
    <div className="card h-100">
      <div className="card-header">
        <div className="d-flex justify-content-between align-items-center">
          <div className="d-flex align-items-center">
            <Icon icon={icons.star} className="me-2" />
            <h6 className="mb-0">Active Positions</h6>
            <span className="badge bg-secondary ms-2">{positions.length}</span>
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
                placeholder="Search positions..."
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
            Loading positions...
          </div>
        ) : positions.length === 0 ? (
          <div className="text-center p-4 text-muted">
            <Icon icon={icons.info} className="mb-2" size="2x" />
            <div>No active positions found</div>
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
                <div className="col-md-4">
                  <div className="text-muted small">Total Positions</div>
                  <div className="fw-bold">{positions.length}</div>
                </div>
                <div className="col-md-4">
                  <div className="text-muted small">Total Value</div>
                  <div className="fw-bold text-primary">
                    {formatCurrency(totalValue)}
                  </div>
                </div>
                <div className="col-md-4">
                  <div className="text-muted small">Total Risk</div>
                  <div className="fw-bold text-danger">
                    {formatCurrency(totalRisk)}
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

export default ActivePositionsTable;
