"""
Portfolio Selection Module

This module handles the selection of the best portfolio based on consistent
Short Window/Long Window combinations in top performing portfolios.
"""

from typing import Optional

import polars as pl

from app.strategies.ma_cross.config_types import Config
from app.tools.portfolio.collection import sort_portfolios
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version,
    ensure_allocation_sum_100_percent,
    normalize_portfolio_data,
)


def get_best_portfolio(
    portfolios: pl.DataFrame, config: Config, log: callable
) -> Optional[dict]:
    """
    Get the best portfolio based on Short Window/Long Window combination frequency in top performers.

    The function analyzes the top performing portfolios to find the most consistent
    Short Window/Long Window combination using four criteria:
    1. If the top 3 portfolios have the same combination
    2. If 3 out of top 5 portfolios have the same combination
    3. If 5 out of top 8 portfolios have the same combination
    4. If 2 out of the top 2 portfolios have the same combination

    Args:
        portfolios (pl.DataFrame): DataFrame containing portfolio results
        config (Config): Configuration dictionary
        log (callable): Logging function

    Returns:
        Optional[dict]: Best portfolio if found, None otherwise

    Raises:
        ValueError: If portfolios DataFrame is empty or missing required columns
    """
    try:
        # Initial validation
        if portfolios is None or portfolios.height == 0:
            log("No portfolios provided for analysis", "error")
            return None

        # Get sort column and validate required columns
        sort_by = config.get("SORT_BY", "Total Return [%]")

        # Check for either "Strategy Type" (new) or "Use SMA" (legacy)
        strategy_type_present = "Strategy Type" in portfolios.columns
        use_sma_present = "Use SMA" in portfolios.columns

        if not (strategy_type_present or use_sma_present):
            log("Missing strategy type information in portfolios DataFrame", "error")
            log(f"Available columns: {', '.join(portfolios.columns)}", "info")
            return None

        # Check other required columns
        other_required_cols = ["Short Window", "Long Window", sort_by]
        if not all(col in portfolios.columns for col in other_required_cols):
            log("Missing required columns in portfolios DataFrame", "error")
            log(f"Required columns: {', '.join(other_required_cols)}", "info")
            log(f"Available columns: {', '.join(portfolios.columns)}", "info")
            return None

        # Check for extended schema columns
        has_allocation = "Allocation [%]" in portfolios.columns
        has_stop_loss = "Stop Loss [%]" in portfolios.columns

        if has_allocation or has_stop_loss:
            log(
                f"Extended schema detected - Allocation: {has_allocation}, Stop Loss: {has_stop_loss}",
                "info",
            )

        # Determine column names based on strategy type
        if strategy_type_present:
            strategy_type = portfolios.select("Strategy Type").row(0)[0]
            use_sma = strategy_type == "SMA"
        else:
            use_sma = portfolios.select("Use SMA").row(0)[0]

        fast_col = "SMA_FAST" if use_sma else "EMA_FAST"
        slow_col = "SMA_SLOW" if use_sma else "EMA_SLOW"

        log(f"Using strategy type: {'SMA' if use_sma else 'EMA'}", "info")
        log(f"Fast column: {fast_col}, Slow column: {slow_col}", "info")

        # Rename columns and sort using centralized function
        renamed_portfolios = portfolios.rename(
            {"Short Window": fast_col, "Long Window": slow_col}
        )
        sorted_portfolios = sort_portfolios(renamed_portfolios, config)

        # Get top portfolios for analysis
        top_3 = sorted_portfolios.head(3)
        top_5 = sorted_portfolios.head(5)
        top_8 = sorted_portfolios.head(8)

        # Function to check if combination appears enough times
        def check_combination_frequency(
            df: pl.DataFrame, required_count: int
        ) -> Optional[tuple]:
            combinations = df.select([fast_col, slow_col]).to_dicts()
            combo_count = {}
            for combo in combinations:
                key = (combo[fast_col], combo[slow_col])
                combo_count[key] = combo_count.get(key, 0) + 1
                if combo_count[key] >= required_count:
                    return key
            return None

        # Check each criterion
        # 1. All top 3 have same combination
        if result := check_combination_frequency(top_3, 3):
            log(
                f"Found matching combination in top 3: {fast_col}={result[0]}, {slow_col}={result[1]}"
            )
            portfolio = (
                sorted_portfolios.filter(
                    (pl.col(fast_col) == result[0]) & (pl.col(slow_col) == result[1])
                )
                .head(1)
                .to_dicts()[0]
            )

            # Remove "Metric Type" column if it exists
            if "Metric Type" in portfolio:
                del portfolio["Metric Type"]

            # Apply schema detection and normalization
            portfolio_list = [portfolio]
            schema_version = detect_schema_version(portfolio_list)
            log(
                f"Detected schema version for best portfolio: {schema_version.name}",
                "info",
            )

            # Normalize portfolio data to handle Allocation [%] and Stop Loss [%] columns
            normalized_portfolio_list = normalize_portfolio_data(
                portfolio_list, schema_version, log
            )

            # Ensure allocation values sum to 100% if they exist
            if schema_version == SchemaVersion.EXTENDED:
                normalized_portfolio_list = ensure_allocation_sum_100_percent(
                    normalized_portfolio_list, log
                )

            normalized_portfolio = normalized_portfolio_list[0]

            # Log allocation information
            if "Allocation [%]" in normalized_portfolio:
                log(
                    f"Best portfolio has allocation: {normalized_portfolio.get('Allocation [%]')}",
                    "info",
                )

            # Add allocation and stop loss from config if not present in portfolio
            if "Allocation [%]" not in normalized_portfolio and "ALLOCATION" in config:
                normalized_portfolio["Allocation [%]"] = config["ALLOCATION"]
                log(f"Added allocation from config: {config['ALLOCATION']}", "info")

            if "Stop Loss [%]" not in normalized_portfolio and "STOP_LOSS" in config:
                normalized_portfolio["Stop Loss [%]"] = config["STOP_LOSS"]
                log(f"Added stop loss from config: {config['STOP_LOSS']}", "info")

            return normalized_portfolio

        # 2. 3 out of top 5 have same combination
        if result := check_combination_frequency(top_5, 3):
            log(
                f"Found matching combination in top 5: {fast_col}={result[0]}, {slow_col}={result[1]}"
            )
            portfolio = (
                sorted_portfolios.filter(
                    (pl.col(fast_col) == result[0]) & (pl.col(slow_col) == result[1])
                )
                .head(1)
                .to_dicts()[0]
            )

            # Remove "Metric Type" column if it exists
            if "Metric Type" in portfolio:
                del portfolio["Metric Type"]

            # Apply schema detection and normalization
            portfolio_list = [portfolio]
            schema_version = detect_schema_version(portfolio_list)
            log(
                f"Detected schema version for best portfolio: {schema_version.name}",
                "info",
            )

            # Normalize portfolio data to handle Allocation [%] and Stop Loss [%] columns
            normalized_portfolio_list = normalize_portfolio_data(
                portfolio_list, schema_version, log
            )

            # Ensure allocation values sum to 100% if they exist
            if schema_version == SchemaVersion.EXTENDED:
                normalized_portfolio_list = ensure_allocation_sum_100_percent(
                    normalized_portfolio_list, log
                )

            normalized_portfolio = normalized_portfolio_list[0]

            # Log allocation information
            if "Allocation [%]" in normalized_portfolio:
                log(
                    f"Best portfolio has allocation: {normalized_portfolio.get('Allocation [%]')}",
                    "info",
                )

            # Add allocation and stop loss from config if not present in portfolio
            if "Allocation [%]" not in normalized_portfolio and "ALLOCATION" in config:
                normalized_portfolio["Allocation [%]"] = config["ALLOCATION"]
                log(f"Added allocation from config: {config['ALLOCATION']}", "info")

            if "Stop Loss [%]" not in normalized_portfolio and "STOP_LOSS" in config:
                normalized_portfolio["Stop Loss [%]"] = config["STOP_LOSS"]
                log(f"Added stop loss from config: {config['STOP_LOSS']}", "info")

            return normalized_portfolio

        # 3. 5 out of top 8 have same combination
        if result := check_combination_frequency(top_8, 5):
            log(
                f"Found matching combination in top 8: {fast_col}={result[0]}, {slow_col}={result[1]}"
            )
            portfolio = (
                sorted_portfolios.filter(
                    (pl.col(fast_col) == result[0]) & (pl.col(slow_col) == result[1])
                )
                .head(1)
                .to_dicts()[0]
            )

            # Remove "Metric Type" column if it exists
            if "Metric Type" in portfolio:
                del portfolio["Metric Type"]

            # Apply schema detection and normalization
            portfolio_list = [portfolio]
            schema_version = detect_schema_version(portfolio_list)
            log(
                f"Detected schema version for best portfolio: {schema_version.name}",
                "info",
            )

            # Normalize portfolio data to handle Allocation [%] and Stop Loss [%] columns
            normalized_portfolio_list = normalize_portfolio_data(
                portfolio_list, schema_version, log
            )

            # Ensure allocation values sum to 100% if they exist
            if schema_version == SchemaVersion.EXTENDED:
                normalized_portfolio_list = ensure_allocation_sum_100_percent(
                    normalized_portfolio_list, log
                )

            normalized_portfolio = normalized_portfolio_list[0]

            # Log allocation information
            if "Allocation [%]" in normalized_portfolio:
                log(
                    f"Best portfolio has allocation: {normalized_portfolio.get('Allocation [%]')}",
                    "info",
                )

            # Add allocation and stop loss from config if not present in portfolio
            if "Allocation [%]" not in normalized_portfolio and "ALLOCATION" in config:
                normalized_portfolio["Allocation [%]"] = config["ALLOCATION"]
                log(f"Added allocation from config: {config['ALLOCATION']}", "info")

            if "Stop Loss [%]" not in normalized_portfolio and "STOP_LOSS" in config:
                normalized_portfolio["Stop Loss [%]"] = config["STOP_LOSS"]
                log(f"Added stop loss from config: {config['STOP_LOSS']}", "info")

            return normalized_portfolio

        # 4. 2 out of top 2 have same combination
        top_2 = sorted_portfolios.head(2)
        if result := check_combination_frequency(top_2, 2):
            log(
                f"Found matching combination in top 2: {fast_col}={result[0]}, {slow_col}={result[1]}"
            )
            portfolio = (
                sorted_portfolios.filter(
                    (pl.col(fast_col) == result[0]) & (pl.col(slow_col) == result[1])
                )
                .head(1)
                .to_dicts()[0]
            )

            # Remove "Metric Type" column if it exists
            if "Metric Type" in portfolio:
                del portfolio["Metric Type"]

            # Apply schema detection and normalization
            portfolio_list = [portfolio]
            schema_version = detect_schema_version(portfolio_list)
            log(
                f"Detected schema version for best portfolio: {schema_version.name}",
                "info",
            )

            # Normalize portfolio data to handle Allocation [%] and Stop Loss [%] columns
            normalized_portfolio_list = normalize_portfolio_data(
                portfolio_list, schema_version, log
            )

            # Ensure allocation values sum to 100% if they exist
            if schema_version == SchemaVersion.EXTENDED:
                normalized_portfolio_list = ensure_allocation_sum_100_percent(
                    normalized_portfolio_list, log
                )

            normalized_portfolio = normalized_portfolio_list[0]

            # Log allocation information
            if "Allocation [%]" in normalized_portfolio:
                log(
                    f"Best portfolio has allocation: {normalized_portfolio.get('Allocation [%]')}",
                    "info",
                )

            # Add allocation and stop loss from config if not present in portfolio
            if "Allocation [%]" not in normalized_portfolio and "ALLOCATION" in config:
                normalized_portfolio["Allocation [%]"] = config["ALLOCATION"]
                log(f"Added allocation from config: {config['ALLOCATION']}", "info")

            if "Stop Loss [%]" not in normalized_portfolio and "STOP_LOSS" in config:
                normalized_portfolio["Stop Loss [%]"] = config["STOP_LOSS"]
                log(f"Added stop loss from config: {config['STOP_LOSS']}", "info")

            return normalized_portfolio

        log(f"No consistent {fast_col}/{slow_col} combination found")
        return None

    except Exception as e:
        log(f"Error in get_best_portfolio: {str(e)}", "error")
        return None
