import React from 'react';
import { usePositionSizingDashboard } from '../../hooks/usePositionSizing';
import Icon from '../Icon';
import { icons } from '../../utils/icons';
import LoadingIndicator from '../LoadingIndicator';
import PortfolioRiskPanel from './PortfolioRiskPanel';
import ActivePositionsTable from './ActivePositionsTable';
import IncomingSignalsTable from './IncomingSignalsTable';
import StrategicHoldingsTable from './StrategicHoldingsTable';
import RiskAllocation from './RiskAllocation';

const PositionSizingDashboard: React.FC = () => {
  const { dashboard, isLoading, error, lastUpdated, refresh } =
    usePositionSizingDashboard(
      true, // autoRefresh
      30000 // refresh every 30 seconds
    );

  const formatLastUpdated = (date: Date | null) => {
    if (!date) return 'Never';
    return date.toLocaleTimeString();
  };

  if (isLoading && !dashboard) {
    return (
      <div
        className="d-flex justify-content-center align-items-center"
        style={{ minHeight: '400px' }}
      >
        <LoadingIndicator />
      </div>
    );
  }

  if (error && !dashboard) {
    return (
      <div className="container-fluid">
        <div className="alert alert-danger d-flex align-items-center">
          <Icon icon={icons.error} className="me-2" />
          <div>
            <strong>Failed to load Position Sizing Dashboard</strong>
            <div>{error}</div>
            <button
              className="btn btn-outline-danger btn-sm mt-2"
              onClick={refresh}
            >
              <Icon icon={icons.refresh} className="me-1" />
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid" data-testid="position-sizing-dashboard">
      {/* Header Section */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h2 className="mb-1">
                <Icon icon={icons.calculator} className="me-2" />
                Position Sizing Dashboard
              </h2>
              <p className="text-muted mb-0">
                Real-time position sizing and risk management
              </p>
            </div>
            <div className="d-flex align-items-center gap-3">
              <small className="text-muted">
                <Icon icon={icons.lastUpdated} className="me-1" />
                Last updated: {formatLastUpdated(lastUpdated)}
              </small>
              <button
                className="btn btn-outline-primary btn-sm"
                onClick={refresh}
                disabled={isLoading}
                title="Refresh dashboard data"
              >
                <Icon
                  icon={icons.refresh}
                  className={`me-1 ${isLoading ? 'fa-spin' : ''}`}
                />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error Alert (if there's an error but we have cached data) */}
      {error && dashboard && (
        <div className="row mb-3">
          <div className="col-12">
            <div className="alert alert-warning d-flex align-items-center">
              <Icon icon={icons.warning} className="me-2" />
              <div>
                <strong>Warning:</strong> Using cached data due to connection
                issue: {error}
              </div>
            </div>
          </div>
        </div>
      )}

      {dashboard && (
        <>
          {/* Top Row - Portfolio Risk Panel */}
          <div className="row mb-4">
            <div className="col-12">
              <PortfolioRiskPanel portfolioRisk={dashboard.portfolioRisk} />
            </div>
          </div>

          {/* Second Row - Risk Allocation */}
          <div className="row mb-4">
            <div className="col-12">
              <RiskAllocation
                accountBalances={dashboard.accountBalances}
                riskAllocation={dashboard.riskAllocation}
              />
            </div>
          </div>

          {/* Third Row - Active Positions and Incoming Signals */}
          <div className="row mb-4">
            <div className="col-xl-8 mb-3">
              <ActivePositionsTable
                positions={dashboard.activePositions}
                isLoading={isLoading}
              />
            </div>
            <div className="col-xl-4 mb-3">
              <IncomingSignalsTable
                signals={dashboard.incomingSignals}
                isLoading={isLoading}
              />
            </div>
          </div>

          {/* Fourth Row - Strategic Holdings */}
          <div className="row mb-4">
            <div className="col-12">
              <StrategicHoldingsTable
                holdings={dashboard.strategicHoldings}
                isLoading={isLoading}
              />
            </div>
          </div>

          {/* Footer Info */}
          <div className="row">
            <div className="col-12">
              <div className="card">
                <div className="card-body">
                  <div className="row text-center">
                    <div className="col-md-3">
                      <div className="d-flex align-items-center justify-content-center">
                        <Icon
                          icon={icons.portfolio}
                          className="me-2 text-primary"
                        />
                        <div>
                          <div className="fw-bold">
                            ${dashboard.portfolioRisk.netWorth.toLocaleString()}
                          </div>
                          <small className="text-muted">Net Worth</small>
                        </div>
                      </div>
                    </div>
                    <div className="col-md-3">
                      <div className="d-flex align-items-center justify-content-center">
                        <Icon icon={icons.star} className="me-2 text-warning" />
                        <div>
                          <div className="fw-bold">
                            {dashboard.activePositions.length}
                          </div>
                          <small className="text-muted">Active Positions</small>
                        </div>
                      </div>
                    </div>
                    <div className="col-md-3">
                      <div className="d-flex align-items-center justify-content-center">
                        <Icon
                          icon={icons.parameterTesting}
                          className="me-2 text-info"
                        />
                        <div>
                          <div className="fw-bold">
                            {dashboard.portfolioRisk.totalStrategies}
                          </div>
                          <small className="text-muted">Total Strategies</small>
                        </div>
                      </div>
                    </div>
                    <div className="col-md-3">
                      <div className="d-flex align-items-center justify-content-center">
                        <Icon icon={icons.info} className="me-2 text-success" />
                        <div>
                          <div className="fw-bold">
                            {dashboard.incomingSignals.length}
                          </div>
                          <small className="text-muted">Pending Signals</small>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default PositionSizingDashboard;
