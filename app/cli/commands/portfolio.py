"""
Portfolio command implementations.

This module provides CLI commands for portfolio processing, aggregation,
and management operations.
"""

import os
from pathlib import Path
from typing import List, Optional

import pandas as pd
import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from app.tools.console_logging import ConsoleLogger
from app.tools.portfolio.strategy_types import derive_use_sma

from ..config import ConfigLoader
from ..models.portfolio import (
    Direction,
    PortfolioConfig,
    PortfolioProcessingConfig,
    PortfolioReviewConfig,
    ReviewStrategyConfig,
    StrategyType,
)
from ..utils import resolve_portfolio_path

# Create portfolio sub-app
app = typer.Typer(
    name="portfolio", help="Portfolio processing and aggregation", no_args_is_help=True
)

console = Console()


def load_strategies_from_raw_csv(
    raw_strategies_name: str, console: ConsoleLogger = None
) -> List[ReviewStrategyConfig]:
    """
    Load strategy configurations from a CSV file in data/raw/strategies/.

    Args:
        raw_strategies_name: Name of the CSV file (without .csv extension)

    Returns:
        List of ReviewStrategyConfig objects

    Raises:
        ValueError: If CSV file doesn't exist or has invalid data
    """
    from pathlib import Path

    import polars as pl

    from app.tools.portfolio.format import convert_csv_to_strategy_config

    # Construct CSV file path
    csv_path = Path("data/raw/strategies") / f"{raw_strategies_name}.csv"

    if not csv_path.exists():
        raise ValueError(f"Raw strategies CSV file does not exist: {csv_path}")

    try:
        # Load CSV using polars
        df = pl.read_csv(str(csv_path))

        # Use console logger if provided, fallback to rprint for backward compatibility
        if console is None:
            console = ConsoleLogger()

        # Simple logging function for the conversion
        def log(message: str, level: str = "info"):
            if level == "error":
                console.error(message)
            elif level == "warning":
                console.warning(message)
            else:
                console.debug(message)

        # Use existing CSV conversion system
        config = {"BASE_DIR": ".", "REFRESH": True, "USE_HOURLY": False}
        strategy_configs = convert_csv_to_strategy_config(df, log, config)

        # Convert to ReviewStrategyConfig objects
        review_strategies = []
        for strategy_config in strategy_configs:
            # Map strategy types
            strategy_type_str = strategy_config.get("STRATEGY_TYPE", "SMA")
            try:
                strategy_type = StrategyType(strategy_type_str)
            except ValueError:
                # Default to SMA if unknown strategy type
                strategy_type = StrategyType.SMA

            # Map direction
            direction_str = strategy_config.get("DIRECTION", "long").lower()
            try:
                direction = Direction(direction_str)
            except ValueError:
                # Default to long if unknown direction
                direction = Direction.LONG

            # Create ReviewStrategyConfig
            review_strategy = ReviewStrategyConfig(
                ticker=strategy_config["TICKER"],
                fast_period=strategy_config.get("FAST_PERIOD", 20),
                slow_period=strategy_config.get("SLOW_PERIOD", 50),
                strategy_type=strategy_type,
                direction=direction,
                stop_loss=strategy_config.get("STOP_LOSS"),
                position_size=strategy_config.get("POSITION_SIZE", 1.0),
                use_hourly=strategy_config.get("USE_HOURLY", False),
                rsi_window=strategy_config.get("RSI_WINDOW"),
                rsi_threshold=strategy_config.get("RSI_THRESHOLD"),
                signal_period=strategy_config.get("SIGNAL_PERIOD", 9),
            )

            review_strategies.append(review_strategy)

        console.success(
            f"Successfully loaded {len(review_strategies)} strategies from {csv_path}"
        )
        return review_strategies

    except Exception as e:
        raise ValueError(f"Failed to load strategies from CSV {csv_path}: {e}")


@app.command()
def update(
    ctx: typer.Context,
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    portfolio_file: Optional[str] = typer.Option(
        None, "--portfolio", "-f", help="Portfolio filename to process"
    ),
    refresh: bool = typer.Option(
        True, "--refresh/--no-refresh", help="Whether to refresh cached data"
    ),
    export_equity: bool = typer.Option(
        False, "--export-equity", help="Export equity data"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview configuration without executing"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Update portfolio results and aggregation.

    This command processes portfolio files, aggregates strategy results,
    and generates updated portfolio summaries with performance metrics.

    Examples:
        trading-cli portfolio update --profile default_portfolio
        trading-cli portfolio update --portfolio DAILY.csv --export-equity
        trading-cli portfolio update --portfolio risk_on.csv --dry-run
    """
    try:
        # Get global CLI options
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False
        global_show_output = ctx.obj.get("show_output", False) if ctx.obj else False
        global_quiet = ctx.obj.get("quiet", True) if ctx.obj else True

        # Initialize console logger - portfolio commands default to rich output
        is_verbose = verbose or global_verbose
        is_quiet = False  # Portfolio commands always show rich output
        console = ConsoleLogger(verbose=is_verbose, quiet=is_quiet)
        # Load configuration
        loader = ConfigLoader()

        # Build configuration overrides from CLI arguments
        overrides = {}
        if portfolio_file:
            overrides["portfolio"] = resolve_portfolio_path(portfolio_file)
        if not refresh:
            overrides["refresh"] = False
        if export_equity:
            overrides["equity_data"] = {"export": True}

        overrides["dry_run"] = dry_run

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, PortfolioConfig, overrides)
        else:
            config = loader.load_from_profile(
                "default_portfolio", PortfolioConfig, overrides
            )

        if dry_run:
            _show_portfolio_config_preview(config, console)
            return

        console.debug("Loading portfolio processing module...")

        # Import and execute portfolio update
        from ...strategies.update_portfolios import run as update_portfolios_run
        from ...tools.config_management import normalize_config

        console.heading("Updating Portfolio Results", level=1)

        # Convert Pydantic model to dict for existing functions
        config_dict = config.dict()

        # Map CLI config to existing config format
        legacy_config = {
            "PORTFOLIO": config.portfolio,
            "REFRESH": config.refresh,
            "DIRECTION": config.direction,
            "SORT_BY": config.sort_by,
            "SORT_ASC": config.sort_ascending,
            "USE_EXTENDED_SCHEMA": config.use_extended_schema,
            "EQUITY_DATA": {
                "EXPORT": config.equity_data.export,
                "METRIC": config.equity_data.metric,
                "FORCE_FRESH_ANALYSIS": config.equity_data.force_fresh_analysis,
            },
            "BASE_DIR": str(config.base_dir),
            "USE_HOURLY": config.use_hourly,
            "USE_4HOUR": config.use_4hour,
            "USE_2DAY": config.use_2day,
        }

        # Normalize the configuration
        normalized_config = normalize_config(legacy_config)

        # Execute portfolio update
        success = update_portfolios_run(
            resolve_portfolio_path(config.portfolio), console
        )

        if success:
            console.success("Portfolio update completed successfully!")
            console.info(f"Processed portfolio: {config.portfolio}")
        else:
            console.error("Portfolio update failed")
            raise typer.Exit(1)

    except Exception as e:
        console.error(f"Error updating portfolio: {e}")
        if verbose or global_verbose:
            raise
        raise typer.Exit(1)


@app.command()
def process(
    ctx: typer.Context,
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    input_dir: Optional[Path] = typer.Option(
        None, "--input-dir", help="Input directory containing portfolio files"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", help="Output directory for processed results"
    ),
    format: str = typer.Option("csv", "--format", help="Output format: csv, json"),
    validate_schemas: bool = typer.Option(
        True, "--validate/--no-validate", help="Validate portfolio schemas"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview processing without executing"
    ),
):
    """
    Process individual portfolio files with comprehensive validation.

    This command processes multiple portfolio files from an input directory,
    validates schemas, normalizes data, and exports results in various formats.

    Examples:
        trading-cli portfolio process --input-dir ./data/raw/strategies --output-dir ./processed
        trading-cli portfolio process --profile portfolio_processing --format json
    """
    try:
        # Get global CLI options
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        # Portfolio commands always show rich output
        console = ConsoleLogger(verbose=global_verbose, quiet=False)

        # Load configuration
        loader = ConfigLoader()

        overrides = {}
        if input_dir:
            overrides["input_dir"] = input_dir
        if output_dir:
            overrides["output_dir"] = output_dir
        if format == "json":
            overrides["export_json"] = True
            overrides["export_csv"] = False

        overrides["validate_schemas"] = validate_schemas
        overrides["dry_run"] = dry_run

        if profile:
            config = loader.load_from_profile(
                profile, PortfolioProcessingConfig, overrides
            )
        else:
            config = loader.load_from_profile(
                "default_portfolio", PortfolioProcessingConfig, overrides
            )

        if dry_run:
            _show_processing_config_preview(config, console)
            return

        console.heading("Processing Portfolio Files", level=1)

        # Import required modules for portfolio processing
        import json
        from pathlib import Path

        from ...tools.portfolio.schema_validation import (
            batch_validate_csv_files,
            generate_schema_compliance_report,
        )

        # Discover portfolio files in input directory
        input_path = Path(config.input_dir)
        if not input_path.exists():
            console.error(f"Input directory does not exist: {input_path}")
            raise typer.Exit(1)

        # Find CSV files
        csv_files = list(input_path.glob("*.csv"))
        if not csv_files:
            console.warning(f"No CSV files found in {input_path}")
            return

        console.info(f"Found {len(csv_files)} portfolio CSV files to process")

        # Create output directory
        output_path = Path(config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Process files
        results = {}
        processed_count = 0
        valid_count = 0

        # Create progress bar for file processing
        with console.progress_context("File Processing") as progress:
            file_task = progress.add_task("Processing files...", total=len(csv_files))

            for csv_file in csv_files:
                progress.update(file_task, description=f"Processing {csv_file.name}...")
                console.progress(f"Processing: {csv_file.name}")

            try:
                # Load and process the CSV file
                import pandas as pd

                df = pd.read_csv(csv_file)
                file_results = {
                    "source_file": str(csv_file),
                    "processed": True,
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "validation": None,
                    "exported_formats": [],
                }

                # Schema validation if enabled
                if config.validate_schemas:
                    from ...tools.portfolio.schema_validation import validate_csv_schema

                    try:
                        validation_result = validate_csv_schema(csv_file, strict=False)
                        file_results["validation"] = validation_result

                        if validation_result["is_valid"]:
                            console.success(
                                f"Schema validation passed for {csv_file.name}"
                            )
                            valid_count += 1
                        else:
                            violations = len(validation_result.get("violations", []))
                            warnings = len(validation_result.get("warnings", []))
                            console.warning(
                                f"Schema validation for {csv_file.name}: {violations} violations, {warnings} warnings"
                            )

                            # Generate and save compliance report
                            report = generate_schema_compliance_report(
                                validation_result
                            )
                            report_file = (
                                output_path / f"{csv_file.stem}_validation_report.txt"
                            )
                            report_file.write_text(report)
                            console.info(f"Validation report saved: {report_file.name}")

                    except Exception as e:
                        console.error(
                            f"Schema validation failed for {csv_file.name}: {e}"
                        )
                        file_results["validation"] = {
                            "is_valid": False,
                            "error": str(e),
                        }

                # Data normalization and processing
                if config.normalize_data:
                    # Basic data cleaning
                    numeric_columns = df.select_dtypes(include=["number"]).columns
                    df[numeric_columns] = df[numeric_columns].fillna(0)

                    # Remove completely empty columns
                    df = df.dropna(axis=1, how="all")

                    console.info(
                        f"Data normalized for {csv_file.name}: {len(df)} rows, {len(df.columns)} columns"
                    )

                # Export in requested formats
                output_name = f"processed_{csv_file.stem}"

                if config.export_csv:
                    csv_output = output_path / f"{output_name}.csv"
                    df.to_csv(csv_output, index=False)
                    file_results["exported_formats"].append("CSV")
                    console.success(f"Exported CSV: {csv_output.name}")

                if config.export_json:
                    json_output = output_path / f"{output_name}.json"
                    df.to_json(json_output, orient="records", indent=2)
                    file_results["exported_formats"].append("JSON")
                    console.success(f"Exported JSON: {json_output.name}")

                processed_count += 1
                progress.update(file_task, advance=1)

            except Exception as e:
                console.error(f"Processing failed for {csv_file.name}: {e}")
                file_results = {
                    "source_file": str(csv_file),
                    "processed": False,
                    "error": str(e),
                }
                progress.update(file_task, advance=1)

            results[str(csv_file)] = file_results

        # Generate summary report
        summary = {
            "total_files": len(csv_files),
            "processed_successfully": processed_count,
            "schema_valid_files": valid_count,
            "processing_date": str(pd.Timestamp.now()),
            "configuration": {
                "input_dir": str(config.input_dir),
                "output_dir": str(config.output_dir),
                "validate_schemas": config.validate_schemas,
                "normalize_data": config.normalize_data,
                "export_csv": config.export_csv,
                "export_json": config.export_json,
            },
            "file_results": results,
        }

        # Save summary report (convert numpy types to native Python types)
        def convert_numpy_types(obj):
            """Convert numpy types to native Python types for JSON serialization."""
            if hasattr(obj, "item"):  # numpy scalar
                return obj.item()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            else:
                return obj

        # Convert summary to native Python types
        json_compatible_summary = convert_numpy_types(summary)

        summary_file = output_path / "processing_summary.json"
        with open(summary_file, "w") as f:
            json.dump(json_compatible_summary, f, indent=2)

        # Display final summary
        _display_processing_summary(summary, console)

        console.success("Portfolio processing completed!")
        console.info(f"Processed {processed_count}/{len(csv_files)} files successfully")
        console.info(f"Results saved to: {output_path}")
        console.info(f"Summary report: {summary_file.name}")

    except Exception as e:
        console.error(f"Error processing portfolios: {e}")
        raise typer.Exit(1)


@app.command()
def aggregate(
    ctx: typer.Context,
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    by_ticker: bool = typer.Option(
        True, "--by-ticker/--no-by-ticker", help="Aggregate results by ticker"
    ),
    by_strategy: bool = typer.Option(
        True,
        "--by-strategy/--no-by-strategy",
        help="Aggregate results by strategy type",
    ),
    calculate_breadth: bool = typer.Option(
        True, "--breadth/--no-breadth", help="Calculate breadth metrics"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output filename for aggregated results"
    ),
):
    """
    Aggregate multiple portfolio results with comprehensive metrics.

    This command aggregates portfolio results across different dimensions
    (ticker, strategy type) and calculates breadth metrics and correlations.

    Examples:
        trading-cli portfolio aggregate --by-ticker --output aggregated_results.csv
        trading-cli portfolio aggregate --profile portfolio_processing --no-breadth
    """
    try:
        # Get global CLI options
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        # Portfolio commands always show rich output
        console = ConsoleLogger(verbose=global_verbose, quiet=False)

        loader = ConfigLoader()

        overrides = {
            "aggregate_by_ticker": by_ticker,
            "aggregate_by_strategy": by_strategy,
            "calculate_breadth_metrics": calculate_breadth,
        }

        if profile:
            config = loader.load_from_profile(
                profile, PortfolioProcessingConfig, overrides
            )
        else:
            config = loader.load_from_profile(
                "default_portfolio", PortfolioProcessingConfig, overrides
            )

        console.heading("Aggregating Portfolio Results", level=1)

        # Show aggregation settings
        settings_table = Table(title="Aggregation Settings", show_header=True)
        settings_table.add_column("Setting", style="cyan")
        settings_table.add_column("Enabled", style="green")

        settings_table.add_row("By Ticker", "✓" if config.aggregate_by_ticker else "✗")
        settings_table.add_row(
            "By Strategy", "✓" if config.aggregate_by_strategy else "✗"
        )
        settings_table.add_row(
            "Breadth Metrics", "✓" if config.calculate_breadth_metrics else "✗"
        )
        settings_table.add_row(
            "Filter Open Trades", "✓" if config.filter_open_trades else "✗"
        )
        settings_table.add_row(
            "Filter Signal Entries", "✓" if config.filter_signal_entries else "✗"
        )

        console.table(settings_table)

        # Import required modules for portfolio aggregation
        import json
        from pathlib import Path

        # Discover portfolio files from default locations
        portfolio_dirs = [
            Path("data/raw/strategies"),
            Path("data/raw/strategies/filtered"),
            Path("data/raw/strategies/best"),
        ]

        all_files = []
        for portfolio_dir in portfolio_dirs:
            if portfolio_dir.exists():
                csv_files = list(portfolio_dir.glob("*.csv"))
                all_files.extend(csv_files)
                console.info(f"Found {len(csv_files)} files in {portfolio_dir}")

        if not all_files:
            console.warning("No portfolio files found to aggregate")
            return

        console.heading(f"Aggregating {len(all_files)} Portfolio Files", level=2)

        # Initialize aggregation data structures
        aggregation_results = {
            "by_ticker": {},
            "by_strategy": {},
            "breadth_metrics": {},
            "summary_stats": {},
            "file_count": len(all_files),
            "processing_date": str(pd.Timestamp.now()),
        }

        # Process each file for aggregation
        processed_files = 0
        total_rows = 0

        for csv_file in all_files:
            try:
                # Read the portfolio file
                df = pd.read_csv(csv_file)
                total_rows += len(df)
                processed_files += 1

                # Extract metadata from filename
                file_info = _extract_file_metadata(csv_file.name)

                # Aggregate by ticker if enabled
                if config.aggregate_by_ticker:
                    _aggregate_by_ticker(
                        df, aggregation_results["by_ticker"], file_info
                    )

                # Aggregate by strategy if enabled
                if config.aggregate_by_strategy:
                    _aggregate_by_strategy(
                        df, aggregation_results["by_strategy"], file_info
                    )

                # Update breadth metrics if enabled
                if config.calculate_breadth_metrics:
                    _update_breadth_metrics(
                        df, aggregation_results["breadth_metrics"], file_info
                    )

            except Exception as e:
                console.error(f"Error processing {csv_file.name}: {e}")
                continue

        # Calculate final aggregated metrics
        _calculate_summary_stats(aggregation_results, processed_files, total_rows)

        # Display aggregation results
        _display_aggregation_results(aggregation_results, config, console)

        # Save results if output file specified
        if output_file:
            output_path = Path(output_file)

            # Convert to JSON-serializable format
            def convert_for_json(obj):
                if hasattr(obj, "item"):
                    return obj.item()
                elif isinstance(obj, set):
                    return list(obj)
                elif isinstance(obj, dict):
                    return {k: convert_for_json(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_for_json(v) for v in obj]
                elif pd.isna(obj):
                    return None
                else:
                    return obj

            json_results = convert_for_json(aggregation_results)

            if output_path.suffix.lower() == ".json":
                with open(output_path, "w") as f:
                    json.dump(json_results, f, indent=2)
                console.success(f"Results saved to JSON: {output_path}")
            else:
                # Save as CSV (flattened format)
                _save_aggregation_csv(aggregation_results, output_path)
                console.success(f"Results saved to CSV: {output_path}")

        console.success("Portfolio aggregation completed!")
        console.info(
            f"Processed {processed_files}/{len(all_files)} files with {total_rows:,} total records"
        )

    except Exception as e:
        console.error(f"Error aggregating portfolios: {e}")
        raise typer.Exit(1)


@app.command()
def review(
    ctx: typer.Context,
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    strategy_name: Optional[str] = typer.Option(
        None, "--strategy", help="Single strategy name (e.g., AAPL_SMA_20_50)"
    ),
    ticker: Optional[str] = typer.Option(None, "--ticker", help="Single ticker symbol"),
    benchmark: Optional[str] = typer.Option(
        None, "--benchmark", help="Benchmark symbol for comparison"
    ),
    output_format: str = typer.Option(
        "standard", "--output-format", help="Output format: standard, detailed, json"
    ),
    save_plots: bool = typer.Option(
        True, "--save-plots/--no-plots", help="Generate and save plots"
    ),
    export_stats: bool = typer.Option(
        True, "--export-stats/--no-export", help="Export statistics and risk metrics"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview configuration without executing"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Suppress non-essential output"
    ),
    export_raw_data: bool = typer.Option(
        False, "--export-raw-data", help="Export raw data from VectorBT portfolios"
    ),
    raw_data_formats: Optional[str] = typer.Option(
        None,
        "--raw-data-formats",
        help="Comma-separated export formats: csv,json,parquet,pickle",
    ),
    raw_data_types: Optional[str] = typer.Option(
        None,
        "--raw-data-types",
        help="Comma-separated data types: portfolio_value,returns,trades,orders,positions,statistics,prices,drawdowns,cumulative_returns,all",
    ),
    include_vectorbt_objects: bool = typer.Option(
        False,
        "--include-vectorbt",
        help="Export VectorBT portfolio objects for full functionality",
    ),
    raw_data_output_dir: Optional[str] = typer.Option(
        None,
        "--raw-data-output-dir",
        help="Custom output directory for raw data exports",
    ),
):
    """
    Run comprehensive portfolio review analysis.

    Supports both single and multi-strategy portfolio analysis with benchmark
    comparison, risk metrics calculation, and comprehensive visualization.

    Examples:
        # Single strategy from profile
        trading-cli portfolio review --profile portfolio_review_btc

        # Multi-strategy analysis
        trading-cli portfolio review --profile portfolio_review_multi_crypto

        # Custom single strategy
        trading-cli portfolio review --ticker BTC-USD --benchmark SPY

        # Review with custom output
        trading-cli portfolio review --profile portfolio_review_op --output-format detailed --save-plots

        # Export raw data for external analysis
        trading-cli portfolio review --profile portfolio_review_btc --export-raw-data

        # Export specific data types and formats
        trading-cli portfolio review --ticker AAPL --export-raw-data --raw-data-formats csv,json --raw-data-types portfolio_value,returns,trades

        # Export with VectorBT objects for full functionality
        trading-cli portfolio review --profile portfolio_review_multi_crypto --export-raw-data --include-vectorbt
    """
    try:
        # Get global CLI options
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        # Portfolio commands always show rich output
        console = ConsoleLogger(verbose=global_verbose, quiet=False)

        # Load configuration
        loader = ConfigLoader()

        # Build configuration overrides from CLI arguments
        overrides = {}

        # Handle single strategy creation from CLI args
        if ticker and not profile:
            # Create single strategy config from CLI args
            strategy_config = {
                "ticker": ticker,
                "fast_period": 20,  # Default values
                "slow_period": 50,
                "strategy_type": "SMA",
                "direction": "long",
                "position_size": 1.0,
                "use_hourly": False,
            }

            overrides["strategies"] = [strategy_config]

            if benchmark:
                overrides["benchmark"] = {
                    "symbol": benchmark,
                    "benchmark_type": "buy_and_hold",
                }

        # Plotting options
        if not save_plots:
            overrides["enable_plotting"] = False

        if not export_stats:
            overrides["calculate_risk_metrics"] = False
            overrides["export_equity_curve"] = False

        # Raw data export options
        if export_raw_data:
            raw_data_config = {"enable": True}

            if raw_data_output_dir:
                raw_data_config["output_dir"] = raw_data_output_dir

            if raw_data_formats:
                formats = [f.strip().lower() for f in raw_data_formats.split(",")]
                raw_data_config["export_formats"] = formats

            if raw_data_types:
                types = [t.strip().lower() for t in raw_data_types.split(",")]
                raw_data_config["data_types"] = types

            if include_vectorbt_objects:
                raw_data_config["include_vectorbt_object"] = True

            overrides["raw_data_export"] = raw_data_config

        overrides["dry_run"] = dry_run

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, PortfolioReviewConfig, overrides)
        else:
            if not ticker:
                console.error("Either --profile or --ticker must be specified")
                raise typer.Exit(1)

            # Create minimal config template for single ticker
            template = {
                "strategies": [overrides["strategies"][0]]
                if "strategies" in overrides
                else [],
                "start_date": "2020-01-01",
                "end_date": "2024-12-31",
                "init_cash": 10000.0,
                "fees": 0.001,
                "calculate_risk_metrics": True,
                "export_equity_curve": True,
                "enable_plotting": True,
            }
            config = loader.load_from_dict(template, PortfolioReviewConfig, overrides)

        # Handle raw_strategies CSV loading
        if config.raw_strategies:
            console.info(f"Loading strategies from CSV: {config.raw_strategies}.csv")

            try:
                # Load strategies from CSV using the utility function
                csv_strategies = load_strategies_from_raw_csv(
                    config.raw_strategies, console
                )

                # Override the strategies in config
                config.strategies = csv_strategies

                # Modify output directories to include raw_strategies filename as subdirectory
                base_plot_dir = config.plot_config.output_dir
                config.plot_config.output_dir = base_plot_dir / config.raw_strategies

                # Modify raw data export directory if enabled
                if config.raw_data_export.enable:
                    base_export_dir = config.raw_data_export.output_dir
                    config.raw_data_export.output_dir = (
                        base_export_dir / config.raw_strategies
                    )

                console.success(
                    f"Successfully loaded {len(csv_strategies)} strategies from CSV"
                )
                console.debug(
                    f"Modified output directories to include subdirectory: {config.raw_strategies}"
                )

            except Exception as e:
                console.error(f"Failed to load strategies from CSV: {e}")
                raise typer.Exit(1)

        # Validate that we have strategies after potential CSV loading
        if not config.strategies and not config.raw_strategies:
            console.error(
                "Configuration error: Either 'strategies' must be provided or 'raw_strategies' must reference a valid CSV file"
            )
            raise typer.Exit(1)

        if not config.strategies and config.raw_strategies:
            console.error(
                f"Configuration error: No strategies were loaded from raw_strategies CSV file: {config.raw_strategies}"
            )
            raise typer.Exit(1)

        if dry_run:
            _show_portfolio_review_config_preview(config, console)
            return

        if verbose:
            console.debug("Loading portfolio review services...")

        # Import portfolio review services
        from ...contexts.portfolio.services.benchmark_comparison_service import (
            BenchmarkComparisonService,
        )
        from ...contexts.portfolio.services.benchmark_comparison_service import (
            BenchmarkConfig as ServiceBenchmarkConfig,
        )
        from ...contexts.portfolio.services.portfolio_data_export_service import (
            DataType,
            ExportConfig,
            ExportFormat,
        )
        from ...contexts.portfolio.services.portfolio_review_service import (
            PortfolioReviewConfig as ServiceConfig,
        )
        from ...contexts.portfolio.services.portfolio_review_service import (
            PortfolioReviewService,
        )
        from ...contexts.portfolio.services.portfolio_review_service import (
            StrategyConfig as ServiceStrategyConfig,
        )
        from ...contexts.portfolio.services.portfolio_visualization_service import (
            PlotConfig as ServicePlotConfig,
        )
        from ...contexts.portfolio.services.portfolio_visualization_service import (
            PortfolioVisualizationService,
        )
        from ...contexts.portfolio.services.risk_metrics_calculator import (
            RiskMetricsCalculator,
        )

        # Convert Pydantic models to service configuration
        service_strategies = []
        for strategy in config.strategies:
            service_strategy = ServiceStrategyConfig(
                ticker=strategy.ticker,
                fast_period=strategy.fast_period,
                slow_period=strategy.slow_period,
                strategy_type=strategy.strategy_type.value
                if hasattr(strategy.strategy_type, "value")
                else strategy.strategy_type,
                direction=strategy.direction.value,
                stop_loss=strategy.stop_loss,
                position_size=strategy.position_size,
                use_sma=derive_use_sma(
                    strategy.strategy_type.value
                    if hasattr(strategy.strategy_type, "value")
                    else strategy.strategy_type
                ),
                use_hourly=strategy.use_hourly,
                rsi_window=strategy.rsi_window,
                rsi_threshold=strategy.rsi_threshold,
                signal_period=strategy.signal_period,
            )
            service_strategies.append(service_strategy)

        # Convert raw data export configuration
        export_config = None
        if config.raw_data_export.enable:
            # Convert CLI enum strings to service enums
            export_formats = []
            for fmt_str in config.raw_data_export.export_formats:
                if hasattr(ExportFormat, fmt_str.upper()):
                    export_formats.append(getattr(ExportFormat, fmt_str.upper()))

            data_types = []
            for type_str in config.raw_data_export.data_types:
                if hasattr(DataType, type_str.upper()):
                    data_types.append(getattr(DataType, type_str.upper()))

            export_config = ExportConfig(
                output_dir=str(config.raw_data_export.output_dir),
                export_formats=export_formats,
                data_types=data_types,
                include_vectorbt_object=config.raw_data_export.include_vectorbt_object,
                filename_prefix=config.raw_data_export.filename_prefix,
                filename_suffix=config.raw_data_export.filename_suffix,
                compress=config.raw_data_export.compress,
            )

        service_config = ServiceConfig(
            strategies=service_strategies,
            start_date=config.start_date,
            end_date=config.end_date,
            init_cash=config.init_cash,
            fees=config.fees,
            benchmark_symbol=config.benchmark.symbol if config.benchmark else None,
            benchmark_type=config.benchmark.benchmark_type.value
            if config.benchmark
            else None,
            enable_plotting=config.enable_plotting,
            export_equity_curve=config.export_equity_curve,
            calculate_risk_metrics=config.calculate_risk_metrics,
            export_raw_data=config.raw_data_export.enable,
            raw_data_export_config=export_config,
        )

        # Initialize portfolio review service
        review_service = PortfolioReviewService(service_config)

        console.heading("Running Portfolio Review Analysis", level=2)

        # Run analysis based on strategy count
        if config.is_single_strategy:
            console.info(f"Analyzing single strategy: {config.strategies[0].ticker}")
            results = review_service.run_single_strategy_review(service_strategies[0])
        else:
            console.info(
                f"Analyzing {len(config.strategies)} strategies across {len(config.unique_tickers)} tickers"
            )
            results = review_service.run_multi_strategy_review()

        # Display results
        _display_portfolio_review_results(results, config, output_format, console)

        # Generate visualizations if enabled
        if config.enable_plotting and save_plots:
            console.heading("Generating Visualizations", level=2)

            plot_config = ServicePlotConfig(
                output_dir=str(config.plot_config.output_dir),
                width=config.plot_config.width,
                height=config.plot_config.height,
                save_html=config.plot_config.save_html,
                save_png=config.plot_config.save_png,
                include_benchmark=config.plot_config.include_benchmark,
                include_risk_metrics=config.plot_config.include_risk_metrics,
            )

            viz_service = PortfolioVisualizationService(plot_config)
            title_prefix = (
                f"{config.strategies[0].ticker}"
                if config.is_single_strategy
                else "Multi-Strategy Portfolio"
            )

            # Handle risk metrics parameter for visualization
            risk_metrics_param = None
            if hasattr(results.risk_metrics, "var_95"):
                risk_metrics_param = results.risk_metrics

            viz_results = viz_service.create_comprehensive_portfolio_plots(
                results.portfolio,
                results.benchmark_portfolio,
                risk_metrics_param,
                title_prefix=title_prefix,
            )

            if viz_results.success:
                console.success(
                    f"Generated {len(viz_results.plot_paths)} visualization files"
                )
                if global_verbose:
                    for plot_path in viz_results.plot_paths:
                        console.debug(f"Plot saved: {plot_path}")
            else:
                console.warning(
                    f"Visualization generation failed: {viz_results.error_message}"
                )

        console.success("Portfolio review completed successfully!")

        if config.is_single_strategy:
            console.info(
                f"Analyzed strategy: {config.strategies[0].ticker} ({config.strategies[0].strategy_type.value})"
            )
        else:
            console.info(
                f"Analyzed {len(config.strategies)} strategies across {len(config.unique_tickers)} tickers"
            )

    except Exception as e:
        console.error(f"Error in portfolio review: {e}")
        if verbose:
            raise
        raise typer.Exit(1)


def _show_portfolio_config_preview(config: PortfolioConfig, console: ConsoleLogger):
    """Display portfolio configuration preview for dry run."""
    table = Table(title="Portfolio Configuration Preview", show_header=True)
    table.add_column("Parameter", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Portfolio File", str(config.portfolio))
    table.add_row("Refresh Data", str(config.refresh))
    table.add_row("Direction", config.direction)
    table.add_row("Sort By", config.sort_by)
    table.add_row("Sort Ascending", str(config.sort_ascending))
    table.add_row("Use Extended Schema", str(config.use_extended_schema))
    table.add_row("Export Equity Data", str(config.equity_data.export))

    if config.equity_data.export:
        table.add_row("Equity Metric", config.equity_data.metric)
        table.add_row(
            "Force Fresh Analysis", str(config.equity_data.force_fresh_analysis)
        )

    console.table(table)
    console.warning("This is a dry run. Use --no-dry-run to execute.")


def _show_processing_config_preview(
    config: PortfolioProcessingConfig, console: ConsoleLogger
):
    """Display portfolio processing configuration preview."""
    table = Table(title="Portfolio Processing Configuration Preview", show_header=True)
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Input Directory", str(config.input_dir))
    table.add_row("Output Directory", str(config.output_dir))
    table.add_row("Export CSV", str(config.export_csv))
    table.add_row("Export JSON", str(config.export_json))
    table.add_row("Validate Schemas", str(config.validate_schemas))
    table.add_row("Process Synthetic Tickers", str(config.process_synthetic_tickers))
    table.add_row("Normalize Data", str(config.normalize_data))

    console.table(table)
    console.warning("This is a dry run. Use --no-dry-run to execute.")


def _display_processing_summary(summary: dict, console: ConsoleLogger):
    """Display portfolio processing summary results."""

    # Processing Summary Table
    summary_table = Table(title="Portfolio Processing Summary", show_header=True)
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Total Files", str(summary["total_files"]))
    summary_table.add_row(
        "Successfully Processed", str(summary["processed_successfully"])
    )
    summary_table.add_row("Schema Valid Files", str(summary["schema_valid_files"]))
    summary_table.add_row("Processing Date", summary["processing_date"])

    console.table(summary_table)

    # File Results Table
    if summary["file_results"]:
        files_table = Table(title="File Processing Results", show_header=True)
        files_table.add_column("File", style="cyan", no_wrap=True)
        files_table.add_column("Status", style="white", no_wrap=True)
        files_table.add_column("Rows", style="yellow", justify="right")
        files_table.add_column("Columns", style="yellow", justify="right")
        files_table.add_column("Schema Valid", style="green", no_wrap=True)
        files_table.add_column("Formats", style="blue")

        for file_path, result in summary["file_results"].items():
            file_name = Path(file_path).name

            if result.get("processed", False):
                status = "✅ Success"
                rows = str(result.get("row_count", 0))
                columns = str(result.get("column_count", 0))

                validation = result.get("validation")
                if validation:
                    schema_valid = "✅ Valid" if validation["is_valid"] else "❌ Invalid"
                else:
                    schema_valid = "⏭️ Skipped"

                formats = ", ".join(result.get("exported_formats", []))
            else:
                status = "❌ Failed"
                rows = "-"
                columns = "-"
                schema_valid = "-"
                formats = "-"

            files_table.add_row(file_name, status, rows, columns, schema_valid, formats)

        console.table(files_table)


def _extract_file_metadata(filename: str) -> dict:
    """Extract metadata from portfolio filename."""
    # Example: AAPL_D_SMA.csv -> ticker=AAPL, timeframe=D, strategy=SMA
    parts = filename.replace(".csv", "").split("_")

    metadata = {
        "filename": filename,
        "ticker": parts[0] if len(parts) > 0 else "UNKNOWN",
        "timeframe": parts[1] if len(parts) > 1 else "D",
        "strategy": parts[2] if len(parts) > 2 else "SMA",
    }

    return metadata


def _aggregate_by_ticker(df: pd.DataFrame, ticker_aggregation: dict, file_info: dict):
    """Aggregate portfolio data by ticker symbol."""
    ticker = file_info["ticker"]

    if ticker not in ticker_aggregation:
        ticker_aggregation[ticker] = {
            "total_strategies": 0,
            "total_rows": 0,
            "avg_score": 0,
            "avg_win_rate": 0,
            "avg_return": 0,
            "best_strategy": None,
            "best_score": 0,
            "strategy_types": set(),
            "timeframes": set(),
        }

    ticker_data = ticker_aggregation[ticker]

    # Update counts
    ticker_data["total_strategies"] += 1
    ticker_data["total_rows"] += len(df)
    ticker_data["strategy_types"].add(file_info["strategy"])
    ticker_data["timeframes"].add(file_info["timeframe"])

    # Calculate metrics if data exists
    if len(df) > 0:
        # Get top strategy from this file
        if "Score" in df.columns:
            top_row = df.loc[df["Score"].idxmax()]
            score = top_row.get("Score", 0)

            # Update averages (running average)
            current_avg_score = ticker_data["avg_score"]
            new_avg_score = (
                (current_avg_score * (ticker_data["total_strategies"] - 1)) + score
            ) / ticker_data["total_strategies"]
            ticker_data["avg_score"] = new_avg_score

            # Update best strategy if this one is better
            if score > ticker_data["best_score"]:
                ticker_data["best_score"] = score
                ticker_data["best_strategy"] = {
                    "filename": file_info["filename"],
                    "strategy": file_info["strategy"],
                    "score": score,
                    "win_rate": top_row.get("Win Rate [%]", 0),
                    "total_return": top_row.get("Total Return [%]", 0),
                    "trades": top_row.get("Total Trades", 0),
                }

            # Update other averages
            if "Win Rate [%]" in df.columns:
                avg_win_rate = df["Win Rate [%]"].mean()
                current_avg_wr = ticker_data["avg_win_rate"]
                ticker_data["avg_win_rate"] = (
                    (current_avg_wr * (ticker_data["total_strategies"] - 1))
                    + avg_win_rate
                ) / ticker_data["total_strategies"]

            if "Total Return [%]" in df.columns:
                avg_return = df["Total Return [%]"].mean()
                current_avg_ret = ticker_data["avg_return"]
                ticker_data["avg_return"] = (
                    (current_avg_ret * (ticker_data["total_strategies"] - 1))
                    + avg_return
                ) / ticker_data["total_strategies"]


def _aggregate_by_strategy(
    df: pd.DataFrame, strategy_aggregation: dict, file_info: dict
):
    """Aggregate portfolio data by strategy type."""
    strategy = file_info["strategy"]

    if strategy not in strategy_aggregation:
        strategy_aggregation[strategy] = {
            "total_files": 0,
            "total_rows": 0,
            "avg_score": 0,
            "avg_win_rate": 0,
            "avg_return": 0,
            "best_performer": None,
            "best_score": 0,
            "tickers": set(),
            "timeframes": set(),
        }

    strategy_data = strategy_aggregation[strategy]

    # Update counts
    strategy_data["total_files"] += 1
    strategy_data["total_rows"] += len(df)
    strategy_data["tickers"].add(file_info["ticker"])
    strategy_data["timeframes"].add(file_info["timeframe"])

    # Calculate metrics if data exists
    if len(df) > 0 and "Score" in df.columns:
        # Get metrics from this file
        avg_score = df["Score"].mean()
        max_score = df["Score"].max()

        # Update running averages
        current_files = strategy_data["total_files"]
        current_avg = strategy_data["avg_score"]
        strategy_data["avg_score"] = (
            (current_avg * (current_files - 1)) + avg_score
        ) / current_files

        # Update best performer if this file has better score
        if max_score > strategy_data["best_score"]:
            best_row = df.loc[df["Score"].idxmax()]
            strategy_data["best_score"] = max_score
            strategy_data["best_performer"] = {
                "filename": file_info["filename"],
                "ticker": file_info["ticker"],
                "score": max_score,
                "win_rate": best_row.get("Win Rate [%]", 0),
                "total_return": best_row.get("Total Return [%]", 0),
                "trades": best_row.get("Total Trades", 0),
            }

        # Update other metrics
        if "Win Rate [%]" in df.columns:
            avg_wr = df["Win Rate [%]"].mean()
            current_avg_wr = strategy_data["avg_win_rate"]
            strategy_data["avg_win_rate"] = (
                (current_avg_wr * (current_files - 1)) + avg_wr
            ) / current_files

        if "Total Return [%]" in df.columns:
            avg_ret = df["Total Return [%]"].mean()
            current_avg_ret = strategy_data["avg_return"]
            strategy_data["avg_return"] = (
                (current_avg_ret * (current_files - 1)) + avg_ret
            ) / current_files


def _update_breadth_metrics(df: pd.DataFrame, breadth_metrics: dict, file_info: dict):
    """Update breadth metrics across all portfolios."""
    if len(df) == 0:
        return

    # Initialize breadth metrics if empty
    if not breadth_metrics:
        breadth_metrics.update(
            {
                "total_strategies": 0,
                "profitable_strategies": 0,
                "high_score_strategies": 0,  # Score > 1.0
                "win_rate_distribution": {"high": 0, "medium": 0, "low": 0},
                "strategy_distribution": {},
                "ticker_coverage": set(),
                "average_metrics": {"score": [], "win_rate": [], "return": []},
            }
        )

    for _, row in df.iterrows():
        breadth_metrics["total_strategies"] += 1

        score = row.get("Score", 0)
        win_rate = row.get("Win Rate [%]", 0)
        total_return = row.get("Total Return [%]", 0)

        # Count profitable strategies
        if total_return > 0:
            breadth_metrics["profitable_strategies"] += 1

        # Count high score strategies
        if score > 1.0:
            breadth_metrics["high_score_strategies"] += 1

        # Win rate distribution
        if win_rate >= 60:
            breadth_metrics["win_rate_distribution"]["high"] += 1
        elif win_rate >= 40:
            breadth_metrics["win_rate_distribution"]["medium"] += 1
        else:
            breadth_metrics["win_rate_distribution"]["low"] += 1

        # Strategy distribution
        strategy = file_info["strategy"]
        if strategy not in breadth_metrics["strategy_distribution"]:
            breadth_metrics["strategy_distribution"][strategy] = 0
        breadth_metrics["strategy_distribution"][strategy] += 1

        # Add to averages
        breadth_metrics["average_metrics"]["score"].append(score)
        breadth_metrics["average_metrics"]["win_rate"].append(win_rate)
        breadth_metrics["average_metrics"]["return"].append(total_return)

    # Add ticker to coverage
    breadth_metrics["ticker_coverage"].add(file_info["ticker"])


def _calculate_summary_stats(
    aggregation_results: dict, processed_files: int, total_rows: int
):
    """Calculate final summary statistics for aggregation."""
    summary = aggregation_results["summary_stats"]

    summary["processed_files"] = processed_files
    summary["total_rows"] = total_rows
    summary["unique_tickers"] = len(aggregation_results["by_ticker"])
    summary["unique_strategies"] = len(aggregation_results["by_strategy"])

    # Calculate breadth metrics summary
    breadth = aggregation_results["breadth_metrics"]
    if breadth:
        total_strategies = breadth["total_strategies"]
        if total_strategies > 0:
            summary["profitability_rate"] = (
                breadth["profitable_strategies"] / total_strategies
            ) * 100
            summary["high_score_rate"] = (
                breadth["high_score_strategies"] / total_strategies
            ) * 100

            # Calculate average metrics
            if breadth["average_metrics"]["score"]:
                summary["overall_avg_score"] = sum(
                    breadth["average_metrics"]["score"]
                ) / len(breadth["average_metrics"]["score"])
            if breadth["average_metrics"]["win_rate"]:
                summary["overall_avg_win_rate"] = sum(
                    breadth["average_metrics"]["win_rate"]
                ) / len(breadth["average_metrics"]["win_rate"])
            if breadth["average_metrics"]["return"]:
                summary["overall_avg_return"] = sum(
                    breadth["average_metrics"]["return"]
                ) / len(breadth["average_metrics"]["return"])


def _display_aggregation_results(
    aggregation_results: dict, config, console: ConsoleLogger
):
    """Display comprehensive aggregation results."""

    # Summary Statistics
    summary_table = Table(title="Aggregation Summary", show_header=True)
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Value", style="green")

    summary = aggregation_results["summary_stats"]
    summary_table.add_row("Total Files", str(summary.get("processed_files", 0)))
    summary_table.add_row("Total Records", f"{summary.get('total_rows', 0):,}")
    summary_table.add_row("Unique Tickers", str(summary.get("unique_tickers", 0)))
    summary_table.add_row("Unique Strategies", str(summary.get("unique_strategies", 0)))

    if "profitability_rate" in summary:
        summary_table.add_row(
            "Profitability Rate", f"{summary['profitability_rate']:.1f}%"
        )
        summary_table.add_row("High Score Rate", f"{summary['high_score_rate']:.1f}%")
        summary_table.add_row(
            "Overall Avg Score", f"{summary.get('overall_avg_score', 0):.2f}"
        )
        summary_table.add_row(
            "Overall Avg Win Rate", f"{summary.get('overall_avg_win_rate', 0):.1f}%"
        )
        summary_table.add_row(
            "Overall Avg Return", f"{summary.get('overall_avg_return', 0):.1f}%"
        )

    console.table(summary_table)

    # Top Tickers by Performance
    if config.aggregate_by_ticker and aggregation_results["by_ticker"]:
        console.heading("Top Performing Tickers", level=2)
        ticker_table = Table(show_header=True)
        ticker_table.add_column("Ticker", style="cyan", no_wrap=True)
        ticker_table.add_column("Strategies", style="yellow", justify="right")
        ticker_table.add_column("Avg Score", style="green", justify="right")
        ticker_table.add_column("Best Score", style="bright_green", justify="right")
        ticker_table.add_column("Best Strategy", style="blue", no_wrap=True)

        # Sort tickers by best score
        sorted_tickers = sorted(
            aggregation_results["by_ticker"].items(),
            key=lambda x: x[1]["best_score"],
            reverse=True,
        )

        for ticker, data in sorted_tickers[:10]:  # Top 10
            best_strategy = (
                data["best_strategy"]["strategy"] if data["best_strategy"] else "N/A"
            )
            ticker_table.add_row(
                ticker,
                str(data["total_strategies"]),
                f"{data['avg_score']:.2f}",
                f"{data['best_score']:.2f}",
                best_strategy,
            )

        console.table(ticker_table)

    # Strategy Performance Comparison
    if config.aggregate_by_strategy and aggregation_results["by_strategy"]:
        console.heading("Strategy Performance Comparison", level=2)
        strategy_table = Table(show_header=True)
        strategy_table.add_column("Strategy", style="cyan", no_wrap=True)
        strategy_table.add_column("Files", style="yellow", justify="right")
        strategy_table.add_column("Tickers", style="yellow", justify="right")
        strategy_table.add_column("Avg Score", style="green", justify="right")
        strategy_table.add_column("Best Score", style="bright_green", justify="right")
        strategy_table.add_column("Best Ticker", style="blue", no_wrap=True)

        for strategy, data in aggregation_results["by_strategy"].items():
            best_ticker = (
                data["best_performer"]["ticker"] if data["best_performer"] else "N/A"
            )
            strategy_table.add_row(
                strategy,
                str(data["total_files"]),
                str(len(data["tickers"])),
                f"{data['avg_score']:.2f}",
                f"{data['best_score']:.2f}",
                best_ticker,
            )

        console.table(strategy_table)


def _save_aggregation_csv(aggregation_results: dict, output_path: Path):
    """Save aggregation results to CSV format."""
    import pandas as pd

    # Create a comprehensive CSV with key metrics
    rows = []

    # Add ticker aggregation data
    for ticker, data in aggregation_results.get("by_ticker", {}).items():
        row = {
            "Type": "Ticker",
            "Name": ticker,
            "Total_Strategies": data["total_strategies"],
            "Avg_Score": data["avg_score"],
            "Best_Score": data["best_score"],
            "Avg_Win_Rate": data["avg_win_rate"],
            "Avg_Return": data["avg_return"],
            "Best_Strategy_Type": data["best_strategy"]["strategy"]
            if data["best_strategy"]
            else None,
            "Strategy_Types": ",".join(data["strategy_types"]),
            "Timeframes": ",".join(data["timeframes"]),
        }
        rows.append(row)

    # Add strategy aggregation data
    for strategy, data in aggregation_results.get("by_strategy", {}).items():
        row = {
            "Type": "Strategy",
            "Name": strategy,
            "Total_Files": data["total_files"],
            "Total_Rows": data["total_rows"],
            "Avg_Score": data["avg_score"],
            "Best_Score": data["best_score"],
            "Avg_Win_Rate": data["avg_win_rate"],
            "Avg_Return": data["avg_return"],
            "Best_Ticker": data["best_performer"]["ticker"]
            if data["best_performer"]
            else None,
            "Ticker_Count": len(data["tickers"]),
            "Timeframes": ",".join(data["timeframes"]),
        }
        rows.append(row)

    # Create DataFrame and save
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)


def _show_portfolio_review_config_preview(
    config: PortfolioReviewConfig, console: ConsoleLogger
):
    """Display portfolio review configuration preview for dry run."""
    table = Table(title="Portfolio Review Configuration Preview", show_header=True)
    table.add_column("Parameter", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    # Basic configuration
    table.add_row(
        "Analysis Type",
        "Single Strategy" if config.is_single_strategy else "Multi-Strategy",
    )
    table.add_row("Date Range", f"{config.start_date} to {config.end_date}")
    table.add_row("Initial Cash", f"${config.init_cash:,.2f}")
    table.add_row("Fees", f"{config.fees:.3%}")

    # Strategy details
    if config.is_single_strategy:
        strategy = config.strategies[0]
        table.add_row("Ticker", strategy.ticker)
        table.add_row("Strategy Type", strategy.strategy_type.value)
        table.add_row("Windows", f"{strategy.fast_period}/{strategy.slow_period}")
        if strategy.stop_loss:
            table.add_row("Stop Loss", f"{strategy.stop_loss:.2%}")
    else:
        table.add_row("Strategies Count", str(len(config.strategies)))
        table.add_row("Unique Tickers", str(len(config.unique_tickers)))
        table.add_row("Tickers", ", ".join(config.unique_tickers))

    # Analysis options
    table.add_row("Risk Metrics", "✓" if config.calculate_risk_metrics else "✗")
    table.add_row("Export Equity", "✓" if config.export_equity_curve else "✗")
    table.add_row("Generate Plots", "✓" if config.enable_plotting else "✗")

    # Raw data export options
    table.add_row("Export Raw Data", "✓" if config.raw_data_export.enable else "✗")
    if config.raw_data_export.enable:
        table.add_row(
            "Export Formats",
            ", ".join([f.value for f in config.raw_data_export.export_formats]),
        )
        table.add_row(
            "Data Types",
            ", ".join([t.value for t in config.raw_data_export.data_types]),
        )
        table.add_row(
            "Include VectorBT",
            "✓" if config.raw_data_export.include_vectorbt_object else "✗",
        )
        table.add_row("Output Directory", str(config.raw_data_export.output_dir))

    # Benchmark
    if config.benchmark:
        table.add_row(
            "Benchmark",
            config.benchmark.symbol
            or f"Portfolio ({config.benchmark.benchmark_type.value})",
        )
    else:
        table.add_row("Benchmark", "None")

    console.console.print(table)
    console.warning("This is a dry run. Use --no-dry-run to execute.")


def _display_portfolio_review_results(
    results, config: PortfolioReviewConfig, output_format: str, console: ConsoleLogger
):
    """Display portfolio review results in specified format."""

    # Portfolio Composition Table (for multi-strategy portfolios)
    if len(config.strategies) > 1:
        composition_table = Table(title="Portfolio Composition", show_header=True)
        composition_table.add_column("Strategy", style="cyan")
        composition_table.add_column("Ticker", style="yellow")
        composition_table.add_column("Type", style="magenta")
        composition_table.add_column("Windows", style="green")
        composition_table.add_column("Position Size", style="blue", justify="right")

        for strategy in config.strategies:
            strategy_type = (
                strategy.strategy_type.value
                if hasattr(strategy.strategy_type, "value")
                else strategy.strategy_type
            )
            windows = f"{strategy.fast_period}/{strategy.slow_period}"
            strategy_name = (
                f"{strategy.ticker}_{strategy.fast_period}_{strategy.slow_period}"
            )

            composition_table.add_row(
                strategy_name,
                strategy.ticker,
                strategy_type,
                windows,
                f"{strategy.position_size:.2f}",
            )

        console.console.print(composition_table)
        console.console.print()  # Add spacing

    # Statistics Table
    title = (
        "Multi-Strategy Portfolio Statistics"
        if len(config.strategies) > 1
        else "Portfolio Performance Statistics"
    )
    stats_table = Table(title=title, show_header=True)
    stats_table.add_column("Metric", style="cyan", no_wrap=True)
    stats_table.add_column("Value", style="green")

    # Add key statistics
    for key, value in results.statistics.items():
        if isinstance(value, (int, float)):
            if "%" in key or "rate" in key.lower():
                stats_table.add_row(
                    key, f"{value:.2%}" if abs(value) < 10 else f"{value:.2f}%"
                )
            elif "ratio" in key.lower():
                stats_table.add_row(key, f"{value:.3f}")
            elif "$" in str(value) or "cash" in key.lower():
                stats_table.add_row(key, f"${value:,.2f}")
            else:
                stats_table.add_row(key, f"{value:,.2f}")
        else:
            stats_table.add_row(key, str(value))

    console.console.print(stats_table)

    # Risk Metrics Table (if available)
    if results.risk_metrics and config.calculate_risk_metrics:
        risk_table = Table(title="Risk Metrics", show_header=True)
        risk_table.add_column("Metric", style="cyan", no_wrap=True)
        risk_table.add_column("Value", style="red")

        risk_metrics = results.risk_metrics
        # Handle both dict and RiskMetrics object
        if isinstance(risk_metrics, dict):
            risk_table.add_row("VaR 95%", f"{risk_metrics.get('VaR 95%', 0):.2%}")
            risk_table.add_row("VaR 99%", f"{risk_metrics.get('VaR 99%', 0):.2%}")
            risk_table.add_row("CVaR 95%", f"{risk_metrics.get('CVaR 95%', 0):.2%}")
            risk_table.add_row("CVaR 99%", f"{risk_metrics.get('CVaR 99%', 0):.2%}")
        else:
            # Assume RiskMetrics dataclass
            risk_table.add_row("VaR 95%", f"{risk_metrics.var_95:.2%}")
            risk_table.add_row("VaR 99%", f"{risk_metrics.var_99:.2%}")
            risk_table.add_row("CVaR 95%", f"{risk_metrics.cvar_95:.2%}")
            risk_table.add_row("CVaR 99%", f"{risk_metrics.cvar_99:.2%}")
            risk_table.add_row("Max Drawdown", f"{risk_metrics.max_drawdown:.2%}")
            risk_table.add_row("Sharpe Ratio", f"{risk_metrics.sharpe_ratio:.3f}")
            risk_table.add_row("Sortino Ratio", f"{risk_metrics.sortino_ratio:.3f}")

        console.console.print(risk_table)

    # Open Positions (if any)
    if results.open_positions:
        positions_table = Table(title="Open Positions", show_header=True)
        positions_table.add_column("Strategy", style="cyan")
        positions_table.add_column("Position Size", style="yellow", justify="right")

        for strategy_name, position_size in results.open_positions:
            positions_table.add_row(strategy_name, f"{position_size:.2f}")

        console.console.print(positions_table)

    # Summary
    if output_format == "detailed":
        summary_table = Table(title="Analysis Summary", show_header=True)
        summary_table.add_column("Component", style="cyan")
        summary_table.add_column("Status", style="green")

        summary_table.add_row("Portfolio Analysis", "✓ Complete")
        summary_table.add_row("Statistics Calculated", "✓ Complete")

        if config.calculate_risk_metrics:
            summary_table.add_row("Risk Metrics", "✓ Complete")

        if config.export_equity_curve and results.equity_curve_path:
            summary_table.add_row(
                "Equity Curve Export", f"✓ {results.equity_curve_path}"
            )

        if results.benchmark_portfolio:
            summary_table.add_row("Benchmark Comparison", "✓ Complete")

        if results.raw_data_export_results and results.raw_data_export_results.success:
            summary_table.add_row(
                "Raw Data Export",
                f"✓ {results.raw_data_export_results.total_files} files exported",
            )
        elif config.raw_data_export.enable:
            summary_table.add_row("Raw Data Export", "✗ Failed")

        console.console.print(summary_table)

    # Raw Data Export Results (if available)
    if results.raw_data_export_results and results.raw_data_export_results.success:
        export_table = Table(title="Raw Data Export Results", show_header=True)
        export_table.add_column("Data Type", style="cyan")
        export_table.add_column("Files Exported", style="green", justify="right")
        export_table.add_column("File Paths", style="dim")

        for (
            data_type,
            file_paths,
        ) in results.raw_data_export_results.exported_files.items():
            # Show just the filename for brevity
            filenames = [os.path.basename(fp) for fp in file_paths]
            export_table.add_row(
                data_type.replace("_", " ").title(),
                str(len(file_paths)),
                ", ".join(filenames[:3]) + ("..." if len(filenames) > 3 else ""),
            )

        console.console.print(export_table)
        console.debug(f"Raw data exported to: {config.raw_data_export.output_dir}")
