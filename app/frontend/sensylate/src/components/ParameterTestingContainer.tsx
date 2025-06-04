import React from 'react';
import Icon from './Icon';
import { icons } from '../utils/icons';
import AnalysisConfiguration from './AnalysisConfiguration';
import ResultsTable from './ResultsTable';
import ErrorBoundary from './ErrorBoundary';
import ProgressIndicator from './ProgressIndicator';
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
    cancelAnalysis,
  } = useParameterTesting();

  // Progress steps for analysis workflow
  const getProgressSteps = () => {
    if (!isAnalyzing) return [];

    const steps = [
      {
        id: 'validation',
        label: 'Validation',
        description: 'Validating configuration',
        status: progress > 0 ? ('completed' as const) : ('active' as const),
      },
      {
        id: 'setup',
        label: 'Setup',
        description: 'Preparing analysis',
        status:
          progress > 20
            ? ('completed' as const)
            : progress > 0
              ? ('active' as const)
              : ('pending' as const),
      },
      {
        id: 'processing',
        label: 'Processing',
        description: 'Running strategy analysis',
        status:
          progress > 70
            ? ('completed' as const)
            : progress > 20
              ? ('active' as const)
              : ('pending' as const),
      },
      {
        id: 'results',
        label: 'Results',
        description: 'Generating results',
        status:
          progress >= 100
            ? ('completed' as const)
            : progress > 70
              ? ('active' as const)
              : ('pending' as const),
      },
    ];

    return steps;
  };

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
            Analyze trading strategies with customizable parameters and
            configurations.
          </p>
        </div>
      </div>

      {/* Analysis Configuration */}
      <AnalysisConfiguration onAnalyze={analyze} isAnalyzing={isAnalyzing} />

      {/* Progress Section */}
      {isAnalyzing && (
        <div className="card mb-4">
          <div className="card-body">
            <div className="d-flex align-items-center justify-content-between mb-3">
              <h6 className="mb-0">Analysis Progress</h6>
              <button
                className="btn btn-sm btn-outline-danger"
                onClick={cancelAnalysis}
                title="Cancel Analysis"
              >
                <Icon icon={icons.times} className="me-1" />
                Cancel
              </button>
            </div>

            <ProgressIndicator
              steps={getProgressSteps()}
              title="Parameter Testing Analysis"
              showPercentage={true}
              percentage={progress}
              variant="horizontal"
              size="md"
            />

            {executionId && (
              <div className="mt-3">
                <small className="text-muted">
                  <Icon icon={icons.lastUpdated} className="me-1" />
                  Execution ID: {executionId}
                </small>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error Section */}
      {error && (
        <div
          className="alert alert-danger alert-dismissible fade show"
          role="alert"
        >
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
      <ErrorBoundary
        onError={(error, errorInfo) => {
          console.error('Results table error:', error, errorInfo);
        }}
      >
        <ResultsTable results={results} isLoading={isAnalyzing} error={error} />
      </ErrorBoundary>
    </div>
  );
};

export default ParameterTestingContainer;
