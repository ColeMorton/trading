"""
Multiple Strategy Portfolio Review Module

This module performs portfolio analysis for multiple trading strategies,
comparing their performance against a benchmark portfolio.
"""

from typing import Dict, List, cast

import vectorbt as vbt

from app.portfolio_review.config import Config
from app.portfolio_review.tools.portfolio_analysis import (
    calculate_risk_metrics,
    check_open_positions,
    create_benchmark_data,
    create_price_dataframe,
    find_common_dates,
    prepare_data,
)
from app.portfolio_review.tools.visualization import (
    create_portfolio_plots,
    print_open_positions,
    print_portfolio_stats,
)
from app.strategies.ma_cross.tools.generate_signals import generate_signals
from app.tools.setup_logging import setup_logging
from app.tools.stats_converter import convert_stats


def run_portfolio_analysis(config_input: Dict = None):
    """
    Run portfolio analysis for multiple strategies.

    Args:
        config_input: Optional configuration dictionary. If not provided,
                     uses default config from config.py
    """
    # Setup logging
    log, log_close, _, _ = setup_logging(
        module_name="portfolio_review",
        log_file="review_multiple.log",
        log_subdir="portfolios",  # Store logs in a dedicated subdirectory
    )

    try:
        # Cast config to proper type
        portfolio_config = cast(
            Config, config_input if config_input is not None else config
        )

        # Validate config structure
        required_fields = ["strategies", "start_date", "end_date", "init_cash", "fees"]
        missing_fields = [
            field for field in required_fields if field not in portfolio_config
        ]
        if missing_fields:
            raise ValueError(f"Missing required config fields: {missing_fields}")

        if not portfolio_config["strategies"]:
            raise ValueError("No strategies defined in config")

        # Validate strategy fields
        for strategy_name, strategy in portfolio_config["strategies"].items():
            required_strategy_fields = [
                "symbol",
                "short_window",
                "long_window",
                "position_size",
                "use_sma",
            ]
            missing_strategy_fields = [
                field for field in required_strategy_fields if field not in strategy
            ]
            if missing_strategy_fields:
                raise ValueError(
                    f"Strategy '{strategy_name}' missing required fields: {missing_strategy_fields}"
                )

            # Validate numeric parameters
            if (
                not isinstance(strategy["short_window"], int)
                or strategy["short_window"] <= 0
            ):
                raise ValueError(f"Strategy '{strategy_name}' has invalid short_window")
            if (
                not isinstance(strategy["long_window"], int)
                or strategy["long_window"] <= 0
            ):
                raise ValueError(f"Strategy '{strategy_name}' has invalid long_window")
            if "stop_loss" in strategy:
                if (
                    not isinstance(strategy["stop_loss"], (int, float))
                    or strategy["stop_loss"] <= 0
                ):
                    raise ValueError(
                        f"Strategy '{strategy_name}' has invalid stop_loss"
                    )
            if (
                not isinstance(strategy["position_size"], (int, float))
                or strategy["position_size"] <= 0
            ):
                raise ValueError(
                    f"Strategy '{strategy_name}' has invalid position_size"
                )

        # Get unique symbols from strategies
        symbols: List[str] = list(
            set(
                strategy["symbol"]
                for strategy in portfolio_config["strategies"].values()
            )
        )
        log(f"Processing symbols: {symbols}")

        if not symbols:
            raise ValueError("No symbols found in strategies")

        # Download and prepare data
        data_dict, pandas_data_dict = prepare_data(symbols, portfolio_config, log)

        # Find common date range
        common_dates = find_common_dates(data_dict, log)
        if not common_dates:
            raise ValueError("No common dates found across symbols")

        # Create price DataFrame
        price_df_pd = create_price_dataframe(
            common_dates, data_dict, portfolio_config, log
        )
        if price_df_pd.empty:
            raise ValueError("Failed to create price DataFrame")

        # Generate signals using the generate_signals utility
        log("Generating trading signals")
        signal_config = {
            "strategies": portfolio_config["strategies"],
            "USE_SMA": portfolio_config.get("USE_SMA", False),
            "USE_RSI": portfolio_config.get("USE_RSI", False),
            "RSI_THRESHOLD": portfolio_config.get("RSI_THRESHOLD", 70),
            "SHORT": portfolio_config.get("SHORT", False),
            "init_cash": portfolio_config.get("init_cash", 10000),
            "fees": portfolio_config.get("fees", 0.001),
        }

        entries_pd, exits_pd = generate_signals(pandas_data_dict, signal_config, log)
        if entries_pd.empty or exits_pd.empty:
            raise ValueError("Failed to generate trading signals")

        # Create size DataFrame (position sizes for each strategy)
        sizes_pd = price_df_pd.copy()
        for strategy_name, strategy in portfolio_config["strategies"].items():
            sizes_pd[strategy_name] = strategy["position_size"]

        # Run the portfolio simulation
        log("Running portfolio simulation")
        try:
            portfolio = vbt.Portfolio.from_signals(
                close=price_df_pd,
                entries=entries_pd.astype(bool),
                exits=exits_pd.astype(bool),
                size=sizes_pd,
                init_cash=portfolio_config["init_cash"],
                fees=portfolio_config["fees"],
                freq="1D",
                group_by=True,
                cash_sharing=True,
            )
        except Exception as e:
            raise ValueError(f"Failed to create portfolio: {str(e)}")

        # Create benchmark portfolio data
        (
            benchmark_close_pd,
            benchmark_entries_pd,
            benchmark_sizes_pd,
        ) = create_benchmark_data(common_dates, data_dict, symbols, log)
        if benchmark_close_pd.empty:
            raise ValueError("Failed to create benchmark data")

        # Create benchmark portfolio
        log("Creating benchmark portfolio")
        try:
            benchmark_portfolio = vbt.Portfolio.from_signals(
                close=benchmark_close_pd,
                entries=benchmark_entries_pd,
                size=benchmark_sizes_pd,
                init_cash=portfolio_config["init_cash"],
                fees=portfolio_config["fees"],
                freq="1D",
                group_by=True,
                cash_sharing=True,
            )
        except Exception as e:
            raise ValueError(f"Failed to create benchmark portfolio: {str(e)}")

        # Validate portfolios before visualization
        if portfolio is None or benchmark_portfolio is None:
            raise ValueError("Portfolio objects not properly initialized")

        try:
            # Calculate portfolio statistics
            stats = portfolio.stats()
            log("Generated portfolio stats")

            # Convert stats to dictionary if needed
            if hasattr(stats, "to_dict"):
                stats_dict = stats.to_dict()
            else:
                stats_dict = dict(stats)

            # Prepare config for stats conversion
            stats_config = {
                "USE_HOURLY": portfolio_config.get("USE_HOURLY", False),
                "TICKER": next(
                    iter(portfolio_config["strategies"].keys()), "Unknown"
                ),  # Use first strategy name as ticker
            }

            try:
                # Convert portfolio statistics
                converted_stats = convert_stats(stats_dict, log, stats_config, None)
                log("Successfully converted portfolio stats")

                # Calculate risk metrics
                returns = portfolio.returns()
                if returns is None:
                    raise ValueError("Portfolio returns not available")

                # Convert returns to numpy array if needed
                if hasattr(returns, "to_numpy"):
                    returns_array = returns.to_numpy()
                else:
                    returns_array = returns.values

                # Calculate risk metrics
                risk_metrics = calculate_risk_metrics(returns_array)
                log("Successfully calculated risk metrics")

                # Print statistics and risk metrics
                print_portfolio_stats(converted_stats, risk_metrics, log)

            except Exception as e:
                log(f"Error processing portfolio statistics: {str(e)}", "error")
                raise ValueError(f"Failed to process portfolio statistics: {str(e)}")

            # Create and display plots
            create_portfolio_plots(portfolio, benchmark_portfolio, log)

            # Check and display open positions
            open_positions = check_open_positions(portfolio, price_df_pd, log)
            print_open_positions(open_positions)

        except Exception as e:
            log(f"Error in portfolio analysis: {str(e)}", "error")
            # Continue execution even if analysis fails
            pass

    except Exception as e:
        log(f"Error in portfolio review: {str(e)}", "error")
        raise
    finally:
        log_close()


if __name__ == "__main__":
    run_portfolio_analysis()
