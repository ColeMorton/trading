import React, { useState } from 'react';
import {
  ArrowRight,
  Shield,
  TrendingUp,
  PiggyBank,
  AlertTriangle,
  CheckCircle,
  Clock,
} from 'lucide-react';
import { TradingPosition } from '../types';
import { useEnhancedPositionManagement } from '../hooks/usePositionSizing';

interface PortfolioTransitionManagerProps {
  position: TradingPosition;
  onTransitionComplete?: (result: {
    success: boolean;
    fromPortfolio: string;
    toPortfolio: string;
    position: TradingPosition;
  }) => void;
  className?: string;
}

interface TransitionState {
  isTransitioning: boolean;
  showConfirmation: boolean;
  transitionType: 'Risk_to_Protected' | 'Protected_to_Investment' | null;
}

const PortfolioTransitionManager: React.FC<PortfolioTransitionManagerProps> = ({
  position,
  onTransitionComplete,
  className = '',
}) => {
  const { transitionPosition, isTransitioning, error } =
    useEnhancedPositionManagement();

  const [state, setState] = useState<TransitionState>({
    isTransitioning: false,
    showConfirmation: false,
    transitionType: null,
  });

  const getPortfolioIcon = (portfolioType: string) => {
    switch (portfolioType) {
      case 'Risk_On':
        return <TrendingUp size={16} className="text-red-500" />;
      case 'Protected':
        return <Shield size={16} className="text-blue-500" />;
      case 'Investment':
        return <PiggyBank size={16} className="text-green-500" />;
      default:
        return <TrendingUp size={16} className="text-gray-500" />;
    }
  };

  const getPortfolioName = (portfolioType: string) => {
    switch (portfolioType) {
      case 'Risk_On':
        return 'Risk On Portfolio';
      case 'Protected':
        return 'Protected Portfolio';
      case 'Investment':
        return 'Investment Portfolio';
      default:
        return 'Unknown Portfolio';
    }
  };

  const canTransitionToProtected = () => {
    return (
      position.portfolioType === 'Risk_On' &&
      position.currentStatus === 'Active' &&
      position.stopStatus === 'Risk'
    );
  };

  const canTransitionToInvestment = () => {
    return (
      position.portfolioType === 'Protected' &&
      position.currentStatus === 'Active'
    );
  };

  const getTransitionDescription = (
    transitionType: 'Risk_to_Protected' | 'Protected_to_Investment'
  ) => {
    if (transitionType === 'Risk_to_Protected') {
      return {
        title: 'Move to Protected Portfolio',
        description:
          'Position stop loss has moved to entry price, protecting your capital.',
        fromPortfolio: 'Risk On Portfolio',
        toPortfolio: 'Protected Portfolio',
        icon: <Shield className="text-blue-500" size={20} />,
        bgColor: 'bg-blue-50',
        borderColor: 'border-blue-200',
      };
    } else {
      return {
        title: 'Move to Investment Portfolio',
        description: 'Position has become a long-term strategic holding.',
        fromPortfolio: 'Protected Portfolio',
        toPortfolio: 'Investment Portfolio',
        icon: <PiggyBank className="text-green-500" size={20} />,
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
      };
    }
  };

  const startTransition = (
    transitionType: 'Risk_to_Protected' | 'Protected_to_Investment'
  ) => {
    setState({
      isTransitioning: false,
      showConfirmation: true,
      transitionType,
    });
  };

  const confirmTransition = async () => {
    if (!state.transitionType) return;

    setState((prev) => ({ ...prev, isTransitioning: true }));

    try {
      const result = await transitionPosition(
        position.symbol,
        state.transitionType
      );

      if (result) {
        setState({
          isTransitioning: false,
          showConfirmation: false,
          transitionType: null,
        });
        onTransitionComplete?.(result);
      }
    } catch (err) {
      setState((prev) => ({ ...prev, isTransitioning: false }));
    }
  };

  const cancelTransition = () => {
    setState({
      isTransitioning: false,
      showConfirmation: false,
      transitionType: null,
    });
  };

  if (state.showConfirmation && state.transitionType) {
    const transition = getTransitionDescription(state.transitionType);

    return (
      <div
        className={`${transition.bgColor} border ${transition.borderColor} rounded-lg p-4 ${className}`}
      >
        <div className="flex items-start space-x-3">
          {transition.icon}
          <div className="flex-1">
            <h4 className="text-sm font-medium text-gray-900 mb-1">
              {transition.title}
            </h4>
            <p className="text-sm text-gray-600 mb-3">
              {transition.description}
            </p>

            <div className="flex items-center space-x-2 text-sm text-gray-600 mb-4">
              <span className="flex items-center">
                {getPortfolioIcon('Risk_On')}
                <span className="ml-1">{transition.fromPortfolio}</span>
              </span>
              <ArrowRight size={16} className="text-gray-400" />
              <span className="flex items-center">
                {getPortfolioIcon(
                  state.transitionType === 'Risk_to_Protected'
                    ? 'Protected'
                    : 'Investment'
                )}
                <span className="ml-1">{transition.toPortfolio}</span>
              </span>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-4">
              <div className="flex">
                <AlertTriangle
                  className="text-yellow-400 mr-2 flex-shrink-0"
                  size={16}
                />
                <div>
                  <h5 className="text-sm font-medium text-yellow-800 mb-1">
                    Confirm Transition
                  </h5>
                  <p className="text-sm text-yellow-700">
                    This will move <strong>{position.symbol}</strong> from{' '}
                    {transition.fromPortfolio} to {transition.toPortfolio}. This
                    action updates your CSV files and cannot be easily undone.
                  </p>
                </div>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
                <div className="flex">
                  <AlertTriangle
                    className="text-red-400 mr-2 flex-shrink-0"
                    size={16}
                  />
                  <div>
                    <h5 className="text-sm font-medium text-red-800">
                      Transition Failed
                    </h5>
                    <p className="text-sm text-red-700 mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-end space-x-3">
              <button
                onClick={cancelTransition}
                disabled={state.isTransitioning}
                className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmTransition}
                disabled={state.isTransitioning}
                className="px-3 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 flex items-center"
              >
                {state.isTransitioning ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Moving...
                  </>
                ) : (
                  <>
                    <CheckCircle size={16} className="mr-2" />
                    Confirm Transition
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {getPortfolioIcon(position.portfolioType || 'Risk_On')}
          <div>
            <h4 className="text-sm font-medium text-gray-900">
              {position.symbol} -{' '}
              {getPortfolioName(position.portfolioType || 'Risk_On')}
            </h4>
            <p className="text-sm text-gray-500">
              Status: {position.currentStatus} • Stop: {position.stopStatus}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Risk to Protected Transition */}
          {canTransitionToProtected() && (
            <button
              onClick={() => startTransition('Risk_to_Protected')}
              disabled={isTransitioning}
              className="flex items-center px-3 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              title="Move to Protected Portfolio (stop loss at entry)"
            >
              <Shield size={16} className="mr-2" />
              Protect
              <ArrowRight size={14} className="ml-2" />
            </button>
          )}

          {/* Protected to Investment Transition */}
          {canTransitionToInvestment() && (
            <button
              onClick={() => startTransition('Protected_to_Investment')}
              disabled={isTransitioning}
              className="flex items-center px-3 py-2 text-sm font-medium text-green-700 bg-green-50 border border-green-200 rounded-md hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
              title="Move to Investment Portfolio (long-term holding)"
            >
              <PiggyBank size={16} className="mr-2" />
              Invest
              <ArrowRight size={14} className="ml-2" />
            </button>
          )}

          {/* No Transitions Available */}
          {!canTransitionToProtected() && !canTransitionToInvestment() && (
            <div className="flex items-center text-sm text-gray-500">
              <Clock size={16} className="mr-2" />
              No transitions available
            </div>
          )}
        </div>
      </div>

      {/* Portfolio Transition Flow Indicator */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-2">
            <span
              className={`flex items-center ${
                position.portfolioType === 'Risk_On'
                  ? 'font-medium text-red-600'
                  : ''
              }`}
            >
              {getPortfolioIcon('Risk_On')}
              <span className="ml-1">Risk On</span>
            </span>
            <ArrowRight size={12} />
            <span
              className={`flex items-center ${
                position.portfolioType === 'Protected'
                  ? 'font-medium text-blue-600'
                  : ''
              }`}
            >
              {getPortfolioIcon('Protected')}
              <span className="ml-1">Protected</span>
            </span>
            <ArrowRight size={12} />
            <span
              className={`flex items-center ${
                position.portfolioType === 'Investment'
                  ? 'font-medium text-green-600'
                  : ''
              }`}
            >
              {getPortfolioIcon('Investment')}
              <span className="ml-1">Investment</span>
            </span>
          </div>
          <span className="text-gray-400">Portfolio Lifecycle</span>
        </div>
      </div>
    </div>
  );
};

export default PortfolioTransitionManager;
