import React, { useState, useEffect } from 'react';
import {
  Save,
  RefreshCw,
  BookOpen,
  Calculator,
  User,
  AlertCircle,
  CheckCircle,
  Clock,
} from 'lucide-react';
import { KellyInput } from '../types';
import { useKellyInput } from '../hooks/usePositionSizing';
import { validateKellyInput } from '../utils/apiErrorHandler';

interface KellyInputFormProps {
  className?: string;
  onUpdate?: (kellyInput: KellyInput) => void;
  showHeader?: boolean;
}

const KellyInputForm: React.FC<KellyInputFormProps> = ({
  className = '',
  onUpdate,
  showHeader = true,
}) => {
  const {
    kellyInput,
    isLoading,
    isUpdating,
    error,
    updateKellyInput,
    refetch,
  } = useKellyInput();

  const [formData, setFormData] = useState({
    kellyCriterion: '',
    source: 'Trading Journal' as const,
    notes: '',
  });

  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Initialize form data when Kelly input is loaded
  useEffect(() => {
    if (kellyInput) {
      setFormData({
        kellyCriterion: kellyInput.kellyCriterion.toString(),
        source: kellyInput.source,
        notes: kellyInput.notes || '',
      });
      setHasUnsavedChanges(false);
    }
  }, [kellyInput]);

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

    setHasUnsavedChanges(true);

    // Clear validation errors when user starts typing
    if (validationErrors.length > 0) {
      setValidationErrors([]);
    }
  };

  const validateForm = (): boolean => {
    const kellyCriterion = parseFloat(formData.kellyCriterion);
    const validation = validateKellyInput({
      kellyCriterion,
      source: formData.source,
    });

    // Additional form-specific validations
    const errors = [...validation.errors];

    if (!formData.kellyCriterion.trim()) {
      errors.push('Kelly Criterion value is required');
    } else if (isNaN(kellyCriterion)) {
      errors.push('Kelly Criterion must be a valid number');
    }

    setValidationErrors(errors);
    return errors.length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const kellyCriterion = parseFloat(formData.kellyCriterion);
    const success = await updateKellyInput({
      kellyCriterion,
      source: formData.source,
      notes: formData.notes.trim() || undefined,
    });

    if (success && kellyInput) {
      setHasUnsavedChanges(false);
      if (onUpdate) {
        onUpdate({
          ...kellyInput,
          kellyCriterion,
          source: formData.source,
          notes: formData.notes.trim() || undefined,
        });
      }
    }
  };

  const handleRefresh = () => {
    refetch();
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'Trading Journal':
        return <BookOpen size={16} />;
      case 'Manual':
        return <User size={16} />;
      case 'Calculated':
        return <Calculator size={16} />;
      default:
        return <BookOpen size={16} />;
    }
  };

  const formatLastUpdated = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    return `${diffDays} days ago`;
  };

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}
    >
      {showHeader && (
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                Kelly Criterion
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                Manage Kelly value from your trading journal
              </p>
            </div>
            <button
              onClick={handleRefresh}
              disabled={isLoading || isUpdating}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
              title="Refresh data"
            >
              <RefreshCw
                size={16}
                className={isLoading ? 'animate-spin' : ''}
              />
            </button>
          </div>
        </div>
      )}

      <div className="p-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading Kelly data...</span>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Kelly Criterion Value */}
            <div>
              <label
                htmlFor="kellyCriterion"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Kelly Criterion Value *
              </label>
              <div className="relative">
                <input
                  type="number"
                  id="kellyCriterion"
                  name="kellyCriterion"
                  value={formData.kellyCriterion}
                  onChange={handleInputChange}
                  disabled={isUpdating}
                  placeholder="0.25"
                  min="0"
                  max="1"
                  step="0.001"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
                  required
                />
                <div className="absolute inset-y-0 right-3 flex items-center text-sm text-gray-500">
                  0.0 - 1.0
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Enter the Kelly Criterion value from your trading journal (0.0
                to 1.0)
              </p>
            </div>

            {/* Source */}
            <div>
              <label
                htmlFor="source"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Source
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none text-gray-400">
                  {getSourceIcon(formData.source)}
                </div>
                <select
                  id="source"
                  name="source"
                  value={formData.source}
                  onChange={handleInputChange}
                  disabled={isUpdating}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
                >
                  <option value="Trading Journal">Trading Journal</option>
                  <option value="Manual">Manual Entry</option>
                  <option value="Calculated">Calculated</option>
                </select>
              </div>
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
                disabled={isUpdating}
                placeholder="Additional notes about this Kelly value..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 resize-none"
              />
            </div>

            {/* Last Updated Info */}
            {kellyInput && (
              <div className="bg-gray-50 rounded-md p-3">
                <div className="flex items-center text-sm text-gray-600">
                  <Clock size={14} className="mr-2" />
                  <span>
                    Last updated:{' '}
                    {formatLastUpdated(new Date(kellyInput.lastUpdated))}
                    {kellyInput.source && (
                      <span className="ml-2 text-gray-500">
                        (from {kellyInput.source})
                      </span>
                    )}
                  </span>
                </div>
              </div>
            )}

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
                      Update Failed
                    </h4>
                    <p className="text-sm text-red-700 mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Unsaved Changes Warning */}
            {hasUnsavedChanges && !error && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                <div className="flex">
                  <AlertCircle
                    className="text-yellow-400 mr-2 flex-shrink-0"
                    size={16}
                  />
                  <p className="text-sm text-yellow-800">
                    You have unsaved changes. Click "Save Changes" to update
                    your Kelly Criterion value.
                  </p>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end space-x-3 pt-4 border-t">
              <button
                type="button"
                onClick={handleRefresh}
                disabled={isLoading || isUpdating}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <RefreshCw
                  size={16}
                  className={`mr-2 ${isLoading ? 'animate-spin' : ''}`}
                />
                Refresh
              </button>
              <button
                type="submit"
                disabled={
                  isUpdating ||
                  validationErrors.length > 0 ||
                  !hasUnsavedChanges
                }
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {isUpdating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Saving...
                  </>
                ) : (
                  <>
                    <Save size={16} className="mr-2" />
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default KellyInputForm;
