import React, { useState, useEffect, useMemo } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  AlertTriangle,
  Target,
  PieChart,
  Calendar,
} from 'lucide-react';
import {
  useRiskAllocationMonitoring,
  useActivePositions,
} from '../hooks/usePositionSizing';

interface RiskTrendData {
  timestamp: Date;
  cvarValue: number;
  utilization: number;
  riskAmount: number;
}

interface PortfolioAllocation {
  portfolioType: string;
  count: number;
  totalValue: number;
  riskContribution: number;
  color: string;
}

interface AdvancedRiskDashboardProps {
  className?: string;
  timeRange?: '1D' | '7D' | '30D' | '90D';
}

const AdvancedRiskDashboard: React.FC<AdvancedRiskDashboardProps> = ({
  className = '',
  timeRange = '7D',
}) => {
  const { riskAllocation, isLoading, error } = useRiskAllocationMonitoring();
  const { positions } = useActivePositions();

  const [selectedChart, setSelectedChart] = useState<
    'trend' | 'allocation' | 'composition'
  >('trend');
  const [trendData, setTrendData] = useState<RiskTrendData[]>([]);

  // Generate mock historical data for demonstration
  useEffect(() => {
    const generateTrendData = () => {
      const now = new Date();
      const data: RiskTrendData[] = [];
      const periods =
        timeRange === '1D'
          ? 24
          : timeRange === '7D'
            ? 7
            : timeRange === '30D'
              ? 30
              : 90;
      const interval =
        timeRange === '1D' ? 60 * 60 * 1000 : 24 * 60 * 60 * 1000; // 1 hour or 1 day

      for (let i = periods; i >= 0; i--) {
        const timestamp = new Date(now.getTime() - i * interval);
        const baseValue = 0.08;
        const variation = (Math.random() - 0.5) * 0.04; // ±2% variation
        const cvarValue = Math.max(0, Math.min(0.15, baseValue + variation));

        data.push({
          timestamp,
          cvarValue,
          utilization: cvarValue / 0.118,
          riskAmount: cvarValue * 1000000, // Assuming $1M portfolio
        });
      }

      // Add current real data if available
      if (riskAllocation) {
        data[data.length - 1] = {
          timestamp: now,
          cvarValue: riskAllocation.currentCVaR,
          utilization: riskAllocation.utilization,
          riskAmount: riskAllocation.riskAmount,
        };
      }

      setTrendData(data);
    };

    generateTrendData();
  }, [timeRange, riskAllocation]);

  const portfolioAllocations = useMemo((): PortfolioAllocation[] => {
    if (!positions.length) return [];

    const allocations = positions.reduce((acc, position) => {
      const portfolioType = position.portfolioType || 'Risk_On';
      const existing = acc.find((a) => a.portfolioType === portfolioType);

      if (existing) {
        existing.count += 1;
        existing.totalValue +=
          position.manualPositionSize || position.positionValue || 0;
        existing.riskContribution +=
          (position.manualPositionSize || position.positionValue || 0) * 0.02; // Estimated risk
      } else {
        acc.push({
          portfolioType,
          count: 1,
          totalValue:
            position.manualPositionSize || position.positionValue || 0,
          riskContribution:
            (position.manualPositionSize || position.positionValue || 0) * 0.02,
          color:
            portfolioType === 'Risk_On'
              ? '#ef4444'
              : portfolioType === 'Protected'
                ? '#3b82f6'
                : '#10b981',
        });
      }
      return acc;
    }, [] as PortfolioAllocation[]);

    return allocations;
  }, [positions]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const getTrendDirection = () => {
    if (trendData.length < 2) return 'neutral';
    const current = trendData[trendData.length - 1];
    const previous = trendData[trendData.length - 2];
    if (current.cvarValue > previous.cvarValue) return 'up';
    if (current.cvarValue < previous.cvarValue) return 'down';
    return 'neutral';
  };

  const trendDirection = getTrendDirection();

  const renderTrendChart = () => {
    if (trendData.length === 0) return null;

    const maxValue = Math.max(...trendData.map((d) => d.cvarValue));
    const minValue = Math.min(...trendData.map((d) => d.cvarValue));
    const range = maxValue - minValue || 0.01;
    const target = 0.118;

    const width = 800;
    const height = 300;
    const padding = 40;
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;

    const getX = (index: number) =>
      padding + (index / (trendData.length - 1)) * chartWidth;
    const getY = (value: number) =>
      padding + (1 - (value - minValue) / range) * chartHeight;

    const pathData = trendData
      .map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(d.cvarValue)}`)
      .join(' ');
    const targetY = getY(target);

    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-medium text-gray-900">CVaR Trend</h4>
          <div className="flex space-x-2">
            {(['1D', '7D', '30D', '90D'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setSelectedChart('trend')}
                className={`px-3 py-1 text-sm rounded ${
                  timeRange === range
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        <svg width={width} height={height} className="w-full">
          {/* Grid lines */}
          <defs>
            <pattern
              id="grid"
              width="40"
              height="30"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M 40 0 L 0 0 0 30"
                fill="none"
                stroke="#f3f4f6"
                strokeWidth="1"
              />
            </pattern>
          </defs>
          <rect width={width} height={height} fill="url(#grid)" />

          {/* Target line */}
          <line
            x1={padding}
            y1={targetY}
            x2={width - padding}
            y2={targetY}
            stroke="#3b82f6"
            strokeWidth="2"
            strokeDasharray="5,5"
          />
          <text
            x={width - padding + 5}
            y={targetY + 5}
            className="text-xs fill-blue-600"
          >
            Target 11.8%
          </text>

          {/* CVaR line */}
          <path d={pathData} fill="none" stroke="#ef4444" strokeWidth="3" />

          {/* Data points */}
          {trendData.map((d, i) => (
            <circle
              key={i}
              cx={getX(i)}
              cy={getY(d.cvarValue)}
              r="4"
              fill="#ef4444"
              className="hover:r-6 transition-all"
            >
              <title>{`${d.timestamp.toLocaleDateString()}: ${formatPercentage(
                d.cvarValue
              )}`}</title>
            </circle>
          ))}

          {/* Y-axis labels */}
          {[0, 0.05, 0.1, 0.15].map((value) => (
            <text
              key={value}
              x={padding - 10}
              y={getY(value) + 5}
              className="text-xs fill-gray-600"
              textAnchor="end"
            >
              {formatPercentage(value)}
            </text>
          ))}
        </svg>
      </div>
    );
  };

  const renderAllocationChart = () => {
    if (portfolioAllocations.length === 0) return null;

    const total = portfolioAllocations.reduce(
      (sum, alloc) => sum + alloc.totalValue,
      0
    );
    let currentAngle = 0;
    const radius = 80;
    const centerX = 120;
    const centerY = 120;

    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h4 className="text-lg font-medium text-gray-900 mb-4">
          Portfolio Allocation
        </h4>

        <div className="flex items-center space-x-8">
          <svg width="240" height="240">
            {portfolioAllocations.map((alloc, index) => {
              const percentage = alloc.totalValue / total;
              const angle = percentage * 360;
              const startAngle = currentAngle;
              const endAngle = currentAngle + angle;

              const startX =
                centerX +
                radius * Math.cos(((startAngle - 90) * Math.PI) / 180);
              const startY =
                centerY +
                radius * Math.sin(((startAngle - 90) * Math.PI) / 180);
              const endX =
                centerX + radius * Math.cos(((endAngle - 90) * Math.PI) / 180);
              const endY =
                centerY + radius * Math.sin(((endAngle - 90) * Math.PI) / 180);

              const largeArcFlag = angle > 180 ? 1 : 0;

              const pathData = [
                `M ${centerX} ${centerY}`,
                `L ${startX} ${startY}`,
                `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${endX} ${endY}`,
                'Z',
              ].join(' ');

              currentAngle += angle;

              return (
                <path
                  key={index}
                  d={pathData}
                  fill={alloc.color}
                  className="hover:opacity-80 transition-opacity"
                >
                  <title>{`${alloc.portfolioType}: ${formatPercentage(
                    percentage
                  )} (${formatCurrency(alloc.totalValue)})`}</title>
                </path>
              );
            })}

            {/* Center circle */}
            <circle
              cx={centerX}
              cy={centerY}
              r="30"
              fill="white"
              stroke="#e5e7eb"
              strokeWidth="2"
            />
            <text
              x={centerX}
              y={centerY - 5}
              className="text-sm fill-gray-600"
              textAnchor="middle"
            >
              Total
            </text>
            <text
              x={centerX}
              y={centerY + 10}
              className="text-xs fill-gray-500"
              textAnchor="middle"
            >
              {formatCurrency(total)}
            </text>
          </svg>

          <div className="space-y-3">
            {portfolioAllocations.map((alloc, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: alloc.color }}
                ></div>
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {alloc.portfolioType.replace('_', ' ')} Portfolio
                  </div>
                  <div className="text-xs text-gray-500">
                    {alloc.count} positions • {formatCurrency(alloc.totalValue)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderCompositionChart = () => {
    if (portfolioAllocations.length === 0) return null;

    const maxValue = Math.max(...portfolioAllocations.map((a) => a.totalValue));

    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h4 className="text-lg font-medium text-gray-900 mb-4">
          Portfolio Composition
        </h4>

        <div className="space-y-4">
          {portfolioAllocations.map((alloc, index) => (
            <div key={index} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  {alloc.portfolioType.replace('_', ' ')} Portfolio
                </span>
                <span className="text-sm text-gray-500">
                  {formatCurrency(alloc.totalValue)} ({alloc.count} positions)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="h-3 rounded-full transition-all duration-500"
                  style={{
                    backgroundColor: alloc.color,
                    width: `${(alloc.totalValue / maxValue) * 100}%`,
                  }}
                ></div>
              </div>
              <div className="text-xs text-gray-500">
                Risk Contribution: {formatCurrency(alloc.riskContribution)}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div
        className={`bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center ${className}`}
      >
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <span className="text-gray-600">
          Loading advanced risk analytics...
        </span>
      </div>
    );
  }

  if (error || !riskAllocation) {
    return (
      <div
        className={`bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center ${className}`}
      >
        <AlertTriangle size={48} className="mx-auto mb-4 text-red-400" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Analytics Unavailable
        </h3>
        <p className="text-sm text-gray-600">
          {error || 'Unable to load risk analytics'}
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header with Key Metrics */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Advanced Risk Analytics
            </h2>
            <p className="text-gray-500">
              Real-time portfolio risk monitoring and analysis
            </p>
          </div>
          <div
            className={`flex items-center space-x-2 ${
              trendDirection === 'up'
                ? 'text-red-600'
                : trendDirection === 'down'
                  ? 'text-green-600'
                  : 'text-gray-600'
            }`}
          >
            {trendDirection === 'up' ? (
              <TrendingUp size={24} />
            ) : trendDirection === 'down' ? (
              <TrendingDown size={24} />
            ) : (
              <Activity size={24} />
            )}
            <span className="font-medium">
              {trendDirection === 'up'
                ? 'Risk Increasing'
                : trendDirection === 'down'
                  ? 'Risk Decreasing'
                  : 'Risk Stable'}
            </span>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">
              {formatPercentage(riskAllocation.currentCVaR)}
            </div>
            <div className="text-sm text-gray-500">Current CVaR</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900">
              {formatPercentage(riskAllocation.utilization)}
            </div>
            <div className="text-sm text-gray-500">Target Utilization</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">
              {formatCurrency(riskAllocation.riskAmount)}
            </div>
            <div className="text-sm text-gray-500">Risk Amount</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600">
              {positions.length}
            </div>
            <div className="text-sm text-gray-500">Active Positions</div>
          </div>
        </div>
      </div>

      {/* Chart Selection */}
      <div className="flex space-x-4">
        <button
          onClick={() => setSelectedChart('trend')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
            selectedChart === 'trend'
              ? 'bg-blue-50 border-blue-200 text-blue-700'
              : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Activity size={16} />
          <span>Risk Trend</span>
        </button>
        <button
          onClick={() => setSelectedChart('allocation')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
            selectedChart === 'allocation'
              ? 'bg-blue-50 border-blue-200 text-blue-700'
              : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
          }`}
        >
          <PieChart size={16} />
          <span>Allocation</span>
        </button>
        <button
          onClick={() => setSelectedChart('composition')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
            selectedChart === 'composition'
              ? 'bg-blue-50 border-blue-200 text-blue-700'
              : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
          }`}
        >
          <BarChart3 size={16} />
          <span>Composition</span>
        </button>
      </div>

      {/* Selected Chart */}
      {selectedChart === 'trend' && renderTrendChart()}
      {selectedChart === 'allocation' && renderAllocationChart()}
      {selectedChart === 'composition' && renderCompositionChart()}
    </div>
  );
};

export default AdvancedRiskDashboard;
