import React from 'react';
import {
  TrendingUp,
  Shield,
  AlertTriangle,
  CheckCircle,
  Target,
} from 'lucide-react';
import { RiskAllocation } from '../types';
import { useRiskAllocationMonitoring } from '../hooks/usePositionSizing';

interface RiskAllocationVisualizationProps {
  className?: string;
  showDetails?: boolean;
}

const RiskAllocationVisualization: React.FC<
  RiskAllocationVisualizationProps
> = ({ className = '', showDetails = true }) => {
  const { riskAllocation, isLoading, error } = useRiskAllocationMonitoring();

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getRiskLevelColor = (utilization: number) => {
    if (utilization <= 0.7) return 'text-green-600';
    if (utilization <= 0.9) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRiskLevelBg = (utilization: number) => {
    if (utilization <= 0.7) return 'bg-green-500';
    if (utilization <= 0.9) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getRiskStatus = (utilization: number) => {
    if (utilization <= 0.7)
      return { icon: CheckCircle, text: 'Conservative', color: 'green' };
    if (utilization <= 0.9)
      return { icon: AlertTriangle, text: 'Moderate', color: 'yellow' };
    return { icon: AlertTriangle, text: 'High Risk', color: 'red' };
  };

  if (isLoading) {
    return (
      <div
        className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}
      >
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading risk allocation...</span>
        </div>
      </div>
    );
  }

  if (error || !riskAllocation) {
    return (
      <div
        className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}
      >
        <div className="text-center text-red-600">
          <AlertTriangle size={48} className="mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Risk Data Unavailable</h3>
          <p className="text-sm">
            {error || 'Unable to load risk allocation data'}
          </p>
        </div>
      </div>
    );
  }

  const utilization = riskAllocation.utilization;
  const riskStatus = getRiskStatus(utilization);
  const StatusIcon = riskStatus.icon;

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Target className="text-blue-600" size={24} />
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                Risk Allocation
              </h3>
              <p className="text-sm text-gray-500">CVaR Target: 11.8%</p>
            </div>
          </div>
          <div
            className={`flex items-center space-x-2 ${getRiskLevelColor(
              utilization
            )}`}
          >
            <StatusIcon size={20} />
            <span className="font-medium">{riskStatus.text}</span>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Main Risk Gauge */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Current Risk Utilization
            </span>
            <span
              className={`text-lg font-bold ${getRiskLevelColor(utilization)}`}
            >
              {formatPercentage(utilization)}
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
            <div
              className={`h-3 rounded-full transition-all duration-500 ${getRiskLevelBg(
                utilization
              )}`}
              style={{ width: `${Math.min(utilization * 100, 100)}%` }}
            ></div>
          </div>

          {/* Target Line Indicator */}
          <div className="relative">
            <div className="absolute left-0 top-0 w-full h-1 bg-gray-100 rounded">
              <div
                className="absolute top-1/2 transform -translate-y-1/2 w-0.5 h-4 bg-blue-600"
                style={{ left: '100%' }}
              ></div>
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-2">
              <span>0%</span>
              <span className="text-blue-600 font-medium">Target: 11.8%</span>
            </div>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <TrendingUp className="text-blue-600" size={16} />
              <span className="text-sm font-medium text-gray-700">
                Current CVaR
              </span>
            </div>
            <div className="text-xl font-bold text-gray-900">
              {formatPercentage(riskAllocation.currentCVaR)}
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Shield className="text-green-600" size={16} />
              <span className="text-sm font-medium text-gray-700">
                Available Risk
              </span>
            </div>
            <div className="text-xl font-bold text-gray-900">
              {formatPercentage(riskAllocation.availableRisk)}
            </div>
          </div>
        </div>

        {/* Risk Amount */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-blue-900 mb-1">
                Total Risk Amount
              </h4>
              <p className="text-xs text-blue-700">
                Based on current portfolio CVaR
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-900">
                {formatCurrency(riskAllocation.riskAmount)}
              </div>
            </div>
          </div>
        </div>

        {showDetails && (
          <>
            {/* Risk Status Messages */}
            <div className="space-y-3">
              {utilization <= 0.7 && (
                <div className="bg-green-50 border border-green-200 rounded-md p-3">
                  <div className="flex">
                    <CheckCircle
                      className="text-green-400 mr-2 flex-shrink-0"
                      size={16}
                    />
                    <div>
                      <h4 className="text-sm font-medium text-green-800">
                        Conservative Risk Level
                      </h4>
                      <p className="text-sm text-green-700 mt-1">
                        You have{' '}
                        {formatCurrency(
                          riskAllocation.riskAmount * (1 - utilization)
                        )}{' '}
                        in additional risk capacity available.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {utilization > 0.7 && utilization <= 0.9 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                  <div className="flex">
                    <AlertTriangle
                      className="text-yellow-400 mr-2 flex-shrink-0"
                      size={16}
                    />
                    <div>
                      <h4 className="text-sm font-medium text-yellow-800">
                        Moderate Risk Level
                      </h4>
                      <p className="text-sm text-yellow-700 mt-1">
                        Approaching risk target. Consider position sizing
                        carefully for new trades.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {utilization > 0.9 && (
                <div className="bg-red-50 border border-red-200 rounded-md p-3">
                  <div className="flex">
                    <AlertTriangle
                      className="text-red-400 mr-2 flex-shrink-0"
                      size={16}
                    />
                    <div>
                      <h4 className="text-sm font-medium text-red-800">
                        High Risk Level
                      </h4>
                      <p className="text-sm text-red-700 mt-1">
                        {utilization >= 1.0
                          ? 'Risk target exceeded. Consider reducing position sizes or closing positions.'
                          : 'Very close to risk limit. New positions should be carefully evaluated.'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Risk Management Guidelines */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-900 mb-3">
                Risk Management Guidelines
              </h4>
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-1.5 flex-shrink-0"></div>
                  <span>
                    <strong>Conservative (&lt;70%):</strong> Room for additional
                    positions
                  </span>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mt-1.5 flex-shrink-0"></div>
                  <span>
                    <strong>Moderate (70-90%):</strong> Selective position
                    sizing
                  </span>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-1.5 flex-shrink-0"></div>
                  <span>
                    <strong>High (&gt;90%):</strong> Consider risk reduction
                  </span>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default RiskAllocationVisualization;
