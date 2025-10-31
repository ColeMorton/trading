"""
Unit tests for metric types table and models.

Tests the metric_types reference table, junction table relationships,
and repository methods for handling metric type classifications.
"""

from uuid import uuid4

import pytest

from app.database.models import (
    MetricType,
    StrategySweepResult,
    StrategySweepResultMetric,
)


@pytest.mark.unit
class TestMetricTypeModel:
    """Test MetricType SQLAlchemy model."""

    def test_metric_type_creation(self):
        """Test creating a MetricType instance."""
        metric = MetricType(
            name="Most Sharpe Ratio",
            category="risk",
            description="Highest Sharpe ratio (risk-adjusted return)",
        )

        assert metric.name == "Most Sharpe Ratio"
        assert metric.category == "risk"
        assert metric.description == "Highest Sharpe ratio (risk-adjusted return)"

    def test_metric_type_to_dict(self):
        """Test MetricType to_dict() method."""
        from datetime import datetime

        metric = MetricType(
            id=1,
            name="Most Total Return [%]",
            category="return",
            description="Highest total return percentage",
            created_at=datetime(2025, 10, 19, 12, 0, 0),
        )

        result = metric.to_dict()

        assert result["id"] == 1
        assert result["name"] == "Most Total Return [%]"
        assert result["category"] == "return"
        assert result["description"] == "Highest total return percentage"
        assert result["created_at"] == "2025-10-19T12:00:00"

    def test_metric_type_repr(self):
        """Test MetricType __repr__ method."""
        metric = MetricType(id=1, name="Most Sharpe Ratio", category="risk")

        repr_str = repr(metric)

        assert "MetricType" in repr_str
        assert "id=1" in repr_str
        assert "Most Sharpe Ratio" in repr_str
        assert "risk" in repr_str


@pytest.mark.unit
class TestStrategySweepResultMetricModel:
    """Test StrategySweepResultMetric junction table model."""

    def test_junction_creation(self):
        """Test creating a junction table instance."""
        sweep_id = uuid4()

        junction = StrategySweepResultMetric(sweep_result_id=sweep_id, metric_type_id=1)

        assert junction.sweep_result_id == sweep_id
        assert junction.metric_type_id == 1

    def test_junction_repr(self):
        """Test junction table __repr__ method."""
        sweep_id = uuid4()

        junction = StrategySweepResultMetric(
            id=1,
            sweep_result_id=sweep_id,
            metric_type_id=5,
        )

        repr_str = repr(junction)

        assert "StrategySweepResultMetric" in repr_str
        assert "id=1" in repr_str
        assert str(sweep_id) in repr_str
        assert "metric_type_id=5" in repr_str


@pytest.mark.unit
class TestStrategySweepResultModel:
    """Test StrategySweepResult model with metric type relationships."""

    def test_sweep_result_creation(self):
        """Test creating a StrategySweepResult instance."""
        sweep_run_id = uuid4()

        result = StrategySweepResult(
            sweep_run_id=sweep_run_id,
            ticker_id=1,  # Changed from ticker string to ticker_id integer
            strategy_type_id=1,  # Use strategy_type_id instead of strategy_type
            fast_period=20,
            slow_period=50,
            score=8.5,
            win_rate_pct=65.5,
            total_trades=100,
        )

        assert result.sweep_run_id == sweep_run_id
        assert result.ticker_id == 1  # Changed from ticker to ticker_id
        assert result.strategy_type_id == 1
        assert result.fast_period == 20
        assert result.slow_period == 50
        assert float(result.score) == 8.5
        assert float(result.win_rate_pct) == 65.5
        assert result.total_trades == 100

    def test_sweep_result_repr(self):
        """Test StrategySweepResult __repr__ method."""
        sweep_run_id = uuid4()
        result_id = uuid4()

        result = StrategySweepResult(
            id=result_id,
            sweep_run_id=sweep_run_id,
            ticker_id=2,  # Changed from ticker string to ticker_id integer
            strategy_type_id=2,  # Use strategy_type_id instead of strategy_type
            score=7.2,
        )

        repr_str = repr(result)

        assert "StrategySweepResult" in repr_str
        assert str(result_id) in repr_str


@pytest.mark.unit
class TestMetricTypeRepository:
    """Test repository methods for metric types."""

    @pytest.fixture(autouse=True)
    def setup_database_url(self, monkeypatch):
        """Set up DATABASE_URL environment variable for tests."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")

    def test_parse_metric_type_string_single(self):
        """Test parsing single metric type."""
        from app.database.config import DatabaseManager
        from app.database.strategy_sweep_repository import StrategySweepRepository

        db_manager = DatabaseManager()
        repo = StrategySweepRepository(db_manager)

        result = repo._parse_metric_type_string("Most Sharpe Ratio")

        assert result == ["Most Sharpe Ratio"]

    def test_parse_metric_type_string_multiple(self):
        """Test parsing multiple metric types."""
        from app.database.config import DatabaseManager
        from app.database.strategy_sweep_repository import StrategySweepRepository

        db_manager = DatabaseManager()
        repo = StrategySweepRepository(db_manager)

        result = repo._parse_metric_type_string(
            "Most Sharpe Ratio, Most Total Return [%]",
        )

        assert result == ["Most Sharpe Ratio", "Most Total Return [%]"]

    def test_parse_metric_type_string_with_whitespace(self):
        """Test parsing metric types with extra whitespace."""
        from app.database.config import DatabaseManager
        from app.database.strategy_sweep_repository import StrategySweepRepository

        db_manager = DatabaseManager()
        repo = StrategySweepRepository(db_manager)

        result = repo._parse_metric_type_string(
            "  Most Sharpe Ratio  ,  Most Total Return [%]  ",
        )

        assert result == ["Most Sharpe Ratio", "Most Total Return [%]"]

    def test_parse_metric_type_string_empty(self):
        """Test parsing empty metric type string."""
        from app.database.config import DatabaseManager
        from app.database.strategy_sweep_repository import StrategySweepRepository

        db_manager = DatabaseManager()
        repo = StrategySweepRepository(db_manager)

        result = repo._parse_metric_type_string("")
        assert result == []

        result = repo._parse_metric_type_string(None)
        assert result == []

        result = repo._parse_metric_type_string("   ")
        assert result == []

    def test_parse_metric_type_string_complex(self):
        """Test parsing complex metric type string with special characters."""
        from app.database.config import DatabaseManager
        from app.database.strategy_sweep_repository import StrategySweepRepository

        db_manager = DatabaseManager()
        repo = StrategySweepRepository(db_manager)

        result = repo._parse_metric_type_string(
            "Most Omega Ratio, Most Sharpe Ratio, Most Total Return [%], Median Win Rate [%]",
        )

        assert result == [
            "Most Omega Ratio",
            "Most Sharpe Ratio",
            "Most Total Return [%]",
            "Median Win Rate [%]",
        ]

    def test_parse_metric_type_string_with_empty_values(self):
        """Test parsing metric type string with empty comma-separated values."""
        from app.database.config import DatabaseManager
        from app.database.strategy_sweep_repository import StrategySweepRepository

        db_manager = DatabaseManager()
        repo = StrategySweepRepository(db_manager)

        result = repo._parse_metric_type_string(
            "Most Sharpe Ratio,,, Most Total Return [%]",
        )

        # Should filter out empty strings
        assert result == ["Most Sharpe Ratio", "Most Total Return [%]"]


@pytest.mark.unit
class TestMetricTypeSeedData:
    """Test that seed data constants are valid."""

    def test_seed_data_structure(self):
        """Test that seed data has correct structure."""
        import importlib.util
        import sys

        # Import migration module dynamically (can't use regular import due to numeric prefix)
        spec = importlib.util.spec_from_file_location(
            "migration_003",
            "/Users/colemorton/Projects/trading/app/database/migrations/versions/003_create_metric_types_table.py",
        )
        migration_module = importlib.util.module_from_spec(spec)
        sys.modules["migration_003"] = migration_module
        spec.loader.exec_module(migration_module)

        metric_types_seed_data = migration_module.metric_types_seed_data

        assert len(metric_types_seed_data) > 0

        for item in metric_types_seed_data:
            assert len(item) == 3, f"Expected 3 elements, got {len(item)} for {item}"
            name, category, description = item
            assert isinstance(name, str) and name, "Name must be non-empty string"
            assert isinstance(category, str), "Category must be string"
            assert isinstance(description, str), "Description must be string"

    def test_seed_data_unique_names(self):
        """Test that all seed data names are unique."""
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "migration_003",
            "/Users/colemorton/Projects/trading/app/database/migrations/versions/003_create_metric_types_table.py",
        )
        migration_module = importlib.util.module_from_spec(spec)
        sys.modules["migration_003"] = migration_module
        spec.loader.exec_module(migration_module)

        metric_types_seed_data = migration_module.metric_types_seed_data

        names = [item[0] for item in metric_types_seed_data]
        unique_names = set(names)

        assert len(names) == len(unique_names), "Duplicate metric type names found"

    def test_seed_data_categories(self):
        """Test that seed data uses valid categories."""
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "migration_003",
            "/Users/colemorton/Projects/trading/app/database/migrations/versions/003_create_metric_types_table.py",
        )
        migration_module = importlib.util.module_from_spec(spec)
        sys.modules["migration_003"] = migration_module
        spec.loader.exec_module(migration_module)

        metric_types_seed_data = migration_module.metric_types_seed_data

        valid_categories = {"return", "risk", "trade", "timing", "composite"}

        for name, category, _ in metric_types_seed_data:
            assert category in valid_categories, (
                f"Invalid category '{category}' for metric '{name}'. "
                f"Must be one of: {valid_categories}"
            )

    def test_seed_data_coverage(self):
        """Test that seed data includes expected metric types."""
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "migration_003",
            "/Users/colemorton/Projects/trading/app/database/migrations/versions/003_create_metric_types_table.py",
        )
        migration_module = importlib.util.module_from_spec(spec)
        sys.modules["migration_003"] = migration_module
        spec.loader.exec_module(migration_module)

        metric_types_seed_data = migration_module.metric_types_seed_data

        names = [item[0] for item in metric_types_seed_data]

        # Check for key metric types
        expected_metrics = [
            "Most Sharpe Ratio",
            "Most Total Return [%]",
            "Most Win Rate [%]",
            "Most Profit Factor",
            "Median Sharpe Ratio",
            "Mean Total Trades",
        ]

        for expected in expected_metrics:
            assert expected in names, (
                f"Expected metric type '{expected}' not found in seed data"
            )

    def test_seed_data_count(self):
        """Test that seed data has reasonable number of entries."""
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "migration_003",
            "/Users/colemorton/Projects/trading/app/database/migrations/versions/003_create_metric_types_table.py",
        )
        migration_module = importlib.util.module_from_spec(spec)
        sys.modules["migration_003"] = migration_module
        spec.loader.exec_module(migration_module)

        metric_types_seed_data = migration_module.metric_types_seed_data

        # Should have between 50-100 metric types based on plan
        assert 50 <= len(metric_types_seed_data) <= 100, (
            f"Expected 50-100 metric types, got {len(metric_types_seed_data)}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
