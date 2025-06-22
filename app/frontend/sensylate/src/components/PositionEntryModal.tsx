import React, { useState, useEffect } from 'react';
import {
  X,
  DollarSign,
  Calendar,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import { TradingPosition, PortfolioType } from '../types';
import { useEnhancedPositionManagement } from '../hooks/usePositionSizing';
import { validatePositionData, APIError } from '../utils/apiErrorHandler';

interface PositionEntryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPositionAdded: (position: TradingPosition) => void;
  initialData?: Partial<TradingPosition>;
  mode: 'add' | 'edit';
  portfolioType?: PortfolioType;
}

interface FormData {
  symbol: string;
  manualPositionSize: string;
  manualEntryDate: string;
  currentStatus: 'Active' | 'Closed' | 'Pending';
  stopStatus: 'Risk' | 'Protected';
  portfolioType: PortfolioType;
  notes: string;
}

const PositionEntryModal: React.FC<PositionEntryModalProps> = ({
  isOpen,
  onClose,
  onPositionAdded,
  initialData,
  mode,
  portfolioType = 'Risk_On',
}) => {
  const { addPosition, updatePosition, isUpdating, error } =
    useEnhancedPositionManagement();

  const [formData, setFormData] = useState<FormData>({
    symbol: '',
    manualPositionSize: '',
    manualEntryDate: new Date().toISOString().slice(0, 10),
    currentStatus: 'Active',
    stopStatus: 'Risk',
    portfolioType,
    notes: '',
  });

  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Reset form when modal opens/closes or initial data changes
  useEffect(() => {
    if (isOpen) {
      if (initialData && mode === 'edit') {
        setFormData({
          symbol: initialData.symbol || '',
          manualPositionSize: initialData.manualPositionSize?.toString() || '',
          manualEntryDate:
            initialData.manualEntryDate ||
            new Date().toISOString().slice(0, 10),
          currentStatus: initialData.currentStatus || 'Active',
          stopStatus: initialData.stopStatus || 'Risk',
          portfolioType: initialData.portfolioType || portfolioType,
          notes: initialData.notes || '',
        });
      } else {
        setFormData({
          symbol: '',
          manualPositionSize: '',
          manualEntryDate: new Date().toISOString().slice(0, 10),
          currentStatus: 'Active',
          stopStatus: 'Risk',
          portfolioType,
          notes: '',
        });
      }
      setValidationErrors([]);
    }
  }, [isOpen, initialData, mode, portfolioType]);

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    // Clear validation errors when user starts typing
    if (validationErrors.length > 0) {
      setValidationErrors([]);
    }
  };

  const validateForm = (): boolean => {
    const positionSize = parseFloat(formData.manualPositionSize);
    const validation = validatePositionData({
      symbol: formData.symbol,
      manualPositionSize: positionSize,
      manualEntryDate: formData.manualEntryDate,
      currentStatus: formData.currentStatus,
      stopStatus: formData.stopStatus,
    });

    // Additional form-specific validations
    const errors = [...validation.errors];

    if (!formData.symbol.trim()) {
      errors.push('Symbol is required');
    }

    if (!formData.manualPositionSize.trim()) {
      errors.push('Position size is required');
    } else if (isNaN(positionSize)) {
      errors.push('Position size must be a valid number');
    }

    setValidationErrors(errors);
    return errors.length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      const positionData = {
        symbol: formData.symbol.toUpperCase().trim(),
        manualPositionSize: parseFloat(formData.manualPositionSize),
        manualEntryDate: formData.manualEntryDate,
        currentStatus: formData.currentStatus,
        stopStatus: formData.stopStatus,
        portfolioType: formData.portfolioType,
        notes: formData.notes.trim() || undefined,
        // Required fields for position entry
        positionValue: parseFloat(formData.manualPositionSize), // Use manual size as position value
        riskPercentage: 0.118, // Default risk percentage
      };

      let result: TradingPosition | null = null;

      if (mode === 'add') {
        result = await addPosition(positionData);
      } else if (mode === 'edit' && initialData?.symbol) {
        result = await updatePosition(initialData.symbol, positionData);
      }

      if (result) {
        onPositionAdded(result);
        onClose();
      }
    } catch (err) {
      console.error('Form submission error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            {mode === 'add' ? 'Add New Position' : 'Edit Position'}
          </h2>
          <button
            onClick={handleClose}
            disabled={isSubmitting}
            className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
          >
            <X size={24} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Symbol */}
          <div>
            <label
              htmlFor="symbol"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Symbol *
            </label>
            <input
              type="text"
              id="symbol"
              name="symbol"
              value={formData.symbol}
              onChange={handleInputChange}
              disabled={mode === 'edit' || isSubmitting}
              placeholder="e.g., AAPL, BTC-USD"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
              required
            />
          </div>

          {/* Position Size */}
          <div>
            <label
              htmlFor="manualPositionSize"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Position Size (USD) *
            </label>
            <div className="relative">
              <DollarSign
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                size={16}
              />
              <input
                type="number"
                id="manualPositionSize"
                name="manualPositionSize"
                value={formData.manualPositionSize}
                onChange={handleInputChange}
                disabled={isSubmitting}
                placeholder="10000"
                min="0"
                step="0.01"
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
                required
              />
            </div>
          </div>

          {/* Entry Date */}
          <div>
            <label
              htmlFor="manualEntryDate"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Entry Date *
            </label>
            <div className="relative">
              <Calendar
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                size={16}
              />
              <input
                type="date"
                id="manualEntryDate"
                name="manualEntryDate"
                value={formData.manualEntryDate}
                onChange={handleInputChange}
                disabled={isSubmitting}
                max={new Date().toISOString().slice(0, 10)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
                required
              />
            </div>
          </div>

          {/* Status Fields */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="currentStatus"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Status
              </label>
              <select
                id="currentStatus"
                name="currentStatus"
                value={formData.currentStatus}
                onChange={handleInputChange}
                disabled={isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Active">Active</option>
                <option value="Closed">Closed</option>
                <option value="Pending">Pending</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="stopStatus"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Stop Status
              </label>
              <select
                id="stopStatus"
                name="stopStatus"
                value={formData.stopStatus}
                onChange={handleInputChange}
                disabled={isSubmitting}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="Risk">Risk</option>
                <option value="Protected">Protected</option>
              </select>
            </div>
          </div>

          {/* Portfolio Type */}
          <div>
            <label
              htmlFor="portfolioType"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Portfolio
            </label>
            <select
              id="portfolioType"
              name="portfolioType"
              value={formData.portfolioType}
              onChange={handleInputChange}
              disabled={isSubmitting}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
            >
              <option value="Risk_On">Risk On Portfolio</option>
              <option value="Protected">Protected Portfolio</option>
              <option value="Investment">Investment Portfolio</option>
            </select>
          </div>

          {/* Notes */}
          <div>
            <label
              htmlFor="notes"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Notes
            </label>
            <textarea
              id="notes"
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              disabled={isSubmitting}
              placeholder="Optional notes about this position..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 resize-none"
            />
          </div>

          {/* Validation Errors */}
          {validationErrors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <div className="flex">
                <AlertCircle
                  className="text-red-400 mr-2 flex-shrink-0"
                  size={16}
                />
                <div>
                  <h4 className="text-sm font-medium text-red-800 mb-1">
                    Please fix the following errors:
                  </h4>
                  <ul className="text-sm text-red-700 space-y-1">
                    {validationErrors.map((error, index) => (
                      <li key={index}>• {error}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* API Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <div className="flex">
                <AlertCircle
                  className="text-red-400 mr-2 flex-shrink-0"
                  size={16}
                />
                <div>
                  <h4 className="text-sm font-medium text-red-800">
                    Operation Failed
                  </h4>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || validationErrors.length > 0}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  {mode === 'add' ? 'Adding...' : 'Updating...'}
                </>
              ) : (
                <>
                  <CheckCircle size={16} className="mr-2" />
                  {mode === 'add' ? 'Add Position' : 'Update Position'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PositionEntryModal;
