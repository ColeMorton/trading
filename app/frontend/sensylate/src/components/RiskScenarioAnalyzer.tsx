import React, { useState, useMemo } from 'react';
import {
  Calculator,
  TrendingDown,
  AlertTriangle,
  BarChart3,
  Play,
  RotateCcw,
} from 'lucide-react';
import { TradingPosition, RiskAllocation } from '../types';
import {
  useActivePositions,
  useRiskAllocationMonitoring,
} from '../hooks/usePositionSizing';

interface ScenarioParameters {
  marketStressLevel: number; // 0-100 (percentage market decline)
  correlationIncrease: number; // 0-100 (how much correlations increase during stress)
  volatilityMultiplier: number; // 1-5 (how much volatility increases)
  liquidityImpact: number; // 0-50 (additional spread/slippage percentage)
}

interface ScenarioResult {
  scenarioName: string;
  parameters: ScenarioParameters;
  projectedCVaR: number;
  riskUtilization: number;
  portfolioValue: number;
  potentialLoss: number;
  positionsAtRisk: number;
  recommendations: string[];
  worstCasePositions: Array<{
    symbol: string;
    currentValue: number;
    projectedLoss: number;
    lossPercentage: number;
  }>;
}

interface RiskScenarioAnalyzerProps {
  className?: string;
}

const RiskScenarioAnalyzer: React.FC<RiskScenarioAnalyzerProps> = ({
  className = '',
}) => {
  const { positions, isLoading } = useActivePositions();
  const { riskAllocation } = useRiskAllocationMonitoring();

  const [selectedScenario, setSelectedScenario] = useState<
    'mild' | 'moderate' | 'severe' | 'custom'
  >('moderate');
  const [customParameters, setCustomParameters] = useState<ScenarioParameters>({
    marketStressLevel: 20,
    correlationIncrease: 30,
    volatilityMultiplier: 2,
    liquidityImpact: 5,
  });

  const [runningAnalysis, setRunningAnalysis] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<ScenarioResult[]>([]);

  const predefinedScenarios: Record<string, ScenarioParameters> = {
    mild: {
      marketStressLevel: 10,
      correlationIncrease: 20,
      volatilityMultiplier: 1.5,
      liquidityImpact: 2,
    },
    moderate: {
      marketStressLevel: 20,
      correlationIncrease: 40,
      volatilityMultiplier: 2.5,
      liquidityImpact: 5,
    },
    severe: {
      marketStressLevel: 40,
      correlationIncrease: 70,
      volatilityMultiplier: 4,
      liquidityImpact: 15,
    },
  };

  const portfolioMetrics = useMemo(() => {
    if (!positions.length) return null;

    const totalValue = positions.reduce(
      (sum, pos) => sum + (pos.manualPositionSize || pos.positionValue || 0),
      0
    );

    const portfoliosByType = positions.reduce(
      (acc, pos) => {
        const type = pos.portfolioType || 'Risk_On';
        if (!acc[type]) acc[type] = { count: 0, value: 0 };
        acc[type].count += 1;
        acc[type].value += pos.manualPositionSize || pos.positionValue || 0;
        return acc;
      },
      {} as Record<string, { count: number; value: number }>
    );

    return {
      totalValue,
      positionCount: positions.length,
      portfoliosByType,
      averagePositionSize: totalValue / positions.length,
    };
  }, [positions]);

  const runScenarioAnalysis = async (
    scenario: 'mild' | 'moderate' | 'severe' | 'custom'
  ) => {
    setRunningAnalysis(true);

    // Simulate analysis delay
    await new Promise((resolve) => setTimeout(resolve, 1500));

    const parameters =
      scenario === 'custom' ? customParameters : predefinedScenarios[scenario];
    const scenarioNames = {
      mild: 'Mild Market Stress',
      moderate: 'Moderate Market Correction',
      severe: 'Severe Market Crisis',
      custom: 'Custom Scenario',
    };

    if (!portfolioMetrics || !riskAllocation) {
      setRunningAnalysis(false);
      return;
    }

    // Calculate stress impact
    const marketDeclineImpact = parameters.marketStressLevel / 100;
    const volatilityImpact = parameters.volatilityMultiplier;
    const liquidityImpact = parameters.liquidityImpact / 100;

    // Simulate portfolio stress testing
    const basePortfolioValue = portfolioMetrics.totalValue;
    const portfolioLoss = basePortfolioValue * marketDeclineImpact;
    const stressedPortfolioValue = basePortfolioValue - portfolioLoss;

    // Calculate stressed CVaR (simplified model)
    const baseCVaR = riskAllocation.currentCVaR;
    const stressedCVaR = Math.min(
      0.3,
      baseCVaR * volatilityImpact * (1 + parameters.correlationIncrease / 100)
    );

    // Additional loss from liquidity impact
    const liquidityLoss = stressedPortfolioValue * liquidityImpact;
    const totalLoss = portfolioLoss + liquidityLoss;

    // Calculate positions at risk (simplified)
    const positionsAtRisk = Math.ceil(
      positions.length * (parameters.marketStressLevel / 100)
    );

    // Generate worst-case positions
    const worstCasePositions = positions
      .map((pos) => {
        const posValue = pos.manualPositionSize || pos.positionValue || 0;
        const baseRisk =
          pos.portfolioType === 'Risk_On'
            ? 0.8
            : pos.portfolioType === 'Protected'
              ? 0.4
              : 0.2;
        const stressMultiplier =
          1 + (parameters.marketStressLevel / 100) * baseRisk;
        const projectedLoss = posValue * marketDeclineImpact * stressMultiplier;

        return {
          symbol: pos.symbol,
          currentValue: posValue,
          projectedLoss,
          lossPercentage: (projectedLoss / posValue) * 100,
        };
      })
      .sort((a, b) => b.projectedLoss - a.projectedLoss)
      .slice(0, 5);

    // Generate recommendations
    const recommendations: string[] = [];

    if (stressedCVaR > 0.15) {
      recommendations.push(
        'Consider reducing position sizes to lower portfolio risk'
      );
    }
    if (parameters.marketStressLevel > 30) {
      recommendations.push(
        'Increase cash reserves for potential opportunities during stress'
      );
    }
    if (positionsAtRisk > positions.length * 0.7) {
      recommendations.push(
        'Diversify across different asset classes and strategies'
      );
    }
    if (liquidityImpact > 0.1) {
      recommendations.push(
        'Review position liquidity and consider more liquid alternatives'
      );
    }

    if (recommendations.length === 0) {
      recommendations.push('Portfolio appears resilient under this scenario');
    }

    const result: ScenarioResult = {
      scenarioName: scenarioNames[scenario],
      parameters,
      projectedCVaR: stressedCVaR,
      riskUtilization: stressedCVaR / 0.118,
      portfolioValue: stressedPortfolioValue,
      potentialLoss: totalLoss,
      positionsAtRisk,
      recommendations,
      worstCasePositions,
    };

    setAnalysisResults((prev) => [result, ...prev.slice(0, 4)]); // Keep last 5 results
    setRunningAnalysis(false);
  };

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

  const getRiskLevelColor = (utilization: number) => {
    if (utilization <= 0.7) return 'text-green-600';
    if (utilization <= 1.0) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRiskLevelBg = (utilization: number) => {
    if (utilization <= 0.7) return 'bg-green-100';
    if (utilization <= 1.0) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  if (isLoading) {
    return (
      <div
        className={`bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center ${className}`}
      >
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <span className="text-gray-600">Loading scenario analysis...</span>
      </div>
    );
  }

  if (!portfolioMetrics) {
    return (
      <div
        className={`bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center ${className}`}
      >
        <Calculator size={48} className="mx-auto mb-4 text-gray-300" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No Portfolio Data
        </h3>
        <p className="text-sm text-gray-600">
          Add positions to run scenario analysis
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Risk Scenario Analysis
            </h2>
            <p className="text-gray-500">
              Stress test your portfolio under different market conditions
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <Calculator className="text-blue-600" size={24} />
            <div className="text-right">
              <div className="text-sm text-gray-500">Portfolio Value</div>
              <div className="text-lg font-semibold text-gray-900">
                {formatCurrency(portfolioMetrics.totalValue)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scenario Configuration */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Scenario Configuration
        </h3>

        {/* Predefined Scenarios */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {(['mild', 'moderate', 'severe', 'custom'] as const).map(
            (scenario) => (
              <button
                key={scenario}
                onClick={() => setSelectedScenario(scenario)}
                className={`p-4 rounded-lg border text-left transition-colors ${
                  selectedScenario === scenario
                    ? 'bg-blue-50 border-blue-200 text-blue-900'
                    : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                }`}
              >
                <div className="font-medium capitalize mb-1">{scenario}</div>
                <div className="text-xs text-gray-500">
                  {scenario === 'mild'
                    ? '10% market decline'
                    : scenario === 'moderate'
                      ? '20% market decline'
                      : scenario === 'severe'
                        ? '40% market decline'
                        : 'Custom parameters'}
                </div>
              </button>
            )
          )}
        </div>

        {/* Custom Parameters */}
        {selectedScenario === 'custom' && (
          <div className="grid grid-cols-2 gap-6 mb-6 p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Market Stress Level: {customParameters.marketStressLevel}%
              </label>
              <input
                type="range"
                min="0"
                max="60"
                value={customParameters.marketStressLevel}
                onChange={(e) =>
                  setCustomParameters((prev) => ({
                    ...prev,
                    marketStressLevel: parseInt(e.target.value),
                  }))
                }
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Correlation Increase: {customParameters.correlationIncrease}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={customParameters.correlationIncrease}
                onChange={(e) =>
                  setCustomParameters((prev) => ({
                    ...prev,
                    correlationIncrease: parseInt(e.target.value),
                  }))
                }
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Volatility Multiplier: {customParameters.volatilityMultiplier}x
              </label>
              <input
                type="range"
                min="1"
                max="5"
                step="0.1"
                value={customParameters.volatilityMultiplier}
                onChange={(e) =>
                  setCustomParameters((prev) => ({
                    ...prev,
                    volatilityMultiplier: parseFloat(e.target.value),
                  }))
                }
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Liquidity Impact: {customParameters.liquidityImpact}%
              </label>
              <input
                type="range"
                min="0"
                max="20"
                value={customParameters.liquidityImpact}
                onChange={(e) =>
                  setCustomParameters((prev) => ({
                    ...prev,
                    liquidityImpact: parseInt(e.target.value),
                  }))
                }
                className="w-full"
              />
            </div>
          </div>
        )}

        {/* Run Analysis Button */}
        <div className="flex justify-center">
          <button
            onClick={() => runScenarioAnalysis(selectedScenario)}
            disabled={runningAnalysis}
            className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {runningAnalysis ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Running Analysis...</span>
              </>
            ) : (
              <>
                <Play size={16} />
                <span>Run Scenario Analysis</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Analysis Results */}
      {analysisResults.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">
              Analysis Results
            </h3>
            <button
              onClick={() => setAnalysisResults([])}
              className="flex items-center space-x-1 text-sm text-gray-500 hover:text-gray-700"
            >
              <RotateCcw size={14} />
              <span>Clear Results</span>
            </button>
          </div>

          {analysisResults.map((result, index) => (
            <div
              key={index}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-medium text-gray-900">
                  {result.scenarioName}
                </h4>
                <div
                  className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskLevelBg(
                    result.riskUtilization
                  )} ${getRiskLevelColor(result.riskUtilization)}`}
                >
                  Risk: {formatPercentage(result.riskUtilization)}
                </div>
              </div>

              <div className="grid grid-cols-4 gap-6 mb-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {formatCurrency(result.potentialLoss)}
                  </div>
                  <div className="text-sm text-gray-500">Potential Loss</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {formatPercentage(result.projectedCVaR)}
                  </div>
                  <div className="text-sm text-gray-500">Projected CVaR</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatCurrency(result.portfolioValue)}
                  </div>
                  <div className="text-sm text-gray-500">Portfolio Value</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {result.positionsAtRisk}
                  </div>
                  <div className="text-sm text-gray-500">Positions at Risk</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                {/* Worst Case Positions */}
                <div>
                  <h5 className="text-sm font-medium text-gray-900 mb-3">
                    Most Impacted Positions
                  </h5>
                  <div className="space-y-2">
                    {result.worstCasePositions.map((pos, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-2 bg-gray-50 rounded"
                      >
                        <span className="text-sm font-medium text-gray-900">
                          {pos.symbol}
                        </span>
                        <div className="text-right">
                          <div className="text-sm text-red-600 font-medium">
                            -{formatCurrency(pos.projectedLoss)}
                          </div>
                          <div className="text-xs text-gray-500">
                            {pos.lossPercentage.toFixed(1)}%
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommendations */}
                <div>
                  <h5 className="text-sm font-medium text-gray-900 mb-3">
                    Recommendations
                  </h5>
                  <div className="space-y-2">
                    {result.recommendations.map((rec, idx) => (
                      <div key={idx} className="flex items-start space-x-2">
                        <AlertTriangle
                          className="text-yellow-500 mt-0.5 flex-shrink-0"
                          size={14}
                        />
                        <span className="text-sm text-gray-700">{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RiskScenarioAnalyzer;
