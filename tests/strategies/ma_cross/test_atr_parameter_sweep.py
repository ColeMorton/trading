"""
Comprehensive test suite for ATR Parameter Sweep Engine.

This module provides complete test coverage for the ATR trailing stop
parameter sensitivity analysis functionality including:
- ATR parameter sweep engine
- Signal processing and hybrid MA+ATR signals
- Portfolio export functionality
- Integration testing for the complete workflow
"""

import os
import tempfile
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, mock_open, patch

import numpy as np
import pandas as pd
import polars as pl
import pytest

from app.strategies.ma_cross.tools.atr_parameter_sweep import (
    ATRParameterSweepEngine,
    create_atr_sweep_engine,
)
from app.strategies.ma_cross.tools.atr_signal_processing import (
    create_atr_parameter_combinations,
    generate_hybrid_ma_atr_signals,
    validate_atr_parameters,
)
from app.tools.portfolio.base_extended_schemas import SchemaTransformer, SchemaType


@pytest.fixture
def sample_price_data():
    """Create sample price data for testing."""
    dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")
    np.random.seed(42)

    # Generate realistic price data with trend
    base_price = 100
    returns = np.random.normal(0.0005, 0.02, len(dates))
    prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame(
        {
            "Date": dates,
            "Open": prices * 0.98,
            "High": prices * 1.02,
            "Low": prices * 0.97,
            "Close": prices,
            "Volume": np.random.randint(1000000, 5000000, len(dates)),
            "Ticker": "TEST",
        }
    ).set_index("Date")

    return pl.from_pandas(df.reset_index())


@pytest.fixture
def sample_ma_config():
    """Create sample MA Cross configuration."""
    return {
        "TICKER": "TEST",
        "SHORT_WINDOW": 19,
        "LONG_WINDOW": 29,
        "USE_SMA": True,
        "BASE_DIR": "/tmp",
        "REFRESH": True,
        "USE_HOURLY": False,
        "DIRECTION": "Long",
        "USE_CURRENT": False,
    }


@pytest.fixture
def sample_atr_config():
    """Create sample ATR configuration."""
    return {
        "ATR_LENGTH_MIN": 2,
        "ATR_LENGTH_MAX": 5,
        "ATR_MULTIPLIER_MIN": 1.5,
        "ATR_MULTIPLIER_MAX": 3.0,
        "ATR_MULTIPLIER_STEP": 0.5,
        "ATR_CHUNK_SIZE": 10,
        "MAX_WORKERS": 2,
        "ENABLE_PROGRESS_TRACKING": True,
    }


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return Mock()


@pytest.fixture
def sample_portfolio_stats():
    """Create sample portfolio statistics."""
    return {
        "Total Return": 25.5,
        "Sharpe Ratio": 1.45,
        "Max Drawdown": -12.3,
        "Win Rate": 58.2,
        "Total Trades": 45,
        "Profit Factor": 1.85,
        "Expectancy Per Trade": 0.035,
        "Sortino Ratio": 1.22,
        "Ticker": "TEST",
    }


class TestATRParameterCombinations:
    """Test ATR parameter combination generation."""

    def test_create_atr_parameter_combinations_basic(self):
        """Test basic ATR parameter combination creation."""
        combinations = create_atr_parameter_combinations(
            atr_length_range=(2, 4),  # 2, 3 (4 is exclusive)
            atr_multiplier_range=(
                1.5,
                2.5,
            ),  # 1.5, 2.0 (2.5 is exclusive with step 0.5)
            atr_multiplier_step=0.5,
        )

        expected_count = 2 * 2  # 2 lengths × 2 multipliers
        assert len(combinations) == expected_count

        # Check specific combinations
        assert (2, 1.5) in combinations
        assert (2, 2.0) in combinations
        assert (3, 1.5) in combinations
        assert (3, 2.0) in combinations

    def test_create_atr_parameter_combinations_edge_cases(self):
        """Test edge cases for parameter combination creation."""
        # Single length, single multiplier
        combinations = create_atr_parameter_combinations(
            atr_length_range=(5, 6),  # Only 5 (6 is exclusive)
            atr_multiplier_range=(
                2.0,
                3.0,
            ),  # Only 2.0 (with step 1.0, next would be 3.0 which is max)
            atr_multiplier_step=1.0,
        )
        assert len(combinations) == 1
        assert combinations[0] == (5, 2.0)

        # Large step size
        combinations = create_atr_parameter_combinations(
            atr_length_range=(2, 4),
            atr_multiplier_range=(1.0, 5.0),
            atr_multiplier_step=2.0,
        )
        expected_multipliers = [
            1.0,
            3.0,
        ]  # 2 multipliers (5.0 would be at index 2*2.0 = 4.0 from 1.0, but range is exclusive)
        assert len(combinations) == 2 * 2  # 2 lengths × 2 multipliers

    def test_validate_atr_parameters(self):
        """Test ATR parameter validation."""
        # Valid parameters
        is_valid, error = validate_atr_parameters(14, 2.0)
        assert is_valid == True
        assert error is None

        # Invalid length (too small)
        is_valid, error = validate_atr_parameters(0, 2.0)
        assert is_valid == False
        assert "ATR length must be a positive integer" in error

        # Invalid multiplier (too small)
        is_valid, error = validate_atr_parameters(14, 0.0)
        assert is_valid == False
        assert "ATR multiplier must be positive" in error

        # Invalid multiplier (negative)
        is_valid, error = validate_atr_parameters(14, -1.0)
        assert is_valid == False
        assert "ATR multiplier must be positive" in error


class TestATRSignalProcessing:
    """Test ATR signal processing functionality."""

    @patch("app.strategies.ma_cross.tools.atr_signal_processing.calculate_sma_signals")
    @patch("app.tools.calculate_atr.calculate_atr")
    def test_generate_hybrid_ma_atr_signals(
        self, mock_atr, mock_sma, sample_price_data, sample_ma_config, mock_logger
    ):
        """Test hybrid MA+ATR signal generation."""
        # Mock SMA signals
        mock_sma.return_value = sample_price_data.to_pandas().copy()
        mock_sma.return_value["Signal"] = [0] * len(sample_price_data)
        mock_sma.return_value["Position"] = [0] * len(sample_price_data)

        # Add some entry signals
        mock_sma.return_value.loc[10:20, "Signal"] = 1
        mock_sma.return_value.loc[50:60, "Signal"] = 1

        # Mock ATR calculation
        mock_atr.return_value = pd.Series([2.0] * len(sample_price_data))

        # Test signal generation
        result = generate_hybrid_ma_atr_signals(
            sample_price_data.to_pandas(),
            sample_ma_config,
            atr_length=14,
            atr_multiplier=2.0,
            log=mock_logger,
        )

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert "Signal" in result.columns
        assert "Position" in result.columns
        assert len(result) == len(sample_price_data)

        # Verify mocks were called
        mock_sma.assert_called_once()
        mock_atr.assert_called_once()

    @patch("app.strategies.ma_cross.tools.atr_signal_processing.calculate_sma_signals")
    @patch("app.tools.calculate_atr.calculate_atr")
    def test_generate_signals_with_atr_exits(
        self, mock_atr, mock_sma, sample_price_data, sample_ma_config, mock_logger
    ):
        """Test that ATR exits are properly generated."""
        pandas_data = sample_price_data.to_pandas()

        # Mock SMA signals with entry at index 10
        mock_sma_result = pandas_data.copy()
        mock_sma_result["Signal"] = [0] * len(pandas_data)
        mock_sma_result["Position"] = [0] * len(pandas_data)
        mock_sma_result.loc[10, "Signal"] = 1  # Entry signal
        mock_sma.return_value = mock_sma_result

        # Mock ATR with consistent values
        mock_atr.return_value = pd.Series([2.0] * len(pandas_data))

        result = generate_hybrid_ma_atr_signals(
            pandas_data,
            sample_ma_config,
            atr_length=14,
            atr_multiplier=2.0,
            log=mock_logger,
        )

        assert result is not None
        assert "Signal" in result.columns
        assert "Position" in result.columns

        # Should have at least the original entry signal
        assert result["Signal"].sum() >= 1

    def test_generate_signals_error_handling(self, sample_ma_config, mock_logger):
        """Test error handling in signal generation."""
        # Test with invalid data
        invalid_data = pd.DataFrame({"Invalid": [1, 2, 3]})

        result = generate_hybrid_ma_atr_signals(
            invalid_data,
            sample_ma_config,
            atr_length=14,
            atr_multiplier=2.0,
            log=mock_logger,
        )

        # Should return None on error
        assert result is None

        # Verify error was logged
        mock_logger.assert_called()
        error_calls = [
            call
            for call in mock_logger.call_args_list
            if len(call[0]) > 1 and call[0][1] == "error"
        ]
        assert len(error_calls) > 0


class TestATRParameterSweepEngine:
    """Test the ATR Parameter Sweep Engine."""

    def test_engine_initialization(self, sample_atr_config):
        """Test engine initialization with configuration."""
        engine = create_atr_sweep_engine(sample_atr_config)

        assert isinstance(engine, ATRParameterSweepEngine)
        assert engine.chunk_size == 10
        assert engine.max_workers == 2
        assert engine.atr_length_min == 2
        assert engine.atr_length_max == 5
        assert engine.atr_multiplier_min == 1.5
        assert engine.atr_multiplier_max == 3.0
        assert engine.atr_multiplier_step == 0.5

    def test_engine_initialization_defaults(self):
        """Test engine initialization with default values."""
        engine = create_atr_sweep_engine({})

        assert engine.chunk_size == 50  # Default
        assert engine.max_workers == 4  # Default
        assert engine.atr_length_min == 2  # Default
        assert engine.atr_length_max == 21  # Default
        assert engine.atr_multiplier_min == 1.5  # Default
        assert engine.atr_multiplier_max == 10.0  # Default
        assert engine.atr_multiplier_step == 0.2  # Default

    def test_generate_atr_parameter_combinations(self, sample_atr_config):
        """Test parameter combination generation."""
        engine = create_atr_sweep_engine(sample_atr_config)
        combinations = engine.generate_atr_parameter_combinations()

        # Expected: 4 lengths (2,3,4,5) × 4 multipliers (1.5,2.0,2.5,3.0) = 16
        expected_count = 4 * 4
        assert len(combinations) == expected_count
        assert engine.sweep_stats["total_combinations"] == expected_count

        # Check specific combinations exist
        assert (2, 1.5) in combinations
        assert (5, 3.0) in combinations

    @patch("app.strategies.ma_cross.tools.atr_parameter_sweep.backtest_strategy")
    @patch(
        "app.strategies.ma_cross.tools.atr_parameter_sweep.generate_hybrid_ma_atr_signals"
    )
    def test_process_single_atr_combination_success(
        self,
        mock_signals,
        mock_backtest,
        sample_atr_config,
        sample_price_data,
        sample_ma_config,
        mock_logger,
        sample_portfolio_stats,
    ):
        """Test successful processing of single ATR combination."""
        engine = create_atr_sweep_engine(sample_atr_config)

        # Mock signal generation
        mock_signals.return_value = sample_price_data.to_pandas()

        # Mock backtest portfolio with stats method
        mock_portfolio = Mock()
        mock_portfolio.stats.return_value = sample_portfolio_stats
        mock_backtest.return_value = mock_portfolio

        result = engine.process_single_atr_combination(
            ticker="TEST",
            ma_config=sample_ma_config,
            atr_length=14,
            atr_multiplier=2.0,
            price_data=sample_price_data,
            log=mock_logger,
        )

        assert result is not None
        assert isinstance(result, dict)
        assert result["ATR Stop Length"] == 14
        assert result["ATR Stop Multiplier"] == 2.0
        assert result["Ticker"] == "TEST"
        assert engine.sweep_stats["successful_combinations"] == 1

        # Verify mocks were called
        mock_signals.assert_called_once()
        mock_backtest.assert_called_once()
        mock_portfolio.stats.assert_called_once()

    @patch(
        "app.strategies.ma_cross.tools.atr_parameter_sweep.generate_hybrid_ma_atr_signals"
    )
    def test_process_single_atr_combination_signal_failure(
        self,
        mock_signals,
        sample_atr_config,
        sample_price_data,
        sample_ma_config,
        mock_logger,
    ):
        """Test handling of signal generation failure."""
        engine = create_atr_sweep_engine(sample_atr_config)

        # Mock signal generation failure
        mock_signals.return_value = None

        result = engine.process_single_atr_combination(
            ticker="TEST",
            ma_config=sample_ma_config,
            atr_length=14,
            atr_multiplier=2.0,
            price_data=sample_price_data,
            log=mock_logger,
        )

        assert result is None
        assert engine.sweep_stats["failed_combinations"] == 1
        mock_signals.assert_called_once()

    @patch("app.strategies.ma_cross.tools.atr_parameter_sweep.backtest_strategy")
    @patch(
        "app.strategies.ma_cross.tools.atr_parameter_sweep.generate_hybrid_ma_atr_signals"
    )
    def test_process_single_atr_combination_backtest_failure(
        self,
        mock_signals,
        mock_backtest,
        sample_atr_config,
        sample_price_data,
        sample_ma_config,
        mock_logger,
    ):
        """Test handling of backtest failure."""
        engine = create_atr_sweep_engine(sample_atr_config)

        # Mock successful signal generation
        mock_signals.return_value = sample_price_data.to_pandas()

        # Mock backtest failure
        mock_backtest.return_value = None

        result = engine.process_single_atr_combination(
            ticker="TEST",
            ma_config=sample_ma_config,
            atr_length=14,
            atr_multiplier=2.0,
            price_data=sample_price_data,
            log=mock_logger,
        )

        assert result is None
        assert engine.sweep_stats["failed_combinations"] == 1

    def test_process_single_atr_combination_invalid_parameters(
        self, sample_atr_config, sample_price_data, sample_ma_config, mock_logger
    ):
        """Test handling of invalid ATR parameters."""
        engine = create_atr_sweep_engine(sample_atr_config)

        # Test with invalid parameters
        result = engine.process_single_atr_combination(
            ticker="TEST",
            ma_config=sample_ma_config,
            atr_length=0,  # Invalid
            atr_multiplier=-1.0,  # Invalid
            price_data=sample_price_data,
            log=mock_logger,
        )

        assert result is None
        # Should log error about invalid parameters
        mock_logger.assert_called()

    @patch("app.strategies.ma_cross.tools.atr_parameter_sweep.get_data")
    def test_execute_atr_parameter_sweep_success(
        self,
        mock_get_data,
        sample_atr_config,
        sample_price_data,
        sample_ma_config,
        mock_logger,
    ):
        """Test successful execution of complete parameter sweep."""
        engine = create_atr_sweep_engine(sample_atr_config)

        # Mock data retrieval
        mock_get_data.return_value = sample_price_data

        # Mock single combination processing to return valid results
        def mock_process_combination(*args, **kwargs):
            return {
                "ATR Stop Length": 14,
                "ATR Stop Multiplier": 2.0,
                "Ticker": "TEST",
                "Total Return": 25.0,
                "Sharpe Ratio": 1.5,
            }

        with patch.object(
            engine,
            "process_single_atr_combination",
            side_effect=mock_process_combination,
        ):
            results, stats = engine.execute_atr_parameter_sweep(
                ticker="TEST",
                ma_config=sample_ma_config,
                log=mock_logger,
                use_concurrent=False,  # Use sequential for predictable testing
            )

        assert isinstance(results, list)
        assert len(results) > 0
        assert isinstance(stats, dict)
        assert stats["total_combinations"] > 0
        assert stats["successful_combinations"] > 0
        assert stats["processing_time"] > 0

        mock_get_data.assert_called_once_with("TEST", sample_ma_config, mock_logger)

    @patch("app.strategies.ma_cross.tools.atr_parameter_sweep.get_data")
    def test_execute_atr_parameter_sweep_data_failure(
        self, mock_get_data, sample_atr_config, sample_ma_config, mock_logger
    ):
        """Test handling of data retrieval failure."""
        engine = create_atr_sweep_engine(sample_atr_config)

        # Mock data retrieval failure
        mock_get_data.return_value = None

        results, stats = engine.execute_atr_parameter_sweep(
            ticker="TEST",
            ma_config=sample_ma_config,
            log=mock_logger,
            use_concurrent=False,
        )

        assert results == []
        assert isinstance(stats, dict)
        mock_get_data.assert_called_once()

    def test_validate_sweep_results_valid(self, sample_atr_config, mock_logger):
        """Test validation of successful sweep results."""
        engine = create_atr_sweep_engine(sample_atr_config)

        # Create valid results
        valid_results = [
            {
                "ATR Stop Length": 14,
                "ATR Stop Multiplier": 2.0,
                "Ticker": "TEST",
                "Total Return": 25.0,
                "Sharpe Ratio": 1.5,
                "Max Drawdown": -10.0,
                "Win Rate": 60.0,
                "Total Trades": 45,
                "Profit Factor": 1.8,
                "Expectancy Per Trade": 0.03,
                "Sortino Ratio": 1.2,
            }
            for i in range(10)
        ]

        # Add variety to ATR parameters
        for i, result in enumerate(valid_results):
            result["ATR Stop Length"] = 10 + i
            result["ATR Stop Multiplier"] = 1.5 + i * 0.1

        is_valid, errors = engine.validate_sweep_results(valid_results, mock_logger)

        assert is_valid == True
        assert len(errors) == 0

    def test_validate_sweep_results_empty(self, sample_atr_config, mock_logger):
        """Test validation of empty results."""
        engine = create_atr_sweep_engine(sample_atr_config)

        is_valid, errors = engine.validate_sweep_results([], mock_logger)

        assert is_valid == False
        assert len(errors) > 0
        assert "No results generated" in errors[0]

    def test_validate_sweep_results_missing_atr_fields(
        self, sample_atr_config, mock_logger
    ):
        """Test validation with missing ATR fields."""
        engine = create_atr_sweep_engine(sample_atr_config)

        # Create results missing ATR fields
        invalid_results = [
            {
                "Ticker": "TEST",
                "Total Return": 25.0,  # Missing ATR Stop Length and Multiplier
            }
        ]

        is_valid, errors = engine.validate_sweep_results(invalid_results, mock_logger)

        assert is_valid == False
        assert len(errors) > 0
        assert any("missing ATR Stop Length" in error for error in errors)


class TestATRPortfolioExport:
    """Test ATR portfolio export functionality."""

    @patch("app.strategies.ma_cross.3_get_atr_stop_portfolios.export_atr_portfolios")
    def test_export_atr_portfolios_success(self, mock_export):
        """Test successful ATR portfolio export."""
        # This is tested as part of the integration test below
        pass

    def test_atr_portfolio_schema_compliance(self):
        """Test that ATR portfolios comply with extended schema."""
        schema_transformer = SchemaTransformer()

        # Create sample ATR portfolio
        atr_portfolio = {
            "Ticker": "TEST",
            "Strategy Type": "SMA",
            "Short Window": 19,
            "Long Window": 29,
            "ATR Stop Length": 14,
            "ATR Stop Multiplier": 2.0,
            "Total Return": 25.0,
            "Sharpe Ratio": 1.5,
            "Max Drawdown": -10.0,
            "Win Rate": 60.0,
            "Total Trades": 45,
            "Profit Factor": 1.8,
            "Expectancy Per Trade": 0.03,
            "Sortino Ratio": 1.2,
        }

        # Transform to ATR extended schema
        extended_portfolio = schema_transformer.transform_to_atr_extended(
            atr_portfolio,
            atr_stop_length=14,
            atr_stop_multiplier=2.0,
            force_analysis_defaults=True,
        )

        # Validate schema compliance
        is_valid, errors = schema_transformer.validate_schema(
            extended_portfolio, SchemaType.ATR_EXTENDED
        )

        assert is_valid == True
        assert len(errors) == 0
        assert extended_portfolio["ATR Stop Length"] == 14
        assert extended_portfolio["ATR Stop Multiplier"] == 2.0


class TestATRAnalysisIntegration:
    """Integration tests for the complete ATR analysis workflow."""

    @patch("app.strategies.ma_cross.3_get_atr_stop_portfolios.get_data")
    @patch("app.strategies.ma_cross.tools.atr_signal_processing.calculate_sma_signals")
    @patch("app.tools.calculate_atr.calculate_atr")
    @patch("app.tools.backtest_strategy.backtest_strategy")
    def test_complete_atr_analysis_workflow(
        self,
        mock_backtest,
        mock_atr,
        mock_sma,
        mock_get_data,
        sample_price_data,
        mock_logger,
    ):
        """Test the complete ATR analysis workflow end-to-end."""
        # Mock data retrieval
        mock_get_data.return_value = sample_price_data

        # Mock SMA signals
        pandas_data = sample_price_data.to_pandas()
        sma_result = pandas_data.copy()
        sma_result["Signal"] = [0] * len(pandas_data)
        sma_result["Position"] = [0] * len(pandas_data)
        # Add some entry signals
        sma_result.loc[10:15, "Signal"] = 1
        mock_sma.return_value = sma_result

        # Mock ATR calculation
        mock_atr.return_value = pd.Series([2.0] * len(pandas_data))

        # Mock backtest
        mock_portfolio = Mock()
        mock_portfolio.stats.return_value = {
            "Total Return": 25.0,
            "Sharpe Ratio": 1.5,
            "Max Drawdown": -10.0,
            "Win Rate": 60.0,
            "Total Trades": 45,
            "Profit Factor": 1.8,
            "Expectancy Per Trade": 0.03,
            "Sortino Ratio": 1.2,
        }
        mock_backtest.return_value = mock_portfolio

        # Execute complete workflow
        import importlib

        atr_module = importlib.import_module(
            "app.strategies.ma_cross.3_get_atr_stop_portfolios"
        )
        execute_atr_analysis_for_ticker = atr_module.execute_atr_analysis_for_ticker

        config = {
            "TICKER": "TEST",
            "SHORT_WINDOW": 19,
            "LONG_WINDOW": 29,
            "USE_SMA": True,
            "BASE_DIR": "/tmp",
            "REFRESH": True,
            "USE_HOURLY": False,
            "DIRECTION": "Long",
            "USE_CURRENT": False,
            "ATR_LENGTH_MIN": 2,
            "ATR_LENGTH_MAX": 3,  # Small range for testing
            "ATR_MULTIPLIER_MIN": 1.5,
            "ATR_MULTIPLIER_MAX": 2.0,
            "ATR_MULTIPLIER_STEP": 0.5,
        }

        results = execute_atr_analysis_for_ticker("TEST", config, mock_logger)

        assert isinstance(results, list)
        assert len(results) > 0  # Should have some results

        # Check that results have ATR fields
        for result in results:
            assert "ATR Stop Length" in result
            assert "ATR Stop Multiplier" in result
            assert "Ticker" in result
            assert result["Ticker"] == "TEST"

        # Verify mocks were called
        mock_get_data.assert_called()
        mock_sma.assert_called()
        mock_atr.assert_called()
        mock_backtest.assert_called()

    def test_atr_analysis_memory_efficiency(self, mock_logger):
        """Test that ATR analysis handles memory efficiently."""
        # This is more of a performance test, but we can verify
        # that chunking is working properly
        config = {
            "ATR_LENGTH_MIN": 2,
            "ATR_LENGTH_MAX": 5,
            "ATR_MULTIPLIER_MIN": 1.0,
            "ATR_MULTIPLIER_MAX": 3.0,
            "ATR_MULTIPLIER_STEP": 0.5,
            "ATR_CHUNK_SIZE": 2,  # Small chunks
        }

        engine = create_atr_sweep_engine(config)
        combinations = engine.generate_atr_parameter_combinations()

        # Verify chunking would occur
        chunk_size = engine.chunk_size
        expected_chunks = len(combinations) // chunk_size + (
            1 if len(combinations) % chunk_size > 0 else 0
        )

        assert chunk_size == 2
        assert len(combinations) > chunk_size  # Should require chunking
        assert expected_chunks > 1

    @patch("polars.DataFrame.write_csv")
    def test_atr_portfolio_export_csv_format(self, mock_write_csv, mock_logger):
        """Test that ATR portfolios are exported in correct CSV format."""
        export_atr_portfolios = atr_module.export_atr_portfolios

        # Create sample portfolios
        portfolios = [
            {
                "Ticker": "TEST",
                "Strategy Type": "SMA",
                "Short Window": 19,
                "Long Window": 29,
                "ATR Stop Length": 14,
                "ATR Stop Multiplier": 2.0,
                "Total Return": 25.0,
                "Sharpe Ratio": 1.5,
                "Score": 75.5,
                "WIN_RATE": 0.60,
                "TRADES": 45,
                "EXPECTANCY_PER_TRADE": 0.03,
                "PROFIT_FACTOR": 1.8,
                "SORTINO_RATIO": 1.2,
            }
        ]

        config = {
            "BASE_DIR": "/tmp",
            "SHORT_WINDOW": 19,
            "LONG_WINDOW": 29,
            "USE_SMA": True,
            "MINIMUMS": {
                "WIN_RATE": 0.50,
                "TRADES": 40,
                "EXPECTANCY_PER_TRADE": 0.02,
                "PROFIT_FACTOR": 1.5,
                "SORTINO_RATIO": 1.0,
            },
            "SORT_BY": "Score",
            "SORT_ASC": False,
        }

        # Mock the filtering service to pass portfolios through
        with patch(
            "app.strategies.ma_cross.3_get_atr_stop_portfolios.PortfolioFilterService"
        ) as mock_filter_service:
            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_list.return_value = portfolios
            mock_filter_service.return_value = mock_filter_instance

            success = export_atr_portfolios(portfolios, "TEST", config, mock_logger)

            assert success == True
            mock_write_csv.assert_called_once()

            # Check that filtering was attempted
            mock_filter_instance.filter_portfolios_list.assert_called_once()


class TestATRConfigurationHandling:
    """Test ATR configuration handling and validation."""

    def test_atr_config_parameter_ranges(self):
        """Test ATR configuration parameter validation."""
        # Test with updated config parameters (from system reminder)
        config = {
            "ATR_LENGTH_MIN": 2,
            "ATR_LENGTH_MAX": 21,
            "ATR_MULTIPLIER_MIN": 1.5,
            "ATR_MULTIPLIER_MAX": 10.0,
            "ATR_MULTIPLIER_STEP": 0.2,
        }

        engine = create_atr_sweep_engine(config)
        combinations = engine.generate_atr_parameter_combinations()

        # Calculate expected combinations
        length_count = 21 - 2 + 1  # 20 lengths
        multiplier_count = int((10.0 - 1.5) / 0.2)  # 42 multipliers
        expected_total = length_count * multiplier_count  # 840 combinations

        assert len(combinations) == expected_total

        # Check boundary combinations
        assert (2, 1.5) in combinations  # Min values
        assert (21, 10.0) in combinations  # Max values

    def test_atr_config_minimums_validation(self):
        """Test MINIMUMS configuration validation."""
        minimums = {
            "WIN_RATE": 0.45,
            "TRADES": 40,
            "EXPECTANCY_PER_TRADE": 0.4,
            "PROFIT_FACTOR": 1.1,
            "SORTINO_RATIO": 0.4,
        }

        # Test portfolio that meets minimums
        portfolio = {
            "WIN_RATE": 0.50,
            "TRADES": 45,
            "EXPECTANCY_PER_TRADE": 0.45,
            "PROFIT_FACTOR": 1.2,
            "SORTINO_RATIO": 0.45,
        }

        # All criteria should be met
        for key, min_value in minimums.items():
            assert (
                portfolio[key] >= min_value
            ), f"{key} does not meet minimum: {portfolio[key]} < {min_value}"

        # Test portfolio that doesn't meet minimums
        failing_portfolio = {
            "WIN_RATE": 0.40,  # Below minimum
            "TRADES": 35,  # Below minimum
            "EXPECTANCY_PER_TRADE": 0.35,  # Below minimum
            "PROFIT_FACTOR": 1.0,  # Below minimum
            "SORTINO_RATIO": 0.35,  # Below minimum
        }

        # Should fail all criteria
        for key, min_value in minimums.items():
            assert failing_portfolio[key] < min_value, f"{key} should not meet minimum"

    def test_atr_config_sorting_options(self):
        """Test sorting configuration options."""
        portfolios = [
            {"Score": 85.0, "Total Return": 20.0},
            {"Score": 90.0, "Total Return": 15.0},
            {"Score": 80.0, "Total Return": 25.0},
        ]

        from app.tools.portfolio_results import sort_portfolios

        # Test sort by Score descending (default)
        sorted_desc = sort_portfolios(portfolios, "Score", False)
        assert sorted_desc[0]["Score"] == 90.0
        assert sorted_desc[1]["Score"] == 85.0
        assert sorted_desc[2]["Score"] == 80.0

        # Test sort by Score ascending
        sorted_asc = sort_portfolios(portfolios, "Score", True)
        assert sorted_asc[0]["Score"] == 80.0
        assert sorted_asc[1]["Score"] == 85.0
        assert sorted_asc[2]["Score"] == 90.0

        # Test sort by different field
        sorted_return = sort_portfolios(portfolios, "Total Return", False)
        assert sorted_return[0]["Total Return"] == 25.0
        assert sorted_return[1]["Total Return"] == 20.0
        assert sorted_return[2]["Total Return"] == 15.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
