import React, { useState } from 'react';
import { AccountBalances } from '../../types';
import { positionSizingApi } from '../../services/positionSizingApi';
import Icon from '../Icon';
import { icons } from '../../utils/icons';

interface AccountBalanceEditorProps {
  accountBalances: AccountBalances;
  onUpdate?: (updatedBalances: AccountBalances) => void;
  disabled?: boolean;
}

interface AccountFormData {
  ibkr: number;
  bybit: number;
  cash: number;
}

const AccountBalanceEditor: React.FC<AccountBalanceEditorProps> = ({
  accountBalances,
  onUpdate,
  disabled = false,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<AccountFormData>({
    ibkr: accountBalances.ibkr || 0,
    bybit: accountBalances.bybit || 0,
    cash: accountBalances.cash || 0,
  });

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getAccountIcon = (account: string) => {
    const iconMap: Record<string, any> = {
      IBKR: icons.star,
      Bybit: icons.portfolio,
      Cash: icons.folder,
    };
    return iconMap[account] || icons.portfolio;
  };

  const getAccountColor = (account: string) => {
    const colorMap: Record<string, string> = {
      IBKR: 'text-primary',
      Bybit: 'text-warning',
      Cash: 'text-success',
    };
    return colorMap[account] || 'text-primary';
  };

  const handleEdit = () => {
    setIsEditing(true);
    setError(null);
    // Reset form data to current values
    setFormData({
      ibkr: accountBalances.ibkr || 0,
      bybit: accountBalances.bybit || 0,
      cash: accountBalances.cash || 0,
    });
  };

  const handleCancel = () => {
    setIsEditing(false);
    setError(null);
    // Reset form to original values
    setFormData({
      ibkr: accountBalances.ibkr || 0,
      bybit: accountBalances.bybit || 0,
      cash: accountBalances.cash || 0,
    });
  };

  const handleSave = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Validate balances
      if (formData.ibkr < 0 || formData.bybit < 0 || formData.cash < 0) {
        throw new Error('Account balances cannot be negative');
      }

      // Update each account balance
      const updates = [
        { account_type: 'IBKR' as const, balance: formData.ibkr },
        { account_type: 'Bybit' as const, balance: formData.bybit },
        { account_type: 'Cash' as const, balance: formData.cash },
      ];

      // Update all balances
      for (const update of updates) {
        await positionSizingApi.updateAccountBalance(update);
      }

      // Get updated balances
      const updatedData = await positionSizingApi.getAccountBalances();
      
      const updatedBalances: AccountBalances = {
        ibkr: updatedData.ibkr_balance || formData.ibkr,
        bybit: updatedData.bybit_balance || formData.bybit,
        cash: updatedData.cash_balance || formData.cash,
        total: updatedData.net_worth,
        accountBreakdown: updatedData.account_breakdown || {},
        lastUpdated: updatedData.last_updated,
      };

      setIsEditing(false);
      onUpdate?.(updatedBalances);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update account balances');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBalanceChange = (account: keyof AccountFormData, value: string) => {
    const numericValue = parseFloat(value) || 0;
    setFormData(prev => ({
      ...prev,
      [account]: numericValue,
    }));
  };

  const totalFormValue = formData.ibkr + formData.bybit + formData.cash;

  if (isEditing) {
    return (
      <div className="card h-100">
        <div className="card-header">
          <div className="d-flex align-items-center">
            <Icon icon={icons.edit} className="me-2 text-primary" />
            <h6 className="mb-0">Edit Account Balances</h6>
          </div>
        </div>
        <div className="card-body">
          {error && (
            <div className="alert alert-danger alert-sm mb-3">
              <Icon icon={icons.error} className="me-1" />
              {error}
            </div>
          )}

          <div className="row g-3">
            {/* IBKR Balance */}
            <div className="col-md-6">
              <label className="form-label small">
                <Icon icon={getAccountIcon('IBKR')} className={`me-1 ${getAccountColor('IBKR')}`} />
                IBKR Balance
              </label>
              <div className="input-group input-group-sm">
                <span className="input-group-text">$</span>
                <input
                  type="number"
                  className="form-control"
                  value={formData.ibkr}
                  onChange={(e) => handleBalanceChange('ibkr', e.target.value)}
                  min="0"
                  step="0.01"
                  disabled={isLoading}
                />
              </div>
              <small className="text-muted">Interactive Brokers</small>
            </div>

            {/* Bybit Balance */}
            <div className="col-md-6">
              <label className="form-label small">
                <Icon icon={getAccountIcon('Bybit')} className={`me-1 ${getAccountColor('Bybit')}`} />
                Bybit Balance
              </label>
              <div className="input-group input-group-sm">
                <span className="input-group-text">$</span>
                <input
                  type="number"
                  className="form-control"
                  value={formData.bybit}
                  onChange={(e) => handleBalanceChange('bybit', e.target.value)}
                  min="0"
                  step="0.01"
                  disabled={isLoading}
                />
              </div>
              <small className="text-muted">Crypto Exchange</small>
            </div>

            {/* Cash Balance */}
            <div className="col-md-6">
              <label className="form-label small">
                <Icon icon={getAccountIcon('Cash')} className={`me-1 ${getAccountColor('Cash')}`} />
                Cash Balance
              </label>
              <div className="input-group input-group-sm">
                <span className="input-group-text">$</span>
                <input
                  type="number"
                  className="form-control"
                  value={formData.cash}
                  onChange={(e) => handleBalanceChange('cash', e.target.value)}
                  min="0"
                  step="0.01"
                  disabled={isLoading}
                />
              </div>
              <small className="text-muted">Liquid Assets</small>
            </div>

            {/* Total Preview */}
            <div className="col-md-6">
              <label className="form-label small">Total Net Worth</label>
              <div className="input-group input-group-sm">
                <span className="input-group-text">$</span>
                <input
                  type="text"
                  className="form-control bg-light"
                  value={totalFormValue.toLocaleString()}
                  disabled
                />
              </div>
              <small className="text-muted">Calculated automatically</small>
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
                  Save All
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card h-100">
      <div className="card-header">
        <div className="d-flex align-items-center justify-content-between">
          <div className="d-flex align-items-center">
            <Icon icon={icons.portfolio} className="me-2" />
            <h6 className="mb-0">Account Balances</h6>
          </div>
          <button
            className="btn btn-outline-primary btn-sm"
            onClick={handleEdit}
            disabled={disabled}
            title="Edit Account Balances"
          >
            <Icon icon={icons.edit} />
          </button>
        </div>
      </div>
      <div className="card-body">
        <div className="row g-3">
          {/* Individual Account Balances */}
          <div className="col-md-6">
            <div className="d-flex align-items-center justify-content-between p-3 border rounded">
              <div className="d-flex align-items-center">
                <Icon
                  icon={getAccountIcon('IBKR')}
                  className={`me-2 ${getAccountColor('IBKR')}`}
                />
                <div>
                  <div className="fw-bold">IBKR</div>
                  <small className="text-muted">Interactive Brokers</small>
                </div>
              </div>
              <div className="text-end">
                <div className="fw-bold">
                  {formatCurrency(accountBalances.ibkr)}
                </div>
              </div>
            </div>
          </div>

          <div className="col-md-6">
            <div className="d-flex align-items-center justify-content-between p-3 border rounded">
              <div className="d-flex align-items-center">
                <Icon
                  icon={getAccountIcon('Bybit')}
                  className={`me-2 ${getAccountColor('Bybit')}`}
                />
                <div>
                  <div className="fw-bold">Bybit</div>
                  <small className="text-muted">Crypto Exchange</small>
                </div>
              </div>
              <div className="text-end">
                <div className="fw-bold">
                  {formatCurrency(accountBalances.bybit)}
                </div>
              </div>
            </div>
          </div>

          <div className="col-md-6">
            <div className="d-flex align-items-center justify-content-between p-3 border rounded">
              <div className="d-flex align-items-center">
                <Icon
                  icon={getAccountIcon('Cash')}
                  className={`me-2 ${getAccountColor('Cash')}`}
                />
                <div>
                  <div className="fw-bold">Cash</div>
                  <small className="text-muted">Liquid Assets</small>
                </div>
              </div>
              <div className="text-end">
                <div className="fw-bold">
                  {formatCurrency(accountBalances.cash)}
                </div>
              </div>
            </div>
          </div>

          {/* Total Net Worth */}
          <div className="col-md-6">
            <div className="d-flex align-items-center justify-content-between p-3 bg-primary text-white rounded">
              <div className="d-flex align-items-center">
                <Icon icon={icons.portfolio} className="me-2" />
                <div>
                  <div className="fw-bold">Total</div>
                  <small>Net Worth</small>
                </div>
              </div>
              <div className="text-end">
                <div className="fw-bold h5 mb-0">
                  {formatCurrency(accountBalances.total)}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Last Updated */}
        <div className="mt-3 pt-3 border-top">
          <small className="text-muted">
            <Icon icon={icons.lastUpdated} className="me-1" />
            Last updated: {new Date(accountBalances.lastUpdated).toLocaleString()}
          </small>
        </div>
      </div>
    </div>
  );
};

export default AccountBalanceEditor;