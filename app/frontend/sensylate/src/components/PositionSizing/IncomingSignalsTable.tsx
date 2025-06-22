import React from 'react';
import { SignalAnalysis } from '../../types';
import Icon from '../Icon';
import { icons } from '../../utils/icons';

interface IncomingSignalsTableProps {
  signals: SignalAnalysis[];
  isLoading?: boolean;
}

const IncomingSignalsTable: React.FC<IncomingSignalsTableProps> = ({
  signals,
  isLoading = false,
}) => {
  const formatCurrency = (value: number | undefined) => {
    if (value === undefined || value === null || isNaN(value)) {
      return '$0';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatTime = (timestamp: string | undefined) => {
    if (!timestamp) return 'N/A';
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return 'Invalid time';
    }
  };

  const getSignalTypeBadge = (signalType: 'entry' | 'exit' | undefined) => {
    if (!signalType) return 'bg-secondary';
    return signalType === 'entry' ? 'bg-success' : 'bg-danger';
  };

  const getConfidenceBadge = (
    confidence: 'primary' | 'outlier' | undefined
  ) => {
    if (!confidence) return 'bg-secondary';
    return confidence === 'primary' ? 'bg-primary' : 'bg-warning';
  };

  const getSignalIcon = (signalType: 'entry' | 'exit' | undefined) => {
    if (!signalType) return icons.question;
    return signalType === 'entry' ? icons.add : icons.remove;
  };

  return (
    <div className="card h-100">
      <div className="card-header">
        <div className="d-flex justify-content-between align-items-center">
          <div className="d-flex align-items-center">
            <Icon icon={icons.notification} className="me-2" />
            <h6 className="mb-0">Incoming Signals</h6>
            <span className="badge bg-secondary ms-2">{signals.length}</span>
          </div>
          {signals.length > 0 && (
            <div className="badge bg-success">
              <Icon icon={icons.success} className="me-1" />
              Live
            </div>
          )}
        </div>
      </div>

      <div className="card-body p-0">
        {isLoading ? (
          <div className="d-flex justify-content-center align-items-center p-4">
            <Icon icon={icons.loading} className="fa-spin me-2" />
            Loading signals...
          </div>
        ) : signals.length === 0 ? (
          <div className="text-center p-4 text-muted">
            <Icon icon={icons.info} className="mb-2" size="2x" />
            <div>No incoming signals</div>
            <small>Signals will appear here when generated</small>
          </div>
        ) : (
          <div className="list-group list-group-flush">
            {signals.map((signal, index) => (
              <div key={index} className="list-group-item">
                <div className="d-flex justify-content-between align-items-start">
                  <div className="flex-grow-1">
                    {/* Signal Header */}
                    <div className="d-flex align-items-center mb-2">
                      <Icon
                        icon={getSignalIcon(signal.signalType)}
                        className={`me-2 ${
                          signal.signalType === 'entry'
                            ? 'text-success'
                            : signal.signalType === 'exit'
                              ? 'text-danger'
                              : 'text-muted'
                        }`}
                      />
                      <span className="fw-bold">{signal.symbol}</span>
                      <span
                        className={`badge ${getSignalTypeBadge(
                          signal.signalType
                        )} ms-2`}
                      >
                        {signal.signalType?.toUpperCase() || 'UNKNOWN'}
                      </span>
                      <span
                        className={`badge ${getConfidenceBadge(
                          signal.confidence
                        )} ms-1`}
                      >
                        {signal.confidence}
                      </span>
                    </div>

                    {/* Signal Details */}
                    <div className="row g-2 small">
                      <div className="col-6">
                        <div className="text-muted">Signal Price</div>
                        <div className="fw-bold">
                          {formatCurrency(signal.price)}
                        </div>
                      </div>
                      <div className="col-6">
                        <div className="text-muted">Position Size</div>
                        <div className="fw-bold">
                          {signal.recommendedSize?.toFixed(4) || '0.0000'}
                        </div>
                      </div>
                      <div className="col-6">
                        <div className="text-muted">Position Value</div>
                        <div className="fw-bold text-primary">
                          {formatCurrency(signal.positionValue)}
                        </div>
                      </div>
                      <div className="col-6">
                        <div className="text-muted">Risk Amount</div>
                        <div className="fw-bold text-danger">
                          {formatCurrency(signal.riskAmount)}
                        </div>
                      </div>
                    </div>

                    {/* Timestamp */}
                    <div className="mt-2">
                      <small className="text-muted">
                        <Icon icon={icons.lastUpdated} className="me-1" />
                        {formatTime(signal.timestamp)}
                      </small>
                    </div>
                  </div>

                  {/* Action Button */}
                  <div className="ms-3">
                    <button
                      className={`btn btn-sm ${
                        signal.signalType === 'entry'
                          ? 'btn-outline-success'
                          : signal.signalType === 'exit'
                            ? 'btn-outline-danger'
                            : 'btn-outline-secondary'
                      }`}
                      title={`Execute ${signal.signalType || 'unknown'} signal`}
                    >
                      <Icon icon={icons.parameterTesting} />
                    </button>
                  </div>
                </div>

                {/* Progress Bar for Position Value vs Risk */}
                <div className="mt-2">
                  <div className="d-flex justify-content-between align-items-center mb-1">
                    <small className="text-muted">Risk/Reward Ratio</small>
                    <small className="text-muted">
                      {signal.positionValue > 0
                        ? (
                            (signal.riskAmount / signal.positionValue) *
                            100
                          ).toFixed(1) + '%'
                        : '0%'}
                    </small>
                  </div>
                  <div className="progress" style={{ height: '4px' }}>
                    <div
                      className="progress-bar bg-danger"
                      style={{
                        width:
                          signal.positionValue > 0
                            ? `${Math.min(
                                (signal.riskAmount / signal.positionValue) *
                                  100,
                                100
                              )}%`
                            : '0%',
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer with Summary */}
      {signals.length > 0 && (
        <div className="card-footer bg-light">
          <div className="row text-center small">
            <div className="col-6">
              <div className="text-muted">Entry Signals</div>
              <div className="fw-bold text-success">
                {signals.filter((s) => s.signalType === 'entry').length}
              </div>
            </div>
            <div className="col-6">
              <div className="text-muted">Exit Signals</div>
              <div className="fw-bold text-danger">
                {signals.filter((s) => s.signalType === 'exit').length}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IncomingSignalsTable;
