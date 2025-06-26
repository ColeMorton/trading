"""
Portfolio Orchestrator Module

This module provides the main orchestration logic for portfolio analysis,
managing the workflow from configuration initialization through result export.
"""

from typing import Any, Callable, Dict, List

from app.strategies.ma_cross.exceptions import (
    MACrossConfigurationError,
    MACrossExecutionError,
    MACrossPortfolioError,
)
from app.tools.config_service import ConfigService
from app.tools.error_context import error_context
from app.tools.exceptions import (
    ConfigurationError,
    ExportError,
    StrategyProcessingError,
    SyntheticTickerError,
)
from app.tools.portfolio.allocation import get_allocation_summary
from app.tools.portfolio.collection import export_best_portfolios
from app.tools.portfolio.schema_detection import SchemaVersion, detect_schema_version
from app.tools.portfolio.stop_loss import get_stop_loss_summary

# Import filter_portfolios from the unified location
from app.tools.strategy.filter_portfolios import filter_portfolios
from app.tools.strategy_utils import get_strategy_types
from app.tools.synthetic_ticker import process_synthetic_config

from .ticker_processor import TickerProcessor

# Optional: Import new export system for gradual migration
try:
    from app.tools.export import ExportContext, ExportFormat, ExportManager

    EXPORT_MANAGER_AVAILABLE = True
except ImportError:
    EXPORT_MANAGER_AVAILABLE = False


class PortfolioOrchestrator:
    """
    Orchestrates the portfolio analysis workflow.

    This class manages the complete workflow of portfolio analysis including:
    - Configuration initialization and validation
    - Synthetic ticker processing
    - Strategy execution coordination
    - Portfolio filtering and processing
    - Result export
    """

    def __init__(self, log: Callable[[str, str], None], use_new_export: bool = False):
        """
        Initialize the orchestrator.

        Args:
            log: Logging function
            use_new_export: Whether to use the new export system (default: False)
        """
        self.log = log
        self.ticker_processor = TickerProcessor(log)
        self.use_new_export = use_new_export and EXPORT_MANAGER_AVAILABLE

        if self.use_new_export:
            self.export_manager = ExportManager()
            self.log("Using new unified export system", "info")

    def run(self, config: Dict[str, Any]) -> bool:
        """
        Run the complete portfolio analysis workflow.

        Args:
            config: Configuration dictionary

        Returns:
            bool: True if successful, False otherwise

        Raises:
            MACrossConfigurationError: If configuration is invalid
            MACrossExecutionError: If strategy execution fails
            MACrossPortfolioError: If portfolio processing fails
            ExportError: If result export fails
        """
        try:
            # Step 1: Initialize configuration
            config = self._initialize_configuration(config)

            # Step 2: Process synthetic configuration if needed
            config = self._process_synthetic_configuration(config)

            # Step 3: Get strategy types
            strategies = self._get_strategies(config)

            # Step 4: Execute strategies
            all_portfolios = self._execute_strategies(config, strategies)

            # Step 5: Process results if any
            if all_portfolios:
                # Filter and process portfolios
                filtered_portfolios = self._filter_and_process_portfolios(
                    all_portfolios, config
                )

                # Export results
                if filtered_portfolios:
                    self._export_results(filtered_portfolios, config)
            else:
                self.log("No portfolios returned from strategies", "warning")

            return True

        except Exception as e:
            self.log(f"Orchestration failed: {str(e)}", "error")
            raise

    def _initialize_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize and validate configuration.

        Args:
            config: Raw configuration dictionary

        Returns:
            Processed configuration

        Raises:
            MACrossConfigurationError: If configuration is invalid
        """
        with error_context(
            "Initializing configuration",
            self.log,
            {
                ConfigurationError: MACrossConfigurationError,
                Exception: MACrossConfigurationError,
            },
            reraise=True,
        ):
            return ConfigService.process_config(config)

    def _process_synthetic_configuration(
        self, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process synthetic ticker configuration if enabled.

        Args:
            config: Configuration dictionary

        Returns:
            Updated configuration

        Raises:
            SyntheticTickerError: If synthetic configuration is invalid
        """
        with error_context(
            "Processing synthetic ticker configuration",
            self.log,
            {ValueError: SyntheticTickerError},
        ):
            return process_synthetic_config(config, self.log)

    def _get_strategies(self, config: Dict[str, Any]) -> List[str]:
        """
        Get list of strategies to execute.

        Args:
            config: Configuration dictionary

        Returns:
            List of strategy types
        """
        return get_strategy_types(config, self.log, "SMA")

    def _execute_strategies(
        self, config: Dict[str, Any], strategies: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Execute all strategies and collect results.

        Args:
            config: Configuration dictionary
            strategies: List of strategy types to execute

        Returns:
            Combined list of portfolios from all strategies

        Raises:
            MACrossExecutionError: If strategy execution fails
        """
        all_portfolios = []

        for strategy_type in strategies:
            with error_context(
                f"Executing {strategy_type} strategy",
                self.log,
                {
                    StrategyProcessingError: MACrossExecutionError,
                    Exception: MACrossExecutionError,
                },
                reraise=True,
            ):
                # Create strategy-specific config
                strategy_config = config.copy()
                strategy_config["STRATEGY_TYPE"] = strategy_type

                # Execute strategy using optimal method (concurrent for 3+ tickers)
                portfolios = self.ticker_processor.execute_strategy(
                    strategy_config, strategy_type
                )

                if portfolios:
                    all_portfolios.extend(portfolios)
                    self.log(f"{strategy_type} portfolios: {len(portfolios)}", "info")
                else:
                    self.log(f"{strategy_type} portfolios: 0", "info")

        return all_portfolios

    def _filter_and_process_portfolios(
        self, portfolios: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filter and process portfolios including schema detection and normalization.

        Args:
            portfolios: List of portfolio dictionaries
            config: Configuration dictionary

        Returns:
            Filtered and processed portfolios

        Raises:
            MACrossPortfolioError: If portfolio processing fails
        """
        with error_context(
            "Processing portfolios",
            self.log,
            {Exception: MACrossPortfolioError},
            reraise=True,
        ):
            # Detect schema version
            schema_version = detect_schema_version(portfolios)
            self.log(
                f"Detected schema version for export: {schema_version.name}", "info"
            )

            # Convert portfolios list to DataFrame for filtering
            import polars as pl

            if portfolios:
                portfolios_df = pl.DataFrame(portfolios)
            else:
                portfolios_df = pl.DataFrame()

            # Filter portfolios with strategy filtering enabled for portfolios_filtered export
            filtered_portfolios_df = filter_portfolios(portfolios_df, config, self.log)

            # Convert DataFrame back to list of dictionaries
            if len(filtered_portfolios_df) > 0:
                filtered_portfolios = filtered_portfolios_df.to_dicts()
            else:
                filtered_portfolios = []

            # Log extended schema information if available
            if schema_version == SchemaVersion.EXTENDED and filtered_portfolios:
                # Log allocation summary
                allocation_summary = get_allocation_summary(
                    filtered_portfolios, self.log
                )
                self.log(f"Allocation summary: {allocation_summary}", "info")

                # Log stop loss summary
                stop_loss_summary = get_stop_loss_summary(filtered_portfolios, self.log)
                self.log(f"Stop loss summary: {stop_loss_summary}", "info")

            return filtered_portfolios

    def _export_results(
        self, portfolios: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> None:
        """
        Export portfolio results.

        Args:
            portfolios: List of portfolios to export
            config: Configuration dictionary

        Raises:
            ExportError: If export fails
        """
        with error_context("Exporting portfolios", self.log, {Exception: ExportError}):
            if self.use_new_export:
                # Use new export system
                self._export_with_manager(portfolios, config)
            else:
                # Use legacy export system
                export_best_portfolios(portfolios, config, self.log)

    def _export_with_manager(
        self, portfolios: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> None:
        """
        Export portfolios using the new unified export manager.

        Args:
            portfolios: List of portfolios to export
            config: Configuration dictionary

        Raises:
            ExportError: If export fails
        """
        # Sort portfolios
        from app.tools.portfolio.collection import sort_portfolios

        sorted_portfolios = sort_portfolios(portfolios, config)
        sort_by = config.get("SORT_BY", "Total Return [%]")

        # Prepare data for export by converting to DataFrame
        import polars as pl

        df = pl.DataFrame(sorted_portfolios)

        # Create export context
        context = ExportContext(
            data=df,
            format=ExportFormat.CSV,
            feature_path="portfolios/portfolios_best",
            config=config,
            log=self.log,
        )

        # Export using the new system
        result = self.export_manager.export(context)

        if result.success:
            self.log(
                f"Exported {result.rows_exported} portfolios sorted by {sort_by}",
                "info",
            )
        else:
            raise ExportError(f"Export failed: {result.error_message}")
