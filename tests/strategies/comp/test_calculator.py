"""
Unit tests for COMP strategy calculator.

Tests component strategy loading, position calculation,
aggregation, and signal generation.
"""

from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import polars as pl
import pytest

from app.strategies.comp.calculator import (
    aggregate_positions,
    calculate_component_position,
    calculate_compound_strategy,
    generate_compound_signals,
    load_component_strategies,
)


class TestLoadComponentStrategies:
    """Test cases for loading component strategies from CSV."""

    def test_load_component_strategies_success(self):
        """Test loading valid CSV with component strategies."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Strategy Type,Fast Period,Slow Period,Signal Period\n")
            f.write("BTC-USD,SMA,10,20,9\n")
            f.write("BTC-USD,EMA,12,26,9\n")
            f.write("BTC-USD,MACD,12,26,9\n")
            csv_path = f.name

        try:
            strategies = load_component_strategies(csv_path)

            assert len(strategies) == 3
            assert strategies[0]["strategy_type"] == "SMA"
            assert strategies[0]["fast_period"] == 10
            assert strategies[0]["slow_period"] == 20
            assert strategies[1]["strategy_type"] == "EMA"
            assert strategies[2]["strategy_type"] == "MACD"
            assert strategies[2]["signal_period"] == 9
        finally:
            Path(csv_path).unlink()

    def test_load_component_strategies_file_not_found(self):
        """Test FileNotFoundError for missing CSV."""
        with pytest.raises(FileNotFoundError):
            load_component_strategies("/nonexistent/path/to/file.csv")

    def test_load_component_strategies_mixed_types(self):
        """Test loading CSV with mixed strategy types."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Strategy Type,Fast Period,Slow Period,Signal Period\n")
            f.write("AAPL,SMA,5,15,9\n")
            f.write("AAPL,EMA,8,21,9\n")
            f.write("AAPL,MACD,12,26,9\n")
            f.write("AAPL,SMA,20,50,9\n")
            csv_path = f.name

        try:
            strategies = load_component_strategies(csv_path)

            assert len(strategies) == 4
            types = [s["strategy_type"] for s in strategies]
            assert "SMA" in types
            assert "EMA" in types
            assert "MACD" in types
            assert types.count("SMA") == 2
        finally:
            Path(csv_path).unlink()


class TestCalculateComponentPosition:
    """Test cases for calculating component positions."""

    @pytest.fixture
    def sample_data(self):
        """Create sample price data."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        prices = 100 + np.cumsum(np.random.randn(100) * 2)

        data = pl.DataFrame(
            {
                "Date": dates,
                "Open": prices,
                "High": prices + np.random.rand(100) * 2,
                "Low": prices - np.random.rand(100) * 2,
                "Close": prices + np.random.randn(100),
                "Volume": np.random.randint(1000000, 10000000, 100),
            }
        )
        return data

    @pytest.fixture
    def config(self):
        """Create sample config."""
        return {
            "STRATEGY_TYPE": "SMA",
            "BASE_DIR": "/tmp",
        }

    @pytest.fixture
    def log_func(self):
        """Create mock log function."""
        return Mock()

    def test_calculate_component_position_sma(self, sample_data, config, log_func):
        """Test SMA position calculation."""
        strategy = {
            "strategy_type": "SMA",
            "fast_period": 10,
            "slow_period": 20,
        }

        with patch(
            "app.strategies.comp.calculator.calculate_ma_and_signals"
        ) as mock_calc:
            # Mock returns data with Position column
            mock_data = sample_data.clone()
            mock_data = mock_data.with_columns(
                [pl.Series("Position", [0, 1, 1, 0] * 25)]
            )
            mock_calc.return_value = mock_data

            position = calculate_component_position(
                sample_data, strategy, config, log_func
            )

            assert position is not None
            assert len(position) == 100
            assert position.dtype == pl.Int32

    def test_calculate_component_position_ema(self, sample_data, config, log_func):
        """Test EMA position calculation."""
        strategy = {
            "strategy_type": "EMA",
            "fast_period": 12,
            "slow_period": 26,
        }

        with patch(
            "app.strategies.comp.calculator.calculate_ma_and_signals"
        ) as mock_calc:
            mock_data = sample_data.clone()
            mock_data = mock_data.with_columns([pl.Series("Position", [1] * 100)])
            mock_calc.return_value = mock_data

            position = calculate_component_position(
                sample_data, strategy, config, log_func
            )

            assert position is not None
            assert all(position == 1)

    def test_calculate_component_position_macd(self, sample_data, config, log_func):
        """Test MACD position calculation."""
        strategy = {
            "strategy_type": "MACD",
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
        }

        with patch(
            "app.strategies.comp.calculator.calculate_macd_and_signals"
        ) as mock_calc:
            mock_data = sample_data.clone()
            mock_data = mock_data.with_columns([pl.Series("Position", [0] * 100)])
            mock_calc.return_value = mock_data

            position = calculate_component_position(
                sample_data, strategy, config, log_func
            )

            assert position is not None
            assert all(position == 0)

    def test_calculate_component_position_unsupported(
        self, sample_data, config, log_func
    ):
        """Test that unsupported strategy type returns None."""
        strategy = {
            "strategy_type": "UNSUPPORTED",
            "fast_period": 10,
            "slow_period": 20,
        }

        position = calculate_component_position(sample_data, strategy, config, log_func)

        assert position is None
        log_func.assert_called()


class TestAggregatePositions:
    """Test cases for aggregating component positions."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data with dates."""
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        return pl.DataFrame({"Date": dates})

    def test_aggregate_positions_multiple_strategies(self, sample_data):
        """Test correct percentage calculation with multiple strategies."""
        log_func = Mock()

        # Create 5 component positions
        positions = [
            pl.Series([1, 1, 0, 0, 1] * 10),  # 30/50 = 60%
            pl.Series([1, 0, 0, 1, 1] * 10),  # 30/50 = 60%
            pl.Series([0, 0, 0, 0, 1] * 10),  # 10/50 = 20%
            pl.Series([1, 1, 1, 1, 1] * 10),  # 50/50 = 100%
            pl.Series([0, 0, 0, 0, 0] * 10),  # 0/50 = 0%
        ]

        result = aggregate_positions(sample_data, positions, log_func)

        assert "percentage_in_position" in result.columns
        assert "num_in_position" in result.columns
        assert "total_strategies" in result.columns
        assert len(result) == 50

        # Check that percentage is correctly calculated
        assert result["total_strategies"][0] == 5
        # First row: 3 strategies in position (60%)
        assert result["percentage_in_position"][0] == 60.0

    def test_aggregate_positions_empty_list(self, sample_data):
        """Test ValueError for empty position list."""
        log_func = Mock()

        with pytest.raises(ValueError, match="No component positions to aggregate"):
            aggregate_positions(sample_data, [], log_func)

    def test_aggregate_positions_all_in(self, sample_data):
        """Test when all strategies are in position."""
        log_func = Mock()

        positions = [
            pl.Series([1] * 50),
            pl.Series([1] * 50),
            pl.Series([1] * 50),
        ]

        result = aggregate_positions(sample_data, positions, log_func)

        assert all(result["percentage_in_position"] == 100.0)
        assert all(result["num_in_position"] == 3)


class TestGenerateCompoundSignals:
    """Test cases for generating compound signals."""

    def test_generate_compound_signals_entry(self):
        """Test signal generation when crossing 50% threshold."""
        log_func = Mock()

        # Create data that crosses 50% threshold
        data = pl.DataFrame(
            {
                "Date": pd.date_range("2024-01-01", periods=10, freq="D"),
                "percentage_in_position": [
                    30.0,
                    40.0,
                    55.0,
                    60.0,
                    70.0,
                    65.0,
                    55.0,
                    45.0,
                    40.0,
                    30.0,
                ],
                "num_in_position": [1, 2, 3, 3, 4, 3, 3, 2, 2, 1],
                "total_strategies": [5] * 10,
            }
        )

        result = generate_compound_signals(data, threshold=50.0, log=log_func)

        assert "Signal" in result.columns
        assert "Position" in result.columns

        # Entry at index 2 (crosses from 40% to 55%)
        assert result["Signal"][2] == 1
        # Stays in position while above 50%
        assert result["Signal"][3] == 1
        assert result["Signal"][4] == 1

    def test_generate_compound_signals_exit(self):
        """Test exit signal when dropping below 50% threshold."""
        log_func = Mock()

        data = pl.DataFrame(
            {
                "Date": pd.date_range("2024-01-01", periods=10, freq="D"),
                "percentage_in_position": [
                    60.0,
                    70.0,
                    65.0,
                    55.0,
                    45.0,
                    40.0,
                    30.0,
                    35.0,
                    40.0,
                    45.0,
                ],
                "num_in_position": [3, 4, 3, 3, 2, 2, 1, 1, 2, 2],
                "total_strategies": [5] * 10,
            }
        )

        result = generate_compound_signals(data, threshold=50.0, log=log_func)

        # In position initially (60%)
        assert result["Signal"][0] == 1
        # Exit at index 4 (drops from 55% to 45%)
        assert result["Signal"][4] == 0
        # Stays out while below 50%
        assert result["Signal"][5] == 0

    def test_generate_compound_signals_stays_in_position(self):
        """Test that position is maintained above threshold."""
        log_func = Mock()

        data = pl.DataFrame(
            {
                "Date": pd.date_range("2024-01-01", periods=10, freq="D"),
                "percentage_in_position": [
                    60.0,
                    65.0,
                    70.0,
                    75.0,
                    80.0,
                    75.0,
                    70.0,
                    65.0,
                    60.0,
                    55.0,
                ],
                "num_in_position": [3] * 10,
                "total_strategies": [5] * 10,
            }
        )

        result = generate_compound_signals(data, threshold=50.0, log=log_func)

        # Should stay in position throughout (all above 50%)
        assert all(result["Signal"] == 1)


class TestCalculateCompoundStrategy:
    """Test cases for full compound strategy calculation."""

    @pytest.fixture
    def sample_csv(self):
        """Create temporary CSV with strategies."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Strategy Type,Fast Period,Slow Period,Signal Period\n")
            f.write("BTC-USD,SMA,10,20,9\n")
            f.write("BTC-USD,EMA,12,26,9\n")
            csv_path = f.name
        return csv_path

    @pytest.fixture
    def sample_data(self):
        """Create sample price data."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        prices = 100 + np.cumsum(np.random.randn(100) * 2)

        return pl.DataFrame(
            {
                "Date": dates,
                "Open": prices,
                "High": prices + 2,
                "Low": prices - 2,
                "Close": prices,
                "Volume": [1000000] * 100,
            }
        )

    def test_calculate_compound_strategy_success(self, sample_csv, sample_data):
        """Test full compound strategy calculation."""
        config = {"STRATEGY_TYPE": "COMP"}
        log_func = Mock()

        with patch(
            "app.strategies.comp.calculator.calculate_component_position"
        ) as mock_pos:
            # Mock component positions
            mock_pos.return_value = pl.Series([1, 0, 1, 0] * 25)

            result = calculate_compound_strategy(
                sample_data, sample_csv, config, log_func
            )

            assert result is not None
            assert "Signal" in result.columns
            assert "Position" in result.columns
            assert "Close" in result.columns
            assert len(result) == 100

        Path(sample_csv).unlink()

    def test_calculate_compound_strategy_no_strategies(self, sample_data):
        """Test error when CSV is empty."""
        # Create empty CSV
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Ticker,Strategy Type,Fast Period,Slow Period\n")
            csv_path = f.name

        try:
            config = {"STRATEGY_TYPE": "COMP"}
            log_func = Mock()

            result = calculate_compound_strategy(
                sample_data, csv_path, config, log_func
            )

            assert result is None
        finally:
            Path(csv_path).unlink()
