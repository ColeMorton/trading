"""Shared fixtures for trade_history_utils CLI testing."""

import csv
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd
import pytest


@pytest.fixture
def temp_portfolio_dir(tmp_path):
    """Create temporary portfolio directory structure."""
    positions_dir = tmp_path / "positions"
    positions_dir.mkdir(parents=True, exist_ok=True)
    return positions_dir


@pytest.fixture
def sample_portfolio_csv(temp_portfolio_dir):
    """Create sample portfolio CSV with known data."""
    portfolio_path = temp_portfolio_dir / "test_portfolio.csv"

    positions = [
        {
            "position_uuid": "AAPL_SMA_20_50_20250101",
            "ticker": "AAPL",
            "strategy_type": "SMA",
            "entry_date": "2025-01-01",
            "entry_price": 180.50,
            "shares": 100,
            "exit_date": "",
            "exit_price": "",
            "status": "open",
            "trade_quality": "GOOD",
            "mfe": 0.05,
            "mae": -0.02,
            "return_pct": 0.03,
        },
        {
            "position_uuid": "MSFT_MACD_12_26_9_20250102",
            "ticker": "MSFT",
            "strategy_type": "MACD",
            "entry_date": "2025-01-02",
            "entry_price": 420.00,
            "shares": 50,
            "exit_date": "2025-01-10",
            "exit_price": 430.00,
            "status": "closed",
            "trade_quality": "EXCELLENT",
            "mfe": 0.08,
            "mae": -0.01,
            "return_pct": 0.07,
        },
        {
            "position_uuid": "GOOGL_RSI_14_20250103",
            "ticker": "GOOGL",
            "strategy_type": "RSI",
            "entry_date": "2025-01-03",
            "entry_price": 140.00,
            "shares": 75,
            "exit_date": "2025-01-08",
            "exit_price": 135.00,
            "status": "closed",
            "trade_quality": "POOR",
            "mfe": 0.02,
            "mae": -0.05,
            "return_pct": -0.04,
        },
    ]

    df = pd.DataFrame(positions)
    df.to_csv(portfolio_path, index=False)

    return portfolio_path


@pytest.fixture
def empty_portfolio_csv(temp_portfolio_dir):
    """Create empty portfolio CSV file."""
    portfolio_path = temp_portfolio_dir / "empty_portfolio.csv"
    df = pd.DataFrame(
        columns=[
            "position_uuid",
            "ticker",
            "strategy_type",
            "entry_date",
            "entry_price",
            "shares",
            "exit_date",
            "exit_price",
            "status",
            "trade_quality",
            "mfe",
            "mae",
            "return_pct",
        ]
    )
    df.to_csv(portfolio_path, index=False)
    return portfolio_path


@pytest.fixture
def multiple_portfolios_csv(temp_portfolio_dir):
    """Create multiple portfolio CSV files."""
    portfolios = {}

    # Portfolio 1: tech_stocks
    tech_data = [
        {
            "position_uuid": "AAPL_SMA_10_20_20250101",
            "ticker": "AAPL",
            "strategy_type": "SMA",
            "entry_date": "2025-01-01",
            "entry_price": 180.00,
            "shares": 100,
            "status": "open",
            "trade_quality": "GOOD",
        }
    ]
    tech_path = temp_portfolio_dir / "tech_stocks.csv"
    pd.DataFrame(tech_data).to_csv(tech_path, index=False)
    portfolios["tech_stocks"] = tech_path

    # Portfolio 2: energy_stocks
    energy_data = [
        {
            "position_uuid": "XOM_MACD_12_26_9_20250102",
            "ticker": "XOM",
            "strategy_type": "MACD",
            "entry_date": "2025-01-02",
            "entry_price": 110.00,
            "shares": 50,
            "status": "open",
            "trade_quality": "EXCELLENT",
        }
    ]
    energy_path = temp_portfolio_dir / "energy_stocks.csv"
    pd.DataFrame(energy_data).to_csv(energy_path, index=False)
    portfolios["energy_stocks"] = energy_path

    return portfolios


@pytest.fixture
def portfolio_with_duplicates_csv(temp_portfolio_dir):
    """Create portfolio CSV with duplicate positions."""
    portfolio_path = temp_portfolio_dir / "duplicates_portfolio.csv"

    positions = [
        {
            "position_uuid": "AAPL_SMA_20_50_20250101",
            "ticker": "AAPL",
            "strategy_type": "SMA",
            "entry_date": "2025-01-01",
            "entry_price": 180.50,
            "shares": 100,
            "status": "open",
        },
        {
            "position_uuid": "AAPL_SMA_20_50_20250101",  # Duplicate UUID
            "ticker": "AAPL",
            "strategy_type": "SMA",
            "entry_date": "2025-01-01",
            "entry_price": 180.50,
            "shares": 100,
            "status": "open",
        },
        {
            "position_uuid": "MSFT_MACD_12_26_9_20250102",
            "ticker": "MSFT",
            "strategy_type": "MACD",
            "entry_date": "2025-01-02",
            "entry_price": 420.00,
            "shares": 50,
            "status": "open",
        },
    ]

    df = pd.DataFrame(positions)
    df.to_csv(portfolio_path, index=False)

    return portfolio_path


@pytest.fixture
def invalid_portfolio_csv(temp_portfolio_dir):
    """Create portfolio CSV with invalid data."""
    portfolio_path = temp_portfolio_dir / "invalid_portfolio.csv"

    positions = [
        {
            "position_uuid": "",  # Missing UUID
            "ticker": "AAPL",
            "entry_date": "invalid-date",  # Invalid date
            "entry_price": "not-a-number",  # Invalid price
            "shares": -100,  # Negative shares
        }
    ]

    df = pd.DataFrame(positions)
    df.to_csv(portfolio_path, index=False)

    return portfolio_path


@pytest.fixture
def mock_config(monkeypatch, temp_portfolio_dir):
    """Mock TradingSystemConfig to use temp directory."""

    class MockConfig:
        def __init__(self, base_dir=None):
            self.base_dir = base_dir or temp_portfolio_dir.parent
            self.positions_dir = temp_portfolio_dir
            self.prices_dir = temp_portfolio_dir.parent / "prices"

        def ensure_directories(self):
            self.positions_dir.mkdir(parents=True, exist_ok=True)
            self.prices_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        "app.tools.position_service_wrapper.TradingSystemConfig", MockConfig
    )
    monkeypatch.setattr(
        "app.tools.position_service_wrapper.get_config", lambda: MockConfig()
    )

    return MockConfig()


@pytest.fixture
def cli_runner():
    """Helper to run trade_history_utils.py as subprocess."""
    import subprocess
    from pathlib import Path

    script_path = (
        Path(__file__).parent.parent.parent.parent
        / "app"
        / "tools"
        / "trade_history_utils.py"
    )

    def run_cli(args: list[str], timeout: int = 30):
        """Run CLI with given arguments."""
        cmd = ["python", str(script_path)] + args
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result

    return run_cli


@pytest.fixture
def captured_output(capsys):
    """Fixture to capture and return stdout/stderr."""
    return capsys


@pytest.fixture
def mock_logger(monkeypatch):
    """Mock logging to capture log messages."""
    import logging
    from io import StringIO

    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)

    logger = logging.getLogger("app.tools.trade_history_utils")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    yield log_stream

    logger.removeHandler(handler)


@pytest.fixture
def cli_args_builder():
    """Helper to build argparse Namespace objects for testing."""
    from argparse import Namespace

    def build_args(**kwargs):
        """Build argparse Namespace with defaults."""
        defaults = {
            "base_dir": None,
            "verbose": False,
            "debug": False,
            "health_check": False,
            "summary": False,
            "compare": False,
            "update_quality": False,
            "merge": False,
            "list_portfolios": False,
            "remove_duplicates": False,
            "find_duplicates": False,
            "find_position": False,
            "export_summary": False,
            "validate_portfolio": False,
            "normalize_portfolio": False,
            "fix_quality": False,
            "portfolio": None,
            "portfolios": None,
            "source": None,
            "target": None,
            "uuid": None,
            "output": None,
        }
        defaults.update(kwargs)
        return Namespace(**defaults)

    return build_args
