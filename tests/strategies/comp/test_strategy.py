"""
Unit tests for COMP strategy execution.

Tests score calculation, strategy execution, ticker processing,
and CSV export functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import polars as pl
import pytest

from app.strategies.comp.strategy import (
    calculate_comp_score,
    export_compound_results,
    get_strategies_csv_path,
    process_ticker,
    run,
)


class TestCalculateCompScore:
    """Test cases for COMP score calculation."""

    def test_calculate_comp_score_high_trades(self):
        """Test score calculation with high trade count (40+)."""
        log_func = Mock()
        
        stats = {
            'Win Rate [%]': 60.0,
            'Total Trades': 50,
            'Sortino Ratio': 1.5,
            'Profit Factor': 2.0,
            'Expectancy per Trade': 0.05,
            'Beats BNH [%]': 20.0,
        }

        score = calculate_comp_score(stats, log_func)

        # Should have full confidence multiplier (1.0)
        assert score > 0
        assert isinstance(score, float)

    def test_calculate_comp_score_medium_trades(self):
        """Test score calculation with medium trade count (20-40)."""
        log_func = Mock()
        
        stats = {
            'Win Rate [%]': 55.0,
            'Total Trades': 30,
            'Sortino Ratio': 1.2,
            'Profit Factor': 1.8,
            'Expectancy per Trade': 0.03,
            'Beats BNH [%]': 15.0,
        }

        score = calculate_comp_score(stats, log_func)

        # Should have partial confidence multiplier (0.5-1.0)
        assert score > 0
        assert isinstance(score, float)

    def test_calculate_comp_score_low_trades(self):
        """Test score calculation with low trade count (<20)."""
        log_func = Mock()
        
        stats = {
            'Win Rate [%]': 70.0,
            'Total Trades': 10,
            'Sortino Ratio': 2.0,
            'Profit Factor': 3.0,
            'Expectancy per Trade': 0.08,
            'Beats BNH [%]': 30.0,
        }

        score = calculate_comp_score(stats, log_func)

        # Should have heavy penalty (confidence < 0.5)
        assert score > 0
        assert isinstance(score, float)

    def test_calculate_comp_score_fallback(self):
        """Test that score with missing metrics still calculates (defaults to 0)."""
        log_func = Mock()
        
        # Missing required metrics (will use defaults of 0)
        stats = {
            'Sortino Ratio': 1.5,
        }

        score = calculate_comp_score(stats, log_func)

        # Should still calculate a score (likely very low due to missing metrics)
        assert isinstance(score, float)
        assert score >= 0


class TestGetStrategiesCSVPath:
    """Test cases for CSV path resolution."""

    def test_get_strategies_csv_path_default(self):
        """Test default CSV path construction."""
        config = {
            'BASE_DIR': '/project/root',
        }

        path = get_strategies_csv_path('BTC-USD', config)

        assert isinstance(path, Path)
        assert str(path) == '/project/root/data/raw/strategies/BTC-USD.csv'

    def test_get_strategies_csv_path_custom(self):
        """Test custom CSV path from config."""
        config = {
            'COMP_STRATEGIES_CSV': '/custom/path/strategies.csv',
        }

        path = get_strategies_csv_path('AAPL', config)

        assert isinstance(path, Path)
        assert str(path) == '/custom/path/strategies.csv'


class TestExportCompoundResults:
    """Test cases for exporting results to CSV."""

    def test_export_compound_results_success(self):
        """Test successful CSV export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'BASE_DIR': tmpdir,
            }
            
            stats = {
                'Ticker': 'BTC-USD',
                'Strategy Type': 'COMP',
                'Total Return [%]': 100.0,
                'Sharpe Ratio': 1.5,
                'Win Rate [%]': 60.0,
                'Total Trades': 50,
                'Score': 1.2,
            }
            
            log_func = Mock()

            result = export_compound_results('BTC-USD', stats, config, log_func)

            assert result is True
            
            # Verify file was created
            output_file = Path(tmpdir) / 'data' / 'outputs' / 'compound' / 'BTC-USD.csv'
            assert output_file.exists()
            
            # Verify contents
            import pandas as pd
            df = pd.read_csv(output_file)
            assert len(df) == 1
            assert df['Ticker'][0] == 'BTC-USD'
            assert df['Score'][0] == 1.2

    def test_export_compound_results_creates_directory(self):
        """Test that export creates output directory if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'BASE_DIR': tmpdir,
            }
            
            stats = {
                'Ticker': 'ETH-USD',
                'Score': 1.0,
            }
            
            log_func = Mock()

            # Directory doesn't exist yet
            output_dir = Path(tmpdir) / 'data' / 'outputs' / 'compound'
            assert not output_dir.exists()

            result = export_compound_results('ETH-USD', stats, config, log_func)

            assert result is True
            assert output_dir.exists()


class TestProcessTicker:
    """Test cases for processing individual tickers."""

    @pytest.fixture
    def mock_dependencies(self):
        """Set up common mocks for ticker processing."""
        with patch('app.strategies.comp.strategy.get_data') as mock_data, \
             patch('app.strategies.comp.strategy.calculate_compound_strategy') as mock_calc, \
             patch('app.strategies.comp.strategy.backtest_strategy') as mock_backtest, \
             patch('app.strategies.comp.strategy.export_compound_results') as mock_export:
            
            # Mock price data
            mock_data.return_value = pl.DataFrame({
                'Date': ['2024-01-01', '2024-01-02'],
                'Close': [100.0, 101.0],
            })
            
            # Mock calculated signals
            mock_calc.return_value = pl.DataFrame({
                'Date': ['2024-01-01', '2024-01-02'],
                'Signal': [0, 1],
                'Position': [0, 0],
            })
            
            # Mock backtest results
            mock_portfolio = Mock()
            mock_portfolio.stats.return_value = {
                'Win Rate [%]': 50.0,
                'Total Trades': 25,
                'Sortino Ratio': 1.0,
                'Profit Factor': 1.5,
                'Expectancy per Trade': 0.02,
                'Beats BNH [%]': 10.0,
                'Total Open Trades': 0,
            }
            mock_backtest.return_value = mock_portfolio
            
            mock_export.return_value = True
            
            yield {
                'data': mock_data,
                'calc': mock_calc,
                'backtest': mock_backtest,
                'export': mock_export,
            }

    def test_process_ticker_success(self, mock_dependencies):
        """Test successful ticker processing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Ticker,Strategy Type,Fast Period,Slow Period\n")
            f.write("BTC-USD,SMA,10,20\n")
            csv_path = f.name

        try:
            config = {
                'BASE_DIR': Path(csv_path).parent,
                'COMP_STRATEGIES_CSV': csv_path,
            }
            log_func = Mock()

            result = process_ticker('BTC-USD', config, log_func)

            assert result is True
            mock_dependencies['data'].assert_called_once()
            mock_dependencies['calc'].assert_called_once()
            mock_dependencies['backtest'].assert_called_once()
            mock_dependencies['export'].assert_called_once()
        finally:
            Path(csv_path).unlink()

    def test_process_ticker_missing_csv(self):
        """Test error when component CSV is missing."""
        config = {
            'BASE_DIR': '/tmp',
        }
        log_func = Mock()

        result = process_ticker('NONEXISTENT', config, log_func)

        assert result is False
        # Should log error about missing CSV (check that error was logged)
        error_calls = [call for call in log_func.call_args_list if len(call[0]) > 1 and call[0][1] == 'error']
        assert len(error_calls) > 0
        assert 'Component strategies CSV not found' in str(error_calls[0])

    def test_process_ticker_no_data(self, mock_dependencies):
        """Test error when price data unavailable."""
        # Mock get_data to return None
        mock_dependencies['data'].return_value = None

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Ticker,Strategy Type,Fast Period,Slow Period\n")
            f.write("AAPL,SMA,10,20\n")
            csv_path = f.name

        try:
            config = {
                'COMP_STRATEGIES_CSV': csv_path,
            }
            log_func = Mock()

            result = process_ticker('AAPL', config, log_func)

            assert result is False
        finally:
            Path(csv_path).unlink()

    def test_process_ticker_no_signals(self, mock_dependencies):
        """Test that processing continues with warning when no signals."""
        # Mock calculate_compound_strategy to return data with no signals
        mock_dependencies['calc'].return_value = pl.DataFrame({
            'Date': ['2024-01-01', '2024-01-02'],
            'Signal': [0, 0],
            'Position': [0, 0],
        })

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Ticker,Strategy Type,Fast Period,Slow Period\n")
            f.write("BTC-USD,SMA,10,20\n")
            csv_path = f.name

        try:
            config = {
                'COMP_STRATEGIES_CSV': csv_path,
            }
            log_func = Mock()

            result = process_ticker('BTC-USD', config, log_func)

            # Should continue and succeed despite no signals
            assert result is True
        finally:
            Path(csv_path).unlink()


class TestRun:
    """Test cases for main run function."""

    def test_run_success_single_ticker(self):
        """Test successful run for single ticker."""
        with patch('app.strategies.comp.strategy.process_ticker') as mock_process:
            mock_process.return_value = True

            config = {
                'TICKER': ['BTC-USD'],
                'BASE_DIR': '/tmp',
            }

            result = run(config)

            assert result is True
            # Verify process_ticker was called once with the right parameters
            assert mock_process.call_count == 1
            call_args = mock_process.call_args[0]
            assert call_args[0] == 'BTC-USD'
            assert call_args[1] == config
            # Third argument is a logging function, check it's callable
            assert callable(call_args[2])
            # Fourth argument is progress_update_fn (None in this case)
            assert call_args[3] is None

    def test_run_success_multiple_tickers(self):
        """Test successful run for multiple tickers."""
        with patch('app.strategies.comp.strategy.process_ticker') as mock_process:
            mock_process.return_value = True

            config = {
                'TICKER': ['BTC-USD', 'ETH-USD', 'SOL-USD'],
                'BASE_DIR': '/tmp',
            }

            result = run(config)

            assert result is True
            assert mock_process.call_count == 3

    def test_run_failure_no_ticker(self):
        """Test error when no ticker in config."""
        config = {
            'BASE_DIR': '/tmp',
        }

        result = run(config)

        assert result is False

    def test_run_handles_string_ticker(self):
        """Test that string ticker is converted to list."""
        with patch('app.strategies.comp.strategy.process_ticker') as mock_process:
            mock_process.return_value = True

            config = {
                'TICKER': 'BTC-USD',  # String instead of list
                'BASE_DIR': '/tmp',
            }

            result = run(config)

            assert result is True
            mock_process.assert_called_once()


class TestCompStrategyIntegration:
    """Integration tests for COMP strategy components."""

    def test_score_calculation_realistic(self):
        """Test score calculation with realistic values."""
        log_func = Mock()
        
        # Realistic backtest results
        stats = {
            'Win Rate [%]': 37.74,
            'Total Trades': 53,
            'Sortino Ratio': 1.24,
            'Profit Factor': 7.2,
            'Expectancy per Trade': 0.47,
            'Beats BNH [%]': 234.0,
        }

        score = calculate_comp_score(stats, log_func)

        # Should produce reasonable score
        assert 0 < score < 5
        assert isinstance(score, float)

    def test_export_preserves_all_metrics(self):
        """Test that export preserves all backtest metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {'BASE_DIR': tmpdir}
            
            stats = {
                'Ticker': 'BTC-USD',
                'Strategy Type': 'COMP',
                'Fast Period': 'N/A',
                'Slow Period': 'N/A',
                'Signal Period': 'N/A',
                'Total Return [%]': 25112.96,
                'Win Rate [%]': 37.74,
                'Total Trades': 53,
                'Sharpe Ratio': 1.24,
                'Sortino Ratio': 1.24,
                'Profit Factor': 7.2,
                'Score': 1.2297,
            }
            
            log_func = Mock()

            export_compound_results('BTC-USD', stats, config, log_func)

            output_file = Path(tmpdir) / 'data' / 'outputs' / 'compound' / 'BTC-USD.csv'
            
            import pandas as pd
            df = pd.read_csv(output_file)
            
            # Verify all metrics are preserved
            assert df['Total Return [%]'][0] == 25112.96
            assert df['Win Rate [%]'][0] == 37.74
            assert df['Score'][0] == 1.2297

