import React from 'react';
import Icon from './Icon';
import { icons } from '../utils/icons';
import { useAppContext } from '../context/AppContext';

const ParameterTestingContainer: React.FC = () => {
  const { parameterTesting } = useAppContext();

  return (
    <div className="parameter-testing-container">
      {/* Header Card */}
      <div className="card mb-4">
        <div className="card-header d-flex align-items-center">
          <Icon icon={icons.parameterTesting} className="me-2" />
          <h5 className="card-title mb-0">Parameter Testing</h5>
        </div>
        <div className="card-body">
          <p className="card-text text-muted mb-0">
            Analyze trading strategies with customizable parameters and configurations.
          </p>
        </div>
      </div>

      {/* Analysis Configuration Card */}
      <div className="card mb-4">
        <div className="card-header d-flex align-items-center">
          <Icon icon={icons.settings} className="me-2" />
          <h6 className="card-title mb-0">Analysis Configuration</h6>
        </div>
        <div className="card-body">
          <div className="row g-3">
            {/* Basic Configuration */}
            <div className="col-md-6">
              <label htmlFor="ticker-input" className="form-label">
                <Icon icon={icons.search} className="me-1" />
                Ticker Symbol(s)
              </label>
              <input
                type="text"
                className="form-control"
                id="ticker-input"
                placeholder="e.g., AAPL, GOOGL, MSFT"
                value={Array.isArray(parameterTesting.configuration.TICKER) 
                  ? parameterTesting.configuration.TICKER.join(', ') 
                  : parameterTesting.configuration.TICKER}
                readOnly
              />
              <div className="form-text">Comma-separated list of ticker symbols</div>
            </div>

            <div className="col-md-3">
              <label htmlFor="windows-input" className="form-label">
                <Icon icon={icons.calculator} className="me-1" />
                Windows
              </label>
              <input
                type="number"
                className="form-control"
                id="windows-input"
                value={parameterTesting.configuration.WINDOWS}
                min="1"
                max="50"
                readOnly
              />
              <div className="form-text">Number of window combinations</div>
            </div>

            <div className="col-md-3">
              <label htmlFor="direction-select" className="form-label">
                <Icon icon={icons.chevronUp} className="me-1" />
                Direction
              </label>
              <select 
                className="form-select" 
                id="direction-select"
                value={parameterTesting.configuration.DIRECTION}
                disabled
              >
                <option value="Long">Long</option>
                <option value="Short">Short</option>
              </select>
            </div>

            {/* Strategy Types */}
            <div className="col-md-6">
              <label className="form-label">
                <Icon icon={icons.brand} className="me-1" />
                Strategy Types
              </label>
              <div className="d-flex gap-3">
                <div className="form-check">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    id="sma-checkbox"
                    checked={parameterTesting.configuration.STRATEGY_TYPES.includes('SMA')}
                    disabled
                  />
                  <label className="form-check-label" htmlFor="sma-checkbox">
                    SMA (Simple Moving Average)
                  </label>
                </div>
                <div className="form-check">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    id="ema-checkbox"
                    checked={parameterTesting.configuration.STRATEGY_TYPES.includes('EMA')}
                    disabled
                  />
                  <label className="form-check-label" htmlFor="ema-checkbox">
                    EMA (Exponential Moving Average)
                  </label>
                </div>
              </div>
            </div>

            {/* Options */}
            <div className="col-md-6">
              <label className="form-label">
                <Icon icon={icons.settings} className="me-1" />
                Options
              </label>
              <div className="row g-2">
                <div className="col-6">
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="use-current-checkbox"
                      checked={parameterTesting.configuration.USE_CURRENT}
                      disabled
                    />
                    <label className="form-check-label" htmlFor="use-current-checkbox">
                      Use Current Price
                    </label>
                  </div>
                </div>
                <div className="col-6">
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="refresh-checkbox"
                      checked={parameterTesting.configuration.REFRESH}
                      disabled
                    />
                    <label className="form-check-label" htmlFor="refresh-checkbox">
                      Refresh Data
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Run Analysis Button */}
            <div className="col-12">
              <button 
                type="button" 
                className="btn btn-primary"
                disabled={parameterTesting.isAnalyzing}
              >
                {parameterTesting.isAnalyzing ? (
                  <>
                    <Icon icon={icons.loading} className="me-2 fa-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Icon icon={icons.parameterTesting} className="me-2" />
                    Run Analysis
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Results Section */}
      {parameterTesting.results.length > 0 && (
        <div className="card mb-4">
          <div className="card-header d-flex align-items-center">
            <Icon icon={icons.table} className="me-2" />
            <h6 className="card-title mb-0">Analysis Results</h6>
            <span className="badge bg-primary ms-2">
              {parameterTesting.results.length} results
            </span>
          </div>
          <div className="card-body">
            <div className="table-responsive">
              <table className="table table-striped table-hover">
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Strategy</th>
                    <th>Windows</th>
                    <th>Win Rate %</th>
                    <th>Profit Factor</th>
                    <th>Expectancy</th>
                    <th>Total Trades</th>
                  </tr>
                </thead>
                <tbody>
                  {parameterTesting.results.slice(0, 10).map((result, index) => (
                    <tr key={index}>
                      <td className="fw-bold">{result.ticker}</td>
                      <td>
                        <span className="badge bg-secondary">
                          {result.strategy_type}
                        </span>
                      </td>
                      <td>{result.short_window}/{result.long_window}/{result.signal_window}</td>
                      <td>{(result.win_rate * 100).toFixed(1)}%</td>
                      <td>{result.profit_factor.toFixed(2)}</td>
                      <td>{result.expectancy_per_trade.toFixed(4)}</td>
                      <td>{result.total_trades}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {parameterTesting.results.length > 10 && (
                <div className="text-center mt-3">
                  <small className="text-muted">
                    Showing top 10 of {parameterTesting.results.length} results
                  </small>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {parameterTesting.error && (
        <div className="card border-danger mb-4">
          <div className="card-header bg-danger text-white d-flex align-items-center">
            <Icon icon={icons.error} className="me-2" />
            <h6 className="card-title mb-0">Analysis Error</h6>
          </div>
          <div className="card-body">
            <p className="text-danger mb-0">{parameterTesting.error}</p>
          </div>
        </div>
      )}

      {/* Progress Display */}
      {parameterTesting.isAnalyzing && parameterTesting.progress > 0 && (
        <div className="card mb-4">
          <div className="card-header d-flex align-items-center">
            <Icon icon={icons.loading} className="me-2 fa-spin" />
            <h6 className="card-title mb-0">Analysis Progress</h6>
          </div>
          <div className="card-body">
            <div className="progress">
              <div 
                className="progress-bar progress-bar-striped progress-bar-animated" 
                role="progressbar" 
                style={{ width: `${parameterTesting.progress}%` }}
                aria-valuenow={parameterTesting.progress}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                {parameterTesting.progress.toFixed(0)}%
              </div>
            </div>
            {parameterTesting.executionId && (
              <small className="text-muted mt-2 d-block">
                Execution ID: {parameterTesting.executionId}
              </small>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ParameterTestingContainer;