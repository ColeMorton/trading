"""
Enhanced Service Coordinator with Position Sizing Integration

This module extends the ServiceCoordinator to include position sizing capabilities,
integrating the PositionSizingOrchestrator with the existing strategy analysis pipeline.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from app.api.models.strategy_analysis import (
    MACrossRequest,
    MACrossResponse,
    StrategyAnalysisRequest,
)
from app.api.services.position_sizing_orchestrator import (
    PositionSizingOrchestrator,
    PositionSizingRequest,
    PositionSizingResponse,
)
from app.core.interfaces import (
    CacheInterface,
    ConfigurationInterface,
    LoggingInterface,
    MonitoringInterface,
    ProgressTrackerInterface,
)
from app.core.strategies.strategy_factory import StrategyFactory
from app.tools.accounts import PortfolioType
from app.tools.services.service_coordinator import ServiceCoordinator


class EnhancedServiceCoordinator(ServiceCoordinator):
    """
    Enhanced Service Coordinator that integrates position sizing with strategy analysis.

    This coordinator extends the base ServiceCoordinator to provide seamless
    integration between strategy analysis and position sizing calculations.
    """

    def __init__(
        self,
        strategy_factory: StrategyFactory,
        cache: CacheInterface,
        config: ConfigurationInterface,
        logger: LoggingInterface,
        metrics: MonitoringInterface,
        progress_tracker: Optional[ProgressTrackerInterface] = None,
        executor: Optional[ThreadPoolExecutor] = None,
        base_dir: Optional[str] = None,
    ):
        """Initialize the enhanced service coordinator with position sizing.

        Args:
            strategy_factory: Factory for creating strategy instances
            cache: Cache interface implementation
            config: Configuration interface implementation
            logger: Logging interface implementation
            metrics: Monitoring interface implementation
            progress_tracker: Optional progress tracking interface
            executor: Optional thread pool executor
            base_dir: Base directory for position sizing components
        """
        # Initialize parent ServiceCoordinator
        super().__init__(
            strategy_factory=strategy_factory,
            cache=cache,
            config=config,
            logger=logger,
            metrics=metrics,
            progress_tracker=progress_tracker,
            executor=executor,
        )

        # Initialize position sizing orchestrator
        self.position_sizing = PositionSizingOrchestrator(base_dir=base_dir)

        # Flag to enable/disable position sizing integration
        self.position_sizing_enabled = True

    async def analyze_strategy_with_position_sizing(
        self, request: StrategyAnalysisRequest
    ) -> Dict[str, Any]:
        """
        Execute strategy analysis with integrated position sizing calculations.

        This method extends the base analyze_strategy to include position sizing
        recommendations for each generated signal.

        Args:
            request: StrategyAnalysisRequest with analysis parameters

        Returns:
            Dictionary containing both strategy analysis results and position sizing

        Raises:
            StrategyAnalysisServiceError: If analysis fails
        """
        # Execute base strategy analysis
        strategy_response = await self.analyze_strategy(request)

        if not self.position_sizing_enabled:
            return {
                "strategy_analysis": strategy_response,
                "position_sizing": None,
                "message": "Position sizing disabled",
            }

        try:
            # Extract portfolio results
            portfolios = strategy_response.deduplicated_portfolios

            # Process each portfolio for position sizing
            position_sizing_results = []

            for portfolio in portfolios:
                ticker = portfolio.get("ticker", request.ticker)

                # Get latest signal (if any)
                if "signals" in portfolio and len(portfolio["signals"]) > 0:
                    latest_signal = portfolio["signals"][-1]

                    # Create position sizing request
                    ps_request = PositionSizingRequest(
                        symbol=ticker,
                        signal_type="entry"
                        if latest_signal.get("position") > 0
                        else "exit",
                        portfolio_type=PortfolioType.RISK_ON,  # Default to Risk On
                        entry_price=latest_signal.get("price"),
                        stop_loss_distance=0.05,  # Default 5% stop loss
                        confidence_level="primary",
                    )

                    # Calculate position size
                    ps_response = self.position_sizing.calculate_position_size(
                        ps_request
                    )

                    position_sizing_results.append(
                        {
                            "symbol": ticker,
                            "signal": latest_signal,
                            "position_sizing": ps_response.__dict__,
                        }
                    )

            # Get current dashboard data
            dashboard_data = self.position_sizing.get_dashboard_data()

            return {
                "strategy_analysis": strategy_response,
                "position_sizing": {
                    "recommendations": position_sizing_results,
                    "dashboard": dashboard_data.__dict__,
                    "calculation_timestamp": time.time(),
                },
            }

        except Exception as e:
            self.logger.log(f"Position sizing calculation failed: {str(e)}", "error")
            return {
                "strategy_analysis": strategy_response,
                "position_sizing": None,
                "error": f"Position sizing failed: {str(e)}",
            }

    async def calculate_position_size_for_signal(
        self,
        symbol: str,
        signal_data: Dict[str, Any],
        portfolio_type: PortfolioType = PortfolioType.RISK_ON,
    ) -> PositionSizingResponse:
        """
        Calculate position size for a specific signal.

        Args:
            symbol: Ticker symbol
            signal_data: Signal data containing price, type, etc.
            portfolio_type: Type of portfolio (Risk On or Investment)

        Returns:
            PositionSizingResponse with calculated position size
        """
        # Create position sizing request from signal data
        ps_request = PositionSizingRequest(
            symbol=symbol,
            signal_type="entry" if signal_data.get("position", 0) > 0 else "exit",
            portfolio_type=portfolio_type,
            entry_price=signal_data.get("price"),
            stop_loss_distance=signal_data.get("stop_loss_distance", 0.05),
            confidence_level=signal_data.get("confidence_level", "primary"),
        )

        # Calculate and return position size
        return self.position_sizing.calculate_position_size(ps_request)

    async def get_position_sizing_dashboard(self) -> Dict[str, Any]:
        """
        Get the complete position sizing dashboard data.

        Returns:
            Dictionary containing dashboard data
        """
        dashboard = self.position_sizing.get_dashboard_data()

        # Convert to dictionary format for API response
        return {
            "net_worth": dashboard.net_worth,
            "account_balances": dashboard.account_balances,
            "portfolio_risk_metrics": dashboard.portfolio_risk_metrics,
            "active_positions": dashboard.active_positions,
            "incoming_signals": dashboard.incoming_signals,
            "strategic_holdings": dashboard.strategic_holdings,
            "risk_allocation_buckets": dashboard.risk_allocation_buckets,
            "total_strategies_count": dashboard.total_strategies_count,
            "last_updated": dashboard.last_updated.isoformat(),
        }

    async def process_new_position(
        self,
        symbol: str,
        position_value: float,
        stop_loss_distance: Optional[float] = None,
        entry_price: Optional[float] = None,
        portfolio_type: str = "Risk_On",
    ) -> Dict[str, Any]:
        """
        Process a new position entry through the position sizing system.

        Args:
            symbol: Ticker symbol
            position_value: Position value from trade fill
            stop_loss_distance: Distance to stop loss (0-1)
            entry_price: Entry price for the position
            portfolio_type: Portfolio type string

        Returns:
            Dictionary with position processing results
        """
        # Convert portfolio type string to enum
        ptype = (
            PortfolioType.RISK_ON
            if portfolio_type == "Risk_On"
            else PortfolioType.INVESTMENT
        )

        # Process through position sizing orchestrator
        result = self.position_sizing.process_new_position(
            symbol=symbol,
            position_value=position_value,
            stop_loss_distance=stop_loss_distance,
            entry_price=entry_price,
            portfolio_type=ptype,
        )

        # Log the position entry
        self.logger.log(
            f"Processed new position: {symbol} - ${position_value:.2f} in {portfolio_type} portfolio"
        )

        return result

    async def update_position_metrics(
        self, symbol: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update position metrics across all tracking systems.

        Args:
            symbol: Ticker symbol to update
            updates: Dictionary of updates

        Returns:
            Dictionary with update results
        """
        success = self.position_sizing.update_position_metrics(symbol, updates)

        if success:
            self.logger.log(f"Updated position metrics for {symbol}")
        else:
            self.logger.log(f"Failed to update position metrics for {symbol}", "error")

        return {"success": success, "symbol": symbol, "updates_applied": updates}

    async def get_position_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive position analysis for a symbol.

        Args:
            symbol: Ticker symbol to analyze

        Returns:
            Dictionary with complete position analysis
        """
        return self.position_sizing.get_position_analysis(symbol)

    async def validate_excel_compatibility(
        self, excel_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate position sizing calculations against Excel formulas.

        Args:
            excel_data: Dictionary with Excel values for comparison

        Returns:
            Validation results with any discrepancies
        """
        return self.position_sizing.validate_excel_compatibility(excel_data)

    async def export_position_sizing_data(self) -> str:
        """
        Export current position sizing system state for Excel migration.

        Returns:
            Path to exported JSON file
        """
        export_path = self.position_sizing.export_for_excel_migration()

        self.logger.log(f"Exported position sizing data to: {export_path}")

        return export_path

    def enable_position_sizing(self, enabled: bool = True) -> None:
        """
        Enable or disable position sizing integration.

        Args:
            enabled: Whether to enable position sizing
        """
        self.position_sizing_enabled = enabled
        self.logger.log(f"Position sizing {'enabled' if enabled else 'disabled'}")

    async def get_risk_allocation_summary(self) -> Dict[str, Any]:
        """
        Get summary of risk allocation across all portfolios.

        Returns:
            Dictionary with risk allocation summary
        """
        dashboard = self.position_sizing.get_dashboard_data()

        # Calculate risk utilization
        net_worth = dashboard.net_worth
        total_risk = sum(
            pos.get("risk_amount", 0) for pos in dashboard.active_positions
        )
        risk_utilization = (
            (total_risk / (net_worth * 0.118)) * 100 if net_worth > 0 else 0
        )

        return {
            "net_worth": net_worth,
            "risk_allocation_limit": net_worth * 0.118,  # 11.8% tier
            "current_risk_exposure": total_risk,
            "risk_utilization_percentage": risk_utilization,
            "available_risk_capacity": max(0, (net_worth * 0.118) - total_risk),
            "risk_buckets": dashboard.risk_allocation_buckets,
            "position_count": len(dashboard.active_positions),
        }

    async def sync_with_strategy_results(
        self, strategy_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synchronize position sizing with latest strategy analysis results.

        Args:
            strategy_results: Results from strategy analysis

        Returns:
            Dictionary with synchronization results
        """
        sync_results = {
            "synced_positions": [],
            "new_signals": [],
            "updated_metrics": [],
        }

        # Process each portfolio in results
        portfolios = strategy_results.get("deduplicated_portfolios", [])

        for portfolio in portfolios:
            ticker = portfolio.get("ticker")
            if not ticker:
                continue

            # Check for new signals
            signals = portfolio.get("signals", [])
            if signals:
                latest_signal = signals[-1]

                # Check if this is a new entry signal
                if latest_signal.get("position", 0) > 0:
                    # Calculate position sizing for new signal
                    ps_response = await self.calculate_position_size_for_signal(
                        ticker, latest_signal
                    )

                    sync_results["new_signals"].append(
                        {
                            "symbol": ticker,
                            "signal": latest_signal,
                            "position_sizing": ps_response.__dict__,
                        }
                    )

            # Update metrics for existing positions
            position_analysis = await self.get_position_analysis(ticker)
            if position_analysis["position_tracking"]["position_value"] > 0:
                sync_results["synced_positions"].append(
                    {"symbol": ticker, "current_analysis": position_analysis}
                )

        return sync_results


# Backward compatibility alias
class ServiceCoordinatorWithPositionSizing(EnhancedServiceCoordinator):
    """Backward compatibility alias for enhanced service coordinator."""

    pass
