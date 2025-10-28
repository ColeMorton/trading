"""
Position Sizing Strategy Execution Engine

This module extends the StrategyExecutionEngine to include real-time position sizing
calculations integrated with strategy analysis workflows.
"""

# API removed - creating local definitions
from dataclasses import dataclass
from enum import Enum
import time
from typing import Any


class StrategyTypeEnum(str, Enum):
    """Strategy type enumeration."""

    SMA = "SMA"
    EMA = "EMA"
    MACD = "MACD"
    RSI = "RSI"
    BOLLINGER_BANDS = "BOLLINGER_BANDS"


@dataclass
class PositionSizingRequest:
    """Position sizing request."""

    portfolio_type: str
    total_capital: float
    risk_per_trade: float = 0.02


@dataclass
class PositionSizingResponse:
    """Position sizing response."""

    position_sizes: dict[str, float]
    risk_metrics: dict[str, float]


class PositionSizingOrchestrator:
    """Position sizing orchestrator."""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    async def calculate_position_sizing(
        self,
        request: PositionSizingRequest,
    ) -> PositionSizingResponse:
        """Calculate position sizing."""
        # Basic position sizing logic
        return PositionSizingResponse(position_sizes={}, risk_metrics={})


from app.core.interfaces import (
    CacheInterface,
    ConfigurationInterface,
    LoggingInterface,
    ProgressTrackerInterface,
)
from app.core.strategies.strategy_factory import StrategyFactory
from app.tools.accounts import PortfolioType
from app.tools.services.strategy_execution_engine import StrategyExecutionEngine


class PositionSizingStrategyEngine(StrategyExecutionEngine):
    """
    Enhanced Strategy Execution Engine with integrated position sizing.

    This class extends the base StrategyExecutionEngine to provide real-time
    position sizing calculations for strategy signals.
    """

    def __init__(
        self,
        strategy_factory: StrategyFactory,
        cache: CacheInterface,
        config: ConfigurationInterface,
        logger: LoggingInterface,
        progress_tracker: ProgressTrackerInterface | None = None,
        executor=None,
        enable_memory_optimization: bool = True,
        enable_position_sizing: bool = True,
        base_dir: str | None = None,
    ):
        """Initialize the position sizing strategy engine.

        Args:
            strategy_factory: Factory for creating strategy instances
            cache: Cache interface implementation
            config: Configuration interface implementation
            logger: Logging interface implementation
            progress_tracker: Optional progress tracking interface
            executor: Optional executor for concurrent operations
            enable_memory_optimization: Enable memory optimization features
            enable_position_sizing: Enable position sizing integration
            base_dir: Base directory for position sizing components
        """
        # Initialize parent StrategyExecutionEngine
        super().__init__(
            strategy_factory=strategy_factory,
            cache=cache,
            config=config,
            logger=logger,
            progress_tracker=progress_tracker,
            executor=executor,
            enable_memory_optimization=enable_memory_optimization,
        )

        # Initialize position sizing orchestrator
        self.enable_position_sizing = enable_position_sizing
        if enable_position_sizing:
            self.position_sizing = PositionSizingOrchestrator(base_dir=base_dir)
        else:
            self.position_sizing = None

    async def execute_strategy_with_position_sizing(
        self,
        strategy_type: StrategyTypeEnum,
        strategy_config: dict[str, Any],
        log,
        execution_id: str | None = None,
        portfolio_type: PortfolioType = PortfolioType.RISK_ON,
        include_position_sizing: bool = True,
    ) -> dict[str, Any]:
        """
        Execute strategy analysis with integrated position sizing calculations.

        Args:
            strategy_type: Type of strategy to execute
            strategy_config: Configuration parameters for the strategy
            log: Logging function
            execution_id: Optional execution ID for tracking
            portfolio_type: Portfolio type for position sizing
            include_position_sizing: Whether to include position sizing

        Returns:
            Dictionary containing strategy results and position sizing data
        """
        log("Starting strategy execution with position sizing integration")

        # Execute base strategy analysis
        portfolio_dicts = await self.execute_strategy_analysis(
            strategy_type=strategy_type,
            strategy_config=strategy_config,
            log=log,
            execution_id=execution_id,
        )

        if not include_position_sizing or not self.enable_position_sizing:
            return {
                "strategy_results": portfolio_dicts,
                "position_sizing": None,
                "message": "Position sizing disabled or not requested",
            }

        try:
            # Process position sizing for each portfolio result
            position_sizing_results = (
                await self._process_position_sizing_for_portfolios(
                    portfolio_dicts=portfolio_dicts,
                    portfolio_type=portfolio_type,
                    log=log,
                )
            )

            # Get current dashboard data
            dashboard_data = self.position_sizing.get_dashboard_data()

            log(
                f"Position sizing calculated for {len(position_sizing_results)} portfolios",
            )

            return {
                "strategy_results": portfolio_dicts,
                "position_sizing": {
                    "recommendations": position_sizing_results,
                    "dashboard": dashboard_data.__dict__,
                    "calculation_timestamp": time.time(),
                },
                "integration_status": "success",
            }

        except Exception as e:
            log(f"Position sizing calculation failed: {e!s}", "error")
            return {
                "strategy_results": portfolio_dicts,
                "position_sizing": None,
                "integration_status": "failed",
                "error": str(e),
            }

    async def _process_position_sizing_for_portfolios(
        self,
        portfolio_dicts: list[dict[str, Any]],
        portfolio_type: PortfolioType,
        log,
    ) -> list[dict[str, Any]]:
        """
        Process position sizing for multiple portfolio results.

        Args:
            portfolio_dicts: List of portfolio dictionaries from strategy execution
            portfolio_type: Portfolio type for position sizing
            log: Logging function

        Returns:
            List of position sizing recommendations
        """
        position_sizing_results = []

        for portfolio in portfolio_dicts:
            try:
                # Extract ticker information
                ticker = portfolio.get("ticker", "")
                if not ticker:
                    continue

                # Get signals from portfolio if available
                signals = portfolio.get("signals", [])
                if not signals:
                    # Use latest portfolio data for position sizing
                    latest_data = self._extract_latest_portfolio_data(portfolio)
                    if latest_data:
                        ps_response = await self._calculate_position_sizing_for_data(
                            ticker=ticker,
                            data=latest_data,
                            portfolio_type=portfolio_type,
                            log=log,
                        )

                        if ps_response:
                            position_sizing_results.append(
                                {
                                    "symbol": ticker,
                                    "signal_source": "portfolio_data",
                                    "position_sizing": ps_response.__dict__,
                                    "portfolio_metrics": portfolio.get("metrics", {}),
                                },
                            )
                else:
                    # Process each signal for position sizing
                    for signal in signals[-3:]:  # Process last 3 signals
                        ps_response = await self._calculate_position_sizing_for_signal(
                            ticker=ticker,
                            signal=signal,
                            portfolio_type=portfolio_type,
                            log=log,
                        )

                        if ps_response:
                            position_sizing_results.append(
                                {
                                    "symbol": ticker,
                                    "signal": signal,
                                    "signal_source": "strategy_signal",
                                    "position_sizing": ps_response.__dict__,
                                    "portfolio_metrics": portfolio.get("metrics", {}),
                                },
                            )

            except Exception as e:
                log(f"Failed to process position sizing for {ticker}: {e!s}", "error")
                continue

        return position_sizing_results

    async def _calculate_position_sizing_for_signal(
        self,
        ticker: str,
        signal: dict[str, Any],
        portfolio_type: PortfolioType,
        log,
    ) -> Any | None:
        """
        Calculate position sizing for a specific signal.

        Args:
            ticker: Ticker symbol
            signal: Signal data dictionary
            portfolio_type: Portfolio type for position sizing
            log: Logging function

        Returns:
            PositionSizingResponse or None if calculation fails
        """
        try:
            # Determine signal type and parameters
            position = signal.get("position", 0)
            signal_type = "entry" if position > 0 else "exit"

            # Extract price and other parameters
            entry_price = (
                signal.get("price") or signal.get("close") or signal.get("entry_price")
            )
            stop_loss_distance = signal.get("stop_loss_distance", 0.05)  # Default 5%
            confidence_level = signal.get("confidence_level", "primary")

            # Create position sizing request
            ps_request = PositionSizingRequest(
                symbol=ticker,
                signal_type=signal_type,
                portfolio_type=portfolio_type,
                entry_price=entry_price,
                stop_loss_distance=stop_loss_distance,
                confidence_level=confidence_level,
            )

            # Calculate position size
            ps_response = self.position_sizing.calculate_position_size(ps_request)

            log(
                f"Position sizing calculated for {ticker}: ${ps_response.position_value:.2f}",
            )
            return ps_response

        except Exception as e:
            log(f"Position sizing calculation failed for {ticker}: {e!s}", "error")
            return None

    async def _calculate_position_sizing_for_data(
        self,
        ticker: str,
        data: dict[str, Any],
        portfolio_type: PortfolioType,
        log,
    ) -> Any | None:
        """
        Calculate position sizing for portfolio data (when no signals available).

        Args:
            ticker: Ticker symbol
            data: Latest portfolio data
            portfolio_type: Portfolio type for position sizing
            log: Logging function

        Returns:
            PositionSizingResponse or None if calculation fails
        """
        try:
            # Create a synthetic entry signal from portfolio data
            ps_request = PositionSizingRequest(
                symbol=ticker,
                signal_type="entry",
                portfolio_type=portfolio_type,
                entry_price=data.get("current_price"),
                stop_loss_distance=0.05,  # Default 5%
                confidence_level="primary",
            )

            # Calculate position size
            ps_response = self.position_sizing.calculate_position_size(ps_request)

            log(
                f"Position sizing calculated for {ticker} (from data): ${ps_response.position_value:.2f}",
            )
            return ps_response

        except Exception as e:
            log(f"Position sizing calculation failed for {ticker}: {e!s}", "error")
            return None

    def _extract_latest_portfolio_data(
        self,
        portfolio: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Extract latest data from portfolio for position sizing.

        Args:
            portfolio: Portfolio dictionary

        Returns:
            Dictionary with latest data or None
        """
        try:
            # Look for current price in various portfolio fields
            current_price = None

            # Check common price fields
            for price_field in ["current_price", "last_price", "close", "price"]:
                if price_field in portfolio:
                    current_price = portfolio[price_field]
                    break

            # Check metrics for price information
            metrics = portfolio.get("metrics", {})
            if not current_price and metrics:
                for price_field in ["current_price", "last_price", "final_price"]:
                    if price_field in metrics:
                        current_price = metrics[price_field]
                        break

            if current_price:
                return {
                    "current_price": current_price,
                    "portfolio_value": portfolio.get("total_value", 0),
                    "metrics": metrics,
                }

            return None

        except Exception:
            return None

    async def sync_positions_with_strategy_results(
        self,
        strategy_results: dict[str, Any],
        auto_update_positions: bool = False,
        log=None,
    ) -> dict[str, Any]:
        """
        Synchronize position sizing with strategy analysis results.

        Args:
            strategy_results: Results from strategy analysis
            auto_update_positions: Whether to automatically update positions
            log: Optional logging function

        Returns:
            Dictionary with synchronization results
        """
        if not self.enable_position_sizing:
            return {"status": "disabled", "message": "Position sizing not enabled"}

        if not log:
            log = self.logger.log

        sync_results = {
            "processed_portfolios": 0,
            "updated_positions": [],
            "new_signals": [],
            "errors": [],
        }

        try:
            portfolio_dicts = strategy_results.get("strategy_results", [])

            for portfolio in portfolio_dicts:
                ticker = portfolio.get("ticker", "")
                if not ticker:
                    continue

                sync_results["processed_portfolios"] += 1

                # Check if we have an existing position for this symbol
                position_analysis = self.position_sizing.get_position_analysis(ticker)

                # Process signals for position updates
                signals = portfolio.get("signals", [])
                for signal in signals[-1:]:  # Process latest signal
                    try:
                        # Determine if this is a new signal requiring position sizing
                        position = signal.get("position", 0)

                        if position > 0:  # Entry signal
                            # Calculate position sizing for this signal
                            ps_response = (
                                await self._calculate_position_sizing_for_signal(
                                    ticker=ticker,
                                    signal=signal,
                                    portfolio_type=PortfolioType.RISK_ON,
                                    log=log,
                                )
                            )

                            if ps_response:
                                sync_results["new_signals"].append(
                                    {
                                        "symbol": ticker,
                                        "signal": signal,
                                        "position_sizing": ps_response.__dict__,
                                    },
                                )

                                # Auto-update position if enabled
                                if auto_update_positions and ps_response.entry_price:
                                    result = self.position_sizing.process_new_position(
                                        symbol=ticker,
                                        position_value=ps_response.position_value,
                                        stop_loss_distance=signal.get(
                                            "stop_loss_distance",
                                        ),
                                        entry_price=ps_response.entry_price,
                                        portfolio_type=PortfolioType.RISK_ON,
                                    )

                                    sync_results["updated_positions"].append(
                                        {
                                            "symbol": ticker,
                                            "action": "new_position",
                                            "result": result,
                                        },
                                    )

                        elif (
                            position < 0
                            and position_analysis["position_tracking"]["position_value"]
                            > 0
                        ):
                            # Exit signal for existing position
                            sync_results["updated_positions"].append(
                                {
                                    "symbol": ticker,
                                    "action": "exit_signal",
                                    "signal": signal,
                                },
                            )

                    except Exception as e:
                        sync_results["errors"].append(
                            {"symbol": ticker, "error": str(e), "signal": signal},
                        )
                        log(f"Error processing signal for {ticker}: {e!s}", "error")

            log(
                f"Sync completed: {sync_results['processed_portfolios']} portfolios, "
                f"{len(sync_results['new_signals'])} new signals, "
                f"{len(sync_results['updated_positions'])} position updates",
            )

            return sync_results

        except Exception as e:
            log(f"Position synchronization failed: {e!s}", "error")
            sync_results["errors"].append({"error": f"Sync failed: {e!s}"})
            return sync_results

    async def get_integrated_dashboard_data(self) -> dict[str, Any]:
        """
        Get integrated dashboard data combining strategy and position sizing metrics.

        Returns:
            Dictionary with comprehensive dashboard data
        """
        if not self.enable_position_sizing:
            return {"status": "disabled", "message": "Position sizing not enabled"}

        try:
            # Get position sizing dashboard data
            dashboard = self.position_sizing.get_dashboard_data()

            # Add strategy execution metrics if available
            strategy_metrics = {
                "memory_optimization_enabled": self.enable_memory_optimization,
                "position_sizing_enabled": self.enable_position_sizing,
                "active_strategies": [],  # Would be populated from strategy factory
                "execution_metrics": {},  # Would be populated from execution history
            }

            # Combine data
            return {
                "position_sizing": dashboard.__dict__,
                "strategy_execution": strategy_metrics,
                "integration_status": "active",
                "last_updated": dashboard.last_updated.isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get integrated dashboard: {e!s}",
            }

    def enable_position_sizing_integration(self, enabled: bool = True) -> None:
        """
        Enable or disable position sizing integration.

        Args:
            enabled: Whether to enable position sizing
        """
        self.enable_position_sizing = enabled

        if enabled and not self.position_sizing:
            self.position_sizing = PositionSizingOrchestrator()

        self.logger.log(
            f"Position sizing integration {'enabled' if enabled else 'disabled'}",
        )

    async def validate_position_sizing_integration(self) -> dict[str, Any]:
        """
        Validate that position sizing integration is working correctly.

        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "position_sizing_enabled": self.enable_position_sizing,
            "orchestrator_available": self.position_sizing is not None,
            "components_status": {},
            "validation_errors": [],
        }

        if not self.enable_position_sizing:
            validation_results["validation_errors"].append(
                "Position sizing is disabled",
            )
            return validation_results

        if not self.position_sizing:
            validation_results["validation_errors"].append(
                "Position sizing orchestrator not available",
            )
            return validation_results

        try:
            # Test basic functionality
            net_worth = self.position_sizing.account_service.calculate_net_worth()
            validation_results["components_status"]["account_service"] = "operational"

            strategies_count = (
                self.position_sizing.strategies_integration.get_total_strategies_count()
            )
            validation_results["components_status"][
                "strategies_integration"
            ] = "operational"

            dashboard = self.position_sizing.get_dashboard_data()
            validation_results["components_status"]["orchestrator"] = "operational"

            validation_results["test_data"] = {
                "net_worth": net_worth.total_net_worth,
                "strategies_count": strategies_count,
                "dashboard_last_updated": dashboard.last_updated.isoformat(),
            }

        except Exception as e:
            validation_results["validation_errors"].append(
                f"Component validation failed: {e!s}",
            )

        return validation_results
