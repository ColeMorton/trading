"""Configuration preview utilities for portfolio commands.

This module provides functions for displaying configuration previews
in dry-run mode before executing portfolio operations.
"""

from rich.table import Table

from app.cli.models.portfolio import (
    PortfolioConfig,
    PortfolioProcessingConfig,
    PortfolioSynthesisConfig,
)
from app.tools.console_logging import ConsoleLogger


def show_portfolio_config_preview(config: PortfolioConfig, console: ConsoleLogger):
    """Display portfolio configuration preview for dry run.

    Args:
        config: Portfolio configuration object
        console: Console logger for output
    """
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


def show_processing_config_preview(
    config: PortfolioProcessingConfig, console: ConsoleLogger
):
    """Display portfolio processing configuration preview.

    Args:
        config: Portfolio processing configuration object
        console: Console logger for output
    """
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


def show_portfolio_synthesis_config_preview(
    config: PortfolioSynthesisConfig, console: ConsoleLogger
):
    """Display portfolio synthesis configuration preview for dry run.

    Args:
        config: Portfolio synthesis configuration object
        console: Console logger for output
    """
    table = Table(title="Portfolio Synthesis Configuration Preview", show_header=True)
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

