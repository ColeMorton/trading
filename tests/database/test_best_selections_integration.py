"""
Integration tests for best portfolio selection with database.

Tests the complete flow of computing, saving, and retrieving best selections
through the repository layer with actual database operations.
"""

from uuid import uuid4

import pytest

from app.database.config import get_db_manager
from app.database.strategy_sweep_repository import StrategySweepRepository


# Mark all tests in this module as requiring database
pytestmark = pytest.mark.asyncio


@pytest.fixture
def db_manager():
    """Get the database manager instance."""
    return get_db_manager()


@pytest.fixture
def repository(db_manager):
    """Create a repository instance."""
    return StrategySweepRepository(db_manager)


@pytest.fixture
def sample_sweep_results_for_best():
    """Sample sweep results with patterns for best selection testing."""
    base_id_1 = str(uuid4())
    base_id_2 = str(uuid4())
    base_id_3 = str(uuid4())
    base_id_4 = str(uuid4())

    return [
        # BTC-USD SMA: Top 3 all have 20/50 (perfect match)
        {
            "id": base_id_1,
            "Ticker": "BTC-USD",
            "Strategy": "SMA",
            "Fast Period": 20,
            "Slow Period": 50,
            "Score": 8.5,
            "Sharpe Ratio": 1.85,
            "Total Return [%]": 125.3,
            "Win Rate [%]": 65.5,
            "Metric Type": "Most Sharpe Ratio, Most Total Return [%]",
        },
        {
            "id": base_id_2,
            "Ticker": "BTC-USD",
            "Strategy": "SMA",
            "Fast Period": 20,
            "Slow Period": 50,
            "Score": 8.3,
            "Sharpe Ratio": 1.80,
            "Total Return [%]": 120.0,
            "Win Rate [%]": 64.0,
            "Metric Type": "Median Win Rate [%]",
        },
        {
            "id": base_id_3,
            "Ticker": "BTC-USD",
            "Strategy": "SMA",
            "Fast Period": 20,
            "Slow Period": 50,
            "Score": 8.2,
            "Sharpe Ratio": 1.78,
            "Total Return [%]": 118.5,
            "Win Rate [%]": 63.5,
            "Metric Type": "",
        },
        # Different combination (lower score)
        {
            "id": base_id_4,
            "Ticker": "BTC-USD",
            "Strategy": "SMA",
            "Fast Period": 15,
            "Slow Period": 45,
            "Score": 7.8,
            "Sharpe Ratio": 1.65,
            "Total Return [%]": 110.0,
            "Win Rate [%]": 62.0,
            "Metric Type": "",
        },
    ]


@pytest.mark.unit
class TestBestSelectionIntegration:
    """Integration tests for best selection functionality."""

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_compute_and_save_best_selections(
        self,
        repository,
        sample_sweep_results_for_best,
    ):
        """Test computing and saving best selections."""
        sweep_run_id = uuid4()
        sweep_config = {
            "tickers": ["BTC-USD"],
            "strategy_types": ["SMA"],
        }

        # Save sweep results first
        await repository.save_sweep_results_with_metrics(
            sweep_run_id,
            sample_sweep_results_for_best,
            sweep_config,
        )

        # Compute and save best selections
        count = await repository.compute_and_save_best_selections(sweep_run_id)

        assert count == 1  # One ticker+strategy combination

        # Retrieve best selections
        selections = await repository.get_best_selections(sweep_run_id)

        assert len(selections) == 1
        selection = selections[0]

        assert selection["ticker"] == "BTC-USD"
        assert selection["strategy_type"] == "SMA"
        assert selection["selection_criteria"] == "top_3_all_match"
        assert float(selection["confidence_score"]) == 100.00
        assert selection["winning_fast_period"] == 20
        assert selection["winning_slow_period"] == 50
        assert float(selection["result_score"]) == 8.5

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_get_best_result_for_ticker(
        self,
        repository,
        sample_sweep_results_for_best,
    ):
        """Test retrieving best result for specific ticker."""
        sweep_run_id = uuid4()
        sweep_config = {"tickers": ["BTC-USD"]}

        # Save and compute
        await repository.save_sweep_results_with_metrics(
            sweep_run_id,
            sample_sweep_results_for_best,
            sweep_config,
        )
        await repository.compute_and_save_best_selections(sweep_run_id)

        # Get best for ticker
        best = await repository.get_best_result_for_ticker(
            sweep_run_id,
            "BTC-USD",
            "SMA",
        )

        assert best is not None
        assert best["ticker"] == "BTC-USD"
        assert float(best["score"]) == 8.5
        assert best["selection_criteria"] == "top_3_all_match"

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_get_sweep_results_with_best_flag(
        self,
        repository,
        sample_sweep_results_for_best,
    ):
        """Test retrieving all results with is_best flag."""
        sweep_run_id = uuid4()
        sweep_config = {"tickers": ["BTC-USD"]}

        # Save and compute
        await repository.save_sweep_results_with_metrics(
            sweep_run_id,
            sample_sweep_results_for_best,
            sweep_config,
        )
        await repository.compute_and_save_best_selections(sweep_run_id)

        # Get all results with best flag
        results = await repository.get_sweep_results_with_best_flag(sweep_run_id)

        assert len(results) == 4  # All 4 original results

        # Check that exactly one is marked as best
        best_results = [r for r in results if r["is_best"]]
        assert len(best_results) == 1
        assert float(best_results[0]["score"]) == 8.5

        # Check that others are not marked as best
        non_best_results = [r for r in results if not r["is_best"]]
        assert len(non_best_results) == 3

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_multiple_ticker_strategy_combinations(self, repository):
        """Test best selection with multiple tickers and strategies."""
        sweep_run_id = uuid4()

        results = []
        # Add results for multiple combinations
        for ticker in ["BTC-USD", "ETH-USD"]:
            for strategy in ["SMA", "EMA"]:
                for i in range(3):
                    results.append(
                        {
                            "id": str(uuid4()),
                            "Ticker": ticker,
                            "Strategy": strategy,
                            "Fast Period": 20,
                            "Slow Period": 50,
                            "Score": 8.0 - (i * 0.1),
                            "Sharpe Ratio": 1.70 - (i * 0.05),
                            "Total Return [%]": 100.0 - (i * 5),
                            "Win Rate [%]": 60.0,
                            "Metric Type": "",
                        },
                    )

        sweep_config = {"tickers": ["BTC-USD", "ETH-USD"]}

        # Save and compute
        await repository.save_sweep_results_with_metrics(
            sweep_run_id,
            results,
            sweep_config,
        )
        count = await repository.compute_and_save_best_selections(sweep_run_id)

        # Should have 4 best selections (2 tickers x 2 strategies)
        assert count == 4

        # Verify each has top_3_all_match (all have same 20/50 combination)
        selections = await repository.get_best_selections(sweep_run_id)
        assert len(selections) == 4

        for selection in selections:
            assert selection["selection_criteria"] == "top_3_all_match"
            assert float(selection["confidence_score"]) == 100.00

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_unique_constraint_enforcement(self, repository):
        """Test that unique constraint prevents duplicate best selections."""
        sweep_run_id = uuid4()

        results = [
            {
                "id": str(uuid4()),
                "Ticker": "AAPL",
                "Strategy": "SMA",
                "Fast Period": 20,
                "Slow Period": 50,
                "Score": 8.0,
                "Metric Type": "",
            },
        ]

        sweep_config = {"tickers": ["AAPL"]}

        await repository.save_sweep_results_with_metrics(
            sweep_run_id,
            results,
            sweep_config,
        )

        # Compute twice - should not fail, should upsert
        count1 = await repository.compute_and_save_best_selections(sweep_run_id)
        count2 = await repository.compute_and_save_best_selections(sweep_run_id)

        assert count1 == 1
        assert count2 == 1  # Same count, just updated

        # Should still only have one selection
        selections = await repository.get_best_selections(sweep_run_id)
        assert len(selections) == 1

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_cascade_delete(self, repository):
        """Test that deleting sweep result cascades to best selection."""
        # This test would verify CASCADE delete behavior
        # when a sweep result is deleted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
