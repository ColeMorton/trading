"""
Integration tests for strategy sweep with metric types.

Tests the complete flow of saving and retrieving strategy sweep results
with metric type classifications through the repository layer.
"""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.database.config import get_db_manager
from app.database.strategy_sweep_repository import StrategySweepRepository


# Mark all tests in this module as requiring database
pytestmark = pytest.mark.asyncio


@pytest.fixture
def db_manager():
    """Get the database manager instance."""
    # DatabaseManager reads connection info from environment variables
    # No arguments needed
    return get_db_manager()


@pytest.fixture
def repository(db_manager):
    """Create a repository instance."""
    return StrategySweepRepository(db_manager)


@pytest.fixture
def sample_sweep_results():
    """Sample sweep results with metric type classifications."""
    return [
        {
            "Ticker": "BTC-USD",
            "Strategy": "SMA_20_50",
            "Fast Period": 20,
            "Slow Period": 50,
            "Total Trades": 100,
            "Win Rate [%]": 65.5,
            "Sharpe Ratio": 1.85,
            "Total Return [%]": 125.3,
            "Score": 8.5,
            "Metric Type": "Most Sharpe Ratio, Most Total Return [%]",
        },
        {
            "Ticker": "ETH-USD",
            "Strategy": "EMA_15_45",
            "Fast Period": 15,
            "Slow Period": 45,
            "Total Trades": 85,
            "Win Rate [%]": 62.0,
            "Sharpe Ratio": 1.65,
            "Total Return [%]": 98.2,
            "Score": 7.8,
            "Metric Type": "Median Win Rate [%]",
        },
        {
            "Ticker": "AAPL",
            "Strategy": "SMA_10_30",
            "Fast Period": 10,
            "Slow Period": 30,
            "Total Trades": 120,
            "Win Rate [%]": 58.5,
            "Sharpe Ratio": 1.42,
            "Total Return [%]": 75.8,
            "Score": 7.2,
            "Metric Type": "Most Total Trades",
        },
    ]


@pytest.mark.unit
class TestMetricTypeIntegration:
    """Integration tests for metric type functionality."""

    @pytest.fixture(autouse=True)
    def setup_database_url(self, monkeypatch):
        """Set up DATABASE_URL environment variable for tests."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")

    def test_parse_metric_type_integration(self):
        """Test metric type parsing with various formats."""
        mock_db_manager = Mock()
        repository = StrategySweepRepository(mock_db_manager)

        # Single metric type
        result = repository._parse_metric_type_string("Most Sharpe Ratio")
        assert result == ["Most Sharpe Ratio"]

        # Multiple metric types
        result = repository._parse_metric_type_string(
            "Most Sharpe Ratio, Most Total Return [%]",
        )
        assert result == ["Most Sharpe Ratio", "Most Total Return [%]"]

        # Empty string
        result = repository._parse_metric_type_string("")
        assert result == []

        # None
        result = repository._parse_metric_type_string(None)
        assert result == []

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_save_and_retrieve_with_metrics(
        self,
        repository,
        sample_sweep_results,
    ):
        """Test saving sweep results with metric types and retrieving them."""
        sweep_run_id = uuid4()
        sweep_config = {
            "tickers": ["BTC-USD", "ETH-USD", "AAPL"],
            "strategy_types": ["SMA", "EMA"],
            "fast_min": 10,
            "fast_max": 20,
            "slow_min": 30,
            "slow_max": 50,
        }

        # Save results with metric types
        inserted_count = await repository.save_sweep_results_with_metrics(
            sweep_run_id,
            sample_sweep_results,
            sweep_config,
        )

        assert inserted_count == len(sample_sweep_results)

        # Retrieve results with metric types
        results = await repository.get_sweep_results_with_metrics(sweep_run_id)

        assert len(results) == len(sample_sweep_results)

        # Verify metric types were saved and retrieved
        btc_result = next(r for r in results if r["ticker"] == "BTC-USD")
        assert "metric_types" in btc_result

        metric_names = [mt["name"] for mt in btc_result["metric_types"]]
        assert "Most Sharpe Ratio" in metric_names
        assert "Most Total Return [%]" in metric_names

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_find_by_metric_type(self, repository, sample_sweep_results):
        """Test finding results by specific metric type."""
        sweep_run_id = uuid4()
        sweep_config = {"tickers": ["BTC-USD", "ETH-USD", "AAPL"]}

        # Save results
        await repository.save_sweep_results_with_metrics(
            sweep_run_id,
            sample_sweep_results,
            sweep_config,
        )

        # Find results with "Most Sharpe Ratio"
        results = await repository.find_results_by_metric_type(
            "Most Sharpe Ratio",
            sweep_run_id,
        )

        assert len(results) > 0
        assert all(r["ticker"] == "BTC-USD" for r in results)

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_get_all_metric_types(self, repository):
        """Test retrieving all available metric types."""
        metric_types = await repository.get_all_metric_types()

        assert len(metric_types) > 0

        # Check structure
        for mt in metric_types:
            assert "id" in mt
            assert "name" in mt
            assert "category" in mt
            assert "description" in mt

        # Check for expected types
        names = [mt["name"] for mt in metric_types]
        assert "Most Sharpe Ratio" in names
        assert "Most Total Return [%]" in names
        assert "Median Win Rate [%]" in names

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_backward_compatibility(self, repository):
        """Test that old metric_type string column still works."""
        sweep_run_id = uuid4()
        sweep_config = {"tickers": ["TEST"]}

        # Create result with old string format
        old_format_result = [
            {
                "Ticker": "TEST",
                "Strategy": "SMA_20_50",
                "Fast Period": 20,
                "Slow Period": 50,
                "Score": 7.5,
                "Metric Type": "Most Sharpe Ratio, Most Total Return [%]",
            },
        ]

        # Save using new method (should populate both string and junction table)
        await repository.save_sweep_results_with_metrics(
            sweep_run_id,
            old_format_result,
            sweep_config,
        )

        # Retrieve and verify both representations exist
        results = await repository.get_sweep_results_with_metrics(sweep_run_id)

        assert len(results) == 1
        result = results[0]

        # Old string column should still be populated
        assert result["metric_type"] == "Most Sharpe Ratio, Most Total Return [%]"

        # New metric_types array should also be populated
        assert "metric_types" in result
        assert len(result["metric_types"]) == 2


@pytest.mark.unit
class TestDataMigration:
    """Test data migration from old string format to new relational format."""

    @pytest.fixture(autouse=True)
    def setup_database_url(self, monkeypatch):
        """Set up DATABASE_URL environment variable for tests."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_migration_existing_data(self, repository):
        """Test that migration correctly converts existing string data."""
        # This test would verify that the migration in 003_create_metric_types_table.py
        # correctly parses existing metric_type strings and populates the junction table

        sweep_run_id = uuid4()

        # Simulate old data that already exists in database
        # (In real test, this would query actual pre-migration data)

        # After migration, verify junction table was populated
        results = await repository.get_sweep_results_with_metrics(sweep_run_id)

        # Should have metric_types array populated from junction table
        for result in results:
            if result.get("metric_type"):
                assert "metric_types" in result
                assert len(result["metric_types"]) > 0


@pytest.mark.unit
class TestComplexScenarios:
    """Test complex scenarios with metric types."""

    @pytest.fixture(autouse=True)
    def setup_database_url(self, monkeypatch):
        """Set up DATABASE_URL environment variable for tests."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_multiple_results_same_metric_type(self, repository):
        """Test multiple results sharing the same metric type."""
        sweep_run_id = uuid4()
        sweep_config = {"tickers": ["BTC-USD", "ETH-USD"]}

        results = [
            {
                "Ticker": "BTC-USD",
                "Strategy": "SMA_20_50",
                "Score": 8.5,
                "Metric Type": "Most Sharpe Ratio",
            },
            {
                "Ticker": "ETH-USD",
                "Strategy": "SMA_20_50",
                "Score": 8.3,
                "Metric Type": "Most Sharpe Ratio",
            },
        ]

        await repository.save_sweep_results_with_metrics(
            sweep_run_id,
            results,
            sweep_config,
        )

        # Find all results with "Most Sharpe Ratio"
        sharpe_results = await repository.find_results_by_metric_type(
            "Most Sharpe Ratio",
            sweep_run_id,
        )

        assert len(sharpe_results) == 2

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_result_with_no_metric_types(self, repository):
        """Test handling results with no metric type classifications."""
        sweep_run_id = uuid4()
        sweep_config = {"tickers": ["TEST"]}

        results = [
            {
                "Ticker": "TEST",
                "Strategy": "SMA_20_50",
                "Score": 7.0,
                "Metric Type": "",  # Empty string
            },
        ]

        await repository.save_sweep_results_with_metrics(
            sweep_run_id,
            results,
            sweep_config,
        )

        retrieved = await repository.get_sweep_results_with_metrics(sweep_run_id)

        assert len(retrieved) == 1
        # Should have empty metric_types array
        assert retrieved[0]["metric_types"] == []

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_result_with_many_metric_types(self, repository):
        """Test result with many metric type classifications."""
        sweep_run_id = uuid4()
        sweep_config = {"tickers": ["BTC-USD"]}

        results = [
            {
                "Ticker": "BTC-USD",
                "Strategy": "SMA_20_50",
                "Score": 9.5,
                "Metric Type": (
                    "Most Sharpe Ratio, Most Total Return [%], "
                    "Most Win Rate [%], Most Profit Factor, "
                    "Median Total Trades"
                ),
            },
        ]

        await repository.save_sweep_results_with_metrics(
            sweep_run_id,
            results,
            sweep_config,
        )

        retrieved = await repository.get_sweep_results_with_metrics(sweep_run_id)

        assert len(retrieved) == 1
        assert len(retrieved[0]["metric_types"]) == 5

    @pytest.mark.skip(reason="Requires live database connection")
    async def test_duplicate_prevention(self, repository):
        """Test that duplicate metric type assignments are prevented."""
        sweep_run_id = uuid4()
        sweep_config = {"tickers": ["TEST"]}

        # Result with duplicate metric type in string (edge case)
        results = [
            {
                "Ticker": "TEST",
                "Strategy": "SMA_20_50",
                "Score": 7.5,
                "Metric Type": "Most Sharpe Ratio, Most Sharpe Ratio",  # Duplicate
            },
        ]

        await repository.save_sweep_results_with_metrics(
            sweep_run_id,
            results,
            sweep_config,
        )

        retrieved = await repository.get_sweep_results_with_metrics(sweep_run_id)

        # Should only have one instance despite duplicate in string
        metric_names = [mt["name"] for mt in retrieved[0]["metric_types"]]
        assert metric_names.count("Most Sharpe Ratio") == 1


@pytest.mark.unit
class TestQueryPerformance:
    """Test query performance with metric types."""

    @pytest.fixture(autouse=True)
    def setup_database_url(self, monkeypatch):
        """Set up DATABASE_URL environment variable for tests."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")

    @pytest.mark.skip(reason="Requires live database connection and large dataset")
    async def test_query_performance_large_dataset(self, repository):
        """Test query performance with large number of results."""
        import time

        sweep_run_id = uuid4()
        sweep_config = {"tickers": ["MANY"]}

        # Create large dataset (1000+ results)
        large_results = []
        for i in range(1000):
            large_results.append(
                {
                    "Ticker": f"TICKER_{i}",
                    "Strategy": "SMA_20_50",
                    "Score": 7.0 + (i % 20) / 10,
                    "Metric Type": (
                        "Most Sharpe Ratio" if i % 3 == 0 else "Most Total Return [%]"
                    ),
                },
            )

        # Measure save time
        start = time.time()
        await repository.save_sweep_results_with_metrics(
            sweep_run_id,
            large_results,
            sweep_config,
        )
        save_time = time.time() - start

        # Should complete in reasonable time (adjust threshold as needed)
        assert save_time < 30.0, f"Save took too long: {save_time}s"

        # Measure retrieval time
        start = time.time()
        results = await repository.get_sweep_results_with_metrics(sweep_run_id)
        retrieve_time = time.time() - start

        assert retrieve_time < 10.0, f"Retrieve took too long: {retrieve_time}s"
        assert len(results) == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
