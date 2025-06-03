"""Portfolio configuration management."""

import json
from pathlib import Path
from typing import Dict, List, Tuple, TypedDict


class PortfolioAsset(TypedDict):
    """Configuration type definition for a portfolio asset.

    Required Fields:
        ticker (str): Asset ticker symbol
        leverage (float): Leverage ratio for the asset
        weight (float): Target portfolio weight as a percentage
    """

    ticker: str
    leverage: float
    weight: float


class PortfolioConfig(TypedDict):
    """Configuration type definition for portfolio settings.

    Required Fields:
        initial_value (float): Initial portfolio value
        target_value (float): Target portfolio value
        use_target_value (bool): Whether to use target value
        portfolio (List[PortfolioAsset]): List of portfolio assets
    """

    initial_value: float
    target_value: float
    use_target_value: bool
    portfolio: List[PortfolioAsset]


def load_portfolio_config(portfolio_name: str) -> PortfolioConfig:
    """Load portfolio configuration from JSON file.

    Args:
        portfolio_name (str): Name of the portfolio JSON file

    Returns:
        PortfolioConfig: Portfolio configuration

    Raises:
        FileNotFoundError: If portfolio file doesn't exist
        KeyError: If JSON file is missing required keys
        ValueError: If JSON structure is invalid
    """
    portfolio_path = Path(__file__).parent.parent / "portfolios" / portfolio_name

    if not portfolio_path.exists():
        raise FileNotFoundError(f"Portfolio file not found: {portfolio_path}")

    with open(portfolio_path) as f:
        data = json.load(f)

    # Validate required fields
    required_fields = ["initial_value", "target_value", "use_target_value", "portfolio"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise KeyError(f"Missing required fields in portfolio config: {missing_fields}")

    return data


def get_portfolio_value(config: PortfolioConfig) -> float:
    """Get the appropriate portfolio value based on configuration.

    Args:
        config (PortfolioConfig): Portfolio configuration

    Returns:
        float: Portfolio value to use
    """
    return (
        config["target_value"]
        if config["use_target_value"]
        else config["initial_value"]
    )


def get_portfolio_tickers(config: PortfolioConfig) -> List[str]:
    """Extract ticker symbols from portfolio configuration.

    Args:
        config (PortfolioConfig): Portfolio configuration

    Returns:
        List[str]: List of ticker symbols
    """
    return [asset["ticker"] for asset in config["portfolio"]]
