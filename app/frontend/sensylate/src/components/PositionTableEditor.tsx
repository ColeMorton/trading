import React, { useState, useEffect } from 'react';
import {
  Edit3,
  Check,
  X,
  DollarSign,
  ArrowRight,
  AlertCircle,
  Trash2,
} from 'lucide-react';
import { TradingPosition } from '../types';
import { useEnhancedPositionManagement } from '../hooks/usePositionSizing';
import { validatePositionData } from '../utils/apiErrorHandler';

interface PositionTableEditorProps {
  positions: TradingPosition[];
  onPositionUpdated?: (position: TradingPosition) => void;
  onPositionDeleted?: (symbol: string) => void;
  className?: string;
  readonly?: boolean;
}

interface EditingCell {
  symbol: string;
  field: keyof TradingPosition;
  value: string;
}

const PositionTableEditor: React.FC<PositionTableEditorProps> = ({
  positions,
  onPositionUpdated,
  onPositionDeleted,
  className = '',
  readonly = false,
}) => {
  const { updatePosition, isUpdating, error } = useEnhancedPositionManagement();

  const [editingCell, setEditingCell] = useState<EditingCell | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Clear validation error when editing changes
  useEffect(() => {
    setValidationError(null);
  }, [editingCell]);

  const startEditing = (
    symbol: string,
    field: keyof TradingPosition,
    currentValue: any
  ) => {
    if (readonly || isUpdating) return;

    setEditingCell({
      symbol,
      field,
      value: currentValue?.toString() || '',
    });
  };

  const cancelEditing = () => {
    setEditingCell(null);
    setValidationError(null);
  };

  const handleInputChange = (value: string) => {
    if (editingCell) {
      setEditingCell({
        ...editingCell,
        value,
      });
    }
  };

  const validateAndSave = async () => {
    if (!editingCell) return;

    const { symbol, field, value } = editingCell;

    // Validate based on field type
    let processedValue: any = value;
    const validationData: any = { symbol };

    switch (field) {
      case 'manualPositionSize':
        processedValue = parseFloat(value);
        if (isNaN(processedValue) || processedValue <= 0) {
          setValidationError('Position size must be a positive number');
          return;
        }
        validationData.manualPositionSize = processedValue;
        break;

      case 'manualEntryDate':
        const date = new Date(value);
        if (isNaN(date.getTime()) || date > new Date()) {
          setValidationError('Please enter a valid date (not in the future)');
          return;
        }
        processedValue = value;
        validationData.manualEntryDate = processedValue;
        break;

      case 'currentStatus':
        if (!['Active', 'Closed', 'Pending'].includes(value)) {
          setValidationError('Status must be Active, Closed, or Pending');
          return;
        }
        processedValue = value as 'Active' | 'Closed' | 'Pending';
        validationData.currentStatus = processedValue;
        break;

      case 'stopStatus':
        if (!['Risk', 'Protected'].includes(value)) {
          setValidationError('Stop status must be Risk or Protected');
          return;
        }
        processedValue = value as 'Risk' | 'Protected';
        validationData.stopStatus = processedValue;
        break;

      case 'notes':
        processedValue = value.trim() || undefined;
        break;

      default:
        setValidationError('This field cannot be edited');
        return;
    }

    // Run validation
    const validation = validatePositionData(validationData);
    if (!validation.valid) {
      setValidationError(validation.errors[0]);
      return;
    }

    // Update position
    try {
      const updateData = { [field]: processedValue };
      const updatedPosition = await updatePosition(symbol, updateData);

      if (updatedPosition) {
        setEditingCell(null);
        setValidationError(null);
        onPositionUpdated?.(updatedPosition);
      }
    } catch (err) {
      setValidationError('Failed to update position');
    }
  };

  const formatCurrency = (value: number | undefined) => {
    if (value === undefined || value === null) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusBadge = (status: string, type: 'current' | 'stop') => {
    const baseClasses =
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';

    if (type === 'current') {
      switch (status) {
        case 'Active':
          return `${baseClasses} bg-green-100 text-green-800`;
        case 'Closed':
          return `${baseClasses} bg-gray-100 text-gray-800`;
        case 'Pending':
          return `${baseClasses} bg-yellow-100 text-yellow-800`;
        default:
          return `${baseClasses} bg-gray-100 text-gray-800`;
      }
    } else {
      switch (status) {
        case 'Risk':
          return `${baseClasses} bg-red-100 text-red-800`;
        case 'Protected':
          return `${baseClasses} bg-blue-100 text-blue-800`;
        default:
          return `${baseClasses} bg-gray-100 text-gray-800`;
      }
    }
  };

  const renderEditableCell = (
    position: TradingPosition,
    field: keyof TradingPosition,
    value: any,
    formatter?: (val: any) => string
  ) => {
    const isEditing =
      editingCell?.symbol === position.symbol && editingCell?.field === field;
    const displayValue = formatter ? formatter(value) : value || '-';

    if (isEditing) {
      return (
        <div className="flex items-center space-x-2">
          {field === 'currentStatus' || field === 'stopStatus' ? (
            <select
              value={editingCell.value}
              onChange={(e) => handleInputChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') validateAndSave();
                if (e.key === 'Escape') cancelEditing();
              }}
              className="text-sm border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
              autoFocus
            >
              {field === 'currentStatus' ? (
                <>
                  <option value="Active">Active</option>
                  <option value="Closed">Closed</option>
                  <option value="Pending">Pending</option>
                </>
              ) : (
                <>
                  <option value="Risk">Risk</option>
                  <option value="Protected">Protected</option>
                </>
              )}
            </select>
          ) : (
            <input
              type={
                field === 'manualPositionSize'
                  ? 'number'
                  : field === 'manualEntryDate'
                    ? 'date'
                    : 'text'
              }
              value={editingCell.value}
              onChange={(e) => handleInputChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') validateAndSave();
                if (e.key === 'Escape') cancelEditing();
              }}
              className="text-sm border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
              autoFocus
              {...(field === 'manualPositionSize' && { min: 0, step: 0.01 })}
              {...(field === 'manualEntryDate' && {
                max: new Date().toISOString().slice(0, 10),
              })}
            />
          )}
          <button
            onClick={validateAndSave}
            disabled={isUpdating}
            className="text-green-600 hover:text-green-800 disabled:opacity-50"
            title="Save"
          >
            <Check size={16} />
          </button>
          <button
            onClick={cancelEditing}
            disabled={isUpdating}
            className="text-red-600 hover:text-red-800 disabled:opacity-50"
            title="Cancel"
          >
            <X size={16} />
          </button>
        </div>
      );
    }

    return (
      <div className="group flex items-center justify-between">
        <span
          className={
            field === 'currentStatus' || field === 'stopStatus'
              ? ''
              : 'truncate'
          }
        >
          {field === 'currentStatus' ? (
            <span className={getStatusBadge(value, 'current')}>
              {value || '-'}
            </span>
          ) : field === 'stopStatus' ? (
            <span className={getStatusBadge(value, 'stop')}>
              {value || '-'}
            </span>
          ) : (
            displayValue
          )}
        </span>
        {!readonly && (
          <button
            onClick={() => startEditing(position.symbol, field, value)}
            className="opacity-0 group-hover:opacity-100 ml-2 text-gray-400 hover:text-gray-600 transition-opacity"
            title="Edit"
          >
            <Edit3 size={14} />
          </button>
        )}
      </div>
    );
  };

  if (positions.length === 0) {
    return (
      <div
        className={`bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center ${className}`}
      >
        <div className="text-gray-500">
          <DollarSign size={48} className="mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No Active Positions
          </h3>
          <p>Add your first position to start tracking your portfolio.</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}
    >
      {/* Validation Error */}
      {validationError && (
        <div className="mx-6 mt-4 bg-red-50 border border-red-200 rounded-md p-3">
          <div className="flex">
            <AlertCircle
              className="text-red-400 mr-2 flex-shrink-0"
              size={16}
            />
            <p className="text-sm text-red-700">{validationError}</p>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Symbol
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Position Size
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Entry Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Stop Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Notes
              </th>
              {!readonly && (
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              )}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {positions.map((position) => (
              <tr key={position.symbol} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {position.symbol}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {renderEditableCell(
                      position,
                      'manualPositionSize',
                      position.manualPositionSize,
                      formatCurrency
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {renderEditableCell(
                      position,
                      'manualEntryDate',
                      position.manualEntryDate,
                      formatDate
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {renderEditableCell(
                      position,
                      'currentStatus',
                      position.currentStatus
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {renderEditableCell(
                      position,
                      'stopStatus',
                      position.stopStatus
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900 max-w-xs">
                    {renderEditableCell(position, 'notes', position.notes)}
                  </div>
                </td>
                {!readonly && (
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-2">
                      {position.stopStatus === 'Risk' &&
                        position.currentStatus === 'Active' && (
                          <button
                            title="Move to Protected Portfolio"
                            className="text-blue-600 hover:text-blue-900 flex items-center"
                          >
                            <ArrowRight size={16} />
                          </button>
                        )}
                      <button
                        onClick={() => onPositionDeleted?.(position.symbol)}
                        title="Delete Position"
                        className="text-red-600 hover:text-red-900"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Loading Overlay */}
      {isUpdating && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center">
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Updating position...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default PositionTableEditor;
