import React, { useState, useMemo } from 'react';
import {
  PieChart,
  BarChart3,
  TrendingUp,
  Shield,
  PiggyBank,
  DollarSign,
  Percent,
  Hash,
} from 'lucide-react';
import { TradingPosition } from '../types';
import { useActivePositions } from '../hooks/usePositionSizing';

interface PortfolioSegment {
  name: string;
  value: number;
  count: number;
  percentage: number;
  color: string;
  icon: React.ReactNode;
}

interface CompositionMetrics {
  totalValue: number;
  totalPositions: number;
  averagePositionSize: number;
  largestPosition: number;
  smallestPosition: number;
  portfolioConcentration: number; // Top 5 positions as % of total
}

interface PortfolioCompositionVisualizerProps {
  className?: string;
  viewMode?: 'portfolio' | 'size' | 'status';
}

const PortfolioCompositionVisualizer: React.FC<
  PortfolioCompositionVisualizerProps
> = ({ className = '', viewMode: initialViewMode = 'portfolio' }) => {
  const { positions, isLoading, error } = useActivePositions();
  const [viewMode, setViewMode] = useState<'portfolio' | 'size' | 'status'>(
    initialViewMode
  );
  const [chartType, setChartType] = useState<'pie' | 'bar'>('pie');

  const compositionData = useMemo(() => {
    if (!positions.length) return { segments: [], metrics: null };

    const totalValue = positions.reduce(
      (sum, pos) => sum + (pos.manualPositionSize || pos.positionValue || 0),
      0
    );

    let segments: PortfolioSegment[] = [];

    if (viewMode === 'portfolio') {
      // Group by portfolio type
      const portfolioGroups = positions.reduce(
        (groups, pos) => {
          const portfolio = pos.portfolioType || 'Risk_On';
          if (!groups[portfolio]) {
            groups[portfolio] = { positions: [], value: 0 };
          }
          groups[portfolio].positions.push(pos);
          groups[portfolio].value +=
            pos.manualPositionSize || pos.positionValue || 0;
          return groups;
        },
        {} as Record<string, { positions: TradingPosition[]; value: number }>
      );

      segments = Object.entries(portfolioGroups).map(([portfolio, data]) => ({
        name: portfolio.replace('_', ' ') + ' Portfolio',
        value: data.value,
        count: data.positions.length,
        percentage: (data.value / totalValue) * 100,
        color:
          portfolio === 'Risk_On'
            ? '#ef4444'
            : portfolio === 'Protected'
              ? '#3b82f6'
              : '#10b981',
        icon:
          portfolio === 'Risk_On' ? (
            <TrendingUp size={16} />
          ) : portfolio === 'Protected' ? (
            <Shield size={16} />
          ) : (
            <PiggyBank size={16} />
          ),
      }));
    } else if (viewMode === 'size') {
      // Group by position size ranges
      const sizeRanges = [
        { name: 'Large (>$50K)', min: 50000, max: Infinity, color: '#ef4444' },
        {
          name: 'Medium ($10K-$50K)',
          min: 10000,
          max: 50000,
          color: '#f59e0b',
        },
        { name: 'Small (<$10K)', min: 0, max: 10000, color: '#10b981' },
      ];

      segments = sizeRanges
        .map((range) => {
          const rangePositions = positions.filter((pos) => {
            const size = pos.manualPositionSize || pos.positionValue || 0;
            return size >= range.min && size < range.max;
          });
          const value = rangePositions.reduce(
            (sum, pos) =>
              sum + (pos.manualPositionSize || pos.positionValue || 0),
            0
          );

          return {
            name: range.name,
            value,
            count: rangePositions.length,
            percentage: (value / totalValue) * 100,
            color: range.color,
            icon: <DollarSign size={16} />,
          };
        })
        .filter((segment) => segment.count > 0);
    } else {
      // Group by status
      const statusGroups = positions.reduce(
        (groups, pos) => {
          const status = pos.currentStatus || 'Unknown';
          if (!groups[status]) {
            groups[status] = { positions: [], value: 0 };
          }
          groups[status].positions.push(pos);
          groups[status].value +=
            pos.manualPositionSize || pos.positionValue || 0;
          return groups;
        },
        {} as Record<string, { positions: TradingPosition[]; value: number }>
      );

      segments = Object.entries(statusGroups).map(([status, data]) => ({
        name: status,
        value: data.value,
        count: data.positions.length,
        percentage: (data.value / totalValue) * 100,
        color:
          status === 'Active'
            ? '#10b981'
            : status === 'Pending'
              ? '#f59e0b'
              : '#6b7280',
        icon: <Hash size={16} />,
      }));
    }

    // Calculate metrics
    const positionSizes = positions.map(
      (pos) => pos.manualPositionSize || pos.positionValue || 0
    );
    const sortedSizes = positionSizes.sort((a, b) => b - a);
    const top5Value = sortedSizes
      .slice(0, 5)
      .reduce((sum, size) => sum + size, 0);

    const metrics: CompositionMetrics = {
      totalValue,
      totalPositions: positions.length,
      averagePositionSize: totalValue / positions.length,
      largestPosition: Math.max(...positionSizes),
      smallestPosition: Math.min(...positionSizes),
      portfolioConcentration: (top5Value / totalValue) * 100,
    };

    return { segments, metrics };
  }, [positions, viewMode]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const renderPieChart = () => {
    if (compositionData.segments.length === 0) return null;

    const radius = 100;
    const centerX = 120;
    const centerY = 120;
    let currentAngle = 0;

    return (
      <div className="flex items-center justify-center">
        <svg width="240" height="240" className="drop-shadow-sm">
          {compositionData.segments.map((segment, index) => {
            const angle = (segment.percentage / 100) * 360;
            const startAngle = currentAngle;
            const endAngle = currentAngle + angle;

            const startX =
              centerX + radius * Math.cos(((startAngle - 90) * Math.PI) / 180);
            const startY =
              centerY + radius * Math.sin(((startAngle - 90) * Math.PI) / 180);
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
                fill={segment.color}
                className="hover:opacity-80 transition-opacity cursor-pointer"
                stroke="white"
                strokeWidth="2"
              >
                <title>
                  {segment.name}: {segment.percentage.toFixed(1)}% (
                  {formatCurrency(segment.value)})
                </title>
              </path>
            );
          })}

          {/* Center circle with total */}
          <circle
            cx={centerX}
            cy={centerY}
            r="35"
            fill="white"
            stroke="#e5e7eb"
            strokeWidth="2"
          />
          <text
            x={centerX}
            y={centerY - 8}
            className="text-sm font-medium fill-gray-900"
            textAnchor="middle"
          >
            Total
          </text>
          <text
            x={centerX}
            y={centerY + 8}
            className="text-xs fill-gray-600"
            textAnchor="middle"
          >
            {compositionData.segments.reduce((sum, s) => sum + s.count, 0)}{' '}
            positions
          </text>
        </svg>
      </div>
    );
  };

  const renderBarChart = () => {
    if (compositionData.segments.length === 0) return null;

    const maxValue = Math.max(...compositionData.segments.map((s) => s.value));

    return (
      <div className="space-y-4">
        {compositionData.segments.map((segment, index) => (
          <div key={index} className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div style={{ color: segment.color }}>{segment.icon}</div>
                <span className="text-sm font-medium text-gray-900">
                  {segment.name}
                </span>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900">
                  {formatCurrency(segment.value)}
                </div>
                <div className="text-xs text-gray-500">
                  {segment.percentage.toFixed(1)}% • {segment.count} positions
                </div>
              </div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="h-3 rounded-full transition-all duration-500"
                style={{
                  backgroundColor: segment.color,
                  width: `${(segment.value / maxValue) * 100}%`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div
        className={`bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center ${className}`}
      >
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <span className="text-gray-600">Loading portfolio composition...</span>
      </div>
    );
  }

  if (error || compositionData.segments.length === 0) {
    return (
      <div
        className={`bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center ${className}`}
      >
        <PieChart size={48} className="mx-auto mb-4 text-gray-300" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No Portfolio Data
        </h3>
        <p className="text-sm text-gray-600">
          {error
            ? 'Unable to load portfolio data'
            : 'Add positions to see composition analysis'}
        </p>
      </div>
    );
  }

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Portfolio Composition
            </h3>
            <p className="text-sm text-gray-500">
              {formatCurrency(compositionData.metrics?.totalValue || 0)} across{' '}
              {compositionData.metrics?.totalPositions || 0} positions
            </p>
          </div>
          <div className="flex items-center space-x-2">
            {/* View Mode Toggle */}
            <select
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value as typeof viewMode)}
              className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="portfolio">By Portfolio</option>
              <option value="size">By Size</option>
              <option value="status">By Status</option>
            </select>

            {/* Chart Type Toggle */}
            <div className="flex border border-gray-300 rounded">
              <button
                onClick={() => setChartType('pie')}
                className={`px-2 py-1 text-sm ${
                  chartType === 'pie'
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                <PieChart size={16} />
              </button>
              <button
                onClick={() => setChartType('bar')}
                className={`px-2 py-1 text-sm border-l border-gray-300 ${
                  chartType === 'bar'
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                <BarChart3 size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Chart */}
          <div>{chartType === 'pie' ? renderPieChart() : renderBarChart()}</div>

          {/* Legend and Details */}
          <div className="space-y-6">
            {/* Legend */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">
                Breakdown
              </h4>
              <div className="space-y-3">
                {compositionData.segments.map((segment, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: segment.color }}
                        />
                        <div style={{ color: segment.color }}>
                          {segment.icon}
                        </div>
                      </div>
                      <span className="text-sm font-medium text-gray-900">
                        {segment.name}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {segment.percentage.toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500">
                        {segment.count} pos.
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Key Metrics */}
            {compositionData.metrics && (
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">
                  Key Metrics
                </h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      Average Position Size
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {formatCurrency(
                        compositionData.metrics.averagePositionSize
                      )}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      Largest Position
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {formatCurrency(compositionData.metrics.largestPosition)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      Smallest Position
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {formatCurrency(compositionData.metrics.smallestPosition)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      Top 5 Concentration
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {compositionData.metrics.portfolioConcentration.toFixed(
                        1
                      )}
                      %
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioCompositionVisualizer;
