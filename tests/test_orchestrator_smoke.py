"""
Smoke tests for the refactored MA Cross module with PortfolioOrchestrator.

This module performs basic smoke tests to ensure the refactored code
maintains compatibility with existing functionality.
"""

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch


# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.strategies.ma_cross.config_types import Config


# Import get_portfolios using importlib due to numeric filename
spec = importlib.util.spec_from_file_location(
    "get_portfolios", str(project_root / "app/strategies/ma_cross/1_get_portfolios.py"),
)
get_portfolios_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(get_portfolios_module)


class TestOrchestratorSmoke(unittest.TestCase):
    """Smoke tests for refactored MA Cross functionality."""

    def test_run_function_exists(self):
        """Test that the run function still exists and is callable."""
        self.assertTrue(hasattr(get_portfolios_module, "run"))
        self.assertTrue(callable(get_portfolios_module.run))

    def test_run_strategies_function_exists(self):
        """Test that the run_strategies function still exists and is callable."""
        self.assertTrue(hasattr(get_portfolios_module, "run_strategies"))
        self.assertTrue(callable(get_portfolios_module.run_strategies))

    @patch("app.tools.orchestration.portfolio_orchestrator.ConfigService")
    @patch("app.tools.orchestration.portfolio_orchestrator.process_synthetic_config")
    @patch("app.tools.orchestration.portfolio_orchestrator.get_strategy_types")
    @patch("app.tools.orchestration.ticker_processor.execute_strategy")
    @patch("app.tools.orchestration.portfolio_orchestrator.filter_portfolios")
    @patch("app.tools.orchestration.portfolio_orchestrator.export_best_portfolios")
    @patch("app.tools.logging_context.logging_context")
    def test_run_function_with_orchestrator(
        self,
        mock_logging_context,
        mock_export,
        mock_filter,
        mock_execute,
        mock_get_strategies,
        mock_synthetic,
        mock_config_service,
    ):
        """Test that run function uses PortfolioOrchestrator."""
        # Set up logging context mock
        mock_log = Mock()
        mock_logging_context.return_value.__enter__ = Mock(return_value=mock_log)
        mock_logging_context.return_value.__exit__ = Mock(return_value=None)

        # Set up other mocks
        config: Config = {"TICKER": ["TEST"], "BASE_DIR": "/tmp"}

        mock_config_service.process_config.return_value = config
        mock_synthetic.return_value = config
        mock_get_strategies.return_value = ["SMA"]
        mock_execute.return_value = []

        # Run using imported module
        result = get_portfolios_module.run(config)

        # Verify it ran successfully
        self.assertTrue(result)
        mock_config_service.process_config.assert_called()

    @patch("app.tools.orchestration.portfolio_orchestrator.ConfigService")
    @patch("app.tools.orchestration.portfolio_orchestrator.process_synthetic_config")
    @patch("app.tools.orchestration.portfolio_orchestrator.get_strategy_types")
    @patch("app.tools.orchestration.ticker_processor.execute_strategy")
    @patch("app.tools.logging_context.logging_context")
    def test_run_strategies_with_orchestrator(
        self,
        mock_logging_context,
        mock_execute,
        mock_get_strategies,
        mock_synthetic,
        mock_config_service,
    ):
        """Test that run_strategies function uses PortfolioOrchestrator."""
        # Set up logging context mock
        mock_log = Mock()
        mock_logging_context.return_value.__enter__ = Mock(return_value=mock_log)
        mock_logging_context.return_value.__exit__ = Mock(return_value=None)

        # Set up other mocks
        config = {
            "TICKER": ["TEST"],
            "BASE_DIR": "/tmp",
            "STRATEGY_TYPES": ["SMA", "EMA"],
        }

        mock_config_service.process_config.return_value = config
        mock_synthetic.return_value = config
        mock_get_strategies.return_value = ["SMA", "EMA"]
        mock_execute.return_value = []

        # Run using imported module
        result = get_portfolios_module.run_strategies(config)

        # Verify it ran successfully
        self.assertTrue(result)
        # Verify USE_MA was set
        config_service_call = mock_config_service.process_config.call_args[0][0]
        self.assertTrue(config_service_call.get("USE_MA"))


if __name__ == "__main__":
    unittest.main()
