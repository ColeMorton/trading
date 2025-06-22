import React, { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  Info,
  X,
  Bell,
  BellOff,
  Settings,
  TrendingUp,
} from 'lucide-react';
import { RiskAllocation } from '../types';
import { useRiskAllocationMonitoring } from '../hooks/usePositionSizing';

interface RiskAlert {
  id: string;
  type: 'warning' | 'error' | 'info' | 'success';
  title: string;
  message: string;
  timestamp: Date;
  threshold?: number;
  currentValue?: number;
  dismissed?: boolean;
  persistent?: boolean;
}

interface AlertThresholds {
  warningLevel: number; // Default: 0.8 (80% of target)
  criticalLevel: number; // Default: 1.0 (100% of target)
  excessiveLevel: number; // Default: 1.2 (120% of target)
}

interface RiskMonitoringAlertsProps {
  className?: string;
  maxAlerts?: number;
  showSettings?: boolean;
}

const RiskMonitoringAlerts: React.FC<RiskMonitoringAlertsProps> = ({
  className = '',
  maxAlerts = 5,
  showSettings = true,
}) => {
  const { riskAllocation, isLoading, error } = useRiskAllocationMonitoring();

  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);
  const [thresholds, setThresholds] = useState<AlertThresholds>({
    warningLevel: 0.8,
    criticalLevel: 1.0,
    excessiveLevel: 1.2,
  });

  const [previousRiskLevel, setPreviousRiskLevel] = useState<number | null>(
    null
  );

  // Generate alerts based on risk allocation changes
  const generateAlerts = useCallback(
    (current: RiskAllocation, previous?: number) => {
      const newAlerts: RiskAlert[] = [];
      const utilization = current.utilization;
      const now = new Date();

      // Risk level threshold alerts
      if (utilization >= thresholds.excessiveLevel) {
        newAlerts.push({
          id: `excessive-risk-${now.getTime()}`,
          type: 'error',
          title: 'Excessive Risk Level',
          message: `Portfolio risk is ${(utilization * 100).toFixed(
            1
          )}% of target (${(thresholds.excessiveLevel * 100).toFixed(
            0
          )}%+). Immediate action required.`,
          timestamp: now,
          threshold: thresholds.excessiveLevel,
          currentValue: utilization,
          persistent: true,
        });
      } else if (utilization >= thresholds.criticalLevel) {
        newAlerts.push({
          id: `critical-risk-${now.getTime()}`,
          type: 'error',
          title: 'Critical Risk Level',
          message: `Portfolio has reached ${(utilization * 100).toFixed(
            1
          )}% of CVaR target. Consider reducing positions.`,
          timestamp: now,
          threshold: thresholds.criticalLevel,
          currentValue: utilization,
          persistent: true,
        });
      } else if (utilization >= thresholds.warningLevel) {
        newAlerts.push({
          id: `warning-risk-${now.getTime()}`,
          type: 'warning',
          title: 'Elevated Risk Level',
          message: `Portfolio risk at ${(utilization * 100).toFixed(
            1
          )}% of target. Monitor position sizing.`,
          timestamp: now,
          threshold: thresholds.warningLevel,
          currentValue: utilization,
        });
      }

      // Risk trend alerts
      if (previous !== null && previous !== undefined) {
        const riskChange = utilization - previous;
        const changePercent = Math.abs(riskChange) * 100;

        if (changePercent > 10) {
          // 10% change threshold
          newAlerts.push({
            id: `risk-change-${now.getTime()}`,
            type: riskChange > 0 ? 'warning' : 'info',
            title: riskChange > 0 ? 'Risk Increasing' : 'Risk Decreasing',
            message: `Portfolio risk ${
              riskChange > 0 ? 'increased' : 'decreased'
            } by ${changePercent.toFixed(1)}% since last update.`,
            timestamp: now,
            currentValue: utilization,
          });
        }
      }

      // Portfolio capacity alerts
      const remainingCapacity = 1 - utilization;
      if (remainingCapacity < 0.1 && remainingCapacity > 0) {
        // Less than 10% capacity
        newAlerts.push({
          id: `low-capacity-${now.getTime()}`,
          type: 'warning',
          title: 'Low Risk Capacity',
          message: `Only ${(remainingCapacity * 100).toFixed(
            1
          )}% risk capacity remaining. New positions will require careful sizing.`,
          timestamp: now,
          currentValue: remainingCapacity,
        });
      }

      return newAlerts;
    },
    [thresholds]
  );

  // Monitor risk allocation changes
  useEffect(() => {
    if (!riskAllocation || !alertsEnabled) return;

    const newAlerts = generateAlerts(riskAllocation, previousRiskLevel);

    if (newAlerts.length > 0) {
      setAlerts((prev) => {
        // Remove non-persistent alerts of same type
        const filtered = prev.filter(
          (alert) =>
            alert.persistent ||
            !newAlerts.some(
              (newAlert) =>
                newAlert.type === alert.type && newAlert.title === alert.title
            )
        );

        // Add new alerts
        const combined = [...filtered, ...newAlerts];

        // Keep only the most recent alerts
        const sorted = combined
          .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
          .slice(0, maxAlerts);

        return sorted;
      });
    }

    setPreviousRiskLevel(riskAllocation.utilization);
  }, [
    riskAllocation,
    alertsEnabled,
    generateAlerts,
    maxAlerts,
    previousRiskLevel,
  ]);

  const dismissAlert = (alertId: string) => {
    setAlerts((prev) =>
      prev.map((alert) =>
        alert.id === alertId ? { ...alert, dismissed: true } : alert
      )
    );
  };

  const clearAllAlerts = () => {
    setAlerts([]);
  };

  const getAlertIcon = (type: RiskAlert['type']) => {
    switch (type) {
      case 'error':
        return <AlertTriangle className="text-red-500" size={20} />;
      case 'warning':
        return <AlertTriangle className="text-yellow-500" size={20} />;
      case 'info':
        return <Info className="text-blue-500" size={20} />;
      case 'success':
        return <CheckCircle className="text-green-500" size={20} />;
    }
  };

  const getAlertBorderColor = (type: RiskAlert['type']) => {
    switch (type) {
      case 'error':
        return 'border-red-200 bg-red-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      case 'info':
        return 'border-blue-200 bg-blue-50';
      case 'success':
        return 'border-green-200 bg-green-50';
    }
  };

  const formatTime = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  const activeAlerts = alerts.filter((alert) => !alert.dismissed);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div
              className={`p-2 rounded-lg ${
                alertsEnabled ? 'bg-blue-100' : 'bg-gray-100'
              }`}
            >
              {alertsEnabled ? (
                <Bell className="text-blue-600" size={20} />
              ) : (
                <BellOff className="text-gray-600" size={20} />
              )}
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                Risk Monitoring
              </h3>
              <p className="text-sm text-gray-500">
                {activeAlerts.length} active alert
                {activeAlerts.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setAlertsEnabled(!alertsEnabled)}
              className={`px-3 py-1 text-sm rounded-md border transition-colors ${
                alertsEnabled
                  ? 'bg-blue-50 border-blue-200 text-blue-700'
                  : 'bg-gray-50 border-gray-200 text-gray-600'
              }`}
            >
              {alertsEnabled ? 'Enabled' : 'Disabled'}
            </button>

            {showSettings && (
              <button
                onClick={() => setShowSettingsPanel(!showSettingsPanel)}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                title="Alert Settings"
              >
                <Settings size={16} />
              </button>
            )}

            {activeAlerts.length > 0 && (
              <button
                onClick={clearAllAlerts}
                className="px-3 py-1 text-sm text-red-600 hover:text-red-800 transition-colors"
              >
                Clear All
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettingsPanel && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <h4 className="text-md font-medium text-gray-900 mb-4">
            Alert Thresholds
          </h4>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Warning Level
              </label>
              <div className="relative">
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={thresholds.warningLevel}
                  onChange={(e) =>
                    setThresholds((prev) => ({
                      ...prev,
                      warningLevel: parseFloat(e.target.value),
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-sm text-gray-500">
                  ({(thresholds.warningLevel * 100).toFixed(0)}%)
                </span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Critical Level
              </label>
              <div className="relative">
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={thresholds.criticalLevel}
                  onChange={(e) =>
                    setThresholds((prev) => ({
                      ...prev,
                      criticalLevel: parseFloat(e.target.value),
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-sm text-gray-500">
                  ({(thresholds.criticalLevel * 100).toFixed(0)}%)
                </span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Excessive Level
              </label>
              <div className="relative">
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={thresholds.excessiveLevel}
                  onChange={(e) =>
                    setThresholds((prev) => ({
                      ...prev,
                      excessiveLevel: parseFloat(e.target.value),
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-sm text-gray-500">
                  ({(thresholds.excessiveLevel * 100).toFixed(0)}%)
                </span>
              </div>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Thresholds are based on percentage of 11.8% CVaR target. For
            example, 1.0 = 100% of target (11.8%).
          </p>
        </div>
      )}

      {/* Alerts List */}
      {isLoading ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <span className="text-sm text-gray-600">Loading alerts...</span>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <AlertTriangle
              className="text-red-400 mr-3 flex-shrink-0"
              size={20}
            />
            <div>
              <h4 className="text-sm font-medium text-red-800">
                Alert System Error
              </h4>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      ) : activeAlerts.length === 0 ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <CheckCircle className="text-green-500 mx-auto mb-2" size={24} />
          <h4 className="text-sm font-medium text-green-800">All Clear</h4>
          <p className="text-sm text-green-700 mt-1">
            No active risk alerts. Portfolio is within normal parameters.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {activeAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`border rounded-lg p-4 ${getAlertBorderColor(
                alert.type
              )}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  {getAlertIcon(alert.type)}
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-1">
                      {alert.title}
                    </h4>
                    <p className="text-sm text-gray-700 mb-2">
                      {alert.message}
                    </p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>{formatTime(alert.timestamp)}</span>
                      {alert.currentValue && (
                        <span>
                          Current: {(alert.currentValue * 100).toFixed(1)}%
                        </span>
                      )}
                      {alert.threshold && (
                        <span>
                          Threshold: {(alert.threshold * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {!alert.persistent && (
                  <button
                    onClick={() => dismissAlert(alert.id)}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                    title="Dismiss alert"
                  >
                    <X size={16} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Current Status Summary */}
      {riskAllocation && alertsEnabled && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <TrendingUp className="text-gray-600" size={16} />
            <div className="text-sm text-gray-700">
              <span className="font-medium">Current Status:</span> Portfolio
              utilizing{' '}
              <span className="font-medium">
                {(riskAllocation.utilization * 100).toFixed(1)}%
              </span>{' '}
              of 11.8% CVaR target (
              {(riskAllocation.currentCVaR * 100).toFixed(1)}% CVaR)
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskMonitoringAlerts;
