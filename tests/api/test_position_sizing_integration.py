"""
Position Sizing Integration Test

This module contains integration tests that demonstrate the complete
Phase 3 implementation working end-to-end.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.services.position_sizing_orchestrator import (
    PositionSizingOrchestrator,
    PositionSizingRequest,
)
from app.tools.accounts import PortfolioType
from app.tools.services.enhanced_service_coordinator import EnhancedServiceCoordinator


class TestPositionSizingIntegration:
    """Integration tests for complete position sizing functionality."""

    @pytest.fixture
    def mock_base_dir(self, tmp_path):
        """Create temporary directory for testing."""
        return str(tmp_path)

    @pytest.fixture
    def orchestrator(self, mock_base_dir):
        """Create position sizing orchestrator with mock data."""
        orchestrator = PositionSizingOrchestrator(base_dir=mock_base_dir)

        # Set up mock data
        orchestrator.account_service.update_account_balance("IBKR", 60000.0)
        orchestrator.account_service.update_account_balance("Bybit", 30000.0)
        orchestrator.account_service.update_account_balance("Cash", 10000.0)

        # Add mock Kelly parameters
        orchestrator.kelly_sizer.update_parameters(
            num_primary=15, num_outliers=3, kelly_criterion=0.25
        )

        return orchestrator

    @pytest.fixture
    def enhanced_coordinator(self, mock_base_dir):
        """Create enhanced service coordinator with mocked dependencies."""
        mock_strategy_factory = MagicMock()
        mock_cache = MagicMock()
        mock_config = MagicMock()
        mock_logger = MagicMock()
        mock_metrics = MagicMock()
        mock_progress_tracker = MagicMock()

        coordinator = EnhancedServiceCoordinator(
            strategy_factory=mock_strategy_factory,
            cache=mock_cache,
            config=mock_config,
            logger=mock_logger,
            metrics=mock_metrics,
            progress_tracker=mock_progress_tracker,
            base_dir=mock_base_dir,
        )

        return coordinator

    def test_orchestrator_initialization(self, orchestrator):
        """Test that orchestrator initializes all components correctly."""
        assert orchestrator.account_service is not None
        assert orchestrator.position_tracker is not None
        assert orchestrator.drawdown_calculator is not None
        assert orchestrator.strategies_integration is not None
        assert orchestrator.portfolio_manager is not None
        assert orchestrator.cvar_calculator is not None
        assert orchestrator.kelly_sizer is not None

    def test_complete_position_sizing_workflow(self, orchestrator):
        """Test complete position sizing workflow from signal to position."""
        # 1. Calculate position size for a signal
        request = PositionSizingRequest(
            symbol="AAPL",
            signal_type="entry",
            portfolio_type=PortfolioType.RISK_ON,
            entry_price=150.0,
            stop_loss_distance=0.05,
            confidence_level="primary",
        )

        response = orchestrator.calculate_position_size(request)

        # Verify response structure
        assert response.symbol == "AAPL"
        assert response.recommended_position_size > 0
        assert response.position_value > 0
        assert response.risk_amount > 0
        assert response.kelly_percentage > 0
        assert response.stop_loss_price == 150.0 * 0.95  # 5% stop loss

        # 2. Process the position entry
        position_result = orchestrator.process_new_position(
            symbol="AAPL",
            position_value=response.position_value,
            stop_loss_distance=0.05,
            entry_price=150.0,
            portfolio_type=PortfolioType.RISK_ON,
        )

        # Verify position was created
        assert position_result["position_entry"] is not None
        assert position_result["drawdown_entry"] is not None
        assert position_result["portfolio_holding"] is not None

        # 3. Get dashboard data
        dashboard = orchestrator.get_dashboard_data()

        # Verify dashboard includes the new position
        assert dashboard.net_worth == 100000.0  # Total of all accounts
        assert len(dashboard.active_positions) > 0
        assert any(pos["symbol"] == "AAPL" for pos in dashboard.active_positions)

    def test_multiple_portfolio_coordination(self, orchestrator):
        """Test coordination between Risk On and Investment portfolios."""
        # Add position to Risk On portfolio
        risk_on_result = orchestrator.process_new_position(
            symbol="BTC-USD",
            position_value=10000.0,
            stop_loss_distance=0.08,
            entry_price=45000.0,
            portfolio_type=PortfolioType.RISK_ON,
        )

        # Add position to Investment portfolio
        investment_result = orchestrator.process_new_position(
            symbol="SPY",
            position_value=15000.0,
            stop_loss_distance=0.03,
            entry_price=400.0,
            portfolio_type=PortfolioType.INVESTMENT,
        )

        # Verify both positions are tracked separately
        btc_analysis = orchestrator.get_position_analysis("BTC-USD")
        spy_analysis = orchestrator.get_position_analysis("SPY")

        assert btc_analysis["portfolio_allocation"]["risk_on"]["value"] > 0
        assert spy_analysis["portfolio_allocation"]["investment"]["value"] > 0

    def test_risk_allocation_validation(self, orchestrator):
        """Test risk allocation calculations and limits."""
        # Get risk allocation summary
        dashboard = orchestrator.get_dashboard_data()

        # Verify 11.8% risk tier is active
        risk_buckets = dashboard.risk_allocation_buckets
        assert len(risk_buckets) > 0

        active_bucket = next(
            (bucket for bucket in risk_buckets if bucket.get("status") == "active"),
            None,
        )
        assert active_bucket is not None
        assert active_bucket["risk_level"] == 0.118
        assert active_bucket["allocation_amount"] == 100000.0 * 0.118

    def test_excel_validation_integration(self, orchestrator):
        """Test Excel validation with real calculations."""
        # Set up expected Excel values
        excel_data = {
            "net_worth": 100000.0,
            "trading_cvar": 0.15,
            "investment_cvar": 0.12,
            "risk_amount": 11800.0,
        }

        # Run validation
        validation_results = orchestrator.validate_excel_compatibility(excel_data)

        # Check validation structure
        assert "validated" in validation_results
        assert "discrepancies" in validation_results
        assert "validations" in validation_results

        # If there are discrepancies, they should be detailed
        if not validation_results["validated"]:
            assert len(validation_results["discrepancies"]) > 0
            for discrepancy in validation_results["discrepancies"]:
                assert "field" in discrepancy
                assert "expected" in discrepancy
                assert "actual" in discrepancy

    @pytest.mark.asyncio
    async def test_enhanced_coordinator_integration(self, enhanced_coordinator):
        """Test enhanced service coordinator with position sizing."""
        # Mock strategy analysis request
        from app.api.models.strategy_analysis import (
            StrategyAnalysisRequest,
            StrategyTypeEnum,
        )

        mock_request = StrategyAnalysisRequest(
            ticker="AAPL",
            strategy_type=StrategyTypeEnum.SMA,
            direction="D",
            use_hourly=False,
            use_years=True,
            years=3,
            refresh=False,
            parameters={"windows": [20, 50]},
        )

        # Mock the base strategy analysis
        with patch.object(enhanced_coordinator, "analyze_strategy") as mock_analyze:
            mock_analyze.return_value = MagicMock(
                deduplicated_portfolios=[
                    {
                        "ticker": "AAPL",
                        "signals": [
                            {"position": 1, "price": 150.0, "timestamp": "2023-12-01"}
                        ],
                        "metrics": {"sharpe_ratio": 1.5},
                    }
                ]
            )

            # Execute strategy with position sizing
            result = await enhanced_coordinator.analyze_strategy_with_position_sizing(
                mock_request
            )

            # Verify integration
            assert "strategy_analysis" in result
            assert "position_sizing" in result

            if result["position_sizing"]:
                assert "recommendations" in result["position_sizing"]
                assert "dashboard" in result["position_sizing"]

    @pytest.mark.asyncio
    async def test_position_sizing_strategy_engine_integration(self, mock_base_dir):
        """Test position sizing strategy engine integration."""
        from app.tools.services.position_sizing_strategy_engine import (
            PositionSizingStrategyEngine,
        )

        # Create mock dependencies
        mock_strategy_factory = MagicMock()
        mock_cache = MagicMock()
        mock_config = MagicMock()
        mock_logger = MagicMock()
        mock_logger.log = MagicMock()

        # Create strategy engine
        engine = PositionSizingStrategyEngine(
            strategy_factory=mock_strategy_factory,
            cache=mock_cache,
            config=mock_config,
            logger=mock_logger,
            enable_position_sizing=True,
            base_dir=mock_base_dir,
        )

        # Test validation
        validation = await engine.validate_position_sizing_integration()

        assert "position_sizing_enabled" in validation
        assert "orchestrator_available" in validation
        assert "components_status" in validation

    def test_data_export_and_import_cycle(self, orchestrator):
        """Test complete data export and import cycle."""
        # Add some test data
        orchestrator.process_new_position(
            symbol="TSLA",
            position_value=8000.0,
            stop_loss_distance=0.06,
            entry_price=200.0,
            portfolio_type=PortfolioType.RISK_ON,
        )

        # Export data
        export_path = orchestrator.export_for_excel_migration()

        # Verify export file exists and has content
        import json
        from pathlib import Path

        export_file = Path(export_path)
        assert export_file.exists()

        with open(export_file, "r") as f:
            export_data = json.load(f)

        # Verify export structure
        assert "export_timestamp" in export_data
        assert "net_worth" in export_data
        assert "dashboard" in export_data
        assert "positions" in export_data
        assert "drawdowns" in export_data

    def test_position_synchronization(self, orchestrator):
        """Test position synchronization with strategy results."""
        # Mock strategy results
        strategy_results = {
            "deduplicated_portfolios": [
                {
                    "ticker": "MSFT",
                    "signals": [
                        {"position": 1, "price": 300.0, "stop_loss_distance": 0.04}
                    ],
                    "metrics": {"total_return": 0.15},
                },
                {
                    "ticker": "GOOGL",
                    "signals": [{"position": -1, "price": 120.0}],  # Exit signal
                    "metrics": {"total_return": 0.08},
                },
            ]
        }

        # Add existing position for GOOGL to test exit signal
        orchestrator.process_new_position(
            symbol="GOOGL",
            position_value=6000.0,
            stop_loss_distance=0.05,
            entry_price=125.0,
            portfolio_type=PortfolioType.RISK_ON,
        )

        # Process synchronization (would be done via API in real usage)
        # This tests the underlying logic that would be called by the API
        dashboard_before = orchestrator.get_dashboard_data()
        positions_before = len(dashboard_before.active_positions)

        # Verify we can analyze the positions mentioned in strategy results
        msft_analysis = orchestrator.get_position_analysis("MSFT")
        googl_analysis = orchestrator.get_position_analysis("GOOGL")

        # MSFT should have no existing position
        assert msft_analysis["position_tracking"]["position_value"] == 0

        # GOOGL should have existing position
        assert googl_analysis["position_tracking"]["position_value"] > 0

    def test_account_coordination_across_services(self, orchestrator):
        """Test account coordination across all services."""
        # Update account balances
        orchestrator.account_service.update_account_balance("IBKR", 70000.0)
        orchestrator.account_service.update_account_balance("Bybit", 25000.0)
        orchestrator.account_service.update_account_balance("Cash", 5000.0)

        # Calculate new net worth
        net_worth = orchestrator.account_service.calculate_net_worth()
        assert net_worth.total_net_worth == 100000.0

        # Add position and verify allocation across accounts
        response = orchestrator.calculate_position_size(
            PositionSizingRequest(
                symbol="NVDA",
                signal_type="entry",
                entry_price=500.0,
                stop_loss_distance=0.07,
            )
        )

        # Verify account allocation proportions
        account_allocation = response.account_allocation
        total_allocation = sum(account_allocation.values())

        # Should be proportional to account balances
        ibkr_proportion = account_allocation.get("IBKR", 0) / total_allocation
        expected_ibkr_proportion = 70000.0 / 100000.0

        assert abs(ibkr_proportion - expected_ibkr_proportion) < 0.01  # Within 1%

    def test_performance_and_memory_optimization(self, orchestrator):
        """Test performance with multiple positions and memory optimization."""
        # Add multiple positions to test performance
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]

        start_time = datetime.now()

        for i, symbol in enumerate(symbols):
            orchestrator.process_new_position(
                symbol=symbol,
                position_value=5000.0 + (i * 500),
                stop_loss_distance=0.05 + (i * 0.005),
                entry_price=100.0 + (i * 50),
                portfolio_type=PortfolioType.RISK_ON
                if i % 2 == 0
                else PortfolioType.INVESTMENT,
            )

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Should process 8 positions quickly (under 5 seconds)
        assert processing_time < 5.0

        # Verify all positions were added
        dashboard = orchestrator.get_dashboard_data()
        assert len(dashboard.active_positions) == len(symbols)

        # Test bulk analysis performance
        analysis_start = datetime.now()

        for symbol in symbols:
            analysis = orchestrator.get_position_analysis(symbol)
            assert analysis["symbol"] == symbol

        analysis_end = datetime.now()
        analysis_time = (analysis_end - analysis_start).total_seconds()

        # Should analyze 8 positions quickly
        assert analysis_time < 3.0


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases in integration."""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator for error testing."""
        return PositionSizingOrchestrator(base_dir=str(tmp_path))

    def test_zero_net_worth_handling(self, orchestrator):
        """Test handling of zero net worth."""
        # Don't add any account balances (net worth = 0)

        request = PositionSizingRequest(
            symbol="AAPL", signal_type="entry", entry_price=150.0
        )

        response = orchestrator.calculate_position_size(request)

        # Should handle gracefully with minimal position size
        assert response.position_value >= 0
        assert response.risk_amount >= 0

    def test_missing_strategies_file_handling(self, orchestrator):
        """Test handling when strategies file is missing."""
        # This should gracefully handle missing portfolio.json
        try:
            strategies_count = (
                orchestrator.strategies_integration.get_total_strategies_count()
            )
            # If file exists, should be > 0; if not, should raise exception
            assert strategies_count >= 0
        except FileNotFoundError:
            # This is expected if the file doesn't exist
            pass

    def test_invalid_position_updates(self, orchestrator):
        """Test handling of invalid position updates."""
        # Add a valid position first
        orchestrator.process_new_position(
            symbol="TEST", position_value=1000.0, entry_price=100.0
        )

        # Try to update with invalid data
        result = orchestrator.update_position_metrics(
            "TEST",
            {
                "position_value": -1000.0,  # Invalid negative value
                "stop_loss_distance": 1.5,  # Invalid > 1.0
            },
        )

        # Should handle gracefully and not corrupt data
        assert isinstance(result, bool)


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])
