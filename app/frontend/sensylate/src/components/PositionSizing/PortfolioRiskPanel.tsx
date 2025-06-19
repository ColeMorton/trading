import React from 'react';
import { PortfolioRiskMetrics } from '../../types';
import Icon from '../Icon';
import { icons } from '../../utils/icons';

interface PortfolioRiskPanelProps {
  portfolioRisk: PortfolioRiskMetrics;
}

const PortfolioRiskPanel: React.FC<PortfolioRiskPanelProps> = ({
  portfolioRisk,
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
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatDecimal = (value: number, decimals = 4) => {
    return value.toFixed(decimals);
  };

  // Calculate additional metrics
  const riskPercentage =
    portfolioRisk.netWorth > 0
      ? portfolioRisk.riskAmount / portfolioRisk.netWorth
      : 0;
  const kellyAmount =
    portfolioRisk.netWorth * portfolioRisk.kellyMetrics.kellyCriterion;

  return (
    <div className="card">
      <div className="card-header">
        <div className="d-flex align-items-center">
          <Icon icon={icons.portfolio} className="me-2" />
          <h5 className="card-title mb-0">Portfolio Risk Metrics</h5>
        </div>
      </div>
      <div className="card-body">
        <div className="row">
          {/* Left Column - Core Metrics */}
          <div className="col-lg-6">
            <div className="row g-3">
              {/* Net Worth */}
              <div className="col-md-6">
                <div className="bg-light p-3 rounded">
                  <div className="d-flex align-items-center justify-content-between">
                    <div>
                      <div className="text-muted small">Net Worth</div>
                      <div className="h4 mb-0 text-primary">
                        {formatCurrency(portfolioRisk.netWorth)}
                      </div>
                    </div>
                    <Icon
                      icon={icons.portfolio}
                      className="text-primary"
                      size="lg"
                    />
                  </div>
                </div>
              </div>

              {/* Risk Amount (11.8% allocation) */}
              <div className="col-md-6">
                <div className="bg-light p-3 rounded">
                  <div className="d-flex align-items-center justify-content-between">
                    <div>
                      <div className="text-muted small">
                        Risk Amount (11.8%)
                      </div>
                      <div className="h4 mb-0 text-danger">
                        {formatCurrency(portfolioRisk.riskAmount)}
                      </div>
                    </div>
                    <Icon
                      icon={icons.warning}
                      className="text-danger"
                      size="lg"
                    />
                  </div>
                </div>
              </div>

              {/* Trading CVaR */}
              <div className="col-md-6">
                <div className="border p-3 rounded">
                  <div className="text-muted small">Trading CVaR (95%)</div>
                  <div className="h5 mb-0">
                    {formatDecimal(portfolioRisk.cvarTrading)}
                  </div>
                  <small className="text-info">Risk On Portfolio</small>
                </div>
              </div>

              {/* Investment CVaR */}
              <div className="col-md-6">
                <div className="border p-3 rounded">
                  <div className="text-muted small">Investment CVaR (95%)</div>
                  <div className="h5 mb-0">
                    {formatDecimal(portfolioRisk.cvarInvestment)}
                  </div>
                  <small className="text-success">Investment Portfolio</small>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Kelly Criterion */}
          <div className="col-lg-6">
            <div className="border p-3 rounded h-100">
              <div className="d-flex align-items-center mb-3">
                <Icon icon={icons.calculator} className="me-2" />
                <h6 className="mb-0">Kelly Criterion Metrics</h6>
              </div>

              <div className="row g-3">
                <div className="col-sm-6">
                  <div className="text-muted small">Kelly Criterion</div>
                  <div className="h5 mb-1 text-primary">
                    {formatPercentage(
                      portfolioRisk.kellyMetrics.kellyCriterion
                    )}
                  </div>
                  <small className="text-muted">
                    Amount: {formatCurrency(kellyAmount)}
                  </small>
                </div>

                <div className="col-sm-6">
                  <div className="text-muted small">Total Strategies</div>
                  <div className="h5 mb-0">{portfolioRisk.totalStrategies}</div>
                </div>

                <div className="col-sm-6">
                  <div className="text-muted small">Primary Trades</div>
                  <div className="fw-bold text-success">
                    {portfolioRisk.kellyMetrics.numPrimary}
                  </div>
                </div>

                <div className="col-sm-6">
                  <div className="text-muted small">Outlier Trades</div>
                  <div className="fw-bold text-warning">
                    {portfolioRisk.kellyMetrics.numOutliers}
                  </div>
                </div>
              </div>

              {/* Confidence Metrics */}
              {portfolioRisk.kellyMetrics.confidenceMetrics &&
                Object.keys(portfolioRisk.kellyMetrics.confidenceMetrics)
                  .length > 0 && (
                  <div className="mt-3 pt-3 border-top">
                    <div className="text-muted small mb-2">
                      Confidence Metrics
                    </div>
                    <div className="row g-2">
                      {Object.entries(
                        portfolioRisk.kellyMetrics.confidenceMetrics
                      ).map(([key, value]) => (
                        <div key={key} className="col-sm-6">
                          <div className="small">
                            <span className="text-muted">{key}:</span>{' '}
                            <span className="fw-bold">
                              {typeof value === 'number'
                                ? formatDecimal(value, 3)
                                : String(value)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
            </div>
          </div>
        </div>

        {/* Bottom Row - Additional Metrics */}
        <div className="row mt-4">
          <div className="col-12">
            <div className="bg-light p-3 rounded">
              <div className="row text-center">
                <div className="col-md-3">
                  <div className="text-muted small">Risk Percentage</div>
                  <div className="fw-bold h6 mb-0">
                    {formatPercentage(riskPercentage)}
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-muted small">Kelly Amount</div>
                  <div className="fw-bold h6 mb-0">
                    {formatCurrency(kellyAmount)}
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-muted small">Available Risk</div>
                  <div className="fw-bold h6 mb-0 text-success">
                    {formatCurrency(portfolioRisk.riskAmount)}
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-muted small">Risk Utilization</div>
                  <div className="fw-bold h6 mb-0">
                    <span className="badge bg-info">Active</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioRiskPanel;
