"""
COMP Strategy Execution

Main execution module for the compound strategy.
"""

from collections.abc import Callable
from pathlib import Path

from app.tools.backtest_strategy import backtest_strategy
from app.tools.get_config import get_config
from app.tools.get_data import get_data
from app.tools.logging_context import logging_context
from app.tools.project_utils import get_project_root
from app.tools.stats_converter import (
    calculate_beats_bnh_normalized,
    calculate_expectancy_per_trade_normalized,
    calculate_profit_factor_normalized,
    calculate_sortino_normalized,
    calculate_total_trades_normalized,
    calculate_win_rate_normalized,
)

from .calculator import calculate_compound_strategy


def calculate_comp_score(stats: dict, log: Callable) -> float:
    """
    Calculate composite Score for COMP strategy using same formula as other strategies.

    Args:
        stats: Portfolio statistics dictionary
        log: Logging function

    Returns:
        Composite score value
    """
    try:
        # Get required metrics with defaults
        win_rate = stats.get("Win Rate [%]", 0)
        total_trades = stats.get("Total Trades", 0)
        sortino = stats.get("Sortino Ratio", 0)
        profit_factor = stats.get("Profit Factor", 1.0)
        expectancy_per_trade = stats.get("Expectancy per Trade", 0)
        beats_bnh = stats.get("Beats BNH [%]", 0)

        # Normalize each component
        win_rate_normalized = calculate_win_rate_normalized(win_rate, total_trades)
        total_trades_normalized = calculate_total_trades_normalized(total_trades)
        sortino_normalized = calculate_sortino_normalized(sortino)
        profit_factor_normalized = calculate_profit_factor_normalized(profit_factor)
        expectancy_per_trade_normalized = calculate_expectancy_per_trade_normalized(
            expectancy_per_trade,
        )
        beats_bnh_normalized = calculate_beats_bnh_normalized(beats_bnh)

        # Calculate composite score with weighted components
        base_score = (
            win_rate_normalized * 2.5
            + total_trades_normalized * 1.5
            + sortino_normalized * 1.2
            + profit_factor_normalized * 1.2
            + expectancy_per_trade_normalized * 1.0
            + beats_bnh_normalized * 0.6
        ) / 8.0

        # Apply statistical confidence multiplier
        if total_trades < 20:
            confidence_multiplier = 0.1 + 0.4 * (total_trades / 20) ** 3
        elif total_trades < 40:
            confidence_multiplier = 0.5 + 0.5 * ((total_trades - 20) / 20)
        else:
            confidence_multiplier = 1.0

        score = base_score * confidence_multiplier

        log(
            f"Calculated Score: {score:.4f} (base: {base_score:.4f}, confidence: {confidence_multiplier:.4f})",
        )

        return score

    except Exception as e:
        log(f"Error calculating Score: {e}", "warning")
        # Fallback to Sortino Ratio as Score
        return stats.get("Sortino Ratio", 0)


def run(
    config: dict,
    external_log: Callable | None = None,
    progress_update_fn: Callable | None = None,
) -> bool:
    """
    Execute the COMP strategy analysis.

    Args:
        config: Configuration dictionary with:
            - TICKER: Ticker symbol (used to find the CSV file)
            - BASE_DIR: Project root directory
            - COMP_STRATEGIES_CSV: Optional path to strategies CSV
            - Other standard config options
        external_log: Optional external logging function
        progress_update_fn: Optional progress update callback

    Returns:
        True if execution successful, False otherwise
    """

    with logging_context("comp_strategy", "comp_strategy.log") as log:
        # Use external log if provided, otherwise use context log
        log_func = external_log if external_log else log

        try:
            log_func("Starting COMP strategy execution")

            # Get ticker from config
            ticker_list = config.get("TICKER", [])
            if isinstance(ticker_list, str):
                ticker_list = [ticker_list]

            if not ticker_list:
                log_func("No ticker specified in config", "error")
                return False

            # Process each ticker
            success = True
            for ticker in ticker_list:
                ticker_success = process_ticker(
                    ticker, config, log_func, progress_update_fn,
                )
                success = success and ticker_success

            return success

        except Exception as e:
            log_func(f"Error in COMP strategy execution: {e}", "error")
            import traceback

            log_func(traceback.format_exc(), "error")
            return False


def process_ticker(
    ticker: str,
    config: dict,
    log: Callable,
    progress_update_fn: Callable | None = None,
) -> bool:
    """
    Process a single ticker for COMP strategy.

    Args:
        ticker: Ticker symbol
        config: Configuration dictionary
        log: Logging function
        progress_update_fn: Optional progress update callback

    Returns:
        True if successful, False otherwise
    """
    try:
        log(f"Processing COMP strategy for {ticker}")

        # Determine path to component strategies CSV
        csv_path = get_strategies_csv_path(ticker, config)
        log(f"Using component strategies from: {csv_path}")

        if not csv_path.exists():
            log(f"Component strategies CSV not found: {csv_path}", "error")
            return False

        # Get price data
        log(f"Fetching price data for {ticker}")
        ticker_config = get_config({**config, "TICKER": ticker})
        data = get_data(ticker, ticker_config, log)

        if data is None or len(data) == 0:
            log(f"Failed to fetch price data for {ticker}", "error")
            return False

        log(
            f"Retrieved {len(data)} data points from {data['Date'].min()} to {data['Date'].max()}",
        )

        # Calculate compound strategy signals
        log("Calculating compound strategy signals...")
        result_data = calculate_compound_strategy(data, csv_path, ticker_config, log)

        if result_data is None:
            log("Failed to calculate compound strategy signals", "error")
            return False

        # Check if any signals were generated
        signal_sum = result_data["Signal"].sum()
        if signal_sum == 0:
            log("No signals generated for compound strategy", "warning")
            # Continue anyway to generate a CSV with zero trades

        # Run backtest
        log("Running backtest on compound strategy...")
        portfolio = backtest_strategy(result_data, ticker_config, log)

        # Get portfolio statistics
        stats = portfolio.stats()

        # Add compound strategy identifier to stats
        stats["Ticker"] = ticker
        stats["Strategy Type"] = "COMP"
        stats["Fast Period"] = "N/A"  # Not applicable for compound strategies
        stats["Slow Period"] = "N/A"
        stats["Signal Period"] = "N/A"

        # Add Signal Entry and Signal Exit based on position status
        # Check if we're currently in a position
        stats.get("Total Open Trades", 0)
        stats[
            "Signal Entry"
        ] = False  # COMP doesn't generate new entry signals in this context
        stats[
            "Signal Exit"
        ] = False  # COMP doesn't generate new exit signals in this context

        # Calculate Score using the same formula as other strategies
        stats["Score"] = calculate_comp_score(stats, log)

        # Update progress if callback provided
        if progress_update_fn:
            progress_update_fn(1)

        # Export results to CSV
        log("Exporting results to CSV...")
        export_success = export_compound_results(ticker, stats, config, log)

        if export_success:
            log(f"✓ COMP strategy completed successfully for {ticker}")
            return True
        log(f"Failed to export results for {ticker}", "error")
        return False

    except Exception as e:
        log(f"Error processing ticker {ticker}: {e}", "error")
        import traceback

        log(traceback.format_exc(), "error")
        return False


def get_strategies_csv_path(ticker: str, config: dict) -> Path:
    """
    Determine the path to the component strategies CSV file.

    Args:
        ticker: Ticker symbol
        config: Configuration dictionary

    Returns:
        Path to the strategies CSV file
    """
    # Check if explicit CSV path is provided
    if "COMP_STRATEGIES_CSV" in config:
        return Path(config["COMP_STRATEGIES_CSV"])

    # Default: look in data/raw/strategies/{ticker}.csv
    base_dir = Path(config.get("BASE_DIR", get_project_root()))
    return base_dir / "data" / "raw" / "strategies" / f"{ticker}.csv"



def export_compound_results(
    ticker: str,
    stats: dict,
    config: dict,
    log: Callable,
) -> bool:
    """
    Export compound strategy results to CSV.

    Args:
        ticker: Ticker symbol
        stats: Portfolio statistics dictionary
        config: Configuration dictionary
        log: Logging function

    Returns:
        True if export successful, False otherwise
    """
    try:
        import pandas as pd

        base_dir = Path(config.get("BASE_DIR", get_project_root()))
        output_dir = base_dir / "data" / "outputs" / "compound"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{ticker}.csv"

        # Convert stats dict to DataFrame and export to CSV
        df = pd.DataFrame([stats])
        df.to_csv(output_file, index=False)

        log(f"Results exported to: {output_file}")
        return True

    except Exception as e:
        log(f"Error exporting results: {e}", "error")
        import traceback

        log(traceback.format_exc(), "error")
        return False
