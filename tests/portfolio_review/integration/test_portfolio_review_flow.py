"""
Integration tests for complete portfolio review workflows.

This module tests end-to-end functionality including strategy processing,
file operations, and complete execution flows.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open

from app.portfolio_review.review import run, CONFIG_OP, process_strategy


class TestPortfolioReviewFlowIntegration:
    """Test complete portfolio review execution flows."""

    def test_complete_sma_strategy_workflow(self):
        """Test complete workflow for SMA strategy execution."""
        mock_config = {
            "TICKER": "TEST-USD",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp"
        }
        
        mock_data = MagicMock()
        mock_portfolio = MagicMock()
        mock_portfolio.stats.return_value = {"total_return": 0.15}
        mock_portfolio.value.return_value = MagicMock()
        mock_portfolio.value.return_value.__getitem__ = MagicMock(return_value=1000)
        mock_portfolio.value.return_value.index = ["2023-01-01", "2023-01-02"]
        mock_portfolio.value.return_value.values = [1000, 1050]
        
        with patch('app.portfolio_review.review.setup_logging') as mock_logging, \
             patch('app.portfolio_review.review.get_config') as mock_get_config, \
             patch('app.portfolio_review.review.get_data') as mock_get_data, \
             patch('app.portfolio_review.review.calculate_ma_and_signals') as mock_calc_ma, \
             patch('app.portfolio_review.review.backtest_strategy') as mock_backtest, \
             patch('app.portfolio_review.review.os.makedirs') as mock_makedirs, \
             patch('app.portfolio_review.review.pl.DataFrame') as mock_df_class, \
             patch('app.tools.plotting.create_portfolio_plot_files') as mock_plot:
            
            # Setup mocks
            mock_log = MagicMock()
            mock_logging.return_value = (mock_log, MagicMock(), None, None)
            mock_get_config.return_value = mock_config
            mock_get_data.return_value = mock_data
            mock_calc_ma.return_value = mock_data
            mock_backtest.return_value = mock_portfolio
            
            mock_df = MagicMock()
            mock_df.write_csv = MagicMock()
            mock_df_class.return_value = mock_df
            
            mock_plot.return_value = ["plot1.png", "plot2.png"]
            
            # Execute SMA strategy workflow
            result = run(
                config_dict=mock_config,
                timeframe="daily",
                strategy_type="SMA",
                signal_period=9
            )
            
            # Verify complete workflow execution
            assert result == True
            
            # Verify function call sequence
            mock_get_config.assert_called_once()
            mock_get_data.assert_called_once_with(mock_config["TICKER"], mock_config, mock_log)
            mock_calc_ma.assert_called_once()
            mock_backtest.assert_called_once()
            
            # Verify SMA strategy path was taken (not MACD)
            enhanced_config = mock_get_config.call_args[0][0]
            assert enhanced_config["STRATEGY_TYPE"] == "SMA"
            assert enhanced_config["USE_SMA"] == True
            
            # Verify file operations
            mock_makedirs.assert_called_once()
            mock_df.write_csv.assert_called_once()
            mock_plot.assert_called_once()

    def test_complete_macd_strategy_workflow(self):
        """Test complete workflow for MACD strategy execution."""
        mock_config = {
            "TICKER": "MACD-USD",
            "FAST_PERIOD": 12,
            "SLOW_PERIOD": 26,
            "BASE_DIR": "/tmp"
        }
        
        mock_data = MagicMock()
        mock_portfolio = MagicMock()
        mock_portfolio.stats.return_value = {"total_return": 0.25}
        mock_portfolio.value.return_value = MagicMock()
        mock_portfolio.value.return_value.__getitem__ = MagicMock(return_value=1000)
        mock_portfolio.value.return_value.index = ["2023-01-01", "2023-01-02"]
        mock_portfolio.value.return_value.values = [1000, 1100]
        
        with patch('app.portfolio_review.review.setup_logging') as mock_logging, \
             patch('app.portfolio_review.review.get_config') as mock_get_config, \
             patch('app.portfolio_review.review.get_data') as mock_get_data, \
             patch('app.portfolio_review.review.calculate_macd_and_signals') as mock_calc_macd, \
             patch('app.portfolio_review.review.backtest_strategy') as mock_backtest, \
             patch('app.portfolio_review.review.os.makedirs') as mock_makedirs, \
             patch('app.portfolio_review.review.pl.DataFrame') as mock_df_class, \
             patch('app.tools.plotting.create_portfolio_plot_files') as mock_plot:
            
            # Setup mocks
            mock_log = MagicMock()
            mock_logging.return_value = (mock_log, MagicMock(), None, None)
            mock_get_config.return_value = mock_config
            mock_get_data.return_value = mock_data
            mock_calc_macd.return_value = mock_data
            mock_backtest.return_value = mock_portfolio
            
            mock_df = MagicMock()
            mock_df.write_csv = MagicMock()
            mock_df_class.return_value = mock_df
            
            mock_plot.return_value = ["macd_plot.png"]
            
            # Execute MACD strategy workflow with custom signal period
            result = run(
                config_dict=mock_config,
                timeframe="4hour",
                strategy_type="MACD", 
                signal_period=14
            )
            
            # Verify complete workflow execution
            assert result == True
            
            # Verify MACD-specific function calls
            mock_calc_macd.assert_called_once()
            call_args = mock_calc_macd.call_args[0]
            assert call_args[0] == mock_data  # data
            assert call_args[1] == mock_config["FAST_PERIOD"]  # fast_period
            assert call_args[2] == mock_config["SLOW_PERIOD"]  # slow_period
            assert call_args[3] == 14  # signal_period (custom)
            assert call_args[4] == mock_config  # config
            assert call_args[5] == mock_log  # log
            
            # Verify MACD strategy configuration
            enhanced_config = mock_get_config.call_args[0][0]
            assert enhanced_config["STRATEGY_TYPE"] == "MACD"
            assert enhanced_config["USE_SMA"] == False
            assert enhanced_config["SIGNAL_PERIOD"] == 14
            assert enhanced_config["USE_4HOUR"] == True

    def test_portfolio_file_processing_workflow(self):
        """Test complete workflow for portfolio JSON file processing."""
        mock_portfolio_data = [
            {
                "ticker": "STOCK1",
                "timeframe": "hourly",
                "fast_period": 5,
                "slow_period": 15,
                "direction": "Long",
                "type": "SMA",
                "signal_period": 9
            },
            {
                "ticker": "STOCK2",
                "timeframe": "daily",
                "fast_period": 12,
                "slow_period": 26,
                "direction": "Long",
                "type": "MACD",
                "signal_period": 9
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_portfolio_data, f)
            temp_file_path = f.name
        
        try:
            mock_portfolio = MagicMock()
            mock_portfolio.stats.return_value = {}
            
            with patch('app.portfolio_review.review.setup_logging') as mock_logging, \
                 patch('app.portfolio_review.review.process_strategy') as mock_process_strategy:
                
                # Setup mocks
                mock_log = MagicMock()
                mock_logging.return_value = (mock_log, MagicMock(), None, None)
                mock_process_strategy.return_value = mock_portfolio
                
                # Execute portfolio file workflow
                result = run(portfolio_file=temp_file_path)
                
                # Verify portfolio file processing
                assert result == True
                
                # Verify process_strategy was called for each strategy
                assert mock_process_strategy.call_count == 2
                
                # Verify configurations for each strategy
                call_configs = [call[0][0] for call in mock_process_strategy.call_args_list]
                
                # First strategy (SMA, hourly)
                config1 = call_configs[0]
                assert config1["TICKER"] == "STOCK1"
                assert config1["USE_HOURLY"] == True
                assert config1["FAST_PERIOD"] == 5
                assert config1["SLOW_PERIOD"] == 15
                assert config1["USE_SMA"] == True
                assert config1["STRATEGY_TYPE"] == "SMA"
                
                # Second strategy (MACD, daily)
                config2 = call_configs[1]
                assert config2["TICKER"] == "STOCK2"
                assert config2["USE_HOURLY"] == False
                assert config2["FAST_PERIOD"] == 12
                assert config2["SLOW_PERIOD"] == 26
                assert config2["USE_SMA"] == False
                assert config2["STRATEGY_TYPE"] == "MACD"
                
        finally:
            os.unlink(temp_file_path)

    def test_updated_config_dictionaries_integration(self):
        """Test that updated config dictionaries work correctly."""
        with patch('app.portfolio_review.review.setup_logging') as mock_logging, \
             patch('app.portfolio_review.review.get_config') as mock_get_config, \
             patch('app.portfolio_review.review.get_data') as mock_get_data, \
             patch('app.portfolio_review.review.calculate_ma_and_signals') as mock_calc_ma, \
             patch('app.portfolio_review.review.backtest_strategy') as mock_backtest, \
             patch('app.portfolio_review.review.os.makedirs'), \
             patch('app.portfolio_review.review.pl.DataFrame') as mock_df_class, \
             patch('app.portfolio_review.review.create_portfolio_plot_files'):
            
            # Setup mocks
            mock_log = MagicMock()
            mock_logging.return_value = (mock_log, MagicMock(), None, None)
            mock_get_config.return_value = CONFIG_OP.copy()
            mock_get_data.return_value = MagicMock()
            mock_calc_ma.return_value = MagicMock()
            
            mock_portfolio = MagicMock()
            mock_portfolio.stats.return_value = {}
            mock_portfolio.value.return_value = MagicMock()
            mock_portfolio.value.return_value.__getitem__ = MagicMock(return_value=1000)
            mock_portfolio.value.return_value.index = []
            mock_portfolio.value.return_value.values = []
            mock_backtest.return_value = mock_portfolio
            
            mock_df = MagicMock()
            mock_df.write_csv = MagicMock()
            mock_df_class.return_value = mock_df
            
            # Test with updated CONFIG_OP (should have new parameter format)
            result = run(config_dict=CONFIG_OP)
            
            # Verify execution succeeded
            assert result == True
            
            # Verify enhanced config contains both new and legacy parameters
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]
            
            # Should have original CONFIG_OP parameters
            assert enhanced_config["TICKER"] == CONFIG_OP["TICKER"]
            assert enhanced_config["FAST_PERIOD"] == CONFIG_OP["FAST_PERIOD"]
            assert enhanced_config["SLOW_PERIOD"] == CONFIG_OP["SLOW_PERIOD"]
            
            # Should have converted parameters based on CONFIG_OP values
            assert enhanced_config["STRATEGY_TYPE"] == CONFIG_OP["STRATEGY_TYPE"]
            assert enhanced_config["SIGNAL_PERIOD"] == CONFIG_OP["SIGNAL_PERIOD"]
            assert enhanced_config["USE_SMA"] == (CONFIG_OP["STRATEGY_TYPE"] == "SMA")

    def test_error_handling_in_strategy_processing(self):
        """Test error handling during strategy processing."""
        mock_config = {
            "TICKER": "ERROR-TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp"
        }
        
        with patch('app.portfolio_review.review.setup_logging') as mock_logging, \
             patch('app.portfolio_review.review.get_config') as mock_get_config, \
             patch('app.portfolio_review.review.get_data') as mock_get_data:
            
            # Setup mocks
            mock_log = MagicMock()
            mock_logging.return_value = (mock_log, MagicMock(), None, None)
            mock_get_config.return_value = mock_config
            
            # Simulate get_data failure
            mock_get_data.side_effect = Exception("Data retrieval failed")
            
            # Execute and expect error propagation
            with pytest.raises(Exception, match="Data retrieval failed"):
                run(config_dict=mock_config)
            
            # Verify logging was setup and get_data was attempted
            mock_logging.assert_called_once()
            mock_get_config.assert_called_once()
            mock_get_data.assert_called_once()

    def test_process_strategy_function_isolation(self):
        """Test process_strategy function works independently."""
        mock_config = {
            "TICKER": "ISOLATED-TEST",
            "FAST_PERIOD": 8,
            "SLOW_PERIOD": 21,
            "STRATEGY_TYPE": "EMA",
            "USE_SMA": False,
            "SIGNAL_PERIOD": 12
        }
        
        mock_data = MagicMock()
        mock_portfolio = MagicMock()
        
        with patch('app.portfolio_review.review.get_data') as mock_get_data, \
             patch('app.portfolio_review.review.calculate_ma_and_signals') as mock_calc_ma, \
             patch('app.portfolio_review.review.backtest_strategy') as mock_backtest:
            
            # Setup mocks
            mock_log = MagicMock()
            mock_get_data.return_value = mock_data
            mock_calc_ma.return_value = mock_data
            mock_backtest.return_value = mock_portfolio
            
            # Test process_strategy directly
            result = process_strategy(mock_config, mock_log)
            
            # Verify result
            assert result == mock_portfolio
            
            # Verify function calls
            mock_get_data.assert_called_once_with(mock_config["TICKER"], mock_config, mock_log)
            mock_calc_ma.assert_called_once_with(
                mock_data, mock_config["FAST_PERIOD"], mock_config["SLOW_PERIOD"], mock_config, mock_log
            )
            mock_backtest.assert_called_once_with(mock_data, mock_config, mock_log)

    def test_process_strategy_with_macd_routing(self):
        """Test process_strategy correctly routes to MACD calculation."""
        mock_config = {
            "TICKER": "MACD-ISOLATED",
            "FAST_PERIOD": 12,
            "SLOW_PERIOD": 26,
            "STRATEGY_TYPE": "MACD",
            "SIGNAL_PERIOD": 9
        }
        
        mock_data = MagicMock()
        mock_portfolio = MagicMock()
        
        with patch('app.portfolio_review.review.get_data') as mock_get_data, \
             patch('app.portfolio_review.review.calculate_macd_and_signals') as mock_calc_macd, \
             patch('app.portfolio_review.review.backtest_strategy') as mock_backtest:
            
            # Setup mocks
            mock_log = MagicMock()
            mock_get_data.return_value = mock_data
            mock_calc_macd.return_value = mock_data
            mock_backtest.return_value = mock_portfolio
            
            # Test process_strategy with MACD
            result = process_strategy(mock_config, mock_log)
            
            # Verify MACD path was taken
            assert result == mock_portfolio
            mock_calc_macd.assert_called_once_with(
                mock_data,
                mock_config["FAST_PERIOD"],    # Fast EMA
                mock_config["SLOW_PERIOD"],    # Slow EMA  
                mock_config["SIGNAL_PERIOD"],  # Signal line EMA
                mock_config,
                mock_log
            )

    def test_directory_creation_and_csv_export(self):
        """Test directory creation and CSV export functionality."""
        mock_config = {
            "TICKER": "EXPORT-TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
            "STRATEGY_TYPE": "SMA"
        }
        
        mock_data = MagicMock()
        mock_portfolio = MagicMock()
        mock_portfolio.stats.return_value = {"total_return": 0.10}
        
        # Mock equity curve data
        mock_value_series = MagicMock()
        mock_value_series.__getitem__ = MagicMock(return_value=1000)  # initial_value
        mock_value_series.index = ["2023-01-01", "2023-01-02"]
        mock_value_series.values = [1000, 1050]
        mock_portfolio.value.return_value = mock_value_series
        
        with patch('app.portfolio_review.review.setup_logging') as mock_logging, \
             patch('app.portfolio_review.review.get_config') as mock_get_config, \
             patch('app.portfolio_review.review.get_data') as mock_get_data, \
             patch('app.portfolio_review.review.calculate_ma_and_signals') as mock_calc_ma, \
             patch('app.portfolio_review.review.backtest_strategy') as mock_backtest, \
             patch('app.portfolio_review.review.os.makedirs') as mock_makedirs, \
             patch('app.portfolio_review.review.pl.DataFrame') as mock_df_class, \
             patch('app.tools.plotting.create_portfolio_plot_files') as mock_plot:
            
            # Setup mocks
            mock_log = MagicMock()
            mock_logging.return_value = (mock_log, MagicMock(), None, None)
            mock_get_config.return_value = mock_config
            mock_get_data.return_value = mock_data
            mock_calc_ma.return_value = mock_data
            mock_backtest.return_value = mock_portfolio
            
            mock_df = MagicMock()
            mock_df.write_csv = MagicMock()
            mock_df_class.return_value = mock_df
            
            mock_plot.return_value = ["plot.png"]
            
            # Execute workflow
            result = run(config_dict=mock_config)
            
            # Verify directory creation
            expected_csv_path = 'data/outputs/portfolio/ma_cross/equity_curve/EXPORT-TEST.csv'
            mock_makedirs.assert_called_once_with(
                os.path.dirname(expected_csv_path), 
                exist_ok=True
            )
            
            # Verify DataFrame creation and export
            mock_df_class.assert_called_once()
            mock_df.write_csv.assert_called_once_with(expected_csv_path)
            
            # Verify plotting
            mock_plot.assert_called_once_with(mock_portfolio, mock_config, mock_log)
            
            assert result == True