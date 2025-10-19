"""
Portfolio Selection Module

This module handles the selection of the best portfolio based on consistent
Fast Period/Slow Period combinations in top performing portfolios.
"""

import polars as pl

from app.strategies.ma_cross.config_types import Config
from app.tools.portfolio.collection import detect_column_names, sort_portfolios
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version,
    ensure_allocation_sum_100_percent,
    normalize_portfolio_data,
)
from app.tools.portfolio.strategy_types import derive_use_sma


def get_best_portfolios_per_strategy_type(
    portfolios: pl.DataFrame, config: Config, log: callable
) -> list[dict]:
    """
    Get the best portfolio for each strategy type based on consistent parameter combinations.

    Groups portfolios by strategy type and finds the best configuration for each using:
    1. If the top 3 portfolios have the same combination
    2. If 3 out of top 5 portfolios have the same combination
    3. If 5 out of top 8 portfolios have the same combination
    4. If 2 out of the top 2 portfolios have the same combination

    Args:
        portfolios (pl.DataFrame): DataFrame containing portfolio results
        config (Config): Configuration dictionary
        log (callable): Logging function

    Returns:
        List[dict]: Best portfolio for each strategy type, empty list if none found

    Raises:
        ValueError: If portfolios DataFrame is empty or missing required columns
    """
    try:
        # Initial validation
        if portfolios is None or portfolios.height == 0:
            log("No portfolios provided for analysis", "error")
            return []

        # Check for strategy type column
        strategy_type_present = "Strategy Type" in portfolios.columns
        use_sma_present = "Use SMA" in portfolios.columns

        if not (strategy_type_present or use_sma_present):
            log("Missing strategy type information in portfolios DataFrame", "error")
            return []

        best_portfolios = []

        if strategy_type_present:
            # Group by strategy type and process each separately
            unique_strategy_types = (
                portfolios.select("Strategy Type").unique().to_series().to_list()
            )
            log(f"Found strategy types: {unique_strategy_types}", "info")

            for strategy_type in unique_strategy_types:
                strategy_portfolios = portfolios.filter(
                    pl.col("Strategy Type") == strategy_type
                )
                log(
                    f"Processing {len(strategy_portfolios)} portfolios for {strategy_type}",
                    "info",
                )

                best_portfolio = _get_best_single_strategy_portfolio(
                    strategy_portfolios, config, log
                )
                if best_portfolio:
                    best_portfolios.append(best_portfolio)
                    # Use detected column names for logging
                    log_mapping = detect_column_names(pl.DataFrame([best_portfolio]))
                    fast_col_name = log_mapping["fast_period"] or "Fast Period"
                    slow_col_name = log_mapping["slow_period"] or "Slow Period"

                    log(
                        f"Found best {strategy_type} portfolio: {best_portfolio.get(fast_col_name, 'N/A')}/{best_portfolio.get(slow_col_name, 'N/A')}",
                        "info",
                    )
        else:
            # Legacy mode - use single strategy selection
            best_portfolio = _get_best_single_strategy_portfolio(
                portfolios, config, log
            )
            if best_portfolio:
                best_portfolios.append(best_portfolio)

        log(
            f"Selected {len(best_portfolios)} best portfolios across all strategy types",
            "info",
        )
        return best_portfolios

    except Exception as e:
        log(f"Error in get_best_portfolios_per_strategy_type: {e!s}", "error")
        return []


def get_best_portfolio(
    portfolios: pl.DataFrame, config: Config, log: callable
) -> dict | None:
    """
    Legacy compatibility function - returns single best portfolio.

    For multi-strategy scenarios, use get_best_portfolios_per_strategy_type instead.
    This function returns the first best portfolio found across all strategy types.

    Args:
        portfolios (pl.DataFrame): DataFrame containing portfolio results
        config (Config): Configuration dictionary
        log (callable): Logging function

    Returns:
        Optional[dict]: Best portfolio if found, None otherwise
    """
    best_portfolios = get_best_portfolios_per_strategy_type(portfolios, config, log)
    return best_portfolios[0] if best_portfolios else None


def _get_best_single_strategy_portfolio(
    portfolios: pl.DataFrame, config: Config, log: callable
) -> dict | None:
    """
    Internal function to get best portfolio for a single strategy type.

    This contains the original logic from get_best_portfolio but works on
    portfolios of a single strategy type only.

    Args:
        portfolios (pl.DataFrame): DataFrame containing single strategy type portfolios
        config (Config): Configuration dictionary
        log (callable): Logging function

    Returns:
        Optional[dict]: Best portfolio if found, None otherwise
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

        # Detect column naming convention
        column_mapping = detect_column_names(portfolios)
        fast_period_col = column_mapping["fast_period"]
        slow_period_col = column_mapping["slow_period"]

        # Check other required columns with detected column names
        if not fast_period_col or not slow_period_col:
            log("Missing required period columns in portfolios DataFrame", "error")
            log("Required: Fast/Slow period columns", "info")
            log(f"Available columns: {', '.join(portfolios.columns)}", "info")
            return None

        if sort_by not in portfolios.columns:
            log(f"Missing sort column '{sort_by}' in portfolios DataFrame", "error")
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

        # Determine strategy type for logging
        if strategy_type_present:
            strategy_type = portfolios.select("Strategy Type").row(0)[0]
            use_sma = derive_use_sma(strategy_type)
            log(f"Processing {strategy_type} strategy portfolios", "info")
        else:
            use_sma = portfolios.select("Use SMA").row(0)[0]
            log(f"Using strategy type: {'SMA' if use_sma else 'EMA'}", "info")

        fast_col = fast_period_col
        slow_col = slow_period_col
        log(f"Fast column: {fast_col}, Slow column: {slow_col}", "info")

        # Sort using centralized function
        sorted_portfolios = sort_portfolios(portfolios, config)

        # Get top portfolios for analysis
        top_3 = sorted_portfolios.head(3)
        top_5 = sorted_portfolios.head(5)
        top_8 = sorted_portfolios.head(8)

        # Function to check if combination appears enough times
        def check_combination_frequency(
            df: pl.DataFrame, required_count: int
        ) -> tuple | None:
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

            # Preserve "Metric Type" column for API compatibility
            # Note: Metric Type is needed for proper frontend display

            # Apply schema detection and normalization
            portfolio_list = [portfolio]
            schema_version = detect_schema_version(portfolio_list)
            log(
                f"Detected schema version for best portfolio: {schema_version.name}",
                "info",
            )

            # Normalize portfolio data to handle Allocation [%] and Stop Loss [%]
            # columns
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

            # Preserve "Metric Type" column for API compatibility
            # Note: Metric Type is needed for proper frontend display

            # Apply schema detection and normalization
            portfolio_list = [portfolio]
            schema_version = detect_schema_version(portfolio_list)
            log(
                f"Detected schema version for best portfolio: {schema_version.name}",
                "info",
            )

            # Normalize portfolio data to handle Allocation [%] and Stop Loss [%]
            # columns
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

            # Preserve "Metric Type" column for API compatibility
            # Note: Metric Type is needed for proper frontend display

            # Apply schema detection and normalization
            portfolio_list = [portfolio]
            schema_version = detect_schema_version(portfolio_list)
            log(
                f"Detected schema version for best portfolio: {schema_version.name}",
                "info",
            )

            # Normalize portfolio data to handle Allocation [%] and Stop Loss [%]
            # columns
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

            # Preserve "Metric Type" column for API compatibility
            # Note: Metric Type is needed for proper frontend display

            # Apply schema detection and normalization
            portfolio_list = [portfolio]
            schema_version = detect_schema_version(portfolio_list)
            log(
                f"Detected schema version for best portfolio: {schema_version.name}",
                "info",
            )

            # Normalize portfolio data to handle Allocation [%] and Stop Loss [%]
            # columns
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
        log(f"Error in get_best_portfolio: {e!s}", "error")
        return None
