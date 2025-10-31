"""
Unit tests for MA Cross core components.
"""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from app.strategies.ma_cross.core.analyzer import MACrossAnalyzer
from app.strategies.ma_cross.core.models import (  # Backward compatibility aliases
    AnalysisConfig,
    AnalysisResult,
    SignalInfo,
    TickerResult,
)
from app.strategies.ma_cross.scanner_adapter import ScannerAdapter


@pytest.fixture
def sample_config():
    """Create sample MA Cross configuration."""
    return AnalysisConfig(
        ticker="AAPL",
        strategy_type="SMA",
        fast_period=20,
        slow_period=50,
        direction="Long",
        windows=89,
        use_hourly=False,
        use_years=False,
        years=1.0,
    )


@pytest.fixture
def sample_price_data():
    """Create sample price data."""
    dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")
    np.random.seed(42)

    # Generate realistic price data
    base_price = 100
    returns = np.random.normal(0.0005, 0.02, len(dates))
    prices = base_price * np.exp(np.cumsum(returns))

    return pd.DataFrame(
        {
            "Date": dates,
            "Open": prices * 0.98,
            "High": prices * 1.02,
            "Low": prices * 0.97,
            "Close": prices,
            "Volume": np.random.randint(1000000, 5000000, len(dates)),
            "Ticker": "AAPL",
        },
    ).set_index("Date")


class TestMACrossConfig:
    """Test MA Cross configuration model."""

    @pytest.mark.unit
    @pytest.mark.smoke
    def test_config_creation(self, sample_config):
        """Test configuration creation."""
        assert sample_config.ticker == "AAPL"
        assert sample_config.use_sma is True
        assert sample_config.fast_period == 20
        assert sample_config.slow_period == 50
        assert sample_config.direction == "Long"
        assert sample_config.windows == 89

    @pytest.mark.unit
    def test_config_validation(self):
        """Test configuration creation with different parameters."""
        # Test that config accepts valid MA periods
        config1 = AnalysisConfig(
            ticker="AAPL",
            fast_period=20,
            slow_period=50,  # Long > Short is valid
            strategy_type="SMA",
        )
        assert config1.fast_period == 20
        assert config1.slow_period == 50

        # Test different direction values (both should work since no validation)
        config2 = AnalysisConfig(ticker="AAPL", direction="Short", strategy_type="SMA")
        assert config2.direction == "Short"

        # Test with different ticker values
        config3 = AnalysisConfig(ticker="MSFT", strategy_type="SMA")
        assert config3.ticker == "MSFT"

    @pytest.mark.unit
    def test_config_defaults(self):
        """Test default configuration values."""
        config = AnalysisConfig(ticker="AAPL")

        assert config.use_sma is True  # Default is SMA
        assert config.use_hourly is False
        assert config.direction == "Long"
        assert config.use_years is False
        assert config.years == 1.0
        assert config.use_synthetic is False


class TestMACrossAnalyzer:
    """Test MA Cross analyzer functionality."""

    @pytest.mark.unit
    @pytest.mark.smoke
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""

        def mock_log(msg, level="info"):
            pass

        analyzer = MACrossAnalyzer(log=mock_log)
        assert analyzer is not None
        # Analyzer doesn't store config, it takes config per analysis

    @pytest.mark.unit
    @patch("app.strategies.ma_cross.core.analyzer.execute_single_strategy")
    def test_analyze_single_ticker(
        self,
        mock_execute,
        sample_config,
        sample_price_data,
    ):
        """Test single ticker analysis."""
        # Mock the strategy execution to return portfolio stats
        mock_execute.return_value = {
            "Total Return": 25.0,
            "Sharpe Ratio": 1.5,
            "Max Drawdown": -15.0,
            "Win Rate": 60.0,
            "Total Trades": 10,
            "Profit Factor": 2.0,
            "Expectancy per Trade": 0.03,
            "Sortino Ratio": 1.2,
            "Beats BnH %": 15.0,
        }

        def mock_log(msg, level="info"):
            pass

        analyzer = MACrossAnalyzer(log=mock_log)
        result = analyzer.analyze_single(sample_config)

        assert isinstance(result, TickerResult)
        assert result.ticker == "AAPL"
        assert result.total_return_pct == 25.0
        assert result.sharpe_ratio == 1.5
        mock_execute.assert_called_once()

    @pytest.mark.unit
    @patch("app.strategies.ma_cross.core.analyzer.execute_single_strategy")
    def test_sma_analysis_behavior(self, mock_execute, sample_price_data):
        """Test SMA analysis produces valid results."""
        mock_execute.return_value = {
            "Total Return": 20.0,
            "Sharpe Ratio": 1.2,
            "Max Drawdown": -10.0,
            "Win Rate": 55.0,
            "Total Trades": 8,
            "Profit Factor": 1.8,
            "Expectancy per Trade": 0.025,
            "Sortino Ratio": 1.0,
            "Beats BnH %": 10.0,
        }

        def mock_log(msg, level="info"):
            pass

        config = AnalysisConfig(
            ticker="AAPL",
            strategy_type="SMA",
            fast_period=20,
            slow_period=50,
        )

        analyzer = MACrossAnalyzer(log=mock_log)
        result = analyzer.analyze_single(config)

        # Test that SMA analysis produces valid portfolio metrics
        assert isinstance(result, TickerResult)
        assert result.ticker == "AAPL"
        assert result.strategy_type == "SMA"
        assert result.fast_period == 20
        assert result.slow_period == 50

    @pytest.mark.unit
    @patch("app.strategies.ma_cross.core.analyzer.execute_single_strategy")
    def test_ema_analysis_behavior(self, mock_execute, sample_price_data):
        """Test EMA analysis produces valid results."""
        mock_execute.return_value = {
            "Total Return": 22.0,
            "Sharpe Ratio": 1.3,
            "Max Drawdown": -12.0,
            "Win Rate": 58.0,
            "Total Trades": 12,
            "Profit Factor": 1.9,
            "Expectancy per Trade": 0.028,
            "Sortino Ratio": 1.1,
            "Beats BnH %": 12.0,
        }

        def mock_log(msg, level="info"):
            pass

        config = AnalysisConfig(
            ticker="AAPL",
            strategy_type="EMA",
            fast_period=12,
            slow_period=26,  # Use EMA
        )

        analyzer = MACrossAnalyzer(log=mock_log)
        result = analyzer.analyze_single(config)

        # Test that EMA analysis produces valid portfolio metrics
        assert isinstance(result, TickerResult)
        assert result.ticker == "AAPL"
        assert result.strategy_type == "EMA"
        assert result.fast_period == 12
        assert result.slow_period == 26

    @pytest.mark.unit
    @patch("app.strategies.ma_cross.core.analyzer.execute_single_strategy")
    def test_signal_generation_behavior(self, mock_execute, sample_price_data):
        """Test signal generation through complete analysis."""
        mock_execute.return_value = {
            "Total Return": 30.0,
            "Sharpe Ratio": 1.8,
            "Max Drawdown": -8.0,
            "Win Rate": 65.0,
            "Total Trades": 15,
            "Profit Factor": 2.2,
            "Expectancy per Trade": 0.04,
            "Sortino Ratio": 1.5,
            "Beats BnH %": 20.0,
        }

        def mock_log(msg, level="info"):
            pass

        config = AnalysisConfig(
            ticker="AAPL",
            strategy_type="SMA",
            fast_period=5,
            slow_period=15,  # Shorter windows for more signals
        )

        analyzer = MACrossAnalyzer(log=mock_log)
        result = analyzer.analyze_single(config)

        # Test that analysis can detect trading signals
        assert isinstance(result, TickerResult)
        assert result.total_trades >= 0  # Should have some trades with trend data

    @pytest.mark.unit
    @patch("app.strategies.ma_cross.core.analyzer.execute_single_strategy")
    def test_portfolio_metrics_calculation(self, mock_execute, sample_price_data):
        """Test portfolio metrics are calculated correctly."""
        mock_execute.return_value = {
            "Total Return": 18.5,
            "Sharpe Ratio": 1.1,
            "Max Drawdown": -11.0,
            "Win Rate": 52.0,
            "Total Trades": 6,
            "Profit Factor": 1.6,
            "Expectancy per Trade": 0.02,
            "Sortino Ratio": 0.9,
            "Beats BnH %": 8.0,
        }

        def mock_log(msg, level="info"):
            pass

        config = AnalysisConfig(
            ticker="AAPL",
            strategy_type="SMA",
            fast_period=10,
            slow_period=20,
        )

        analyzer = MACrossAnalyzer(log=mock_log)
        result = analyzer.analyze_single(config)

        # Test that portfolio metrics are calculated and valid
        assert isinstance(result, TickerResult)
        assert hasattr(result, "total_return_pct")
        assert hasattr(result, "win_rate_pct")
        assert hasattr(result, "max_drawdown_pct")
        assert hasattr(result, "total_trades")

        # Metrics should be reasonable values
        assert -100 <= result.total_return_pct <= 1000  # Reasonable return range
        assert 0 <= result.win_rate_pct <= 100  # Win rate percentage
        assert result.max_drawdown_pct <= 0  # Drawdown should be negative

    @pytest.mark.unit
    @patch("app.strategies.ma_cross.core.analyzer.execute_single_strategy")
    def test_multiple_ticker_analysis(self, mock_execute, sample_price_data):
        """Test analysis of multiple tickers."""
        # Return different results for each ticker
        mock_execute.side_effect = [
            {
                "Total Return": 25.0,
                "Sharpe Ratio": 1.5,
                "Max Drawdown": -15.0,
                "Win Rate": 60.0,
                "Total Trades": 10,
                "Profit Factor": 2.0,
                "Expectancy per Trade": 0.03,
                "Sortino Ratio": 1.2,
                "Beats BnH %": 15.0,
            },
            {
                "Total Return": 30.0,
                "Sharpe Ratio": 1.8,
                "Max Drawdown": -12.0,
                "Win Rate": 65.0,
                "Total Trades": 12,
                "Profit Factor": 2.2,
                "Expectancy per Trade": 0.035,
                "Sortino Ratio": 1.4,
                "Beats BnH %": 18.0,
            },
        ]

        def mock_log(msg, level="info"):
            pass

        base_config = AnalysisConfig(
            ticker="AAPL",  # Will be overridden per ticker
            strategy_type="SMA",
            fast_period=20,
            slow_period=50,
        )

        tickers = ["AAPL", "MSFT"]

        analyzer = MACrossAnalyzer(log=mock_log)
        result = analyzer.analyze_portfolio(tickers, base_config)

        assert isinstance(result, AnalysisResult)
        assert len(result.tickers) == 2
        assert all(isinstance(r, TickerResult) for r in result.tickers)
        assert result.tickers[0].ticker == "AAPL"
        assert result.tickers[1].ticker == "MSFT"

    @pytest.mark.unit
    def test_analyzer_cleanup(self):
        """Test analyzer cleanup functionality."""

        def mock_log(msg, level="info"):
            pass

        analyzer = MACrossAnalyzer(log=mock_log)

        # Test that cleanup works without error
        analyzer.close()

        # Should be able to call close multiple times
        analyzer.close()

    @pytest.mark.unit
    def test_config_to_dict_behavior(self):
        """Test configuration dictionary conversion."""
        config = AnalysisConfig(
            ticker="AAPL",
            strategy_type="SMA",
            fast_period=20,
            slow_period=50,
            direction="Long",
        )

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["TICKER"] == "AAPL"
        assert config_dict["STRATEGY_TYPE"] == "SMA"
        assert config_dict["FAST_PERIOD"] == 20
        assert config_dict["SLOW_PERIOD"] == 50
        assert config_dict["DIRECTION"] == "Long"


class TestScannerAdapter:
    """Test scanner adapter for CLI compatibility."""

    @pytest.mark.unit
    @pytest.mark.smoke
    def test_adapter_initialization(self):
        """Test adapter initialization."""
        adapter = ScannerAdapter()
        assert adapter is not None

    @pytest.mark.unit
    def test_json_to_config_conversion(self):
        """Test JSON portfolio to config conversion."""
        json_portfolio = {
            "name": "AAPL_D_SMA",
            "symbols": ["AAPL"],
            "timeframes": ["D"],
            "ma_types": ["SMA"],
            "fast_periods": [20],
            "slow_periods": [50],
            "allocations": {"AAPL": 1.0},
        }

        adapter = ScannerAdapter()
        config = adapter._json_to_config(json_portfolio)

        assert isinstance(config, AnalysisConfig)
        assert config.ticker == "AAPL"  # Should convert to single ticker
        assert config.use_sma is True
        assert config.fast_period == 20
        assert config.slow_period == 50

    @pytest.mark.unit
    @patch("app.tools.download_data.download_data")
    def test_scan_portfolio(self, mock_download, sample_price_data):
        """Test portfolio scanning."""
        mock_download.return_value = sample_price_data

        json_portfolio = {
            "name": "TEST_PORTFOLIO",
            "symbols": ["AAPL", "MSFT"],
            "timeframes": ["D"],
            "ma_types": ["SMA"],
            "fast_periods": [20],
            "slow_periods": [50],
            "allocations": {"AAPL": 0.5, "MSFT": 0.5},
        }

        adapter = ScannerAdapter()
        results = adapter.scan_portfolio(json_portfolio)

        assert isinstance(results, list)
        assert len(results) == 2
        assert all("symbol" in r for r in results)
        assert all("total_return" in r for r in results)

    @pytest.mark.unit
    def test_timeframe_conversion(self):
        """Test timeframe conversion."""
        adapter = ScannerAdapter()

        assert adapter._convert_timeframe("D") == "1d"
        assert adapter._convert_timeframe("H") == "1h"
        assert adapter._convert_timeframe("W") == "1wk"
        assert adapter._convert_timeframe("M") == "1mo"

        with pytest.raises(ValueError):
            adapter._convert_timeframe("X")  # Invalid timeframe

    @pytest.mark.unit
    def test_result_formatting(self):
        """Test result formatting for CLI output."""
        portfolio_result = TickerResult(
            ticker="AAPL",
            strategy_type="SMA",
            fast_period=20,
            slow_period=50,
            total_trades=10,
            total_return_pct=25.0,
            sharpe_ratio=1.5,
            max_drawdown_pct=-15.0,
            win_rate_pct=60.0,
            profit_factor=2.0,
            expectancy_per_trade=0.03,
            sortino_ratio=1.2,
            beats_bnh_pct=15.0,
        )

        adapter = ScannerAdapter()
        formatted = adapter._format_result(portfolio_result)

        assert isinstance(formatted, dict)
        assert formatted["ticker"] == "AAPL"
        assert formatted["total_return_pct"] == 25.0
        assert formatted["sharpe_ratio"] == 1.5
        assert "strategy_type" in formatted


class TestSignalInfo:
    """Test signal info model."""

    @pytest.mark.unit
    def test_signal_creation(self):
        """Test signal creation."""
        signal = SignalInfo(
            date="2023-01-01",
            signal_entry=True,
            signal_exit=False,
            current_position=1,
            price=100.0,
        )

        assert signal.signal_entry is True
        assert signal.signal_exit is False
        assert signal.current_position == 1
        assert signal.price == 100.0

    @pytest.mark.unit
    def test_signal_validation(self):
        """Test signal validation."""
        # Test valid signal creation
        signal = SignalInfo(
            date="2023-01-01",
            signal_entry=False,
            signal_exit=True,
            current_position=0,
            price=99.50,
        )

        assert signal.date == "2023-01-01"
        assert signal.signal_entry is False
        assert signal.signal_exit is True
        assert signal.current_position == 0
        assert signal.price == 99.50

        # Test with different position values
        long_signal = SignalInfo(
            date="2023-01-02",
            signal_entry=True,
            signal_exit=False,
            current_position=1,
            price=101.25,
        )

        assert long_signal.current_position == 1  # Long position
