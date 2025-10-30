"""
Unit tests for best portfolio selection functionality.

Tests the SelectionAlgorithm and SweepBestSelection models,
along with the BestSelectionService logic.
"""

from uuid import uuid4

import pytest

from app.cli.services.best_selection_service import BestSelectionService
from app.database.models import SelectionAlgorithm, SweepBestSelection


class TestSelectionAlgorithmModel:
    """Test SelectionAlgorithm SQLAlchemy model."""

    def test_selection_algorithm_creation(self):
        """Test creating a SelectionAlgorithm instance."""
        algorithm = SelectionAlgorithm(
            algorithm_code="top_3_all_match",
            algorithm_name="Top 3 All Match",
            description="All top 3 results have same parameter combination",
            min_confidence=100.00,
            max_confidence=100.00,
        )

        assert algorithm.algorithm_code == "top_3_all_match"
        assert algorithm.algorithm_name == "Top 3 All Match"
        assert float(algorithm.min_confidence) == 100.00
        assert float(algorithm.max_confidence) == 100.00

    def test_selection_algorithm_to_dict(self):
        """Test SelectionAlgorithm to_dict() method."""
        algorithm = SelectionAlgorithm(
            id=1,
            algorithm_code="top_5_3_of_5",
            algorithm_name="Top 5 - 3 of 5 Match",
            description="3 out of top 5 match",
            min_confidence=60.00,
            max_confidence=80.00,
        )

        result = algorithm.to_dict()

        assert result["id"] == 1
        assert result["algorithm_code"] == "top_5_3_of_5"
        assert result["algorithm_name"] == "Top 5 - 3 of 5 Match"
        assert result["min_confidence"] == 60.00
        assert result["max_confidence"] == 80.00


class TestSweepBestSelectionModel:
    """Test SweepBestSelection SQLAlchemy model."""

    def test_best_selection_creation(self):
        """Test creating a SweepBestSelection instance."""
        sweep_run_id = uuid4()
        best_result_id = uuid4()

        selection = SweepBestSelection(
            sweep_run_id=sweep_run_id,
            ticker_id=1,
            strategy_type="SMA",
            best_result_id=best_result_id,
            selection_algorithm="parameter_consistency",
            selection_criteria="top_3_all_match",
            confidence_score=100.00,
            alternatives_considered=50,
            winning_fast_period=20,
            winning_slow_period=50,
            result_score=8.5,
            result_sharpe_ratio=1.85,
        )

        assert selection.sweep_run_id == sweep_run_id
        assert selection.ticker_id == 1
        assert selection.strategy_type == "SMA"
        assert selection.best_result_id == best_result_id
        assert selection.selection_criteria == "top_3_all_match"
        assert float(selection.confidence_score) == 100.00
        assert selection.winning_fast_period == 20
        assert selection.winning_slow_period == 50

    def test_best_selection_to_dict(self):
        """Test SweepBestSelection to_dict() method."""
        from datetime import datetime

        sweep_run_id = uuid4()
        best_result_id = uuid4()

        selection = SweepBestSelection(
            id=1,
            sweep_run_id=sweep_run_id,
            ticker_id=5,
            strategy_type="EMA",
            best_result_id=best_result_id,
            selection_algorithm="parameter_consistency",
            selection_criteria="top_5_3_of_5",
            confidence_score=60.00,
            alternatives_considered=25,
            winning_fast_period=15,
            winning_slow_period=45,
            winning_signal_period=9,
            result_score=7.8,
            result_sharpe_ratio=1.65,
            result_total_return_pct=95.2,
            result_win_rate_pct=62.5,
            created_at=datetime(2025, 10, 19, 12, 0, 0),
        )

        result = selection.to_dict()

        assert result["id"] == 1
        assert result["ticker_id"] == 5
        assert result["strategy_type"] == "EMA"
        assert result["selection_criteria"] == "top_5_3_of_5"
        assert result["confidence_score"] == 60.00
        assert result["winning_fast_period"] == 15
        assert result["winning_slow_period"] == 45
        assert result["winning_signal_period"] == 9
        assert result["result_score"] == 7.8


class TestBestSelectionService:
    """Test BestSelectionService logic."""

    @pytest.fixture
    def service(self):
        """Create BestSelectionService instance."""
        return BestSelectionService()

    @pytest.fixture
    def sample_results(self):
        """Sample sweep results for testing."""
        return [
            # Top 3 all have same 20/50 combination
            {
                "id": str(uuid4()),
                "ticker": "BTC-USD",
                "strategy_type": "SMA",
                "fast_period": 20,
                "slow_period": 50,
                "signal_period": None,
                "score": 8.5,
                "sharpe_ratio": 1.85,
                "total_return_pct": 125.3,
                "win_rate_pct": 65.5,
            },
            {
                "id": str(uuid4()),
                "ticker": "BTC-USD",
                "strategy_type": "SMA",
                "fast_period": 20,
                "slow_period": 50,
                "signal_period": None,
                "score": 8.3,
                "sharpe_ratio": 1.80,
                "total_return_pct": 120.0,
                "win_rate_pct": 64.0,
            },
            {
                "id": str(uuid4()),
                "ticker": "BTC-USD",
                "strategy_type": "SMA",
                "fast_period": 20,
                "slow_period": 50,
                "signal_period": None,
                "score": 8.2,
                "sharpe_ratio": 1.78,
                "total_return_pct": 118.5,
                "win_rate_pct": 63.5,
            },
            # Different combination
            {
                "id": str(uuid4()),
                "ticker": "BTC-USD",
                "strategy_type": "SMA",
                "fast_period": 15,
                "slow_period": 45,
                "signal_period": None,
                "score": 7.8,
                "sharpe_ratio": 1.65,
                "total_return_pct": 110.0,
                "win_rate_pct": 62.0,
            },
        ]

    def test_get_parameter_combination(self, service):
        """Test extracting parameter combination from result."""
        result = {
            "fast_period": 20,
            "slow_period": 50,
            "signal_period": 9,
        }

        combo = service._get_parameter_combination(result)

        assert combo == (20, 50, 9)

    def test_top_3_all_match(self, service, sample_results):
        """Test finding best when top 3 all match."""
        selection = service.find_best_for_ticker_strategy(
            sample_results,
            "BTC-USD",
            "SMA",
        )

        assert selection is not None
        assert selection["selection_criteria"] == "top_3_all_match"
        assert selection["confidence_score"] == 100.00
        assert selection["winning_combination"] == (20, 50, None)
        assert selection["alternatives_considered"] == 4
        assert float(selection["best_result"]["score"]) == 8.5

    def test_no_match_fallback(self, service):
        """Test fallback to highest score when no pattern found."""
        # All different combinations
        results = [
            {
                "id": str(uuid4()),
                "ticker": "ETH-USD",
                "strategy_type": "EMA",
                "fast_period": 10,
                "slow_period": 30,
                "signal_period": None,
                "score": 7.5,
                "sharpe_ratio": 1.50,
                "total_return_pct": 95.0,
                "win_rate_pct": 58.0,
            },
            {
                "id": str(uuid4()),
                "ticker": "ETH-USD",
                "strategy_type": "EMA",
                "fast_period": 15,
                "slow_period": 45,
                "signal_period": None,
                "score": 7.3,
                "sharpe_ratio": 1.48,
                "total_return_pct": 92.0,
                "win_rate_pct": 57.5,
            },
        ]

        selection = service.find_best_for_ticker_strategy(results, "ETH-USD", "EMA")

        assert selection is not None
        assert selection["selection_criteria"] == "highest_score_fallback"
        assert selection["confidence_score"] == 25.00
        assert float(selection["best_result"]["score"]) == 7.5

    def test_empty_results(self, service):
        """Test handling empty results list."""
        selection = service.find_best_for_ticker_strategy([], "AAPL", "SMA")

        assert selection is None

    def test_filter_by_ticker_and_strategy(self, service):
        """Test filtering to specific ticker and strategy."""
        results = [
            {
                "id": str(uuid4()),
                "ticker": "BTC-USD",
                "strategy_type": "SMA",
                "fast_period": 20,
                "slow_period": 50,
                "score": 8.5,
            },
            {
                "id": str(uuid4()),
                "ticker": "ETH-USD",  # Different ticker
                "strategy_type": "SMA",
                "fast_period": 20,
                "slow_period": 50,
                "score": 8.0,
            },
            {
                "id": str(uuid4()),
                "ticker": "BTC-USD",
                "strategy_type": "EMA",  # Different strategy
                "fast_period": 20,
                "slow_period": 50,
                "score": 7.5,
            },
        ]

        # Should only consider BTC-USD + SMA
        selection = service.find_best_for_ticker_strategy(results, "BTC-USD", "SMA")

        assert selection is not None
        assert selection["best_result"]["ticker"] == "BTC-USD"
        assert selection["best_result"]["strategy_type"] == "SMA"
        assert selection["alternatives_considered"] == 1  # Only 1 BTC-USD SMA result


class TestSelectionAlgorithmSeedData:
    """Test selection algorithm seed data."""

    def test_seed_data_structure(self):
        """Test that seed data has correct structure."""
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "migration_005",
            "/Users/colemorton/Projects/trading/app/database/migrations/versions/005_create_best_selections_table.py",
        )
        migration_module = importlib.util.module_from_spec(spec)
        sys.modules["migration_005"] = migration_module
        spec.loader.exec_module(migration_module)

        selection_algorithms = migration_module.selection_algorithms

        assert len(selection_algorithms) > 0

        for item in selection_algorithms:
            assert len(item) == 5, f"Expected 5 elements, got {len(item)}"
            code, name, desc, min_conf, max_conf = item
            assert isinstance(code, str) and code
            assert isinstance(name, str) and name
            assert isinstance(desc, str)
            assert isinstance(min_conf, int | float)
            assert isinstance(max_conf, int | float)
            assert 0 <= min_conf <= 100
            assert 0 <= max_conf <= 100
            assert min_conf <= max_conf

    def test_seed_data_unique_codes(self):
        """Test that all algorithm codes are unique."""
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "migration_005",
            "/Users/colemorton/Projects/trading/app/database/migrations/versions/005_create_best_selections_table.py",
        )
        migration_module = importlib.util.module_from_spec(spec)
        sys.modules["migration_005"] = migration_module
        spec.loader.exec_module(migration_module)

        selection_algorithms = migration_module.selection_algorithms

        codes = [item[0] for item in selection_algorithms]
        unique_codes = set(codes)

        assert len(codes) == len(unique_codes), "Duplicate algorithm codes found"

    def test_seed_data_expected_algorithms(self):
        """Test that expected algorithms are present."""
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "migration_005",
            "/Users/colemorton/Projects/trading/app/database/migrations/versions/005_create_best_selections_table.py",
        )
        migration_module = importlib.util.module_from_spec(spec)
        sys.modules["migration_005"] = migration_module
        spec.loader.exec_module(migration_module)

        selection_algorithms = migration_module.selection_algorithms

        codes = [item[0] for item in selection_algorithms]

        expected = [
            "top_3_all_match",
            "top_5_3_of_5",
            "top_8_5_of_8",
            "top_2_both_match",
            "highest_score_fallback",
        ]

        for expected_code in expected:
            assert expected_code in codes, (
                f"Expected algorithm '{expected_code}' not found"
            )


class TestParameterConsistencyAlgorithm:
    """Test parameter consistency detection algorithm."""

    @pytest.fixture
    def service(self):
        return BestSelectionService()

    def test_check_top_3_all_match_success(self, service):
        """Test successful top 3 all match detection."""
        results = [
            {"fast_period": 20, "slow_period": 50, "signal_period": None, "score": 8.5},
            {"fast_period": 20, "slow_period": 50, "signal_period": None, "score": 8.3},
            {"fast_period": 20, "slow_period": 50, "signal_period": None, "score": 8.2},
        ]

        result = service._check_top_n_all_match(results, 3)

        assert result is not None
        assert result["combination"] == (20, 50, None)
        assert result["best_result"]["score"] == 8.5

    def test_check_top_3_all_match_failure(self, service):
        """Test top 3 match detection when they don't match."""
        results = [
            {"fast_period": 20, "slow_period": 50, "signal_period": None, "score": 8.5},
            {"fast_period": 15, "slow_period": 45, "signal_period": None, "score": 8.3},
            {"fast_period": 10, "slow_period": 30, "signal_period": None, "score": 8.2},
        ]

        result = service._check_top_n_all_match(results, 3)

        assert result is None

    def test_check_top_n_k_match_success(self, service):
        """Test successful K of N match detection."""
        results = [
            {"fast_period": 20, "slow_period": 50, "signal_period": None, "score": 8.5},
            {"fast_period": 20, "slow_period": 50, "signal_period": None, "score": 8.3},
            {"fast_period": 15, "slow_period": 45, "signal_period": None, "score": 8.2},
            {"fast_period": 20, "slow_period": 50, "signal_period": None, "score": 8.0},
            {"fast_period": 10, "slow_period": 30, "signal_period": None, "score": 7.8},
        ]

        # 3 of 5 have 20/50 combination
        result = service._check_top_n_k_match(results, 5, 3)

        assert result is not None
        assert result["combination"] == (20, 50, None)
        assert result["match_count"] == 3
        assert result["best_result"]["score"] == 8.5  # Highest with that combo

    def test_check_top_n_k_match_failure(self, service):
        """Test K of N match when threshold not met."""
        results = [
            {"fast_period": 20, "slow_period": 50, "signal_period": None, "score": 8.5},
            {"fast_period": 15, "slow_period": 45, "signal_period": None, "score": 8.3},
            {"fast_period": 10, "slow_period": 30, "signal_period": None, "score": 8.2},
            {"fast_period": 25, "slow_period": 55, "signal_period": None, "score": 8.0},
            {"fast_period": 12, "slow_period": 35, "signal_period": None, "score": 7.8},
        ]

        # No combination appears 3+ times
        result = service._check_top_n_k_match(results, 5, 3)

        assert result is None

    def test_macd_with_signal_period(self, service):
        """Test parameter combination extraction for MACD strategy."""
        results = [
            {
                "ticker": "BTC-USD",
                "strategy_type": "MACD",
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9,
                "score": 8.0,
            },
            {
                "ticker": "BTC-USD",
                "strategy_type": "MACD",
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9,
                "score": 7.9,
            },
        ]

        selection = service.find_best_for_ticker_strategy(results, "BTC-USD", "MACD")

        assert selection is not None
        assert selection["winning_combination"] == (12, 26, 9)
        assert selection["selection_criteria"] == "top_2_both_match"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
