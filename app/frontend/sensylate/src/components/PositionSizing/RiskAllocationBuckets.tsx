import React from 'react';
import { RiskBucket, AccountBalances, RiskAllocation } from '../../types';
import Icon from '../Icon';
import { icons } from '../../utils/icons';

interface RiskAllocationBucketsProps {
  riskBuckets?: RiskBucket[];
  accountBalances: AccountBalances;
  riskAllocation?: RiskAllocation;
}

const RiskAllocationBuckets: React.FC<RiskAllocationBucketsProps> = ({
  riskBuckets = [],
  accountBalances,
  riskAllocation,
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getBucketStatus = (status: 'active' | 'future') => {
    return status === 'active'
      ? { badge: 'bg-success', icon: icons.success, text: 'Active' }
      : { badge: 'bg-secondary', icon: icons.lastUpdated, text: 'Future' };
  };

  const getAccountIcon = (account: string) => {
    const iconMap: Record<string, any> = {
      IBKR: icons.star,
      Bybit: icons.portfolio,
      Cash: icons.folder,
    };
    return iconMap[account] || icons.portfolio;
  };

  // Handle both legacy buckets and new single risk allocation
  const activeBucket = riskBuckets?.find(
    (bucket) => bucket.status === 'active'
  );
  const futureBuckets =
    riskBuckets?.filter((bucket) => bucket.status === 'future') || [];

  // Create a virtual active bucket from new risk allocation if available
  const virtualActiveBucket = riskAllocation
    ? {
        status: 'active' as const,
        percentage: 11.8, // Fixed 11.8% target
        allocationAmount: accountBalances.total * 0.118,
        riskLevel: riskAllocation.currentCVaR / 0.118, // Current utilization
        currentCVaR: riskAllocation.currentCVaR,
        utilization: riskAllocation.utilization,
        availableRisk: riskAllocation.availableRisk,
      }
    : null;

  // Use virtual bucket if no legacy buckets exist
  const displayBucket = activeBucket || virtualActiveBucket;

  return (
    <div className="row">
      {/* Account Balances Card */}
      <div className="col-lg-6 mb-3">
        <div className="card h-100">
          <div className="card-header">
            <div className="d-flex align-items-center">
              <Icon icon={icons.portfolio} className="me-2" />
              <h6 className="mb-0">Account Balances</h6>
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
                      className="me-2 text-primary"
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
                      className="me-2 text-warning"
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
                      className="me-2 text-success"
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
                Last updated: {formatDate(accountBalances.lastUpdated)}
              </small>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Allocation Buckets Card */}
      <div className="col-lg-6 mb-3">
        <div className="card h-100">
          <div className="card-header">
            <div className="d-flex align-items-center justify-content-between">
              <div className="d-flex align-items-center">
                <Icon icon={icons.warning} className="me-2" />
                <h6 className="mb-0">Risk Allocation Buckets</h6>
              </div>
              <span className="badge bg-info">
                {displayBucket ? '1' : '0'} Active
              </span>
            </div>
          </div>
          <div className="card-body">
            {/* Active Risk Bucket (11.8%) */}
            {displayBucket && (
              <div className="mb-4">
                <div className="d-flex align-items-center justify-content-between mb-2">
                  <div className="d-flex align-items-center">
                    <span
                      className={`badge ${
                        getBucketStatus(displayBucket.status).badge
                      } me-2`}
                    >
                      <Icon
                        icon={getBucketStatus(displayBucket.status).icon}
                        className="me-1"
                      />
                      {getBucketStatus(displayBucket.status).text}
                    </span>
                    <span className="fw-bold">Current Risk Tier</span>
                  </div>
                  <span className="badge bg-danger text-white px-3 py-2">
                    {formatPercentage(displayBucket.percentage)}
                  </span>
                </div>

                <div className="bg-light p-3 rounded">
                  <div className="d-flex justify-content-between align-items-center">
                    <div>
                      <div className="text-muted small">
                        Maximum Risk Allocation
                      </div>
                      <div className="h4 mb-0 text-danger">
                        {formatCurrency(displayBucket.allocationAmount)}
                      </div>
                    </div>
                    <div className="text-end">
                      <div className="text-muted small">Current CVaR</div>
                      <div className="fw-bold">
                        {displayBucket.currentCVaR
                          ? formatPercentage(displayBucket.currentCVaR * 100)
                          : formatPercentage(displayBucket.riskLevel * 100)}
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
                      className="progress-bar bg-danger"
                      style={{
                        width: `${
                          displayBucket.utilization
                            ? Math.min(displayBucket.utilization * 100, 100)
                            : displayBucket.riskLevel * 100
                        }%`,
                      }}
                    />
                  </div>
                  <div className="d-flex justify-content-between mt-1">
                    <small className="text-muted">
                      {displayBucket.utilization
                        ? formatPercentage(displayBucket.utilization * 100)
                        : formatPercentage(displayBucket.riskLevel * 100)}{' '}
                      Used
                    </small>
                    <small className="text-success">
                      {displayBucket.availableRisk
                        ? formatPercentage(displayBucket.availableRisk * 100)
                        : formatPercentage(
                            (1 - displayBucket.riskLevel) * 100
                          )}{' '}
                      Available
                    </small>
                  </div>
                </div>
              </div>
            )}

            {/* Future Risk Buckets */}
            {futureBuckets.length > 0 && (
              <div>
                <div className="border-top pt-3">
                  <div className="d-flex align-items-center mb-3">
                    <Icon
                      icon={icons.lastUpdated}
                      className="me-2 text-muted"
                    />
                    <span className="text-muted fw-bold">
                      Future Risk Tiers
                    </span>
                  </div>

                  <div className="row g-2">
                    {futureBuckets.map((bucket, index) => (
                      <div key={index} className="col-md-6">
                        <div className="border rounded p-2 text-center">
                          <div className="text-muted small">Risk Level</div>
                          <div className="fw-bold">
                            {formatPercentage(bucket.percentage)}
                          </div>
                          <span
                            className={`badge ${
                              getBucketStatus(bucket.status).badge
                            } mt-1`}
                          >
                            {getBucketStatus(bucket.status).text}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskAllocationBuckets;
