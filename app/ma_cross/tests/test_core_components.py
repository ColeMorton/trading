"""
Unit tests for MA Cross core components.
"""

import pytest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.ma_cross.core.analyzer import MACrossAnalyzer
from app.ma_cross.core.models import (
    MACrossConfig,
    MACrossResult,
    PortfolioResult,
    TradingSignal
)
from app.ma_cross.core.scanner_adapter import ScannerAdapter


@pytest.fixture
def sample_config():
    """Create sample MA Cross configuration."""
    return MACrossConfig(
        tickers=["AAPL", "MSFT"],
        start_date="2023-01-01",
        end_date="2023-12-31",
        interval="1d",
        ma_type="SMA",
        fast_period=20,
        slow_period=50,
        initial_capital=100000,
        max_allocation=0.3
    )


@pytest.fixture
def sample_price_data():
    """Create sample price data."""
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
    np.random.seed(42)
    
    # Generate realistic price data
    base_price = 100
    returns = np.random.normal(0.0005, 0.02, len(dates))
    prices = base_price * np.exp(np.cumsum(returns))
    
    return pd.DataFrame({
        'Date': dates,
        'Open': prices * 0.98,
        'High': prices * 1.02,
        'Low': prices * 0.97,
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, len(dates))
    }).set_index('Date')


class TestMACrossConfig:
    """Test MA Cross configuration model."""
    
    def test_config_creation(self, sample_config):
        """Test configuration creation."""
        assert sample_config.tickers == ["AAPL", "MSFT"]
        assert sample_config.start_date == "2023-01-01"
        assert sample_config.end_date == "2023-12-31"
        assert sample_config.ma_type == "SMA"
        assert sample_config.fast_period == 20
        assert sample_config.slow_period == 50
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid MA periods
        with pytest.raises(ValueError):
            MACrossConfig(
                tickers=["AAPL"],
                start_date="2023-01-01",
                end_date="2023-12-31",
                fast_period=50,
                slow_period=20  # Slow < Fast should fail
            )
        
        # Test invalid dates
        with pytest.raises(ValueError):
            MACrossConfig(
                tickers=["AAPL"],
                start_date="2023-12-31",
                end_date="2023-01-01"  # End < Start should fail
            )
        
        # Test empty tickers
        with pytest.raises(ValueError):
            MACrossConfig(
                tickers=[],
                start_date="2023-01-01",
                end_date="2023-12-31"
            )
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = MACrossConfig(
            tickers=["AAPL"],
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        assert config.interval == "1d"
        assert config.ma_type == "SMA"
        assert config.fast_period == 20
        assert config.slow_period == 50
        assert config.initial_capital == 100000
        assert config.max_allocation == 1.0


class TestMACrossAnalyzer:
    """Test MA Cross analyzer functionality."""
    
    def test_analyzer_initialization(self, sample_config):
        """Test analyzer initialization."""
        analyzer = MACrossAnalyzer(sample_config)
        
        assert analyzer.config == sample_config
        assert analyzer._data_cache == {}
    
    @patch('yfinance.download')
    def test_fetch_data(self, mock_download, sample_config, sample_price_data):
        """Test data fetching."""
        mock_download.return_value = sample_price_data
        
        analyzer = MACrossAnalyzer(sample_config)
        data = analyzer._fetch_data("AAPL")
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) == len(sample_price_data)
        assert all(col in data.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])
        
        mock_download.assert_called_once()
    
    def test_calculate_sma(self, sample_price_data):
        """Test SMA calculation."""
        analyzer = MACrossAnalyzer(Mock())
        
        sma_20 = analyzer._calculate_ma(sample_price_data['Close'], 20, 'SMA')
        sma_50 = analyzer._calculate_ma(sample_price_data['Close'], 50, 'SMA')
        
        assert isinstance(sma_20, pd.Series)
        assert isinstance(sma_50, pd.Series)
        assert len(sma_20) == len(sample_price_data)
        assert len(sma_50) == len(sample_price_data)
        assert sma_20.isna().sum() == 19  # First 19 values should be NaN
        assert sma_50.isna().sum() == 49  # First 49 values should be NaN
    
    def test_calculate_ema(self, sample_price_data):
        """Test EMA calculation."""
        analyzer = MACrossAnalyzer(Mock())
        
        ema_12 = analyzer._calculate_ma(sample_price_data['Close'], 12, 'EMA')
        ema_26 = analyzer._calculate_ma(sample_price_data['Close'], 26, 'EMA')
        
        assert isinstance(ema_12, pd.Series)
        assert isinstance(ema_26, pd.Series)
        assert len(ema_12) == len(sample_price_data)
        assert len(ema_26) == len(sample_price_data)
        # EMA should have fewer NaN values than SMA
        assert ema_12.isna().sum() < 12
        assert ema_26.isna().sum() < 26
    
    def test_generate_signals(self, sample_price_data):
        """Test signal generation."""
        analyzer = MACrossAnalyzer(Mock())
        
        # Create synthetic MA data
        fast_ma = pd.Series([90, 95, 100, 105, 110], index=sample_price_data.index[:5])
        slow_ma = pd.Series([100, 98, 96, 94, 92], index=sample_price_data.index[:5])
        
        signals = analyzer._generate_signals(fast_ma, slow_ma)
        
        assert isinstance(signals, pd.Series)
        assert all(signals.isin([0, 1, -1]))
        # Should have buy signal when fast crosses above slow
        assert 1 in signals.values
    
    def test_calculate_metrics(self):
        """Test metrics calculation."""
        analyzer = MACrossAnalyzer(Mock())
        
        # Create sample portfolio data
        returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        equity_curve = pd.Series([100000, 101000, 99000, 102000, 101000, 103000])
        
        metrics = analyzer._calculate_metrics(returns, equity_curve, num_trades=5)
        
        assert 'total_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'win_rate' in metrics
        assert metrics['num_trades'] == 5
        assert isinstance(metrics['total_return'], float)
        assert isinstance(metrics['sharpe_ratio'], float)
        assert metrics['max_drawdown'] < 0  # Drawdown should be negative
    
    @patch('yfinance.download')
    def test_analyze_single_ticker(self, mock_download, sample_config, sample_price_data):
        """Test analysis of single ticker."""
        mock_download.return_value = sample_price_data
        
        analyzer = MACrossAnalyzer(sample_config)
        result = analyzer._analyze_ticker("AAPL")
        
        assert isinstance(result, PortfolioResult)
        assert result.symbol == "AAPL"
        assert result.timeframe == "D"
        assert result.ma_type == "SMA"
        assert result.fast_period == 20
        assert result.slow_period == 50
        assert result.num_trades >= 0
        assert -1 <= result.total_return <= 10  # Reasonable return range
        assert result.max_drawdown <= 0
    
    @patch('yfinance.download')
    def test_analyze_multiple_tickers(self, mock_download, sample_config, sample_price_data):
        """Test analysis of multiple tickers."""
        mock_download.return_value = sample_price_data
        
        analyzer = MACrossAnalyzer(sample_config)
        result = analyzer.analyze()
        
        assert isinstance(result, MACrossResult)
        assert len(result.portfolios) == 2  # AAPL and MSFT
        assert all(isinstance(p, PortfolioResult) for p in result.portfolios)
        assert result.portfolios[0].symbol == "AAPL"
        assert result.portfolios[1].symbol == "MSFT"
    
    def test_progress_callback(self, sample_config):
        """Test progress callback functionality."""
        analyzer = MACrossAnalyzer(sample_config)
        
        progress_updates = []
        def progress_callback(progress, message):
            progress_updates.append((progress, message))
        
        with patch.object(analyzer, '_fetch_data', return_value=pd.DataFrame()):
            with patch.object(analyzer, '_analyze_ticker', return_value=Mock()):
                analyzer.analyze(progress_callback=progress_callback)
        
        assert len(progress_updates) > 0
        assert progress_updates[0][0] == 0  # First update at 0%
        assert progress_updates[-1][0] == 100  # Last update at 100%
        assert all(0 <= p[0] <= 100 for p in progress_updates)


class TestScannerAdapter:
    """Test scanner adapter for CLI compatibility."""
    
    def test_adapter_initialization(self):
        """Test adapter initialization."""
        adapter = ScannerAdapter()
        assert adapter is not None
    
    def test_json_to_config_conversion(self):
        """Test JSON portfolio to config conversion."""
        json_portfolio = {
            "name": "AAPL_D_SMA",
            "symbols": ["AAPL"],
            "timeframes": ["D"],
            "ma_types": ["SMA"],
            "fast_periods": [20],
            "slow_periods": [50],
            "allocations": {"AAPL": 1.0}
        }
        
        adapter = ScannerAdapter()
        config = adapter._json_to_config(json_portfolio)
        
        assert isinstance(config, MACrossConfig)
        assert config.tickers == ["AAPL"]
        assert config.interval == "1d"
        assert config.ma_type == "SMA"
        assert config.fast_period == 20
        assert config.slow_period == 50
    
    @patch('yfinance.download')
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
            "allocations": {"AAPL": 0.5, "MSFT": 0.5}
        }
        
        adapter = ScannerAdapter()
        results = adapter.scan_portfolio(json_portfolio)
        
        assert isinstance(results, list)
        assert len(results) == 2
        assert all('symbol' in r for r in results)
        assert all('total_return' in r for r in results)
    
    def test_timeframe_conversion(self):
        """Test timeframe conversion."""
        adapter = ScannerAdapter()
        
        assert adapter._convert_timeframe("D") == "1d"
        assert adapter._convert_timeframe("H") == "1h"
        assert adapter._convert_timeframe("W") == "1wk"
        assert adapter._convert_timeframe("M") == "1mo"
        
        with pytest.raises(ValueError):
            adapter._convert_timeframe("X")  # Invalid timeframe
    
    def test_result_formatting(self):
        """Test result formatting for CLI output."""
        portfolio_result = PortfolioResult(
            symbol="AAPL",
            timeframe="D",
            ma_type="SMA",
            fast_period=20,
            slow_period=50,
            initial_capital=100000,
            allocation=1.0,
            num_trades=10,
            total_return=0.25,
            sharpe_ratio=1.5,
            max_drawdown=-0.15,
            win_rate=0.6,
            avg_gain=0.05,
            avg_loss=-0.02,
            expectancy=0.03,
            final_balance=125000,
            roi=0.25
        )
        
        adapter = ScannerAdapter()
        formatted = adapter._format_result(portfolio_result)
        
        assert isinstance(formatted, dict)
        assert formatted['symbol'] == "AAPL"
        assert formatted['total_return'] == 0.25
        assert formatted['sharpe_ratio'] == 1.5
        assert 'timestamp' in formatted


class TestTradingSignal:
    """Test trading signal model."""
    
    def test_signal_creation(self):
        """Test signal creation."""
        signal = TradingSignal(
            timestamp=datetime.now(),
            signal_type="BUY",
            price=100.0,
            quantity=10,
            reason="MA crossover"
        )
        
        assert signal.signal_type == "BUY"
        assert signal.price == 100.0
        assert signal.quantity == 10
        assert signal.reason == "MA crossover"
    
    def test_signal_validation(self):
        """Test signal validation."""
        # Invalid signal type
        with pytest.raises(ValueError):
            TradingSignal(
                timestamp=datetime.now(),
                signal_type="INVALID",
                price=100.0,
                quantity=10
            )
        
        # Negative price
        with pytest.raises(ValueError):
            TradingSignal(
                timestamp=datetime.now(),
                signal_type="BUY",
                price=-100.0,
                quantity=10
            )
        
        # Zero quantity
        with pytest.raises(ValueError):
            TradingSignal(
                timestamp=datetime.now(),
                signal_type="BUY",
                price=100.0,
                quantity=0
            )