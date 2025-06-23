import React, { useState } from 'react';
import { KellyInput } from '../../types';
import { positionSizingApi } from '../../services/positionSizingApi';
import Icon from '../Icon';
import { icons } from '../../utils/icons';

interface KellyEditorProps {
  kellyInput: KellyInput | null;
  onUpdate?: (updatedKelly: KellyInput) => void;
  disabled?: boolean;
}

const KellyEditor: React.FC<KellyEditorProps> = ({
  kellyInput,
  onUpdate,
  disabled = false,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    kellyCriterion: kellyInput?.kellyCriterion || 0.0448, // Default to 4.48%
    numPrimary: kellyInput?.numPrimary || 214,
    numOutliers: kellyInput?.numOutliers || 25,
    source: kellyInput?.source || 'Trading Journal' as const,
    notes: kellyInput?.notes || '',
  });

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const handleEdit = () => {
    setIsEditing(true);
    setError(null);
    // Reset form data to current values
    setFormData({
      kellyCriterion: kellyInput?.kellyCriterion || 0.0448,
      numPrimary: kellyInput?.numPrimary || 214,
      numOutliers: kellyInput?.numOutliers || 25,
      source: kellyInput?.source || 'Trading Journal',
      notes: kellyInput?.notes || '',
    });
  };

  const handleCancel = () => {
    setIsEditing(false);
    setError(null);
    // Reset form to original values
    setFormData({
      kellyCriterion: kellyInput?.kellyCriterion || 0.0448,
      numPrimary: kellyInput?.numPrimary || 214,
      numOutliers: kellyInput?.numOutliers || 25,
      source: kellyInput?.source || 'Trading Journal',
      notes: kellyInput?.notes || '',
    });
  };

  const handleSave = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Validate Kelly Criterion value
      if (formData.kellyCriterion <= 0 || formData.kellyCriterion > 1) {
        throw new Error('Kelly Criterion must be between 0% and 100%');
      }

      const updatedKelly = await positionSizingApi.updateKellyInput({
        kellyCriterion: formData.kellyCriterion,
        numPrimary: formData.numPrimary,
        numOutliers: formData.numOutliers,
        source: formData.source,
        notes: formData.notes,
      });

      setIsEditing(false);
      onUpdate?.(updatedKelly);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update Kelly Criterion');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePercentageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const percentageValue = parseFloat(e.target.value) || 0;
    const decimalValue = percentageValue / 100;
    setFormData(prev => ({
      ...prev,
      kellyCriterion: decimalValue,
    }));
  };

  if (isEditing) {
    return (
      <div className="border rounded p-3">
        <div className="d-flex align-items-center mb-3">
          <Icon icon={icons.edit} className="me-2 text-primary" />
          <h6 className="mb-0">Edit Kelly Criterion</h6>
        </div>

        {error && (
          <div className="alert alert-danger alert-sm mb-3">
            <Icon icon={icons.error} className="me-1" />
            {error}
          </div>
        )}

        <div className="row g-3">
          <div className="col-sm-4">
            <label className="form-label small">Kelly Criterion (%)</label>
            <div className="input-group input-group-sm">
              <input
                type="number"
                className="form-control"
                value={(formData.kellyCriterion * 100).toFixed(2)}
                onChange={handlePercentageChange}
                min="0"
                max="100"
                step="0.01"
                disabled={isLoading}
              />
              <span className="input-group-text">%</span>
            </div>
          </div>

          <div className="col-sm-4">
            <label className="form-label small">Primary Trades</label>
            <input
              type="number"
              className="form-control form-control-sm"
              value={formData.numPrimary}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                numPrimary: parseInt(e.target.value) || 0,
              }))}
              min="0"
              disabled={isLoading}
            />
          </div>

          <div className="col-sm-4">
            <label className="form-label small">Outlier Trades</label>
            <input
              type="number"
              className="form-control form-control-sm"
              value={formData.numOutliers}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                numOutliers: parseInt(e.target.value) || 0,
              }))}
              min="0"
              disabled={isLoading}
            />
          </div>

          <div className="col-sm-6">
            <label className="form-label small">Source</label>
            <select
              className="form-select form-select-sm"
              value={formData.source}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                source: e.target.value as KellyInput['source'],
              }))}
              disabled={isLoading}
            >
              <option value="Trading Journal">Trading Journal</option>
              <option value="Manual">Manual Entry</option>
              <option value="Calculated">Calculated</option>
            </select>
          </div>

          <div className="col-12">
            <label className="form-label small">Notes (optional)</label>
            <textarea
              className="form-control form-control-sm"
              rows={2}
              value={formData.notes}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                notes: e.target.value,
              }))}
              placeholder="Add any notes about this Kelly Criterion update..."
              disabled={isLoading}
            />
          </div>
        </div>

        <div className="d-flex justify-content-end gap-2 mt-3">
          <button
            className="btn btn-outline-secondary btn-sm"
            onClick={handleCancel}
            disabled={isLoading}
          >
            <Icon icon={icons.times} className="me-1" />
            Cancel
          </button>
          <button
            className="btn btn-primary btn-sm"
            onClick={handleSave}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Icon icon={icons.refresh} className="me-1 fa-spin" />
                Saving...
              </>
            ) : (
              <>
                <Icon icon={icons.success} className="me-1" />
                Save
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="d-flex align-items-center justify-content-between">
      <div>
        <div className="text-muted small">Kelly Criterion</div>
        <div className="h5 mb-1 text-primary">
          {formatPercentage(kellyInput?.kellyCriterion || 0.0448)}
        </div>
        {kellyInput?.source && (
          <small className="text-muted">
            Source: {kellyInput.source}
            {kellyInput.lastUpdated && (
              <> • Updated: {new Date(kellyInput.lastUpdated).toLocaleDateString()}</>
            )}
          </small>
        )}
      </div>
      <button
        className="btn btn-outline-primary btn-sm"
        onClick={handleEdit}
        disabled={disabled}
        title="Edit Kelly Criterion"
      >
        <Icon icon={icons.edit} />
      </button>
    </div>
  );
};

export default KellyEditor;