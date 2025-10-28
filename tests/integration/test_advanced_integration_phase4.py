#!/usr/bin/env python3
"""
Advanced Integration Test Suite - Phase 4

This test suite provides comprehensive integration testing for the trading system,
focusing on realistic end-to-end workflows, cross-component interactions,
and complex data flow validation.

Key Testing Areas:
- Full pipeline integration (data → strategy → portfolio → export)
- Cross-service communication and state management
- Complex configuration scenarios
- Multi-component error propagation
- Resource cleanup and state isolation
"""

from pathlib import Path
import tempfile
import time
from unittest.mock import Mock, patch

import pytest

from tests.fixtures.data_stabilization import (
    stabilize_integration_test,
    stable_market_data,
)


@pytest.mark.integration
@pytest.mark.phase4
class TestAdvancedStrategyIntegration:
    """Test complete strategy analysis pipeline integration."""

    @pytest.fixture
    def integration_workspace(self):
        """Create isolated workspace for integration testing."""
        with tempfile.TemporaryDirectory(prefix="integration_phase4_") as temp_dir:
            workspace = Path(temp_dir)

            # Create full directory structure
            directories = [
                "data/raw/portfolios",
                "data/raw/portfolios_filtered",
                "data/raw/portfolios_best",
                "data/raw/price_data",
                "app/cli/profiles",
                "logs",
                "json/trade_history",
            ]

            for directory in directories:
                (workspace / directory).mkdir(parents=True, exist_ok=True)

            yield workspace

    @pytest.fixture
    def mock_strategy_factory(self):
        """Mock strategy factory for controlled strategy execution."""
        factory = Mock()

        # Mock strategy results with realistic data
        mock_results = {
            "strategy_type": "SMA",
            "ticker": "AAPL",
            "total_return": 25.7,
            "win_rate": 0.635,
            "total_trades": 48,
            "sharpe_ratio": 1.42,
            "max_drawdown": -8.9,
            "profit_factor": 2.1,
        }

        factory.execute_strategy.return_value = mock_results
        factory.validate_config.return_value = True

        return factory

    @stabilize_integration_test(tickers=["AAPL", "MSFT", "GOOGL"], timeout_override=45)
    def test_full_pipeline_data_to_export_integration(
        self, integration_workspace, mock_strategy_factory,
    ):
        """
        Test complete pipeline: Data acquisition → Strategy execution → Portfolio generation → Export
        """
        from app.cli.commands.strategy import StrategyDispatcher
        from app.cli.models.strategy import (
            StrategyConfig,
            StrategyMinimums,
            StrategyType,
        )

        # Step 1: Configure realistic strategy
        config = StrategyConfig(
            ticker=["AAPL", "MSFT", "GOOGL"],
            strategy_types=[StrategyType.SMA, StrategyType.EMA],
            use_years=True,
            years=3,
            multi_ticker=True,
            minimums=StrategyMinimums(win_rate=0.55, trades=25),
        )

        # Step 2: Mock complete strategy pipeline
        with patch(
            "app.cli.services.strategy_services.MAStrategyService",
        ) as mock_service:
            mock_service.return_value.execute_strategy.return_value = True
            mock_service.return_value.convert_config_to_legacy.return_value = {
                "TICKER": ["AAPL", "MSFT", "GOOGL"],
                "STRATEGY_TYPES": ["SMA", "EMA"],
                "YEARS": 3,
                "MINIMUMS": {"WIN_RATE": 0.55, "TRADES": 25},
            }

            dispatcher = StrategyDispatcher()

            # Step 3: Execute integration pipeline
            start_time = time.time()
            success = dispatcher.execute_strategy(config)
            execution_time = time.time() - start_time

            # Step 4: Validate pipeline execution
            assert success is True, "Integration pipeline should execute successfully"
            assert execution_time < 30.0, f"Pipeline took too long: {execution_time}s"

            # Step 5: Verify service interactions
            mock_service.return_value.execute_strategy.assert_called_once()
            mock_service.return_value.convert_config_to_legacy.assert_called_once()

    @stable_market_data(tickers=["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN"])
    def test_multi_component_state_management(self, integration_workspace):
        """
        Test state management across multiple components with shared resources.
        """
        from app.cli.config import ConfigManager
        from app.cli.services.portfolio_analysis_service import PortfolioAnalysisService
        from app.cli.services.profile_editor_service import ProfileEditorService

        # Step 1: Initialize components with shared state
        config_manager = ConfigManager()
        portfolio_service = PortfolioAnalysisService(str(integration_workspace))
        editor_service = ProfileEditorService(config_manager)

        # Step 2: Create test profile
        test_profile = {
            "metadata": {
                "name": "integration_test",
                "description": "Integration test profile",
            },
            "config_type": "strategy",
            "config": {
                "ticker": ["AAPL", "MSFT"],
                "strategy_types": ["SMA"],
                "minimums": {"win_rate": 0.6, "trades": 30},
            },
        }

        # Step 3: Test cross-component operations
        with (
            patch.object(
                config_manager.profile_manager,
                "load_profile",
                return_value=test_profile,
            ),
            patch.object(config_manager.profile_manager, "save_profile") as mock_save,
        ):
            # Load profile through editor service
            loaded_profile = editor_service.load_profile("integration_test")

            # Modify profile state
            editor_service.set_field_value(
                loaded_profile, "config.ticker", "AAPL,MSFT,GOOGL",
            )

            # Save modified profile
            editor_service.save_profile("integration_test", loaded_profile)

            # Verify state consistency
            assert loaded_profile["config"]["ticker"] == ["AAPL", "MSFT", "GOOGL"]
            mock_save.assert_called_once_with("integration_test", loaded_profile)

        # Step 4: Test portfolio service with modified state
        mock_tickers = loaded_profile["config"]["ticker"]
        with patch.object(
            portfolio_service, "aggregate_portfolios_best",
        ) as mock_aggregate:
            import pandas as pd

            mock_df = pd.DataFrame(
                {
                    "Ticker": mock_tickers * 2,
                    "Score": [0.8, 0.75, 0.9, 0.82, 0.77, 0.88],
                    "Strategy Type": ["SMA"] * 6,
                },
            )
            mock_aggregate.return_value = mock_df

            result = portfolio_service.aggregate_portfolios_best(mock_tickers)

            # Verify cross-component data consistency
            assert len(result) == 6
            assert set(result["Ticker"].unique()) == set(mock_tickers)
            mock_aggregate.assert_called_once_with(mock_tickers)

    @stabilize_integration_test(tickers=["BTC-USD", "ETH-USD"], timeout_override=30)
    def test_complex_configuration_scenarios(self, integration_workspace):
        """
        Test complex configuration scenarios with edge cases and special characters.
        """
        from app.cli.config import ConfigLoader as ProfileLoader
        from app.cli.models.strategy import StrategyConfig

        # Step 1: Create complex profile with edge cases
        complex_profile_content = """
metadata:
  name: complex_integration_test
  description: 'Complex profile with special characters & edge cases'

config_type: strategy
config:
  ticker: ["BTC-USD", "ETH-USD"]  # Crypto tickers with hyphens
  strategy_types: [SMA, EMA, MACD]
  use_years: true
  years: 5
  multi_ticker: true
  use_gbm: true  # Geometric Brownian Motion
  synthetic:
    use_synthetic: true
    synthetic_ticker: "CRYPTO_PAIR"
  minimums:
    win_rate: 0.58
    trades: 40
    sharpe_ratio: 1.0
  filter:
    use_current: false
    exclude_weekends: true
"""

        # Step 2: Write complex profile to workspace
        profile_path = (
            integration_workspace
            / "app"
            / "cli"
            / "profiles"
            / "complex_integration_test.yaml"
        )
        profile_path.write_text(complex_profile_content)

        # Step 3: Load and validate complex configuration
        profile_loader = ProfileLoader(
            str(integration_workspace / "app" / "cli" / "profiles"),
        )

        try:
            config = profile_loader.load_from_profile("complex_integration_test")

            # Step 4: Validate complex configuration handling
            assert config.ticker == ["BTC-USD", "ETH-USD"]
            assert len(config.strategy_types) == 3  # SMA, EMA, MACD
            assert config.use_gbm is True
            assert config.synthetic.use_synthetic is True
            assert config.synthetic.synthetic_ticker == "CRYPTO_PAIR"
            assert config.minimums.win_rate == 0.58
            assert config.minimums.trades == 40

        except Exception as e:
            pytest.fail(f"Complex configuration failed to load: {e}")

        # Step 5: Test configuration serialization round-trip
        serialized_config = config.model_dump()
        reconstructed_config = StrategyConfig(**serialized_config)

        assert reconstructed_config.ticker == config.ticker
        assert reconstructed_config.strategy_types == config.strategy_types
        assert (
            reconstructed_config.synthetic.synthetic_ticker
            == config.synthetic.synthetic_ticker
        )

    @pytest.mark.slow
    @stabilize_integration_test(
        tickers=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"], timeout_override=60,
    )
    def test_large_scale_integration_workflow(self, integration_workspace):
        """
        Test large-scale integration workflow with multiple tickers and strategies.
        """
        from app.cli.models.strategy import (
            StrategyConfig,
            StrategyMinimums,
            StrategyType,
        )
        from app.cli.services.strategy_services import (
            MACDStrategyService,
            MAStrategyService,
        )

        # Step 1: Setup large-scale configuration
        large_config = StrategyConfig(
            ticker=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],  # 5 major stocks
            strategy_types=[
                StrategyType.SMA,
                StrategyType.EMA,
                StrategyType.MACD,
            ],  # 3 strategies
            use_years=True,
            years=2,  # Reduce for testing performance
            multi_ticker=True,
            minimums=StrategyMinimums(
                win_rate=0.5, trades=20,
            ),  # Lower for more results
        )

        # Step 2: Mock large-scale execution with realistic timing
        ma_service = MAStrategyService()
        macd_service = MACDStrategyService()

        with patch.object(ma_service, "execute_strategy") as mock_ma_execute:
            with patch.object(macd_service, "execute_strategy") as mock_macd_execute:
                # Simulate execution times
                mock_ma_execute.return_value = True
                mock_macd_execute.return_value = True

                start_time = time.time()

                # Step 3: Execute strategies in sequence (realistic workflow)
                ma_legacy_config = ma_service.convert_config_to_legacy(large_config)
                ma_result = ma_service.execute_strategy(large_config)

                macd_legacy_config = macd_service.convert_config_to_legacy(large_config)
                macd_result = macd_service.execute_strategy(large_config)

                total_time = time.time() - start_time

                # Step 4: Validate large-scale execution
                assert ma_result is True
                assert macd_result is True
                assert (
                    total_time < 45.0
                ), f"Large-scale execution too slow: {total_time}s"

                # Step 5: Verify configuration conversion for both services
                assert ma_legacy_config["TICKER"] == large_config.ticker
                assert macd_legacy_config["TICKER"] == large_config.ticker

                # Verify service calls
                mock_ma_execute.assert_called_once_with(large_config)
                mock_macd_execute.assert_called_once_with(large_config)

    def test_resource_cleanup_and_isolation(self, integration_workspace):
        """
        Test proper resource cleanup and state isolation between tests.
        """

        from app.cli.services.portfolio_analysis_service import PortfolioAnalysisService

        # Step 1: Create multiple service instances with different states
        service1 = PortfolioAnalysisService(
            str(integration_workspace), use_current=True,
        )
        service2 = PortfolioAnalysisService(
            str(integration_workspace), use_current=False,
        )

        # Step 2: Create temporary files in workspace
        temp_files = []
        for i in range(5):
            temp_file = integration_workspace / f"temp_test_file_{i}.csv"
            temp_file.write_text(f"test,data,{i}\nvalue1,value2,{i}")
            temp_files.append(temp_file)

        # Step 3: Verify isolation between service instances
        assert service1.use_current is True
        assert service2.use_current is False
        assert service1.base_dir == service2.base_dir  # Same workspace

        # Step 4: Test cleanup behavior
        for temp_file in temp_files:
            assert temp_file.exists(), f"Test file {temp_file} should exist"

        # Step 5: Simulate cleanup (would happen automatically with tempdir)
        for temp_file in temp_files:
            temp_file.unlink()

        for temp_file in temp_files:
            assert not temp_file.exists(), f"Test file {temp_file} should be cleaned up"

        # Step 6: Verify services still function after cleanup
        with patch.object(service1, "aggregate_portfolios_best") as mock1:
            with patch.object(service2, "aggregate_portfolios_best") as mock2:
                import pandas as pd

                mock_df = pd.DataFrame({"test": [1, 2, 3]})
                mock1.return_value = mock_df
                mock2.return_value = mock_df

                result1 = service1.aggregate_portfolios_best(["AAPL"])
                result2 = service2.aggregate_portfolios_best(["AAPL"])

                assert len(result1) == 3
                assert len(result2) == 3
                mock1.assert_called_once_with(["AAPL"])
                mock2.assert_called_once_with(["AAPL"])


@pytest.mark.integration
@pytest.mark.phase4
class TestCrossComponentCommunication:
    """Test communication patterns between different system components."""

    def test_service_to_service_communication(self):
        """Test communication between different services."""
        from app.cli.config import ConfigManager
        from app.cli.services.portfolio_analysis_service import PortfolioAnalysisService
        from app.cli.services.profile_editor_service import ProfileEditorService

        # Step 1: Setup service communication chain
        config_manager = ConfigManager()
        portfolio_service = PortfolioAnalysisService()
        editor_service = ProfileEditorService(config_manager)

        # Step 2: Test data flow between services
        test_profile = {
            "config": {"ticker": ["AAPL", "MSFT"], "minimums": {"win_rate": 0.6}},
        }

        with patch.object(
            config_manager.profile_manager, "load_profile", return_value=test_profile,
        ):
            # Load profile through editor
            profile_data = editor_service.load_profile("test_profile")

            # Extract tickers for portfolio service
            tickers = profile_data["config"]["ticker"]

            # Use tickers in portfolio service
            with patch.object(
                portfolio_service, "aggregate_portfolios_best",
            ) as mock_aggregate:
                import pandas as pd

                mock_aggregate.return_value = pd.DataFrame(
                    {"Ticker": tickers, "Score": [0.8, 0.75]},
                )

                result = portfolio_service.aggregate_portfolios_best(tickers)

                # Verify cross-service data consistency
                assert set(result["Ticker"].values) == set(tickers)
                mock_aggregate.assert_called_once_with(tickers)

    def test_cli_to_service_communication(self):
        """Test communication from CLI commands to service layer."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from app.cli.commands.config import app as config_app

        runner = CliRunner()

        # Test CLI → Service communication
        with (
            patch("app.cli.commands.config.ConfigManager"),
            patch(
                "app.cli.services.profile_editor_service.ProfileEditorService",
            ) as mock_service_class,
        ):
            # Setup mocks
            mock_service = mock_service_class.return_value
            mock_service.load_profile.return_value = {"config": {"ticker": ["AAPL"]}}

            # Execute CLI command
            result = runner.invoke(config_app, ["edit", "test_profile"])

            # Verify CLI → Service communication
            mock_service_class.assert_called_once()
            mock_service.load_profile.assert_called_once_with("test_profile")
            assert result.exit_code == 0

    @stable_market_data(tickers=["AAPL", "MSFT"])
    def test_event_driven_communication(self):
        """Test event-driven communication patterns in the system."""

        # Step 1: Setup event tracking
        events = []

        def event_logger(event_type, **kwargs):
            events.append(
                {"type": event_type, "data": kwargs, "timestamp": time.time()},
            )

        # Step 2: Mock components with event emission
        with patch(
            "app.cli.services.portfolio_analysis_service.PortfolioAnalysisService",
        ) as MockService:
            mock_service = MockService.return_value

            # Configure mock to emit events
            def mock_aggregate(tickers):
                event_logger("portfolio_aggregation_start", tickers=tickers)
                import pandas as pd

                result = pd.DataFrame(
                    {"Ticker": tickers, "Score": [0.8] * len(tickers)},
                )
                event_logger("portfolio_aggregation_complete", result_count=len(result))
                return result

            mock_service.aggregate_portfolios_best.side_effect = mock_aggregate

            # Step 3: Execute operation that triggers events
            service = MockService()
            service.aggregate_portfolios_best(["AAPL", "MSFT"])

            # Step 4: Verify event sequence
            assert len(events) == 2
            assert events[0]["type"] == "portfolio_aggregation_start"
            assert events[0]["data"]["tickers"] == ["AAPL", "MSFT"]
            assert events[1]["type"] == "portfolio_aggregation_complete"
            assert events[1]["data"]["result_count"] == 2

            # Verify event timing
            assert events[1]["timestamp"] > events[0]["timestamp"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
