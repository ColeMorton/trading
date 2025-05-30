import React from 'react';
import Icon from './Icon';
import { icons } from '../utils/icons';
import AnalysisConfiguration from './AnalysisConfiguration';
import { useParameterTesting } from '../hooks/useParameterTesting';

const ParameterTestingContainer: React.FC = () => {
  const { 
    analyze, 
    results, 
    isAnalyzing, 
    progress, 
    error, 
    executionId,
    clearResults,
    cancelAnalysis 
  } = useParameterTesting();

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

      {/* Analysis Configuration */}
      <AnalysisConfiguration onAnalyze={analyze} isAnalyzing={isAnalyzing} />
      
      {/* Progress Section */}
      {isAnalyzing && (
        <div className="card mb-4">
          <div className="card-body">
            <div className="d-flex align-items-center justify-content-between mb-2">
              <h6 className="mb-0">Analyzing...</h6>
              <button 
                className="btn btn-sm btn-outline-danger"
                onClick={cancelAnalysis}
              >
                Cancel
              </button>
            </div>
            <div className="progress">
              <div 
                className="progress-bar progress-bar-striped progress-bar-animated" 
                role="progressbar" 
                style={{ width: `${progress}%` }}
                aria-valuenow={progress} 
                aria-valuemin={0} 
                aria-valuemax={100}
              >
                {progress}%
              </div>
            </div>
            {executionId && (
              <small className="text-muted">Execution ID: {executionId}</small>
            )}
          </div>
        </div>
      )}
      
      {/* Error Section */}
      {error && (
        <div className="alert alert-danger alert-dismissible fade show" role="alert">
          <Icon icon={icons.warning} className="me-2" />
          <strong>Error:</strong> {error}
          <button 
            type="button" 
            className="btn-close" 
            onClick={() => clearResults()}
            aria-label="Close"
          ></button>
        </div>
      )}

      {/* Results Section */}
      {results.length > 0 && (
        <div className="card mb-4">
          <div className="card-header d-flex align-items-center">
            <Icon icon={icons.table} className="me-2" />
            <h6 className="card-title mb-0">Analysis Results</h6>
            <span className="badge bg-primary ms-2">
              {results.length} results
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
                  {results.slice(0, 10).map((result, index) => (
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
              {results.length > 10 && (
                <div className="text-center mt-3">
                  <small className="text-muted">
                    Showing top 10 of {results.length} results
                  </small>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ParameterTestingContainer;