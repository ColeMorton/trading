"""
Backtesting Parameter Service

Focused service for converting statistical analysis results to backtesting parameters.
Extracted from the larger backtesting_parameter_export_service for better maintainability.
"""

from dataclasses import dataclass
import logging
from typing import Any

import pandas as pd

from app.tools.config.statistical_analysis_config import SPDSConfig, get_spds_config


@dataclass
class BacktestingParameters:
    """Backtesting parameters for a strategy."""

    strategy_name: str
    ticker: str
    timeframe: str
    entry_threshold: float
    exit_threshold: float
    stop_loss_pct: float
    take_profit_pct: float
    max_holding_days: int
    min_holding_days: int
    position_size_pct: float
    risk_per_trade_pct: float
    trailing_stop_enabled: bool
    trailing_stop_pct: float
    momentum_exit_enabled: bool
    momentum_exit_threshold: float
    volatility_adjustment: bool
    volatility_multiplier: float


@dataclass
class VectorBTParameters:
    """VectorBT-specific parameters."""

    strategy_params: dict[str, Any]
    portfolio_params: dict[str, Any]
    risk_params: dict[str, Any]


class BacktestingParameterService:
    """
    Service for converting analysis results to backtesting parameters.

    This service handles:
    - Statistical analysis to parameter conversion
    - Risk management parameter calculation
    - Framework-specific parameter generation
    - Parameter validation and optimization
    """

    def __init__(
        self,
        config: SPDSConfig | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize the backtesting parameter service."""
        self.config = config or get_spds_config()
        self.logger = logger or logging.getLogger(__name__)

    def convert_analysis_to_parameters(
        self, analysis_result: dict[str, Any], strategy_type: str = "ma_cross",
    ) -> BacktestingParameters:
        """Convert statistical analysis results to backtesting parameters."""
        try:
            # Extract key metrics from analysis
            strategy_name = analysis_result.get("strategy_name", "UNKNOWN")
            ticker = analysis_result.get("ticker", "UNKNOWN")
            timeframe = analysis_result.get("timeframe", "D")

            # Extract statistical metrics
            performance_metrics = analysis_result.get("performance_metrics", {})
            risk_metrics = analysis_result.get("risk_metrics", {})

            # Calculate entry/exit thresholds
            entry_threshold = self._calculate_entry_threshold(analysis_result)
            exit_threshold = self._calculate_exit_threshold(analysis_result)

            # Calculate risk management parameters
            stop_loss_pct = self._calculate_stop_loss(risk_metrics)
            take_profit_pct = self._calculate_take_profit(performance_metrics)

            # Calculate position sizing
            position_size_pct = self._calculate_position_size(analysis_result)
            risk_per_trade_pct = self._calculate_risk_per_trade(risk_metrics)

            # Calculate holding period parameters
            max_holding_days = self._calculate_max_holding_days(analysis_result)
            min_holding_days = self._calculate_min_holding_days(analysis_result)

            # Calculate trailing stop parameters
            trailing_stop_enabled = self._should_enable_trailing_stop(analysis_result)
            trailing_stop_pct = self._calculate_trailing_stop(analysis_result)

            # Calculate momentum exit parameters
            momentum_exit_enabled = self._should_enable_momentum_exit(analysis_result)
            momentum_exit_threshold = self._calculate_momentum_exit_threshold(
                analysis_result,
            )

            # Calculate volatility adjustment parameters
            volatility_adjustment = self._should_enable_volatility_adjustment(
                analysis_result,
            )
            volatility_multiplier = self._calculate_volatility_multiplier(
                analysis_result,
            )

            return BacktestingParameters(
                strategy_name=strategy_name,
                ticker=ticker,
                timeframe=timeframe,
                entry_threshold=entry_threshold,
                exit_threshold=exit_threshold,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct,
                max_holding_days=max_holding_days,
                min_holding_days=min_holding_days,
                position_size_pct=position_size_pct,
                risk_per_trade_pct=risk_per_trade_pct,
                trailing_stop_enabled=trailing_stop_enabled,
                trailing_stop_pct=trailing_stop_pct,
                momentum_exit_enabled=momentum_exit_enabled,
                momentum_exit_threshold=momentum_exit_threshold,
                volatility_adjustment=volatility_adjustment,
                volatility_multiplier=volatility_multiplier,
            )

        except Exception as e:
            self.logger.exception(f"Parameter conversion failed: {e!s}")
            # Return default parameters
            return self._get_default_parameters(strategy_type)

    def generate_vectorbt_parameters(
        self, backtesting_params: BacktestingParameters,
    ) -> VectorBTParameters:
        """Generate VectorBT-specific parameters."""
        strategy_params = {
            "fast_window": 20,  # Default, should be extracted from analysis
            "slow_window": 50,  # Default, should be extracted from analysis
            "entry_threshold": backtesting_params.entry_threshold,
            "exit_threshold": backtesting_params.exit_threshold,
        }

        portfolio_params = {
            "init_cash": 10000,
            "fees": 0.001,
            "slippage": 0.0005,
            "size": backtesting_params.position_size_pct,
            "size_type": "percent",
        }

        risk_params = {
            "stop_loss": backtesting_params.stop_loss_pct,
            "take_profit": backtesting_params.take_profit_pct,
            "max_holding_days": backtesting_params.max_holding_days,
            "min_holding_days": backtesting_params.min_holding_days,
            "trailing_stop": (
                backtesting_params.trailing_stop_pct
                if backtesting_params.trailing_stop_enabled
                else None
            ),
        }

        return VectorBTParameters(
            strategy_params=strategy_params,
            portfolio_params=portfolio_params,
            risk_params=risk_params,
        )

    def generate_backtrader_parameters(
        self, backtesting_params: BacktestingParameters,
    ) -> dict[str, Any]:
        """Generate Backtrader-specific parameters."""
        return {
            "strategy_params": {
                "entry_threshold": backtesting_params.entry_threshold,
                "exit_threshold": backtesting_params.exit_threshold,
                "stop_loss_pct": backtesting_params.stop_loss_pct,
                "take_profit_pct": backtesting_params.take_profit_pct,
            },
            "cerebro_params": {
                "cash": 10000,
                "commission": 0.001,
            },
            "sizer_params": {
                "percents": backtesting_params.position_size_pct * 100,
            },
            "risk_params": {
                "max_holding_days": backtesting_params.max_holding_days,
                "min_holding_days": backtesting_params.min_holding_days,
                "trailing_stop_enabled": backtesting_params.trailing_stop_enabled,
                "trailing_stop_pct": backtesting_params.trailing_stop_pct,
            },
        }

    def validate_parameters(self, parameters: BacktestingParameters) -> dict[str, Any]:
        """Validate backtesting parameters for consistency and safety."""
        validation_results = {"is_valid": True, "warnings": [], "errors": []}

        # Validate thresholds
        if parameters.entry_threshold <= 0:
            validation_results["errors"].append("Entry threshold must be positive")
            validation_results["is_valid"] = False

        if parameters.exit_threshold <= 0:
            validation_results["errors"].append("Exit threshold must be positive")
            validation_results["is_valid"] = False

        # Validate risk parameters
        if parameters.stop_loss_pct < 0 or parameters.stop_loss_pct > 1:
            validation_results["errors"].append("Stop loss must be between 0 and 1")
            validation_results["is_valid"] = False

        if parameters.take_profit_pct < 0 or parameters.take_profit_pct > 1:
            validation_results["errors"].append("Take profit must be between 0 and 1")
            validation_results["is_valid"] = False

        # Validate position sizing
        if parameters.position_size_pct <= 0 or parameters.position_size_pct > 1:
            validation_results["errors"].append("Position size must be between 0 and 1")
            validation_results["is_valid"] = False

        if parameters.risk_per_trade_pct <= 0 or parameters.risk_per_trade_pct > 0.1:
            validation_results["warnings"].append(
                "Risk per trade above 10% is very aggressive",
            )

        # Validate holding periods
        if parameters.max_holding_days <= parameters.min_holding_days:
            validation_results["errors"].append(
                "Max holding days must be greater than min holding days",
            )
            validation_results["is_valid"] = False

        # Validate trailing stop
        if parameters.trailing_stop_enabled and parameters.trailing_stop_pct <= 0:
            validation_results["errors"].append(
                "Trailing stop percentage must be positive when enabled",
            )
            validation_results["is_valid"] = False

        return validation_results

    def optimize_parameters(
        self,
        parameters: BacktestingParameters,
        historical_data: pd.DataFrame | None = None,
    ) -> BacktestingParameters:
        """Optimize parameters based on historical performance."""
        # This is a simplified optimization
        # In practice, you would use more sophisticated optimization algorithms

        optimized_params = parameters

        if historical_data is not None and not historical_data.empty:
            # Calculate volatility-adjusted parameters
            returns = historical_data["close"].pct_change().dropna()
            volatility = returns.std()

            # Adjust stop loss based on volatility
            volatility_adjusted_stop = parameters.stop_loss_pct * (1 + volatility)
            optimized_params.stop_loss_pct = min(
                volatility_adjusted_stop, 0.1,
            )  # Cap at 10%

            # Adjust position size based on volatility
            volatility_adjusted_size = parameters.position_size_pct * (1 - volatility)
            optimized_params.position_size_pct = max(
                volatility_adjusted_size, 0.01,
            )  # Minimum 1%

        return optimized_params

    def _calculate_entry_threshold(self, analysis_result: dict[str, Any]) -> float:
        """Calculate entry threshold from analysis results."""
        # Default threshold
        threshold = 0.6

        # Extract from analysis if available
        if "entry_signal_strength" in analysis_result:
            threshold = analysis_result["entry_signal_strength"]
        elif "confidence_level" in analysis_result:
            threshold = analysis_result["confidence_level"]

        return max(0.5, min(threshold, 0.9))  # Clamp between 0.5 and 0.9

    def _calculate_exit_threshold(self, analysis_result: dict[str, Any]) -> float:
        """Calculate exit threshold from analysis results."""
        # Default threshold
        threshold = 0.4

        # Extract from analysis if available
        if "exit_signal_strength" in analysis_result:
            threshold = analysis_result["exit_signal_strength"]
        elif "confidence_level" in analysis_result:
            threshold = analysis_result["confidence_level"] * 0.7  # Lower than entry

        return max(0.3, min(threshold, 0.8))  # Clamp between 0.3 and 0.8

    def _calculate_stop_loss(self, risk_metrics: dict[str, Any]) -> float:
        """Calculate stop loss percentage from risk metrics."""
        # Default stop loss
        stop_loss = 0.05  # 5%

        # Extract from risk metrics if available
        if "max_drawdown" in risk_metrics:
            # Set stop loss based on historical drawdown
            stop_loss = abs(risk_metrics["max_drawdown"]) * 0.8
        elif "volatility" in risk_metrics:
            # Set stop loss based on volatility
            stop_loss = risk_metrics["volatility"] * 2.0

        return max(0.02, min(stop_loss, 0.15))  # Between 2% and 15%

    def _calculate_take_profit(self, performance_metrics: dict[str, Any]) -> float:
        """Calculate take profit percentage from performance metrics."""
        # Default take profit
        take_profit = 0.1  # 10%

        # Extract from performance metrics if available
        if "avg_win" in performance_metrics:
            take_profit = performance_metrics["avg_win"] * 0.8
        elif "expected_return" in performance_metrics:
            take_profit = performance_metrics["expected_return"] * 1.5

        return max(0.05, min(take_profit, 0.25))  # Between 5% and 25%

    def _calculate_position_size(self, analysis_result: dict[str, Any]) -> float:
        """Calculate position size percentage."""
        # Default position size
        position_size = 0.1  # 10%

        # Adjust based on confidence
        if "confidence_level" in analysis_result:
            confidence = analysis_result["confidence_level"]
            position_size = 0.05 + (confidence * 0.15)  # 5% to 20% based on confidence

        return max(0.01, min(position_size, 0.25))  # Between 1% and 25%

    def _calculate_risk_per_trade(self, risk_metrics: dict[str, Any]) -> float:
        """Calculate risk per trade percentage."""
        # Default risk per trade
        risk_per_trade = 0.02  # 2%

        # Adjust based on risk metrics
        if "sharpe_ratio" in risk_metrics:
            sharpe = risk_metrics["sharpe_ratio"]
            if sharpe > 1.0:
                risk_per_trade = 0.03  # Higher risk for better risk-adjusted returns
            elif sharpe < 0.5:
                risk_per_trade = 0.01  # Lower risk for poor risk-adjusted returns

        return max(0.005, min(risk_per_trade, 0.05))  # Between 0.5% and 5%

    def _calculate_max_holding_days(self, analysis_result: dict[str, Any]) -> int:
        """Calculate maximum holding days."""
        # Default max holding days
        max_days = 30

        # Extract from analysis if available
        if "avg_holding_period" in analysis_result:
            avg_holding = analysis_result["avg_holding_period"]
            max_days = int(avg_holding * 2)  # 2x average holding period

        return max(5, min(max_days, 252))  # Between 5 days and 1 year

    def _calculate_min_holding_days(self, analysis_result: dict[str, Any]) -> int:
        """Calculate minimum holding days."""
        # Default min holding days
        min_days = 1

        # Extract from analysis if available
        if "avg_holding_period" in analysis_result:
            avg_holding = analysis_result["avg_holding_period"]
            min_days = max(1, int(avg_holding * 0.2))  # 20% of average holding period

        return max(1, min(min_days, 10))  # Between 1 and 10 days

    def _should_enable_trailing_stop(self, analysis_result: dict[str, Any]) -> bool:
        """Determine if trailing stop should be enabled."""
        # Enable trailing stop for trending strategies
        if "trend_strength" in analysis_result:
            return analysis_result["trend_strength"] > 0.6

        # Enable if win rate is high
        if "win_rate" in analysis_result:
            return analysis_result["win_rate"] > 0.6

        return False  # Default to disabled

    def _calculate_trailing_stop(self, analysis_result: dict[str, Any]) -> float:
        """Calculate trailing stop percentage."""
        # Default trailing stop
        trailing_stop = 0.03  # 3%

        # Adjust based on volatility
        if "volatility" in analysis_result:
            volatility = analysis_result["volatility"]
            trailing_stop = volatility * 1.5

        return max(0.01, min(trailing_stop, 0.08))  # Between 1% and 8%

    def _should_enable_momentum_exit(self, analysis_result: dict[str, Any]) -> bool:
        """Determine if momentum exit should be enabled."""
        # Enable momentum exit for momentum strategies
        if "momentum_strength" in analysis_result:
            return analysis_result["momentum_strength"] > 0.5

        return False  # Default to disabled

    def _calculate_momentum_exit_threshold(
        self, analysis_result: dict[str, Any],
    ) -> float:
        """Calculate momentum exit threshold."""
        # Default momentum exit threshold
        threshold = 0.5

        # Adjust based on momentum strength
        if "momentum_strength" in analysis_result:
            threshold = analysis_result["momentum_strength"] * 0.8

        return max(0.3, min(threshold, 0.8))  # Between 0.3 and 0.8

    def _should_enable_volatility_adjustment(
        self, analysis_result: dict[str, Any],
    ) -> bool:
        """Determine if volatility adjustment should be enabled."""
        # Enable for high volatility environments
        if "volatility" in analysis_result:
            return analysis_result["volatility"] > 0.3

        return False  # Default to disabled

    def _calculate_volatility_multiplier(
        self, analysis_result: dict[str, Any],
    ) -> float:
        """Calculate volatility multiplier."""
        # Default volatility multiplier
        multiplier = 1.0

        # Adjust based on volatility
        if "volatility" in analysis_result:
            volatility = analysis_result["volatility"]
            multiplier = 1.0 + (
                volatility - 0.2
            )  # Adjust based on volatility above 20%

        return max(0.5, min(multiplier, 2.0))  # Between 0.5 and 2.0

    def _get_default_parameters(self, strategy_type: str) -> BacktestingParameters:
        """Get default parameters for a strategy type."""
        return BacktestingParameters(
            strategy_name=f"DEFAULT_{strategy_type}",
            ticker="UNKNOWN",
            timeframe="D",
            entry_threshold=0.6,
            exit_threshold=0.4,
            stop_loss_pct=0.05,
            take_profit_pct=0.1,
            max_holding_days=30,
            min_holding_days=1,
            position_size_pct=0.1,
            risk_per_trade_pct=0.02,
            trailing_stop_enabled=False,
            trailing_stop_pct=0.03,
            momentum_exit_enabled=False,
            momentum_exit_threshold=0.5,
            volatility_adjustment=False,
            volatility_multiplier=1.0,
        )
