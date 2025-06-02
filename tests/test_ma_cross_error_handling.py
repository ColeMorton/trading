"""
Tests for MA Cross Error Handling Standardization

This module tests the standardized error handling patterns implemented
in Phase 6 of the MA Cross optimization plan.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from app.strategies.ma_cross.exceptions import (
    MACrossError,
    MACrossConfigurationError,
    MACrossDataError,
    MACrossCalculationError,
    MACrossPortfolioError,
    MACrossValidationError,
    MACrossExecutionError,
    MACrossSyntheticTickerError
)


class TestMACrossExceptions:
    """Test MA Cross specific exception types."""
    
    def test_ma_cross_error_base(self):
        """Test base MACrossError exception."""
        error = MACrossError("Test error")
        assert str(error) == "Test error"
        assert error.details == {}
    
    def test_ma_cross_configuration_error(self):
        """Test MACrossConfigurationError with details."""
        error = MACrossConfigurationError(
            "Invalid config field",
            config_field="TICKER",
            config_value="invalid"
        )
        assert error.details["config_field"] == "TICKER"
        assert error.details["config_value"] == "invalid"
        assert error.details["error_type"] == "configuration"
    
    def test_ma_cross_data_error(self):
        """Test MACrossDataError with details."""
        error = MACrossDataError(
            "Data processing failed",
            ticker="BTC-USD",
            data_type="price_data"
        )
        assert error.details["ticker"] == "BTC-USD"
        assert error.details["data_type"] == "price_data"
        assert error.details["error_type"] == "data_processing"
    
    def test_ma_cross_calculation_error(self):
        """Test MACrossCalculationError with details."""
        error = MACrossCalculationError(
            "Calculation failed",
            ticker="BTC-USD",
            calculation_type="moving_average"
        )
        assert error.details["ticker"] == "BTC-USD"
        assert error.details["calculation_type"] == "moving_average"
        assert error.details["error_type"] == "calculation"
    
    def test_ma_cross_portfolio_error(self):
        """Test MACrossPortfolioError with details."""
        error = MACrossPortfolioError(
            "Portfolio operation failed",
            ticker="BTC-USD",
            operation="filtering"
        )
        assert error.details["ticker"] == "BTC-USD"
        assert error.details["operation"] == "filtering"
        assert error.details["error_type"] == "portfolio_processing"
    
    def test_ma_cross_validation_error(self):
        """Test MACrossValidationError with details."""
        error = MACrossValidationError(
            "Validation failed",
            field="WINDOWS",
            value=0
        )
        assert error.details["field"] == "WINDOWS"
        assert error.details["value"] == 0
        assert error.details["error_type"] == "validation"
    
    def test_ma_cross_execution_error(self):
        """Test MACrossExecutionError with details."""
        error = MACrossExecutionError(
            "Strategy execution failed",
            ticker="BTC-USD",
            stage="signal_generation"
        )
        assert error.details["ticker"] == "BTC-USD"
        assert error.details["execution_stage"] == "signal_generation"
        assert error.details["error_type"] == "execution"
    
    def test_ma_cross_synthetic_ticker_error(self):
        """Test MACrossSyntheticTickerError with details."""
        error = MACrossSyntheticTickerError(
            "Synthetic ticker processing failed",
            synthetic_ticker="BTC_USD",
            component_tickers=["BTC-USD", "USD"]
        )
        assert error.details["synthetic_ticker"] == "BTC_USD"
        assert error.details["component_tickers"] == ["BTC-USD", "USD"]
        assert error.details["error_type"] == "synthetic_ticker"


class TestPortfolioOrchestratorErrorHandling:
    """Test error handling in PortfolioOrchestrator."""
    
    @pytest.fixture
    def mock_log(self):
        return Mock()
    
    @pytest.fixture
    def orchestrator(self, mock_log):
        from app.tools.orchestration.portfolio_orchestrator import PortfolioOrchestrator
        return PortfolioOrchestrator(mock_log)
    
    def test_configuration_error_mapping(self, orchestrator, mock_log):
        """Test that configuration errors are mapped to MACrossConfigurationError."""
        from app.tools.exceptions import ConfigurationError
        
        with patch('app.tools.config_service.ConfigService.process_config') as mock_process:
            mock_process.side_effect = ConfigurationError("Invalid config")
            
            with pytest.raises(MACrossConfigurationError) as exc_info:
                orchestrator._initialize_configuration({"invalid": "config"})
            
            assert "Invalid config" in str(exc_info.value)
    
    def test_strategy_execution_error_mapping(self, orchestrator, mock_log):
        """Test that strategy execution errors are mapped to MACrossExecutionError."""
        from app.tools.exceptions import StrategyProcessingError
        
        with patch.object(orchestrator.ticker_processor, 'execute_strategy') as mock_execute:
            mock_execute.side_effect = StrategyProcessingError("Strategy failed")
            
            with pytest.raises(MACrossExecutionError) as exc_info:
                orchestrator._execute_strategies({"STRATEGY_TYPE": "SMA"}, ["SMA"])
            
            assert "Strategy failed" in str(exc_info.value)
    
    def test_portfolio_processing_error_mapping(self, orchestrator, mock_log):
        """Test that portfolio processing errors are mapped to MACrossPortfolioError."""
        with patch('app.tools.portfolio.schema_detection.detect_schema_version') as mock_detect:
            mock_detect.side_effect = ValueError("Schema detection failed")
            
            with pytest.raises(MACrossPortfolioError) as exc_info:
                orchestrator._filter_and_process_portfolios([{}], {})
            
            assert "Schema detection failed" in str(exc_info.value)


class TestTickerProcessorErrorHandling:
    """Test error handling in TickerProcessor."""
    
    @pytest.fixture
    def mock_log(self):
        return Mock()
    
    @pytest.fixture
    def ticker_processor(self, mock_log):
        from app.tools.orchestration.ticker_processor import TickerProcessor
        return TickerProcessor(mock_log)
    
    def test_strategy_execution_error_handling(self, ticker_processor, mock_log):
        """Test error handling in strategy execution."""
        with patch.object(ticker_processor, 'log', mock_log):
            with patch('app.strategies.ma_cross.tools.strategy_execution.execute_strategy') as mock_execute:
                mock_execute.side_effect = Exception("Execution failed")
                
                with pytest.raises(MACrossExecutionError) as exc_info:
                    ticker_processor.execute_strategy({"TICKER": ["BTC-USD"]}, "SMA")
                
                assert "Execution failed" in str(exc_info.value)
    
    def test_ticker_processing_error_handling(self, ticker_processor, mock_log):
        """Test error handling in ticker processing."""
        with patch.object(ticker_processor, 'log', mock_log):
            with patch('app.strategies.ma_cross.tools.strategy_execution.process_single_ticker') as mock_process:
                mock_process.side_effect = Exception("Processing failed")
                
                with pytest.raises(MACrossDataError) as exc_info:
                    ticker_processor.process_ticker("BTC-USD", {})
                
                assert "Processing failed" in str(exc_info.value)
    
    def test_synthetic_ticker_extraction_success(self, ticker_processor, mock_log):
        """Test successful synthetic ticker component extraction."""
        config = {}
        ticker_processor._extract_synthetic_components("BTC_USD", config)
        
        assert config["TICKER_1"] == "BTC"
        assert config["TICKER_2"] == "USD"
        mock_log.assert_called()
    
    def test_synthetic_ticker_extraction_invalid_format(self, ticker_processor, mock_log):
        """Test error handling for invalid synthetic ticker format."""
        config = {}
        
        with pytest.raises(MACrossSyntheticTickerError) as exc_info:
            ticker_processor._extract_synthetic_components("BTC", config)
        
        assert "Not a synthetic ticker" in str(exc_info.value)
    
    def test_synthetic_ticker_extraction_insufficient_parts(self, ticker_processor, mock_log):
        """Test error handling for synthetic ticker with insufficient parts."""
        config = {}
        
        # Test with underscore at the end which gives empty second component
        with pytest.raises(MACrossSyntheticTickerError) as exc_info:
            ticker_processor._extract_synthetic_components("BTC_", config)
        
        assert "Invalid synthetic ticker format" in str(exc_info.value)


class TestMainScriptErrorHandling:
    """Test error handling in main script functions."""
    
    @pytest.fixture
    def mock_logging_context(self):
        return MagicMock()
    
    def test_run_function_error_decoration(self):
        """Test that run function has proper error decoration."""
        import importlib.util
        import sys
        
        # Load the module with a numeric name
        spec = importlib.util.spec_from_file_location(
            "get_portfolios", 
            "/Users/colemorton/Projects/trading/app/strategies/ma_cross/1_get_portfolios.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check that the function has the error handling decorator
        assert hasattr(module.run, '__wrapped__')  # This indicates a decorator was applied
    
    def test_run_strategies_function_error_decoration(self):
        """Test that run_strategies function has proper error decoration."""
        import importlib.util
        import sys
        
        # Load the module with a numeric name
        spec = importlib.util.spec_from_file_location(
            "get_portfolios", 
            "/Users/colemorton/Projects/trading/app/strategies/ma_cross/1_get_portfolios.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check that the function has the error handling decorator
        assert hasattr(module.run_strategies, '__wrapped__')  # This indicates a decorator was applied
    
    @patch('app.tools.orchestration.portfolio_orchestrator.PortfolioOrchestrator')
    def test_run_function_orchestrator_error_handling(self, mock_orchestrator_class):
        """Test error handling in run function."""
        import importlib.util
        
        # Load the module with a numeric name
        spec = importlib.util.spec_from_file_location(
            "get_portfolios", 
            "/Users/colemorton/Projects/trading/app/strategies/ma_cross/1_get_portfolios.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Setup mocks
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_orchestrator.run.side_effect = Exception("Orchestrator failed")
        
        # This should raise an error that gets handled by the decorator
        with pytest.raises(MACrossError):
            module.run({"TICKER": ["BTC-USD"]})
    
    @patch('app.tools.orchestration.portfolio_orchestrator.PortfolioOrchestrator')
    def test_run_strategies_function_orchestrator_error_handling(self, mock_orchestrator_class):
        """Test error handling in run_strategies function."""
        import importlib.util
        
        # Load the module with a numeric name
        spec = importlib.util.spec_from_file_location(
            "get_portfolios", 
            "/Users/colemorton/Projects/trading/app/strategies/ma_cross/1_get_portfolios.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Setup mocks
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_orchestrator.run.side_effect = Exception("Orchestrator failed")
        
        # This should raise an error that gets handled by the decorator
        with pytest.raises(MACrossError):
            module.run_strategies({"TICKER": ["BTC-USD"]})


class TestErrorContextIntegration:
    """Test integration with error context management."""
    
    def test_error_context_usage_in_orchestrator(self):
        """Test that error context is properly used in orchestrator methods."""
        from app.tools.orchestration.portfolio_orchestrator import PortfolioOrchestrator
        import inspect
        
        # Get the source code to verify error_context usage
        source = inspect.getsource(PortfolioOrchestrator._initialize_configuration)
        assert "error_context" in source
        assert "MACrossConfigurationError" in source
    
    def test_error_context_usage_in_ticker_processor(self):
        """Test that error context is properly used in ticker processor methods."""
        from app.tools.orchestration.ticker_processor import TickerProcessor
        import inspect
        
        # Get the source code to verify error_context usage
        source = inspect.getsource(TickerProcessor.execute_strategy)
        assert "error_context" in source
        assert "MACrossExecutionError" in source


class TestErrorDetailEnrichment:
    """Test that errors include rich contextual information."""
    
    def test_configuration_error_includes_context(self):
        """Test that configuration errors include field and value context."""
        error = MACrossConfigurationError(
            "Invalid ticker format",
            config_field="TICKER",
            config_value="INVALID_TICKER"
        )
        
        details = error.details
        assert details["config_field"] == "TICKER"
        assert details["config_value"] == "INVALID_TICKER"
        assert details["error_type"] == "configuration"
    
    def test_execution_error_includes_context(self):
        """Test that execution errors include ticker and stage context."""
        error = MACrossExecutionError(
            "Strategy execution failed during signal generation",
            ticker="BTC-USD",
            stage="signal_generation"
        )
        
        details = error.details
        assert details["ticker"] == "BTC-USD"
        assert details["execution_stage"] == "signal_generation"
        assert details["error_type"] == "execution"
    
    def test_synthetic_ticker_error_includes_context(self):
        """Test that synthetic ticker errors include component information."""
        error = MACrossSyntheticTickerError(
            "Failed to process synthetic ticker components",
            synthetic_ticker="BTC_USD",
            component_tickers=["BTC-USD", "USD"]
        )
        
        details = error.details
        assert details["synthetic_ticker"] == "BTC_USD"
        assert details["component_tickers"] == ["BTC-USD", "USD"]
        assert details["error_type"] == "synthetic_ticker"


if __name__ == "__main__":
    pytest.main([__file__])