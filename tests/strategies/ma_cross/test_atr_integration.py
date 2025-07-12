"""
Integration tests for ATR Analysis Feature.

This module provides end-to-end integration testing for the complete
ATR trailing stop parameter sensitivity analysis workflow including:
- Complete workflow from data loading to export
- Portfolio filtering and sorting integration
- Schema compliance and validation
- Memory optimization integration
- Error handling and recovery
"""

import importlib
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import numpy as np
import pandas as pd
import polars as pl
import pytest

atr_module = importlib.import_module(
    "app.strategies.ma_cross.3_get_atr_stop_portfolios"
)
execute_atr_analysis_for_ticker = atr_module.execute_atr_analysis_for_ticker
export_atr_portfolios = atr_module.export_atr_portfolios
run_atr_analysis = atr_module.run_atr_analysis
from app.tools.portfolio.base_extended_schemas import SchemaTransformer, SchemaType
from app.tools.portfolio.filtering_service import PortfolioFilterService


@pytest.fixture
def sample_price_data():
    """Create comprehensive sample price data for integration testing."""
    np.random.seed(42)
    dates = pd.date_range("2022-01-01", "2023-12-31", freq="D")

    # Create realistic price data with multiple trends
    base_price = 100
    trend_changes = [0, 200, 400, 600]  # Points where trend changes
    trends = [0.0002, -0.0001, 0.0003, -0.0002]  # Different trend rates

    returns = []
    for i, date in enumerate(dates):
        # Determine which trend period we're in
        trend_idx = 0
        for j, change_point in enumerate(trend_changes[1:], 1):
            if i >= change_point:
                trend_idx = j

        # Add trend + noise
        trend_return = trends[trend_idx]
        noise = np.random.normal(0, 0.015)  # 1.5% daily volatility
        returns.append(trend_return + noise)

    prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame(
        {
            "Date": dates,
            "Open": prices * 0.995,
            "High": prices * 1.02,
            "Low": prices * 0.98,
            "Close": prices,
            "Volume": np.random.randint(1000000, 10000000, len(dates)),
            "Ticker": "INTEGRATION_TEST",
        }
    ).set_index("Date")

    return pl.from_pandas(df.reset_index())


@pytest.fixture
def comprehensive_config():
    """Create comprehensive configuration for integration testing."""
    return {
        "TICKER": "INTEGRATION_TEST",
        "SHORT_WINDOW": 10,
        "LONG_WINDOW": 20,
        "USE_SMA": True,
        "BASE_DIR": "/tmp/atr_test",
        "REFRESH": True,
        "USE_HOURLY": False,
        "RELATIVE": False,
        "DIRECTION": "Long",
        "USE_CURRENT": False,
        "USE_RSI": False,
        "RSI_WINDOW": 4,
        "RSI_THRESHOLD": 52,
        # ATR parameter configuration
        "ATR_LENGTH_MIN": 5,
        "ATR_LENGTH_MAX": 7,  # Small range for testing
        "ATR_MULTIPLIER_MIN": 1.5,
        "ATR_MULTIPLIER_MAX": 2.5,
        "ATR_MULTIPLIER_STEP": 0.5,
        # Filtering and sorting
        "MINIMUMS": {
            "WIN_RATE": 0.30,  # Lenient for testing
            "TRADES": 5,
            "EXPECTANCY_PER_TRADE": 0.01,
            "PROFIT_FACTOR": 1.0,
            "SORTINO_RATIO": 0.1,
        },
        "SORT_BY": "Score",
        "SORT_ASC": False,
    }


@pytest.fixture
def mock_logger():
    """Create mock logger for integration testing."""
    return Mock()


@pytest.fixture
def sample_atr_portfolios():
    """Create sample ATR portfolio results for testing."""
    portfolios = []
    atr_lengths = [5, 6, 7]
    atr_multipliers = [1.5, 2.0, 2.5]

    for i, (length, multiplier) in enumerate(
        [(l, m) for l in atr_lengths for m in atr_multipliers]
    ):
        portfolio = {
            "Ticker": "INTEGRATION_TEST",
            "Strategy Type": "SMA",
            "Short Window": 10,
            "Long Window": 20,
            "ATR Stop Length": length,
            "ATR Stop Multiplier": multiplier,
            "Total Return": 15.0 + i * 2,  # Varying returns
            "Sharpe Ratio": 1.2 + i * 0.1,
            "Max Drawdown": -8.0 - i * 0.5,
            "Win Rate": 55.0 + i,
            "Total Trades": 30 + i * 2,
            "Profit Factor": 1.5 + i * 0.1,
            "Expectancy Per Trade": 0.025 + i * 0.005,
            "Sortino Ratio": 1.0 + i * 0.1,
            "Score": 70.0 + i * 2,
            # Additional fields for filtering
            "WIN_RATE": (55.0 + i) / 100.0,
            "TRADES": 30 + i * 2,
            "EXPECTANCY_PER_TRADE": 0.025 + i * 0.005,
            "PROFIT_FACTOR": 1.5 + i * 0.1,
            "SORTINO_RATIO": 1.0 + i * 0.1,
        }
        portfolios.append(portfolio)

    return portfolios


class TestCompleteATRWorkflow:
    """Test the complete ATR analysis workflow end-to-end."""

    @patch.object(atr_module, "get_data")
    @patch("app.strategies.ma_cross.tools.atr_signal_processing.calculate_sma_signals")
    @patch("app.tools.calculate_atr.calculate_atr")
    @patch("app.tools.backtest_strategy.backtest_strategy")
    def test_complete_workflow_success(
        self,
        mock_backtest,
        mock_atr,
        mock_sma,
        mock_get_data,
        sample_price_data,
        comprehensive_config,
        mock_logger,
    ):
        """Test successful completion of entire ATR analysis workflow."""
        # Mock data loading
        mock_get_data.return_value = sample_price_data

        # Mock SMA signal generation
        pandas_data = sample_price_data.to_pandas()
        sma_result = pandas_data.copy()
        sma_result["Signal"] = [0] * len(pandas_data)
        sma_result["Position"] = [0] * len(pandas_data)
        # Add realistic entry signals
        entry_points = [50, 150, 300, 500, 600]
        for point in entry_points:
            if point < len(sma_result):
                sma_result.loc[sma_result.index[point], "Signal"] = 1
        mock_sma.return_value = sma_result

        # Mock ATR calculation
        mock_atr.return_value = pd.Series(
            [2.5] * len(pandas_data), index=pandas_data.index
        )

        # Mock backtest with varying results
        def create_mock_portfolio(call_count=[0]):
            call_count[0] += 1
            portfolio = Mock()
            portfolio.stats.return_value = {
                "Total Return": 20.0 + call_count[0],
                "Sharpe Ratio": 1.3 + call_count[0] * 0.1,
                "Max Drawdown": -12.0 - call_count[0] * 0.5,
                "Win Rate": 58.0 + call_count[0],
                "Total Trades": 25 + call_count[0] * 3,
                "Profit Factor": 1.6 + call_count[0] * 0.1,
                "Expectancy Per Trade": 0.03 + call_count[0] * 0.005,
                "Sortino Ratio": 1.1 + call_count[0] * 0.1,
            }
            return portfolio

        mock_backtest.side_effect = lambda *args, **kwargs: create_mock_portfolio()

        # Execute complete workflow
        results = execute_atr_analysis_for_ticker(
            "INTEGRATION_TEST", comprehensive_config, mock_logger
        )

        # Verify results
        assert isinstance(results, list)
        assert len(results) > 0

        # Check expected number of combinations: 3 lengths × 3 multipliers = 9
        expected_combinations = 3 * 3
        assert len(results) == expected_combinations

        # Verify each result has required ATR fields
        for result in results:
            assert "ATR Stop Length" in result
            assert "ATR Stop Multiplier" in result
            assert "Ticker" in result
            assert result["Ticker"] == "INTEGRATION_TEST"
            assert 5 <= result["ATR Stop Length"] <= 7
            assert 1.5 <= result["ATR Stop Multiplier"] <= 2.5

        # Verify unique combinations
        combinations = [
            (r["ATR Stop Length"], r["ATR Stop Multiplier"]) for r in results
        ]
        assert len(set(combinations)) == len(combinations)  # All unique

        # Verify mocks were called appropriately
        mock_get_data.assert_called_once()
        assert mock_sma.call_count == expected_combinations
        assert mock_atr.call_count == expected_combinations
        assert mock_backtest.call_count == expected_combinations

    @patch.object(atr_module, "get_data")
    def test_workflow_data_loading_failure(
        self, mock_get_data, comprehensive_config, mock_logger
    ):
        """Test workflow handling of data loading failure."""
        # Mock data loading failure
        mock_get_data.return_value = None

        results = execute_atr_analysis_for_ticker(
            "INTEGRATION_TEST", comprehensive_config, mock_logger
        )

        assert results == []
        mock_get_data.assert_called_once()

        # Verify error was logged
        error_calls = [
            call
            for call in mock_logger.call_args_list
            if len(call[0]) > 1 and call[0][1] == "error"
        ]
        assert len(error_calls) > 0

    @patch.object(atr_module, "get_data")
    @patch("app.strategies.ma_cross.tools.atr_signal_processing.calculate_sma_signals")
    def test_workflow_partial_failures(
        self,
        mock_sma,
        mock_get_data,
        sample_price_data,
        comprehensive_config,
        mock_logger,
    ):
        """Test workflow handling when some combinations fail."""
        # Mock data loading success
        mock_get_data.return_value = sample_price_data

        # Mock SMA to fail for some calls
        call_count = [0]

        def mock_sma_with_failures(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 3 == 0:  # Fail every 3rd call
                return None
            else:
                pandas_data = sample_price_data.to_pandas()
                result = pandas_data.copy()
                result["Signal"] = [0] * len(pandas_data)
                result["Position"] = [0] * len(pandas_data)
                return result

        mock_sma.side_effect = mock_sma_with_failures

        results = execute_atr_analysis_for_ticker(
            "INTEGRATION_TEST", comprehensive_config, mock_logger
        )

        # Should have some results but not all (due to failures)
        expected_total = 3 * 3  # 9 combinations
        expected_successful = expected_total - (expected_total // 3)  # Minus failures
        assert len(results) == expected_successful

        # All returned results should be valid
        for result in results:
            assert "ATR Stop Length" in result
            assert "ATR Stop Multiplier" in result


class TestATRPortfolioExportIntegration:
    """Test ATR portfolio export functionality integration."""

    def test_export_atr_portfolios_full_workflow(
        self, sample_atr_portfolios, comprehensive_config, mock_logger
    ):
        """Test complete portfolio export workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Update config to use temp directory
            config = comprehensive_config.copy()
            config["BASE_DIR"] = temp_dir

            # Mock file operations
            with patch("polars.DataFrame.write_csv") as mock_write_csv:
                with patch.object(
                    atr_module, "PortfolioFilterService"
                ) as mock_filter_service:
                    # Mock filtering service
                    mock_filter_instance = Mock()
                    mock_filter_instance.filter_portfolios_list.return_value = (
                        sample_atr_portfolios
                    )
                    mock_filter_service.return_value = mock_filter_instance

                    # Execute export
                    success = export_atr_portfolios(
                        sample_atr_portfolios, "INTEGRATION_TEST", config, mock_logger
                    )

                    assert success == True

                    # Verify filtering was applied
                    mock_filter_instance.filter_portfolios_list.assert_called_once_with(
                        sample_atr_portfolios, config, mock_logger
                    )

                    # Verify CSV export was attempted
                    mock_write_csv.assert_called_once()

                    # Check expected filename format
                    expected_filename = "INTEGRATION_TEST_D_SMA_10_20_ATR.csv"
                    # The file path should contain this filename
                    call_args = mock_write_csv.call_args[0][0]
                    assert expected_filename in call_args

    def test_export_filtering_integration(
        self, sample_atr_portfolios, comprehensive_config, mock_logger
    ):
        """Test integration of portfolio filtering with export."""
        # Create portfolios with varying quality
        varied_portfolios = sample_atr_portfolios.copy()

        # Make some portfolios fail minimum criteria
        for i in [0, 2, 4]:  # Make every other portfolio fail
            varied_portfolios[i]["WIN_RATE"] = 0.25  # Below minimum
            varied_portfolios[i]["TRADES"] = 3  # Below minimum
            varied_portfolios[i]["PROFIT_FACTOR"] = 0.8  # Below minimum

        with tempfile.TemporaryDirectory() as temp_dir:
            config = comprehensive_config.copy()
            config["BASE_DIR"] = temp_dir

            with patch("polars.DataFrame.write_csv") as mock_write_csv:
                # Use real filtering service to test actual filtering logic
                success = export_atr_portfolios(
                    varied_portfolios, "INTEGRATION_TEST", config, mock_logger
                )

                # Should still succeed but with fewer portfolios
                assert success == True
                mock_write_csv.assert_called_once()

                # Check that filtering log messages were generated
                filter_calls = [
                    call
                    for call in mock_logger.call_args_list
                    if "Filtered portfolios" in str(call)
                ]
                assert len(filter_calls) > 0

    def test_export_sorting_integration(
        self, sample_atr_portfolios, comprehensive_config, mock_logger
    ):
        """Test integration of portfolio sorting with export."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = comprehensive_config.copy()
            config["BASE_DIR"] = temp_dir
            config["SORT_BY"] = "Total Return"
            config["SORT_ASC"] = True  # Ascending sort

            # Capture the DataFrame that gets written
            written_data = None

            def capture_write_csv(self, path):
                nonlocal written_data
                written_data = self.to_pandas()

            with patch("polars.DataFrame.write_csv", side_effect=capture_write_csv):
                with patch.object(
                    atr_module, "PortfolioFilterService"
                ) as mock_filter_service:
                    # Mock filtering to pass all portfolios
                    mock_filter_instance = Mock()
                    mock_filter_instance.filter_portfolios_list.return_value = (
                        sample_atr_portfolios
                    )
                    mock_filter_service.return_value = mock_filter_instance

                    success = export_atr_portfolios(
                        sample_atr_portfolios, "INTEGRATION_TEST", config, mock_logger
                    )

                    assert success == True
                    assert written_data is not None

                    # Verify sorting was applied (ascending order by Total Return)
                    total_returns = written_data["Total Return"].tolist()
                    assert total_returns == sorted(
                        total_returns
                    )  # Should be sorted ascending

    def test_export_schema_compliance(
        self, sample_atr_portfolios, comprehensive_config, mock_logger
    ):
        """Test that exported portfolios comply with ATR extended schema."""
        # Transform portfolios to ATR extended schema
        schema_transformer = SchemaTransformer()
        extended_portfolios = []

        for portfolio in sample_atr_portfolios:
            extended = schema_transformer.transform_to_atr_extended(
                portfolio,
                atr_stop_length=portfolio["ATR Stop Length"],
                atr_stop_multiplier=portfolio["ATR Stop Multiplier"],
                force_analysis_defaults=True,
            )
            extended_portfolios.append(extended)

        # Validate each portfolio
        for portfolio in extended_portfolios:
            is_valid, errors = schema_transformer.validate_schema(
                portfolio, SchemaType.ATR_EXTENDED
            )
            assert is_valid == True, f"Schema validation failed: {errors}"

    def test_export_empty_portfolios_handling(self, comprehensive_config, mock_logger):
        """Test handling of empty portfolio list in export."""
        success = export_atr_portfolios(
            [], "INTEGRATION_TEST", comprehensive_config, mock_logger
        )

        assert success == False

        # Should log warning about no portfolios
        warning_calls = [
            call
            for call in mock_logger.call_args_list
            if len(call[0]) > 1 and call[0][1] == "warning"
        ]
        assert len(warning_calls) > 0


class TestATRAnalysisMemoryIntegration:
    """Test memory optimization integration in ATR analysis."""

    def test_memory_optimization_integration(self, comprehensive_config, mock_logger):
        """Test that memory optimization is properly integrated."""
        from app.strategies.ma_cross.tools.atr_parameter_sweep import (
            create_atr_sweep_engine,
        )

        # Create engine with memory optimization enabled
        engine = create_atr_sweep_engine(
            comprehensive_config, enable_memory_optimization=True
        )

        # Verify memory optimization settings
        assert engine.enable_memory_optimization == True

        # Check that memory optimizer is available (if the module exists)
        if engine.memory_optimizer is not None:
            assert hasattr(engine, "memory_optimizer")

        # Verify chunking is configured for memory efficiency
        assert engine.chunk_size > 0
        assert engine.chunk_size <= 50  # Reasonable chunk size

    def test_chunking_behavior_integration(self, comprehensive_config, mock_logger):
        """Test that parameter combinations are properly chunked."""
        from app.strategies.ma_cross.tools.atr_parameter_sweep import (
            create_atr_sweep_engine,
        )

        # Configure for small chunks to test chunking behavior
        config = comprehensive_config.copy()
        config["ATR_CHUNK_SIZE"] = 2
        config["ATR_LENGTH_MIN"] = 5
        config["ATR_LENGTH_MAX"] = 8  # 4 lengths
        config["ATR_MULTIPLIER_MIN"] = 1.0
        config["ATR_MULTIPLIER_MAX"] = 2.0  # 3 multipliers (1.0, 1.5, 2.0)
        config["ATR_MULTIPLIER_STEP"] = 0.5

        engine = create_atr_sweep_engine(config)
        combinations = engine.generate_atr_parameter_combinations()

        # Total combinations: 4 lengths × 3 multipliers = 12
        assert len(combinations) == 12

        # With chunk size 2, should create 6 chunks
        chunk_size = engine.chunk_size
        expected_chunks = len(combinations) // chunk_size + (
            1 if len(combinations) % chunk_size > 0 else 0
        )
        assert expected_chunks == 6


class TestATRErrorHandlingIntegration:
    """Test error handling integration across the ATR analysis workflow."""

    @patch.object(atr_module, "get_data")
    def test_graceful_degradation_on_errors(
        self, mock_get_data, comprehensive_config, mock_logger
    ):
        """Test that system degrades gracefully when errors occur."""
        # Simulate various types of failures
        mock_get_data.side_effect = Exception("Data loading failed")

        results = execute_atr_analysis_for_ticker(
            "INTEGRATION_TEST", comprehensive_config, mock_logger
        )

        # Should return empty list instead of crashing
        assert results == []

        # Should log error details
        error_calls = [
            call
            for call in mock_logger.call_args_list
            if len(call[0]) > 1 and call[0][1] == "error"
        ]
        assert len(error_calls) > 0

    def test_configuration_error_handling(self, mock_logger):
        """Test handling of invalid configuration."""
        # Invalid configuration with missing required fields
        invalid_config = {
            "TICKER": "TEST",
            # Missing SHORT_WINDOW, LONG_WINDOW, etc.
        }

        # Should handle gracefully without crashing
        try:
            results = execute_atr_analysis_for_ticker(
                "TEST", invalid_config, mock_logger
            )
            # If it doesn't crash, should return empty results
            assert results == []
        except Exception as e:
            # If it does throw an exception, it should be informative
            assert "config" in str(e).lower() or "missing" in str(e).lower()

    def test_file_permission_error_handling(self, sample_atr_portfolios, mock_logger):
        """Test handling of file permission errors during export."""
        config = {
            "BASE_DIR": "/root/readonly",  # Directory that shouldn't be writable
            "SHORT_WINDOW": 10,
            "LONG_WINDOW": 20,
            "USE_SMA": True,
            "MINIMUMS": {},
            "SORT_BY": "Score",
            "SORT_ASC": False,
        }

        # Mock to simulate permission error
        with patch("os.makedirs", side_effect=PermissionError("Permission denied")):
            success = export_atr_portfolios(
                sample_atr_portfolios, "TEST", config, mock_logger
            )

            assert success == False

            # Should log error
            error_calls = [
                call
                for call in mock_logger.call_args_list
                if len(call[0]) > 1 and call[0][1] == "error"
            ]
            assert len(error_calls) > 0


class TestATREndToEndScenarios:
    """Test real-world end-to-end scenarios for ATR analysis."""

    @patch.object(atr_module, "run_atr_analysis")
    def test_command_line_execution_scenario(self, mock_run):
        """Test scenario of running ATR analysis from command line."""
        # Mock successful execution
        mock_run.return_value = True

        # This would typically be called from command line
        default_config = atr_module.default_config

        # Verify default config has required ATR parameters
        assert "ATR_LENGTH_MIN" in default_config
        assert "ATR_LENGTH_MAX" in default_config
        assert "ATR_MULTIPLIER_MIN" in default_config
        assert "ATR_MULTIPLIER_MAX" in default_config
        assert "ATR_MULTIPLIER_STEP" in default_config
        assert "MINIMUMS" in default_config
        assert "SORT_BY" in default_config
        assert "SORT_ASC" in default_config

        # Verify MINIMUMS has expected fields
        minimums = default_config["MINIMUMS"]
        expected_minimum_fields = [
            "WIN_RATE",
            "TRADES",
            "EXPECTANCY_PER_TRADE",
            "PROFIT_FACTOR",
            "SORTINO_RATIO",
        ]
        for field in expected_minimum_fields:
            assert field in minimums

    def test_large_parameter_space_scenario(self, mock_logger):
        """Test scenario with large parameter space (similar to production)."""
        # Configuration similar to production (but smaller for testing)
        large_config = {
            "ATR_LENGTH_MIN": 2,
            "ATR_LENGTH_MAX": 10,  # 9 lengths
            "ATR_MULTIPLIER_MIN": 1.0,
            "ATR_MULTIPLIER_MAX": 3.0,  # 21 multipliers (step 0.1)
            "ATR_MULTIPLIER_STEP": 0.1,
            "ATR_CHUNK_SIZE": 25,  # Reasonable chunk size
        }

        from app.strategies.ma_cross.tools.atr_parameter_sweep import (
            create_atr_sweep_engine,
        )

        engine = create_atr_sweep_engine(large_config)
        combinations = engine.generate_atr_parameter_combinations()

        # Expected combinations: 9 lengths × 21 multipliers = 189
        expected_total = 9 * 21
        assert len(combinations) == expected_total

        # Verify chunking would be effective
        chunk_count = len(combinations) // engine.chunk_size + (
            1 if len(combinations) % engine.chunk_size > 0 else 0
        )
        assert chunk_count > 1  # Should require multiple chunks

    def test_realistic_filtering_scenario(self, mock_logger):
        """Test realistic filtering scenario with mixed portfolio quality."""
        # Create portfolios with realistic distribution of quality
        portfolios = []

        # Good portfolios (should pass filtering)
        for i in range(10):
            portfolios.append(
                {
                    "WIN_RATE": 0.55 + i * 0.01,
                    "TRADES": 50 + i * 5,
                    "EXPECTANCY_PER_TRADE": 0.05 + i * 0.01,
                    "PROFIT_FACTOR": 1.8 + i * 0.1,
                    "SORTINO_RATIO": 1.2 + i * 0.1,
                    "Score": 80 + i * 2,
                    "ATR Stop Length": 10 + i,
                    "ATR Stop Multiplier": 1.5 + i * 0.1,
                }
            )

        # Mediocre portfolios (some should pass, some should fail)
        for i in range(10):
            portfolios.append(
                {
                    "WIN_RATE": 0.40 + i * 0.02,
                    "TRADES": 30 + i * 3,
                    "EXPECTANCY_PER_TRADE": 0.02 + i * 0.005,
                    "PROFIT_FACTOR": 1.2 + i * 0.05,
                    "SORTINO_RATIO": 0.8 + i * 0.05,
                    "Score": 60 + i,
                    "ATR Stop Length": 15 + i,
                    "ATR Stop Multiplier": 2.0 + i * 0.05,
                }
            )

        # Poor portfolios (should mostly fail filtering)
        for i in range(10):
            portfolios.append(
                {
                    "WIN_RATE": 0.25 + i * 0.01,
                    "TRADES": 10 + i * 2,
                    "EXPECTANCY_PER_TRADE": 0.005 + i * 0.002,
                    "PROFIT_FACTOR": 0.8 + i * 0.02,
                    "SORTINO_RATIO": 0.3 + i * 0.02,
                    "Score": 40 + i,
                    "ATR Stop Length": 20 + i,
                    "ATR Stop Multiplier": 2.5 + i * 0.02,
                }
            )

        # Apply realistic filtering criteria
        config = {
            "MINIMUMS": {
                "WIN_RATE": 0.45,
                "TRADES": 40,
                "EXPECTANCY_PER_TRADE": 0.03,
                "PROFIT_FACTOR": 1.5,
                "SORTINO_RATIO": 1.0,
            }
        }

        filter_service = PortfolioFilterService()
        filtered = filter_service.filter_portfolios_list(
            portfolios, config, mock_logger
        )

        # Should have significantly fewer portfolios after filtering
        assert len(filtered) < len(portfolios)
        assert len(filtered) > 0  # But should have some survivors

        # All remaining portfolios should meet minimum criteria
        for portfolio in filtered:
            assert portfolio["WIN_RATE"] >= config["MINIMUMS"]["WIN_RATE"]
            assert portfolio["TRADES"] >= config["MINIMUMS"]["TRADES"]
            assert (
                portfolio["EXPECTANCY_PER_TRADE"]
                >= config["MINIMUMS"]["EXPECTANCY_PER_TRADE"]
            )
            assert portfolio["PROFIT_FACTOR"] >= config["MINIMUMS"]["PROFIT_FACTOR"]
            assert portfolio["SORTINO_RATIO"] >= config["MINIMUMS"]["SORTINO_RATIO"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
