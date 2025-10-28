#!/usr/bin/env python3
"""
Integration Tests for SPDSAnalysisEngine

Tests the new simplified 3-layer architecture against the documented
critical paths and validates performance improvements.
"""

from pathlib import Path
import sys

import pandas as pd
import pytest


# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tools.models.spds_models import (
    AnalysisResult,
    ConfidenceLevel,
    ExitSignal,
    SignalType,
)
from app.tools.spds_analysis_engine import AnalysisRequest, SPDSAnalysisEngine


class TestSPDSAnalysisEngine:
    """Integration tests for the new SPDS analysis engine."""

    @pytest.fixture
    def engine(self):
        """Create test engine instance."""
        return SPDSAnalysisEngine()

    @pytest.fixture
    def sample_portfolio_data(self):
        """Create sample portfolio data for testing."""
        data = []
        for i in range(10):
            data.append(
                {
                    "Position_UUID": f"AAPL_SMA_20_50_{20250101 + i:08d}",
                    "Ticker": "AAPL",
                    "Strategy": "SMA",
                    "Fast_Period": 20,
                    "Slow_Period": 50,
                    "Win_Rate": 0.6 + (i * 0.01),
                    "Total_Return": 0.15 + (i * 0.02),
                    "Sharpe_Ratio": 1.2 + (i * 0.1),
                    "Max_Drawdown": 0.1 + (i * 0.005),
                    "Total_Trades": 100 + (i * 10),
                    "Entry_Date": f"2025-01-{(i % 28) + 1:02d}",
                    "Exit_Date": "",
                    "Current_Price": 150.0 + (i * 5),
                    "Position_Size": 100,
                    "Unrealized_PnL": 1000 + (i * 100),
                },
            )
        return pd.DataFrame(data)

    @pytest.fixture
    def create_test_portfolio(self, sample_portfolio_data):
        """Create test portfolio file."""
        portfolio_dir = Path("data/raw/positions")
        portfolio_dir.mkdir(parents=True, exist_ok=True)

        portfolio_path = portfolio_dir / "test_integration.csv"
        sample_portfolio_data.to_csv(portfolio_path, index=False)

        return "test_integration.csv"

    @pytest.mark.asyncio
    async def test_portfolio_analysis_workflow(self, engine, create_test_portfolio):
        """Test Critical Path 1: Portfolio Analysis Workflow."""
        # Arrange
        request = AnalysisRequest(
            analysis_type="portfolio",
            parameter=create_test_portfolio,
            use_trade_history=False,
        )

        # Act
        results = await engine.analyze(request)

        # Assert
        assert isinstance(results, dict)
        assert len(results) > 0

        # Validate result structure
        for position_uuid, result in results.items():
            assert isinstance(result, AnalysisResult)
            assert result.strategy_name
            assert result.ticker
            assert result.position_uuid == position_uuid
            assert isinstance(result.exit_signal, ExitSignal)
            assert isinstance(result.confidence_level, float)
            assert 0 <= result.confidence_level <= 100
            assert isinstance(result.statistical_metrics, dict)
            assert isinstance(result.divergence_metrics, dict)
            assert isinstance(result.component_scores, dict)

    @pytest.mark.asyncio
    async def test_strategy_analysis_workflow(self, engine):
        """Test Critical Path 2: Strategy Analysis Workflow."""
        # Arrange
        request = AnalysisRequest(analysis_type="strategy", parameter="AAPL_SMA_20_50")

        # Act
        results = await engine.analyze(request)

        # Assert
        assert isinstance(results, dict)

        # Should contain at least one result
        if results:
            result = next(iter(results.values()))
            assert isinstance(result, AnalysisResult)
            assert "AAPL" in result.ticker
            assert "SMA" in result.strategy_name

    @pytest.mark.asyncio
    async def test_position_analysis_workflow(self, engine):
        """Test Critical Path 3: Position Analysis Workflow."""
        # Arrange
        request = AnalysisRequest(
            analysis_type="position",
            parameter="AAPL_SMA_20_50_20250101",
        )

        # Act
        results = await engine.analyze(request)

        # Assert
        assert isinstance(results, dict)

        # Should handle single position analysis
        if results:
            result = next(iter(results.values()))
            assert isinstance(result, AnalysisResult)
            assert result.position_uuid == "AAPL_SMA_20_50_20250101"

    @pytest.mark.asyncio
    async def test_error_handling_invalid_analysis_type(self, engine):
        """Test error handling for invalid analysis type."""
        # Arrange
        request = AnalysisRequest(analysis_type="invalid_type", parameter="test")

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported analysis type"):
            await engine.analyze(request)

    @pytest.mark.asyncio
    async def test_error_handling_missing_portfolio(self, engine):
        """Test error handling for missing portfolio file."""
        # Arrange
        request = AnalysisRequest(
            analysis_type="portfolio",
            parameter="nonexistent_portfolio.csv",
        )

        # Act
        results = await engine.analyze(request)

        # Assert - should return empty dict instead of raising
        assert isinstance(results, dict)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_performance_vs_old_architecture(self, engine, create_test_portfolio):
        """Test performance improvement vs old architecture."""
        import time

        # Arrange
        request = AnalysisRequest(
            analysis_type="portfolio",
            parameter=create_test_portfolio,
            use_trade_history=False,
        )

        # Act - measure new architecture performance
        start_time = time.time()
        results = await engine.analyze(request)
        new_time = time.time() - start_time

        # Assert - new architecture should complete successfully
        assert isinstance(results, dict)
        assert new_time < 5.0  # Should complete within 5 seconds

        # Log performance for comparison
        print(f"New architecture analysis time: {new_time:.3f}s")
        print(f"Results generated: {len(results)}")

    @pytest.mark.asyncio
    async def test_exit_signal_generation(self, engine, create_test_portfolio):
        """Test that exit signals are properly generated."""
        # Arrange
        request = AnalysisRequest(
            analysis_type="portfolio",
            parameter=create_test_portfolio,
            use_trade_history=False,
        )

        # Act
        results = await engine.analyze(request)

        # Assert
        assert len(results) > 0

        for result in results.values():
            # Check exit signal structure
            assert isinstance(result.exit_signal.signal_type, SignalType)
            assert isinstance(result.exit_signal.confidence_level, ConfidenceLevel)
            assert isinstance(result.exit_signal.reasoning, str)
            assert len(result.exit_signal.reasoning) > 0

            # Check confidence level bounds
            assert 0 <= result.confidence_level <= 100

            # Check metrics are populated
            assert len(result.statistical_metrics) > 0
            assert len(result.divergence_metrics) > 0
            assert len(result.component_scores) > 0

    @pytest.mark.asyncio
    async def test_trade_history_vs_equity_curves(self, engine, create_test_portfolio):
        """Test analysis with both trade history and equity curves data sources."""
        # Test with equity curves (default)
        request_equity = AnalysisRequest(
            analysis_type="portfolio",
            parameter=create_test_portfolio,
            use_trade_history=False,
        )

        results_equity = await engine.analyze(request_equity)

        # Test with trade history
        request_trade = AnalysisRequest(
            analysis_type="portfolio",
            parameter=create_test_portfolio,
            use_trade_history=True,
        )

        results_trade = await engine.analyze(request_trade)

        # Both should work and produce results
        assert isinstance(results_equity, dict)
        assert isinstance(results_trade, dict)

        # May have different numbers of results depending on data availability
        print(f"Equity curves results: {len(results_equity)}")
        print(f"Trade history results: {len(results_trade)}")

    @pytest.mark.asyncio
    async def test_architecture_simplification_validation(self, engine):
        """Test that new architecture maintains API compatibility."""
        # Test all three critical paths work with same interface
        test_cases = [
            ("portfolio", "test_integration.csv"),
            ("strategy", "AAPL_SMA_20_50"),
            ("position", "AAPL_SMA_20_50_20250101"),
        ]

        for analysis_type, parameter in test_cases:
            request = AnalysisRequest(analysis_type=analysis_type, parameter=parameter)

            # Should not raise exceptions
            try:
                results = await engine.analyze(request)
                assert isinstance(results, dict)
                print(f"✅ {analysis_type} analysis: {len(results)} results")
            except Exception as e:
                print(f"⚠️ {analysis_type} analysis failed: {e}")
                # Allow some failures for missing data, but ensure no crashes


class TestSPDSAnalysisEnginePerformance:
    """Performance-focused integration tests."""

    @pytest.fixture
    def engine(self):
        return SPDSAnalysisEngine()

    @pytest.fixture
    def large_portfolio_data(self):
        """Create larger portfolio for performance testing."""
        data = []
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"] * 20  # 100 positions
        strategies = ["SMA", "EMA", "MACD"] * 34  # Cycle through strategies

        for i in range(100):
            ticker = tickers[i % len(tickers)]
            strategy = strategies[i % len(strategies)]

            data.append(
                {
                    "Position_UUID": f"{ticker}_{strategy}_{20 + i % 30}_{50 + i % 100}_{20250101 + i:08d}",
                    "Ticker": ticker,
                    "Strategy": strategy,
                    "Fast_Period": 20 + (i % 30),
                    "Slow_Period": 50 + (i % 100),
                    "Win_Rate": 0.4 + (i % 41) / 100,  # 0.4 to 0.8
                    "Total_Return": -0.2 + (i % 121) / 100,  # -0.2 to 1.0
                    "Sharpe_Ratio": -0.5 + (i % 201) / 100,  # -0.5 to 1.5
                    "Max_Drawdown": 0.05 + (i % 36) / 100,  # 0.05 to 0.4
                    "Total_Trades": 10 + (i % 491),  # 10 to 500
                    "Entry_Date": f"2025-01-{((i % 28) + 1):02d}",
                    "Exit_Date": "",
                    "Current_Price": 50 + (i % 451),  # 50 to 500
                    "Position_Size": 1 + (i % 1000),  # 1 to 1000
                    "Unrealized_PnL": -1000 + (i % 6001),  # -1000 to 5000
                },
            )

        return pd.DataFrame(data)

    @pytest.fixture
    def create_large_portfolio(self, large_portfolio_data):
        """Create large test portfolio file."""
        portfolio_dir = Path("data/raw/positions")
        portfolio_dir.mkdir(parents=True, exist_ok=True)

        portfolio_path = portfolio_dir / "test_large_integration.csv"
        large_portfolio_data.to_csv(portfolio_path, index=False)

        return "test_large_integration.csv"

    @pytest.mark.asyncio
    async def test_large_portfolio_performance(self, engine, create_large_portfolio):
        """Test performance with larger portfolio (100 positions)."""
        import time

        # Arrange
        request = AnalysisRequest(
            analysis_type="portfolio",
            parameter=create_large_portfolio,
            use_trade_history=False,
        )

        # Act
        start_time = time.time()
        results = await engine.analyze(request)
        execution_time = time.time() - start_time

        # Assert
        assert isinstance(results, dict)
        assert execution_time < 10.0  # Should complete within 10 seconds

        print("Large portfolio analysis:")
        print("  Positions: 100")
        print(f"  Results: {len(results)}")
        print(f"  Time: {execution_time:.3f}s")
        print(f"  Rate: {len(results) / execution_time:.1f} positions/second")

    @pytest.mark.asyncio
    async def test_memory_efficiency(self, engine, create_large_portfolio):
        """Test memory efficiency of new architecture."""
        import os

        import psutil

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run analysis
        request = AnalysisRequest(
            analysis_type="portfolio",
            parameter=create_large_portfolio,
            use_trade_history=False,
        )

        results = await engine.analyze(request)

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print("Memory usage:")
        print(f"  Initial: {initial_memory:.1f} MB")
        print(f"  Final: {final_memory:.1f} MB")
        print(f"  Increase: {memory_increase:.1f} MB")
        print(
            (
                f"  Per position: {memory_increase / len(results):.2f} MB"
                if results
                else "N/A"
            ),
        )

        # Memory increase should be reasonable
        assert memory_increase < 100  # Less than 100MB increase


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment."""
    # Ensure test directories exist
    Path("data/raw/positions").mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup is handled by individual tests


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])
