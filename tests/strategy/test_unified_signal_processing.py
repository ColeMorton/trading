"""
Test Suite for Unified Signal Processing System

This module tests the consolidated signal processing functionality to ensure
it properly handles all strategy types while eliminating code duplication.
"""

from unittest.mock import Mock, patch

import polars as pl
import pytest

from app.tools.strategy.signal_processing import (
    MACDSignalProcessor,
    MASignalProcessor,
    MeanReversionSignalProcessor,
    SignalProcessorBase,
    SignalProcessorFactory,
    process_current_signals,
    process_ticker_portfolios,
)


class TestSignalProcessorBase:
    """Test cases for SignalProcessorBase abstract class."""

    def test_abstract_class_cannot_be_instantiated(self):
        """Test that abstract base class cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SignalProcessorBase("SMA")


class TestMASignalProcessor:
    """Test cases for MASignalProcessor."""

    def test_ma_processor_initialization(self):
        """Test MA signal processor initialization."""
        processor = MASignalProcessor("SMA")
        assert processor.strategy_type == "SMA"
        assert processor.ma_type == "SMA"

        ema_processor = MASignalProcessor("EMA")
        assert ema_processor.strategy_type == "EMA"
        assert ema_processor.ma_type == "EMA"

    def test_extract_strategy_parameters(self):
        """Test extraction of MA-specific parameters."""
        processor = MASignalProcessor("SMA")
        row = {"Fast Period": 10, "Slow Period": 50}

        params = processor._extract_strategy_parameters(row)

        assert params["fast_period"] == 10
        assert params["slow_period"] == 50

    @patch("app.strategies.ma_cross.tools.signal_generation.generate_current_signals")
    def test_generate_current_signals_success(self, mock_generate):
        """Test successful signal generation for MA strategy."""
        processor = MASignalProcessor("SMA")
        mock_log = Mock()
        config = {"TICKER": "AAPL", "STRATEGY_TYPE": "SMA"}

        mock_df = pl.DataFrame({"Fast Period": [10], "Slow Period": [50]})
        mock_generate.return_value = mock_df

        result = processor.generate_current_signals(config, mock_log)

        assert result.equals(mock_df)
        mock_generate.assert_called_once_with(config, mock_log)

    @patch("app.strategies.ma_cross.tools.signal_generation.generate_current_signals")
    def test_generate_current_signals_import_error(self, mock_generate):
        """Test signal generation with import error."""
        processor = MASignalProcessor("SMA")
        mock_log = Mock()
        config = {"TICKER": "AAPL"}

        # Simulate ImportError
        mock_generate.side_effect = ImportError("Module not found")

        result = processor.generate_current_signals(config, mock_log)

        assert len(result) == 0
        mock_log.assert_called_with(
            "Failed to import MA signal generation for SMA", "error",
        )

    @patch(
        "app.strategies.ma_cross.tools.sensitivity_analysis.analyze_window_combination",
    )
    def test_analyze_parameter_combination_success(self, mock_analyze):
        """Test successful parameter combination analysis."""
        processor = MASignalProcessor("SMA")
        mock_log = Mock()
        data = pl.DataFrame({"Close": [100, 101, 102]})
        config = {"TICKER": "AAPL"}

        expected_result = {"Total Return [%]": 5.0, "Win Rate [%]": 60.0}
        mock_analyze.return_value = expected_result

        result = processor.analyze_parameter_combination(
            data, config, mock_log, fast_period=10, slow_period=50,
        )

        assert result == expected_result
        mock_analyze.assert_called_once_with(
            data=data, fast_period=10, slow_period=50, config=config, log=mock_log,
        )


class TestMACDSignalProcessor:
    """Test cases for MACDSignalProcessor."""

    def test_macd_processor_initialization(self):
        """Test MACD signal processor initialization."""
        processor = MACDSignalProcessor()
        assert processor.strategy_type == "MACD"

    def test_extract_strategy_parameters(self):
        """Test extraction of MACD-specific parameters."""
        processor = MACDSignalProcessor()
        row = {"Fast Period": 12, "Slow Period": 26, "Signal Period": 9}

        params = processor._extract_strategy_parameters(row)

        assert params["fast_period"] == 12
        assert params["slow_period"] == 26
        assert params["signal_period"] == 9

    @patch("app.strategies.macd.tools.signal_generation.generate_current_signals")
    def test_generate_current_signals_success(self, mock_generate):
        """Test successful signal generation for MACD strategy."""
        processor = MACDSignalProcessor()
        mock_log = Mock()
        config = {"TICKER": "AAPL", "STRATEGY_TYPE": "MACD"}

        mock_df = pl.DataFrame(
            {"Fast Period": [12], "Slow Period": [26], "Signal Period": [9]},
        )
        mock_generate.return_value = mock_df

        result = processor.generate_current_signals(config, mock_log)

        assert result.equals(mock_df)
        mock_generate.assert_called_once_with(config, mock_log)


class TestMeanReversionSignalProcessor:
    """Test cases for MeanReversionSignalProcessor."""

    def test_mean_reversion_processor_initialization(self):
        """Test Mean Reversion signal processor initialization."""
        processor = MeanReversionSignalProcessor()
        assert processor.strategy_type == "MEAN_REVERSION"

    def test_extract_strategy_parameters(self):
        """Test extraction of Mean Reversion-specific parameters."""
        processor = MeanReversionSignalProcessor()
        row = {"Change PCT": 0.05}

        params = processor._extract_strategy_parameters(row)

        assert params["change_pct"] == 0.05


class TestSignalProcessorFactory:
    """Test cases for SignalProcessorFactory."""

    def test_create_sma_processor(self):
        """Test creating SMA processor."""
        processor = SignalProcessorFactory.create_processor("SMA")
        assert isinstance(processor, MASignalProcessor)
        assert processor.ma_type == "SMA"

    def test_create_ema_processor(self):
        """Test creating EMA processor."""
        processor = SignalProcessorFactory.create_processor("EMA")
        assert isinstance(processor, MASignalProcessor)
        assert processor.ma_type == "EMA"

    def test_create_macd_processor(self):
        """Test creating MACD processor."""
        processor = SignalProcessorFactory.create_processor("MACD")
        assert isinstance(processor, MACDSignalProcessor)

    def test_create_mean_reversion_processor(self):
        """Test creating Mean Reversion processor."""
        processor = SignalProcessorFactory.create_processor("MEAN_REVERSION")
        assert isinstance(processor, MeanReversionSignalProcessor)

    def test_create_processor_case_insensitive(self):
        """Test factory handles case-insensitive strategy types."""
        processor = SignalProcessorFactory.create_processor("sma")
        assert isinstance(processor, MASignalProcessor)

        processor = SignalProcessorFactory.create_processor("Macd")
        assert isinstance(processor, MACDSignalProcessor)

    def test_create_processor_unsupported_strategy(self):
        """Test factory raises error for unsupported strategy."""
        with pytest.raises(ValueError, match="Unsupported strategy type: INVALID"):
            SignalProcessorFactory.create_processor("INVALID")

    def test_get_supported_strategies(self):
        """Test getting list of supported strategies."""
        strategies = SignalProcessorFactory.get_supported_strategies()

        expected = ["SMA", "EMA", "MACD", "MEAN_REVERSION", "MA_CROSS"]
        assert all(strategy in strategies for strategy in expected)


class TestUnifiedSignalProcessing:
    """Test cases for unified signal processing functionality."""

    @patch(
        "app.tools.strategy.signal_processing.SignalProcessorFactory.create_processor",
    )
    def test_process_current_signals_with_strategy_type(self, mock_create):
        """Test process_current_signals with explicit strategy type."""
        mock_processor = Mock()
        mock_processor.process_current_signals.return_value = pl.DataFrame(
            {"result": [1]},
        )
        mock_create.return_value = mock_processor

        mock_log = Mock()
        config = {"TICKER": "AAPL"}

        result = process_current_signals("AAPL", config, mock_log, "SMA")

        mock_create.assert_called_once_with("SMA")
        mock_processor.process_current_signals.assert_called_once_with(
            "AAPL", config, mock_log,
        )
        assert len(result) == 1

    @patch(
        "app.tools.strategy.signal_processing.SignalProcessorFactory.create_processor",
    )
    def test_process_current_signals_auto_detect_strategy(self, mock_create):
        """Test process_current_signals with auto-detected strategy type."""
        mock_processor = Mock()
        mock_processor.process_current_signals.return_value = pl.DataFrame(
            {"result": [1]},
        )
        mock_create.return_value = mock_processor

        mock_log = Mock()
        config = {"TICKER": "AAPL", "STRATEGY_TYPE": "MACD"}

        process_current_signals("AAPL", config, mock_log)

        mock_create.assert_called_once_with("MACD")
        mock_processor.process_current_signals.assert_called_once_with(
            "AAPL", config, mock_log,
        )

    @patch(
        "app.tools.strategy.signal_processing.SignalProcessorFactory.create_processor",
    )
    def test_process_ticker_portfolios_with_strategy_type(self, mock_create):
        """Test process_ticker_portfolios with explicit strategy type."""
        mock_processor = Mock()
        mock_processor.process_ticker_portfolios.return_value = pl.DataFrame(
            {"result": [1]},
        )
        mock_create.return_value = mock_processor

        mock_log = Mock()
        config = {"TICKER": "AAPL"}

        result = process_ticker_portfolios("AAPL", config, mock_log, "EMA")

        mock_create.assert_called_once_with("EMA")
        mock_processor.process_ticker_portfolios.assert_called_once_with(
            "AAPL", config, mock_log,
        )
        assert len(result) == 1


class TestProcessCurrentSignalsIntegration:
    """Integration tests for process_current_signals method."""

    @patch("app.tools.get_data.get_data")
    @patch("app.tools.strategy.unified_config.ConfigValidator.validate_base_config")
    def test_process_current_signals_validation_failure(
        self, mock_validate, mock_get_data,
    ):
        """Test process_current_signals with validation failure."""
        processor = MASignalProcessor("SMA")
        mock_log = Mock()
        config = {"TICKER": "AAPL"}

        # Mock validation failure
        mock_validate.return_value = {
            "is_valid": False,
            "errors": ["Missing required field"],
        }

        result = processor.process_current_signals("AAPL", config, mock_log)

        assert result is None
        mock_log.assert_called_with(
            "Invalid configuration for AAPL: ['Missing required field']", "error",
        )
        mock_get_data.assert_not_called()

    @patch("app.strategies.ma_cross.tools.signal_generation.generate_current_signals")
    @patch("app.tools.get_data.get_data")
    @patch("app.tools.strategy.unified_config.ConfigValidator.validate_base_config")
    def test_process_current_signals_no_signals(
        self, mock_validate, mock_get_data, mock_generate,
    ):
        """Test process_current_signals with no signals found."""
        processor = MASignalProcessor("SMA")
        mock_log = Mock()
        config = {"TICKER": "AAPL", "DIRECTION": "Long"}

        # Mock successful validation but no signals
        mock_validate.return_value = {"is_valid": True, "errors": []}
        mock_generate.return_value = pl.DataFrame()  # Empty DataFrame

        result = processor.process_current_signals("AAPL", config, mock_log)

        assert result is None
        mock_log.assert_called_with(
            "No current signals found for AAPL Long SMA", "warning",
        )
        mock_get_data.assert_not_called()

    @patch("app.strategies.ma_cross.tools.signal_generation.generate_current_signals")
    @patch("app.tools.get_data.get_data")
    @patch("app.tools.strategy.unified_config.ConfigValidator.validate_base_config")
    def test_process_current_signals_data_fetch_failure(
        self, mock_validate, mock_get_data, mock_generate,
    ):
        """Test process_current_signals with data fetch failure."""
        processor = MASignalProcessor("SMA")
        mock_log = Mock()
        config = {"TICKER": "AAPL"}

        # Mock successful validation and signals but data fetch failure
        mock_validate.return_value = {"is_valid": True, "errors": []}
        mock_generate.return_value = pl.DataFrame(
            {"Fast Period": [10], "Slow Period": [50]},
        )
        mock_get_data.return_value = None

        result = processor.process_current_signals("AAPL", config, mock_log)

        assert result is None
        # Check that an error was logged (could be data fetch or processing error)
        error_calls = [
            call
            for call in mock_log.call_args_list
            if len(call[0]) > 1 and call[0][1] == "error"
        ]
        assert len(error_calls) > 0
        assert "AAPL" in error_calls[-1][0][0]


class TestProcessTickerPortfoliosIntegration:
    """Integration tests for process_ticker_portfolios method."""

    @patch(
        "app.tools.strategy.signal_processing.MASignalProcessor.process_current_signals",
    )
    def test_process_ticker_portfolios_use_current(self, mock_process_current):
        """Test process_ticker_portfolios with USE_CURRENT=True."""
        processor = MASignalProcessor("SMA")
        mock_log = Mock()
        config = {"TICKER": "AAPL", "USE_CURRENT": True}

        expected_df = pl.DataFrame({"result": [1]})
        mock_process_current.return_value = expected_df

        result = processor.process_ticker_portfolios("AAPL", config, mock_log)

        assert result.equals(expected_df)
        mock_process_current.assert_called_once_with("AAPL", config, mock_log)

    @patch("app.tools.portfolio.processing.process_single_ticker")
    def test_process_ticker_portfolios_full_analysis(self, mock_process_single):
        """Test process_ticker_portfolios with full analysis."""
        processor = MASignalProcessor("SMA")
        mock_log = Mock()
        config = {"TICKER": "AAPL", "USE_CURRENT": False, "DIRECTION": "Long"}

        mock_portfolios = [{"Total Return [%]": 5.0}]
        mock_process_single.return_value = mock_portfolios

        result = processor.process_ticker_portfolios("AAPL", config, mock_log)

        assert len(result) == 1
        assert result["Total Return [%]"][0] == 5.0
        mock_log.assert_called_with("Results for AAPL Long SMA")


if __name__ == "__main__":
    pytest.main([__file__])
