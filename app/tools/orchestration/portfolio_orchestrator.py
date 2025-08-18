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
            # Check if we should skip analysis and load existing portfolios
            if config.get("skip_analysis", False):
                self.log(
                    "Skip analysis mode enabled - loading existing portfolios", "info"
                )
                all_portfolios = self._load_existing_portfolios(config)
            else:
                # Step 1: Initialize configuration
                config = self._initialize_configuration(config)

                # Step 2: Process synthetic configuration if needed
                config = self._process_synthetic_configuration(config)

                # Step 3: Get strategy types
                strategies = self._get_strategies(config)

                # Step 4: Execute strategies
                all_portfolios = self._execute_strategies(config, strategies)

                # Export raw portfolios first - always export to ensure files are created even when empty
                self._export_raw_portfolios(all_portfolios or [], config)

            # Step 5: Export minimums-filtered portfolios
            # Apply minimums filtering and export to portfolios_filtered
            minimums_filtered_portfolios = self._export_minimums_filtered_portfolios(
                all_portfolios or [], config
            )

            # Step 6: Apply extreme filtering and export to portfolios_metrics
            # Apply extreme value analysis to minimums-filtered portfolios
            extreme_filtered_portfolios = (
                self._apply_extreme_filtering_and_process_portfolios(
                    minimums_filtered_portfolios or [], config
                )
            )

            # Export portfolios with extreme value analysis to portfolios_metrics
            self._export_portfolios_metrics(extreme_filtered_portfolios or [], config)

            # Step 7: Export best portfolios based on portfolios_metrics data
            self._export_results(extreme_filtered_portfolios or [], config)

            # Log appropriate messages for empty results
            if not all_portfolios:
                if config.get("skip_analysis", False):
                    self.log(
                        "No existing portfolio files found in data/raw/portfolios/",
                        "warning",
                    )
                else:
                    self.log("No portfolios returned from strategies", "warning")
                self.log(
                    "Created empty CSV files with headers for configured ticker+strategy combinations",
                    "info",
                )

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
        # Preserve the intended strategy type from config instead of always defaulting to SMA
        intended_strategy = None
        if "STRATEGY_TYPE" in config:
            intended_strategy = config["STRATEGY_TYPE"]
        elif "STRATEGY_TYPES" in config and config["STRATEGY_TYPES"]:
            intended_strategy = config["STRATEGY_TYPES"][0]

        return get_strategy_types(config, self.log, intended_strategy or "SMA")

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

    def _apply_extreme_filtering_and_process_portfolios(
        self, portfolios: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply extreme value filtering and process portfolios for portfolios_metrics export.

        Note: This assumes portfolios have already been filtered by minimums criteria.

        Args:
            portfolios: List of portfolio dictionaries (already minimums-filtered)
            config: Configuration dictionary

        Returns:
            Portfolios with extreme value analysis applied

        Raises:
            MACrossPortfolioError: If portfolio processing fails
        """
        with error_context(
            "Processing portfolios for extreme value analysis",
            self.log,
            {Exception: MACrossPortfolioError},
            reraise=True,
        ):
            # Detect schema version
            schema_version = detect_schema_version(portfolios)
            self.log(
                f"Detected schema version for extreme value analysis: {schema_version.name}",
                "info",
            )

            # Convert portfolios list to DataFrame for extreme value filtering
            import polars as pl

            if portfolios:
                portfolios_df = pl.DataFrame(portfolios)
            else:
                portfolios_df = pl.DataFrame()

            # Apply extreme value filtering (this adds Metric Type column and performs extreme value analysis)
            self.log(
                "Applying extreme value filtering for portfolios_metrics export", "info"
            )
            filtered_portfolios_df = filter_portfolios(portfolios_df, config, self.log)

            # Convert DataFrame back to list of dictionaries
            if len(filtered_portfolios_df) > 0:
                filtered_portfolios = filtered_portfolios_df.to_dicts()
                self.log(
                    f"Extreme value filtering: {len(portfolios)} -> {len(filtered_portfolios)} portfolios",
                    "info",
                )
            else:
                filtered_portfolios = []
                self.log(
                    "No portfolios remain after extreme value filtering", "warning"
                )

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

    def _export_raw_portfolios(
        self, portfolios: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> None:
        """
        Export raw portfolios before filtering.

        Args:
            portfolios: List of raw portfolios to export
            config: Configuration dictionary

        Raises:
            ExportError: If export fails
        """
        with error_context(
            "Exporting raw portfolios", self.log, {Exception: ExportError}
        ):
            from app.tools.strategy.export_portfolios import export_portfolios

            try:
                # Check if we're in skip analysis mode and have multiple tickers
                if config.get("skip_analysis", False) and self._has_multiple_tickers(
                    portfolios
                ):
                    # Group portfolios by ticker+strategy and export individually
                    self._export_grouped_portfolios(portfolios, config, "portfolios")
                else:
                    # Normal export for single ticker or non-skip mode
                    _, success = export_portfolios(
                        portfolios=portfolios,
                        config=config,
                        export_type="portfolios",
                        log=self.log,
                    )
                    if success:
                        self.log(
                            f"Successfully exported {len(portfolios)} raw portfolios"
                        )
                    else:
                        self.log("Failed to export raw portfolios", "warning")
            except Exception as e:
                self.log(f"Error exporting raw portfolios: {str(e)}", "error")
                raise ExportError(f"Raw portfolio export failed: {str(e)}")

    def _export_minimums_filtered_portfolios(
        self, portfolios: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply minimums filtering and export to portfolios_filtered directory.

        Args:
            portfolios: List of raw portfolios to filter
            config: Configuration dictionary

        Returns:
            List of portfolios that passed minimums filtering

        Raises:
            ExportError: If export fails
        """
        with error_context(
            "Exporting minimums-filtered portfolios", self.log, {Exception: ExportError}
        ):
            from app.tools.strategy.export_portfolios import export_portfolios

            try:
                # Apply only minimums filtering (no extreme value analysis)
                minimums_filtered = portfolios
                if portfolios and "MINIMUMS" in config:
                    self.log(
                        "Applying MINIMUMS filtering for portfolios_filtered export",
                        "info",
                    )
                    from app.tools.portfolio.filtering_service import (
                        PortfolioFilterService,
                    )

                    filter_service = PortfolioFilterService()
                    minimums_filtered = filter_service.filter_portfolios_list(
                        portfolios, config, self.log
                    )

                    if minimums_filtered:
                        self.log(
                            f"MINIMUMS filtering: {len(portfolios)} -> {len(minimums_filtered)} portfolios",
                            "info",
                        )
                    else:
                        self.log(
                            "No portfolios remain after MINIMUMS filtering", "warning"
                        )
                        minimums_filtered = []

                # Export to portfolios_filtered directory
                skip_analysis = config.get("skip_analysis", False)
                has_multiple_tickers = self._has_multiple_tickers(minimums_filtered)

                if skip_analysis or config.get("USE_CURRENT", False):
                    mode_reason = (
                        "skip analysis mode" if skip_analysis else "USE_CURRENT mode"
                    )
                    self.log(
                        f"Using grouped export for portfolios_filtered ({mode_reason})",
                        "info",
                    )
                    # Group portfolios by ticker+strategy and export individually
                    self._export_grouped_portfolios(
                        minimums_filtered, config, "portfolios_filtered"
                    )
                else:
                    self.log(
                        "Using normal export for portfolios_filtered (minimums only)",
                        "info",
                    )
                    # Normal export for minimums-filtered portfolios
                    _, success = export_portfolios(
                        portfolios=minimums_filtered,
                        config=config,
                        export_type="portfolios_filtered",
                        log=self.log,
                    )
                    if success:
                        self.log(
                            f"Successfully exported {len(minimums_filtered)} minimums-filtered portfolios"
                        )
                    else:
                        self.log(
                            "Failed to export minimums-filtered portfolios", "warning"
                        )

                return minimums_filtered

            except Exception as e:
                self.log(
                    f"Error exporting minimums-filtered portfolios: {str(e)}", "error"
                )
                raise ExportError(
                    f"Minimums-filtered portfolio export failed: {str(e)}"
                )

    def _export_portfolios_metrics(
        self, portfolios: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> None:
        """
        Export portfolios with extreme value analysis to portfolios_metrics directory.

        Args:
            portfolios: List of portfolios with extreme value analysis applied
            config: Configuration dictionary

        Raises:
            ExportError: If export fails
        """
        with error_context(
            "Exporting portfolios_metrics", self.log, {Exception: ExportError}
        ):
            from app.tools.strategy.export_portfolios import export_portfolios

            try:
                skip_analysis = config.get("skip_analysis", False)
                has_multiple_tickers = self._has_multiple_tickers(portfolios)

                self.log(
                    f"Export conditions - skip_analysis: {skip_analysis}, has_multiple_tickers: {has_multiple_tickers}",
                    "debug",
                )

                # Use grouped export for skip analysis mode OR USE_CURRENT mode for individual ticker+strategy files
                use_current = config.get("USE_CURRENT", False)
                if skip_analysis or use_current:
                    mode_reason = (
                        "skip analysis mode" if skip_analysis else "USE_CURRENT mode"
                    )
                    self.log(
                        f"Using grouped export for portfolios_metrics ({mode_reason})",
                        "info",
                    )
                    # Group portfolios by ticker+strategy and export individually
                    self._export_grouped_portfolios(
                        portfolios, config, "portfolios_metrics"
                    )
                else:
                    self.log(
                        "Using normal export for portfolios_metrics (extreme value analysis)",
                        "info",
                    )
                    # Normal export for extreme value portfolios
                    _, success = export_portfolios(
                        portfolios=portfolios,
                        config=config,
                        export_type="portfolios_metrics",
                        log=self.log,
                    )
                    if success:
                        self.log(
                            f"Successfully exported {len(portfolios)} portfolios with extreme value analysis"
                        )
                    else:
                        self.log("Failed to export portfolios_metrics", "warning")
            except Exception as e:
                self.log(f"Error exporting portfolios_metrics: {str(e)}", "error")
                raise ExportError(f"Portfolios_metrics export failed: {str(e)}")

    def _export_results(
        self, portfolios: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> None:
        """
        Export final portfolio results (best portfolios).

        Args:
            portfolios: List of portfolios to export
            config: Configuration dictionary

        Raises:
            ExportError: If export fails
        """
        with error_context(
            "Exporting best portfolios", self.log, {Exception: ExportError}
        ):
            if self.use_new_export:
                # Use new export system
                self._export_with_manager(portfolios, config)
            else:
                skip_analysis = config.get("skip_analysis", False)
                has_multiple_tickers = self._has_multiple_tickers(portfolios)

                self.log(
                    f"Export results conditions - skip_analysis: {skip_analysis}, has_multiple_tickers: {has_multiple_tickers}",
                    "debug",
                )

                # Use grouped export for skip analysis mode OR USE_CURRENT mode for individual ticker+strategy files
                use_current = config.get("USE_CURRENT", False)
                if skip_analysis or use_current:
                    mode_reason = (
                        "skip analysis mode" if skip_analysis else "USE_CURRENT mode"
                    )
                    self.log(
                        f"Using grouped export for portfolios_best ({mode_reason})",
                        "info",
                    )
                    # Group portfolios by ticker+strategy and export individually
                    self._export_grouped_portfolios(
                        portfolios, config, "portfolios_best"
                    )
                else:
                    self.log(
                        "Using legacy export for portfolios_best (standard mode)",
                        "info",
                    )
                    # Use legacy export system for normal mode
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

    def _extract_ticker_from_filename(self, filename: str) -> str:
        """
        Extract ticker symbol from portfolio filename.

        Args:
            filename: Portfolio filename (e.g., "TSLA_D_MACD.csv", "AAVE-USD_D_EMA.csv")

        Returns:
            Ticker symbol (e.g., "TSLA", "AAVE-USD")

        Examples:
            TSLA_D_MACD.csv → TSLA
            AAVE-USD_D_EMA.csv → AAVE-USD
            UNI7083-USD_D.csv → UNI7083-USD
            BTC-USD_4H_SMA.csv → BTC-USD
        """
        # Remove .csv extension first if present
        filename = filename.replace(".csv", "")

        # Extract ticker - everything before the first underscore
        ticker = filename.split("_")[0]

        return ticker

    def _has_multiple_tickers(self, portfolios: List[Dict[str, Any]]) -> bool:
        """
        Check if portfolios contain multiple different tickers.

        Args:
            portfolios: List of portfolio dictionaries

        Returns:
            True if multiple tickers are present, False otherwise
        """
        if not portfolios:
            self.log("_has_multiple_tickers: No portfolios provided", "debug")
            return False

        tickers = set()
        for portfolio in portfolios:
            ticker = portfolio.get("Ticker")
            if ticker:
                tickers.add(ticker)

        self.log(
            f"_has_multiple_tickers: Found {len(tickers)} unique tickers: {list(tickers)[:5]}{'...' if len(tickers) > 5 else ''}",
            "debug",
        )
        return len(tickers) > 1

    def _export_grouped_portfolios(
        self, portfolios: List[Dict[str, Any]], config: Dict[str, Any], export_type: str
    ) -> None:
        """
        Group portfolios by ticker+strategy combination and export each group individually.

        Args:
            portfolios: List of portfolios to group and export
            config: Configuration dictionary
            export_type: Type of export (e.g., "portfolios_filtered")

        Raises:
            ExportError: If any export fails
        """
        from collections import defaultdict

        from app.tools.strategy.export_portfolios import export_portfolios

        # Group portfolios by ticker+strategy combination
        groups = defaultdict(list)

        for portfolio in portfolios:
            ticker = portfolio.get("Ticker", "UNKNOWN")
            # Robust strategy extraction - check multiple possible field names
            strategy = (
                portfolio.get("Strategy Type")
                or portfolio.get("Strategy")
                or portfolio.get("strategy_type")
                or "UNKNOWN"
            )

            if strategy == "UNKNOWN":
                self.log(
                    f"Warning: Portfolio missing strategy type data: {portfolio.keys()}",
                    "warning",
                )

            group_key = f"{ticker}_{strategy}"
            groups[group_key].append(portfolio)

        self.log(
            f"Grouped {len(portfolios)} portfolios into {len(groups)} ticker+strategy combinations",
            "info",
        )

        # Ensure ALL configured ticker+strategy combinations have groups, even if no portfolios were generated
        # This handles cases where strategies fail to complete or all portfolios are filtered out
        configured_strategies = config.get("STRATEGY_TYPES", [])
        configured_tickers = config.get("TICKER", [])
        if isinstance(configured_tickers, str):
            configured_tickers = [configured_tickers]

        # Create groups for every configured combination to ensure consistent file creation
        for strategy in configured_strategies:
            for ticker in configured_tickers:
                group_key = f"{ticker}_{strategy}"
                if group_key not in groups:
                    # Create empty group for this ticker+strategy combination
                    groups[group_key] = []
                    self.log(
                        f"Creating empty group for {ticker} {strategy} (no portfolios generated or all filtered out)",
                        "info",
                    )

        # Log the final group count to verify all combinations are included
        expected_combinations = len(configured_strategies) * len(configured_tickers)
        self.log(
            f"Export will create {len(groups)} files for {expected_combinations} expected ticker+strategy combinations",
            "info",
        )

        # Export each group individually
        export_count = 0
        for group_key, group_portfolios in groups.items():
            try:
                # Handle empty groups (for strategies with no qualifying portfolios)
                if not group_portfolios:
                    # Extract ticker and strategy from group key
                    ticker, strategy = group_key.split("_", 1)
                else:
                    # Extract ticker and strategy from group key - use robust extraction
                    ticker = group_portfolios[0].get("Ticker")
                    strategy = (
                        group_portfolios[0].get("Strategy Type")
                        or group_portfolios[0].get("Strategy")
                        or group_portfolios[0].get("strategy_type")
                        or "SMA"  # Only as last resort for backward compatibility
                    )

                # Create individual config for this ticker+strategy
                group_config = config.copy()
                group_config["TICKER"] = ticker
                group_config["STRATEGY_TYPE"] = strategy
                group_config["STRATEGY_TYPES"] = [strategy]
                group_config[
                    "USE_MA"
                ] = True  # Explicitly ensure strategy suffix is included

                self.log(
                    f"Exporting {len(group_portfolios)} portfolios for {ticker} {strategy}",
                    "info",
                )

                # Export this group
                _, success = export_portfolios(
                    portfolios=group_portfolios,
                    config=group_config,
                    export_type=export_type,
                    log=self.log,
                )

                if success:
                    export_count += len(group_portfolios)
                    self.log(
                        f"Successfully exported {ticker}_{strategy} group to individual file",
                        "info",
                    )
                else:
                    self.log(f"Failed to export {ticker}_{strategy} group", "warning")

            except Exception as e:
                self.log(f"Error exporting group {group_key}: {str(e)}", "error")
                raise ExportError(f"Group export failed for {group_key}: {str(e)}")

        self.log(
            f"Successfully exported {export_count} total portfolios in {len(groups)} individual files",
            "info",
        )

    def _load_existing_portfolios(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Load existing portfolio files from data/raw/portfolios/ directory.

        Args:
            config: Configuration dictionary

        Returns:
            List of portfolio dictionaries loaded from CSV files

        Raises:
            MACrossPortfolioError: If no portfolio files are found or loading fails
        """
        from pathlib import Path

        import polars as pl

        from app.tools.project_utils import get_project_root

        with error_context(
            "Loading existing portfolios",
            self.log,
            {Exception: MACrossPortfolioError},
            reraise=True,
        ):
            # Determine portfolio directory
            project_root = Path(get_project_root())
            portfolio_dir = project_root / "data" / "raw" / "portfolios"

            if not portfolio_dir.exists():
                raise MACrossPortfolioError(
                    f"Portfolio directory does not exist: {portfolio_dir}"
                )

            # Get configured ticker list for filtering - handle synthetic mode
            if config.get("USE_SYNTHETIC", False):
                # In synthetic mode, create synthetic ticker name for file matching
                ticker_1 = config.get("TICKER_1", "")
                ticker_2 = config.get("TICKER_2", "")
                if ticker_1 and ticker_2:
                    synthetic_ticker = f"{ticker_1}_{ticker_2}"
                    configured_tickers = [synthetic_ticker]
                    self.log(
                        f"Synthetic mode: looking for portfolio files matching {synthetic_ticker}",
                        "info",
                    )
                else:
                    configured_tickers = []
            else:
                # Normal mode: use TICKER field
                configured_tickers = config.get("TICKER", [])
                if isinstance(configured_tickers, str):
                    configured_tickers = [configured_tickers]

            # Find all CSV files in the portfolio directory
            all_csv_files = list(portfolio_dir.glob("*.csv"))

            if not all_csv_files:
                raise MACrossPortfolioError(f"No CSV files found in {portfolio_dir}")

            # Filter CSV files to only include those matching configured tickers
            csv_files = []
            for csv_file in all_csv_files:
                ticker = self._extract_ticker_from_filename(csv_file.name)
                if ticker in configured_tickers:
                    csv_files.append(csv_file)

            if not csv_files:
                self.log(
                    f"No portfolio files found matching configured tickers: {configured_tickers}",
                    "warning",
                )
                raise MACrossPortfolioError(
                    f"No portfolio files found for configured tickers: {configured_tickers}"
                )

            self.log(
                f"Found {len(all_csv_files)} total portfolio files, {len(csv_files)} match configured tickers",
                "info",
            )

            all_portfolios = []

            # Load each CSV file
            for csv_file in csv_files:
                try:
                    self.log(f"Loading portfolio file: {csv_file.name}", "info")

                    # Load CSV using polars
                    df = pl.read_csv(csv_file)

                    # Convert to list of dictionaries
                    portfolios = df.to_dicts()
                    all_portfolios.extend(portfolios)

                    self.log(
                        f"Loaded {len(portfolios)} portfolios from {csv_file.name}",
                        "info",
                    )

                except Exception as e:
                    self.log(f"Failed to load {csv_file.name}: {str(e)}", "error")
                    raise MACrossPortfolioError(
                        f"Failed to load portfolio file {csv_file.name}: {str(e)}"
                    )

            self.log(
                f"Successfully loaded {len(all_portfolios)} total portfolios from {len(csv_files)} files",
                "info",
            )

            # Apply MINIMUMS filtering to loaded portfolios if configuration exists
            if "MINIMUMS" in config and all_portfolios:
                self.log("Applying MINIMUMS filtering to loaded portfolios", "info")
                from app.tools.portfolio.filtering_service import PortfolioFilterService

                # Use the filtering service to apply MINIMUMS
                filter_service = PortfolioFilterService()
                filtered_portfolios = filter_service.filter_portfolios_list(
                    all_portfolios, config, self.log
                )

                if filtered_portfolios:
                    self.log(
                        f"MINIMUMS filtering: {len(all_portfolios)} -> {len(filtered_portfolios)} portfolios remain",
                        "info",
                    )
                    return filtered_portfolios
                else:
                    self.log("No portfolios remain after MINIMUMS filtering", "warning")
                    return []

            return all_portfolios
