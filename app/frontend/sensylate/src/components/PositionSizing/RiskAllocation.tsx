import React from 'react';
import {
  AccountBalances,
  RiskAllocation as RiskAllocationData,
} from '../../types';
import Icon from '../Icon';
import { icons } from '../../utils/icons';
import AccountBalanceEditor from './AccountBalanceEditor';

interface RiskAllocationProps {
  accountBalances: AccountBalances;
  riskAllocation?: RiskAllocationData;
  onBalanceUpdate?: (updatedBalances: AccountBalances) => void;
}

const RiskAllocation: React.FC<RiskAllocationProps> = ({
  accountBalances,
  riskAllocation,
  onBalanceUpdate,
}) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getRiskStatus = (utilization: number) => {
    if (utilization < 0.7)
      return { badge: 'bg-success', icon: icons.success, text: 'Conservative' };
    if (utilization < 0.9)
      return { badge: 'bg-warning', icon: icons.warning, text: 'Moderate' };
    return { badge: 'bg-danger', icon: icons.error, text: 'High' };
  };

  // Single 11.8% CVaR target risk allocation
  const targetCVaR = 0.118; // 11.8% fixed target
  const currentCVaR = riskAllocation?.currentCVaR || 0;
  const utilization = riskAllocation?.utilization || 0;
  const availableRisk = riskAllocation?.availableRisk || targetCVaR;
  const maxRiskAmount = accountBalances.total * targetCVaR;

  const riskStatus = getRiskStatus(utilization);

  return (
    <div className="row">
      {/* Account Balances Card */}
      <div className="col-lg-6 mb-3">
        <AccountBalanceEditor
          accountBalances={accountBalances}
          onUpdate={onBalanceUpdate}
        />
      </div>

      {/* Risk Allocation Card */}
      <div className="col-lg-6 mb-3">
        <div className="card h-100">
          <div className="card-header">
            <div className="d-flex align-items-center justify-content-between">
              <div className="d-flex align-items-center">
                <Icon icon={icons.warning} className="me-2" />
                <h6 className="mb-0">Risk Allocation</h6>
              </div>
              <span className={`badge ${riskStatus.badge}`}>
                <Icon icon={riskStatus.icon} className="me-1" />
                {riskStatus.text}
              </span>
            </div>
          </div>
          <div className="card-body">
            {/* Single 11.8% CVaR Target */}
            <div className="mb-4">
              <div className="d-flex align-items-center justify-content-between mb-2">
                <div className="d-flex align-items-center">
                  <span className="fw-bold">CVaR Target (95%)</span>
                </div>
                <span className="badge bg-primary text-white px-3 py-2">
                  {formatPercentage(targetCVaR * 100)}
                </span>
              </div>

              <div className="bg-light p-3 rounded">
                <div className="d-flex justify-content-between align-items-center">
                  <div>
                    <div className="text-muted small">Maximum Risk Amount</div>
                    <div className="h4 mb-0 text-danger">
                      {formatCurrency(maxRiskAmount)}
                    </div>
                  </div>
                  <div className="text-end">
                    <div className="text-muted small">Current CVaR</div>
                    <div className="fw-bold">
                      {formatPercentage(currentCVaR * 100)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Risk Utilization Progress */}
              <div className="mt-3">
                <div className="d-flex justify-content-between align-items-center mb-1">
                  <small className="text-muted">Risk Utilization</small>
                  <small className="text-muted">Available</small>
                </div>
                <div className="progress" style={{ height: '8px' }}>
                  <div
                    className={`progress-bar ${
                      utilization < 0.7
                        ? 'bg-success'
                        : utilization < 0.9
                          ? 'bg-warning'
                          : 'bg-danger'
                    }`}
                    style={{
                      width: `${Math.min(utilization * 100, 100)}%`,
                    }}
                  />
                </div>
                <div className="d-flex justify-content-between mt-1">
                  <small className="text-muted">
                    {formatPercentage(utilization * 100)} Used
                  </small>
                  <small className="text-success">
                    {formatPercentage(availableRisk * 100)} Available
                  </small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskAllocation;
