"""Portfolio loading and processing utilities.

This module provides utilities for loading and processing portfolio data,
with standardized error handling and logging.
"""

import csv
import json
import os
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

from app.concurrency.tools.strategy_id import generate_strategy_id
from app.tools.exceptions import PortfolioLoadError


def process_portfolio_strategies(
    strategies: list[dict[str, Any]],
    log: Callable,
) -> list[dict[str, Any]]:
    """Process portfolio strategies and assign strategy IDs.

    Args:
        strategies (List[Dict[str, Any]]): List of strategy configurations
        log (Callable): Logging function

    Returns:
        List[Dict[str, Any]]: Processed strategies with strategy IDs
    """
    processed_strategies = []

    for i, strategy in enumerate(strategies):
        # Create a copy to avoid modifying the original
        processed_strategy = strategy.copy()

        # Generate and assign strategy ID if not already present
        if "strategy_id" not in processed_strategy:
            try:
                strategy_id = generate_strategy_id(processed_strategy)
                processed_strategy["strategy_id"] = strategy_id
                log(
                    f"Generated strategy ID for strategy {i + 1}: {strategy_id}",
                    "debug",
                )
            except ValueError as e:
                log(
                    f"Could not generate strategy ID for strategy {i + 1}: {e!s}",
                    "warning",
                )

        processed_strategies.append(processed_strategy)

    return processed_strategies


def resolve_portfolio_path(portfolio_name: str, base_dir: str = ".") -> str:
    """Resolve the full path to a portfolio file.

    Args:
        portfolio_name: Name of the portfolio file
        base_dir: Base directory for portfolio files

    Returns:
        Full path to the portfolio file

    Raises:
        PortfolioLoadError: If the portfolio file cannot be found
    """
    # Check if the portfolio name already has a path
    if os.path.dirname(portfolio_name):
        # If it has a path, use it directly
        portfolio_path = portfolio_name
    else:
        # Try different locations
        possible_paths = [
            os.path.join(base_dir, "csv", "strategies", portfolio_name),
            os.path.join(base_dir, "csv", "portfolios", portfolio_name),
            os.path.join(base_dir, "json", "portfolios", portfolio_name),
            os.path.join(base_dir, portfolio_name),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                portfolio_path = path
                break
        else:
            msg = f"Portfolio file not found: {portfolio_name}"
            raise PortfolioLoadError(msg)

    return portfolio_path


def load_csv_portfolio(file_path: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    """Load portfolio data from a CSV file.

    Detects and handles both Base Schema and Extended Schema formats:
    - Base Schema: Original schema without Allocation [%] and Stop Loss [%] columns
    - Extended Schema: New schema with Allocation [%] (2nd column) and Stop Loss [%] (7th column)

    Args:
        file_path: Path to the CSV file
        config: Configuration dictionary

    Returns:
        List of portfolio entries with normalized schema

    Raises:
        PortfolioLoadError: If the CSV file cannot be loaded
    """
    try:
        # Import here to avoid circular imports
        from app.tools.portfolio.schema_detection import (
            detect_schema_version_from_file,
            normalize_portfolio_data,
        )

        # First load the raw CSV data
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            raw_data = list(reader)

        # Get a logging function if available in config
        log_func = config.get("log_func")

        # Detect schema version
        try:
            schema_version = detect_schema_version_from_file(file_path)
            if log_func:
                log_func(f"Detected CSV schema version: {schema_version.name}", "info")
        except Exception as e:
            if log_func:
                log_func(
                    f"Error detecting schema version, using raw data: {e!s}",
                    "warning",
                )
            return raw_data

        # Normalize the data to handle both schema versions
        try:
            normalized_data = normalize_portfolio_data(
                raw_data,
                schema_version,
                log_func,
            )

            # Add schema version information to each row
            for row in normalized_data:
                row["_schema_version"] = schema_version.name

            return normalized_data
        except Exception as e:
            if log_func:
                log_func(f"Error normalizing data, using raw data: {e!s}", "warning")
            return raw_data

    except FileNotFoundError:
        msg = f"CSV file not found: {file_path}"
        raise PortfolioLoadError(msg)
    except PermissionError:
        msg = f"Permission denied when accessing CSV file: {file_path}"
        raise PortfolioLoadError(
            msg,
        )
    except csv.Error as e:
        msg = f"CSV parsing error: {e!s}"
        raise PortfolioLoadError(msg)
    except Exception as e:
        msg = f"Unexpected error loading CSV file: {e!s}"
        raise PortfolioLoadError(msg)


def load_json_portfolio(file_path: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    """Load portfolio data from a JSON file.

    Args:
        file_path: Path to the JSON file
        config: Configuration dictionary

    Returns:
        List of portfolio entries

    Raises:
        PortfolioLoadError: If the JSON file cannot be loaded
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

            # Handle different JSON formats
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "strategies" in data:
                return data["strategies"]
            msg = f"Unsupported JSON format in {file_path}"
            raise PortfolioLoadError(msg)
    except FileNotFoundError:
        msg = f"JSON file not found: {file_path}"
        raise PortfolioLoadError(msg)
    except PermissionError:
        msg = f"Permission denied when accessing JSON file: {file_path}"
        raise PortfolioLoadError(
            msg,
        )
    except json.JSONDecodeError as e:
        msg = f"JSON parsing error: {e!s}"
        raise PortfolioLoadError(msg)
    except Exception as e:
        msg = f"Unexpected error loading JSON file: {e!s}"
        raise PortfolioLoadError(msg)


def load_portfolio_with_logging(
    portfolio_name: str,
    log: Callable[[str, str | None], None],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Load portfolio data with logging.

    Args:
        portfolio_name: Name of the portfolio file
        log: Logging function
        config: Configuration dictionary

    Returns:
        List of portfolio entries

    Raises:
        PortfolioLoadError: If the portfolio cannot be loaded
    """
    try:
        log(f"Loading portfolio: {portfolio_name}", "info")

        # Resolve portfolio path
        portfolio_path = resolve_portfolio_path(
            portfolio_name,
            config.get("BASE_DIR", "."),
        )

        log(f"Resolved portfolio path: {portfolio_path}", "info")

        # Add logging function to config for use in load_csv_portfolio
        config_with_log = config.copy()
        config_with_log["log_func"] = log

        # Load portfolio based on file extension
        if portfolio_path.endswith(".csv"):
            portfolio_data = load_csv_portfolio(portfolio_path, config_with_log)
        elif portfolio_path.endswith(".json"):
            portfolio_data = load_json_portfolio(portfolio_path, config)
        else:
            msg = f"Unsupported portfolio format: {portfolio_path}"
            raise PortfolioLoadError(msg)

        log(f"Successfully loaded portfolio with {len(portfolio_data)} entries", "info")

        # Process strategies to assign strategy IDs
        return process_portfolio_strategies(portfolio_data, log)

    except PortfolioLoadError as e:
        log(f"Portfolio load error: {e!s}", "error")
        raise
    except Exception as e:
        error_msg = f"Unexpected error loading portfolio: {e!s}"
        log(error_msg, "error")
        raise PortfolioLoadError(error_msg)


@contextmanager
def portfolio_context(
    portfolio_name: str,
    log: Callable[[str, str | None], None],
    config: dict[str, Any],
):
    """Context manager for portfolio loading and error handling.

    Args:
        portfolio_name: Name of the portfolio file
        log: Logging function
        config: Configuration dictionary

    Yields:
        Loaded portfolio data

    Raises:
        PortfolioLoadError: If the portfolio cannot be loaded
    """
    try:
        # Resolve portfolio path
        portfolio_path = resolve_portfolio_path(
            portfolio_name,
            config.get("BASE_DIR", "."),
        )

        log(f"Loading portfolio from {portfolio_path}", "info")

        # Add logging function to config for use in load_csv_portfolio
        config_with_log = config.copy()
        config_with_log["log_func"] = log

        # Load portfolio based on file extension
        if portfolio_path.endswith(".csv"):
            portfolio_data = load_csv_portfolio(portfolio_path, config_with_log)
        elif portfolio_path.endswith(".json"):
            portfolio_data = load_json_portfolio(portfolio_path, config)
        else:
            msg = f"Unsupported portfolio format: {portfolio_path}"
            raise PortfolioLoadError(msg)

        log(f"Successfully loaded portfolio with {len(portfolio_data)} entries", "info")

        # Process strategies to assign strategy IDs
        processed_data = process_portfolio_strategies(portfolio_data, log)

        # Yield the processed portfolio data
        yield processed_data
    except FileNotFoundError as e:
        msg = f"Portfolio file not found: {e!s}"
        raise PortfolioLoadError(msg)
    except PermissionError as e:
        msg = f"Permission denied when accessing portfolio: {e!s}"
        raise PortfolioLoadError(msg)
    except ValueError as e:
        msg = f"Invalid portfolio data: {e!s}"
        raise PortfolioLoadError(msg)
    except Exception as e:
        msg = f"Unexpected error loading portfolio: {e!s}"
        raise PortfolioLoadError(msg)
