import React from 'react';
import Icon from './Icon';
import { icons } from '../utils/icons';
import AnalysisConfiguration from './AnalysisConfiguration';
import ResultsTable from './ResultsTable';
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

      {/* Results Table */}
      <ResultsTable 
        results={results} 
        isLoading={isAnalyzing}
        error={error}
      />
    </div>
  );
};

export default ParameterTestingContainer;