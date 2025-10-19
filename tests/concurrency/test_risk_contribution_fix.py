"""
Unit tests for the fixed risk contribution calculator.

These tests verify that the new implementation correctly calculates
risk contributions that sum to 100%.
"""

import numpy as np
import polars as pl
import pytest

from app.concurrency.tools.risk_contribution_calculator import (
    RiskContributionCalculator,
    calculate_risk_contributions_fixed,
)


class TestRiskContributionCalculator:
    """Test suite for the fixed risk contribution calculator."""

    def test_risk_contributions_sum_to_one(self):
        """Test that risk contributions always sum to 100%."""
        # Create test data
        n_periods = 100
        n_strategies = 3

        # Generate random returns
        np.random.seed(42)
        returns = np.random.randn(n_periods, n_strategies) * 0.01

        # Test with equal weights
        weights = np.array([1 / 3, 1 / 3, 1 / 3])
        strategy_names = ["Strategy_A", "Strategy_B", "Strategy_C"]

        calculator = RiskContributionCalculator()
        metrics = calculator.calculate_portfolio_metrics(
            returns, weights, strategy_names
        )

        # Extract risk contribution percentages
        risk_contribs = [
            metrics["risk_contributions"][name]["risk_contribution_pct"]
            for name in strategy_names
        ]

        # Assert sum equals 1.0
        total = sum(risk_contribs)
        assert np.isclose(
            total, 1.0, rtol=1e-5
        ), f"Risk contributions sum to {total}, expected 1.0"

    def test_risk_contributions_with_correlation(self):
        """Test risk contributions with known correlation structure."""
        # Create perfectly correlated assets
        n_periods = 252
        base_returns = np.random.randn(n_periods) * 0.01

        # Three assets with different volatilities but perfect correlation
        returns = np.column_stack(
            [
                base_returns * 1.0,  # Vol = 1x
                base_returns * 2.0,  # Vol = 2x
                base_returns * 3.0,  # Vol = 3x
            ]
        )

        weights = np.array([0.5, 0.3, 0.2])
        strategy_names = ["Low_Vol", "Med_Vol", "High_Vol"]

        calculator = RiskContributionCalculator()
        metrics = calculator.calculate_portfolio_metrics(
            returns, weights, strategy_names
        )

        # With perfect correlation, risk contributions should be proportional to
        # weight * volatility
        risk_contribs = {
            name: metrics["risk_contributions"][name]["risk_contribution_pct"]
            for name in strategy_names
        }

        # Verify sum to 1.0
        assert np.isclose(sum(risk_contribs.values()), 1.0, rtol=1e-5)

        # Verify relative proportions match weight * volatility
        # For perfect correlation: RC_i ∝ w_i * σ_i
        expected_proportions = weights * np.array([1.0, 2.0, 3.0])
        expected_proportions = expected_proportions / np.sum(expected_proportions)

        actual_proportions = np.array([risk_contribs[name] for name in strategy_names])

        # Check proportions are close (within 1%)
        np.testing.assert_allclose(actual_proportions, expected_proportions, rtol=0.01)

    def test_risk_contributions_uncorrelated(self):
        """Test risk contributions with uncorrelated assets."""
        n_periods = 1000
        n_strategies = 4

        # Generate independent returns
        np.random.seed(123)
        returns = np.random.randn(n_periods, n_strategies) * 0.01

        # Different weights
        weights = np.array([0.4, 0.3, 0.2, 0.1])
        strategy_names = [f"Strategy_{i+1}" for i in range(n_strategies)]

        calculator = RiskContributionCalculator()
        metrics = calculator.calculate_portfolio_metrics(
            returns, weights, strategy_names
        )

        # Verify sum to 1.0
        risk_contribs = [
            metrics["risk_contributions"][name]["risk_contribution_pct"]
            for name in strategy_names
        ]
        total = sum(risk_contribs)
        assert np.isclose(total, 1.0, rtol=1e-5)

        # With uncorrelated assets of equal volatility,
        # risk contributions should be close to weights squared normalized
        # This is because RC_i ≈ w_i² * σ_i² / Σ(w_j² * σ_j²)
        # Verify all contributions are positive
        assert all(contrib > 0 for contrib in risk_contribs)

    def test_single_strategy(self):
        """Test edge case with single strategy."""
        n_periods = 100
        returns = np.random.randn(n_periods, 1) * 0.01
        weights = np.array([1.0])
        strategy_names = ["Only_Strategy"]

        calculator = RiskContributionCalculator()
        metrics = calculator.calculate_portfolio_metrics(
            returns, weights, strategy_names
        )

        # Single strategy should have 100% risk contribution
        risk_contrib = metrics["risk_contributions"]["Only_Strategy"][
            "risk_contribution_pct"
        ]
        assert np.isclose(risk_contrib, 1.0, rtol=1e-5)

    def test_validate_risk_contributions(self):
        """Test the validation function."""
        calculator = RiskContributionCalculator()

        # Valid contributions
        valid_contribs = {"A": 0.3, "B": 0.5, "C": 0.2}
        is_valid, msg = calculator.validate_risk_contributions(valid_contribs)
        assert is_valid
        assert "valid" in msg.lower()

        # Invalid contributions
        invalid_contribs = {"A": 0.3, "B": 0.5, "C": 0.5}  # Sum = 1.3
        is_valid, msg = calculator.validate_risk_contributions(invalid_contribs)
        assert not is_valid
        assert "invalid" in msg.lower()
        assert "130.00%" in msg

    def test_calculate_from_dataframes(self):
        """Test calculation from position arrays and dataframes."""
        n_periods = 100
        n_strategies = 3

        # Create mock dataframes with price data
        data_list = []
        position_arrays = []

        np.random.seed(456)
        for i in range(n_strategies):
            # Generate price series
            returns = np.random.randn(n_periods) * 0.01
            prices = 100 * np.exp(np.cumsum(returns))

            # Create position array (1 = long, 0 = no position)
            positions = np.random.choice([0, 1], size=n_periods, p=[0.3, 0.7])
            position_arrays.append(positions)

            # Create dataframe with required columns: Date, Close, Position
            import datetime

            start_date = datetime.date(2024, 1, 1)
            dates = [start_date + datetime.timedelta(days=j) for j in range(n_periods)]
            df = pl.DataFrame({"Date": dates, "Close": prices, "Position": positions})
            data_list.append(df)

        # Allocations
        strategy_allocations = [40.0, 35.0, 25.0]
        strategy_names = ["Strat_A", "Strat_B", "Strat_C"]

        # Calculate risk metrics
        risk_metrics = (
            RiskContributionCalculator.calculate_risk_metrics_from_dataframes(
                position_arrays, data_list, strategy_allocations, strategy_names
            )
        )

        # Verify risk contributions sum to 1.0
        risk_contribs = [
            risk_metrics["risk_contributions"][name]["risk_contribution_pct"]
            for name in strategy_names
        ]
        total = sum(risk_contribs)
        assert np.isclose(total, 1.0, rtol=1e-5)

        # Verify all required fields are present
        assert "portfolio_volatility" in risk_metrics
        assert "portfolio_variance" in risk_metrics
        assert "total_risk_contribution" in risk_metrics

        # Verify VaR/CVaR metrics are calculated
        for i in range(n_strategies):
            assert f"strategy_{i+1}_var_95" in risk_metrics
            assert f"strategy_{i+1}_cvar_95" in risk_metrics
            assert f"strategy_{i+1}_var_99" in risk_metrics
            assert f"strategy_{i+1}_cvar_99" in risk_metrics

    def test_fixed_implementation_always_used(self):
        """Test that the fixed implementation is always used (no feature flag)."""
        n_periods = 50
        n_strategies = 2

        # Create mock data
        data_list = []
        position_arrays = []

        for _i in range(n_strategies):
            prices = 100 + np.cumsum(np.random.randn(n_periods) * 0.5)
            positions = np.ones(n_periods)
            position_arrays.append(positions)

            # Create dataframe with required columns: Date, Close, Position
            import datetime

            start_date = datetime.date(2024, 1, 1)
            dates = [start_date + datetime.timedelta(days=j) for j in range(n_periods)]
            df = pl.DataFrame({"Date": dates, "Close": prices, "Position": positions})
            data_list.append(df)

        strategy_allocations = [50.0, 50.0]

        # Mock logging function
        logs = []

        def mock_log(msg, level):
            logs.append((msg, level))

        # Test that fixed implementation is always used
        result = calculate_risk_contributions_fixed(
            position_arrays, data_list, strategy_allocations, mock_log
        )

        # Check logs indicate fixed usage
        assert any("fixed" in log[0].lower() for log in logs)

        # Verify risk contributions sum correctly with fixed implementation
        risk_contribs = [v for k, v in result.items() if k.endswith("_risk_contrib")]
        if risk_contribs:
            total = sum(risk_contribs)
            # With fixed implementation, should be close to 1.0
            assert np.isclose(
                total, 1.0, rtol=0.01
            ), f"Risk contributions sum to {total*100:.2f}%"

    def test_extreme_allocations(self):
        """Test with extreme allocation weights."""
        n_periods = 100
        n_strategies = 3

        np.random.seed(789)
        returns = np.random.randn(n_periods, n_strategies) * 0.01

        # Extreme weights (one strategy dominates)
        weights = np.array([0.95, 0.04, 0.01])
        strategy_names = ["Dominant", "Small", "Tiny"]

        calculator = RiskContributionCalculator()
        metrics = calculator.calculate_portfolio_metrics(
            returns, weights, strategy_names
        )

        # Verify sum to 1.0
        risk_contribs = [
            metrics["risk_contributions"][name]["risk_contribution_pct"]
            for name in strategy_names
        ]
        total = sum(risk_contribs)
        assert np.isclose(total, 1.0, rtol=1e-5)

        # Dominant strategy should have highest risk contribution
        assert risk_contribs[0] > risk_contribs[1]
        assert risk_contribs[1] > risk_contribs[2]

    def test_zero_returns(self):
        """Test with zero returns (no volatility)."""
        n_periods = 100
        n_strategies = 2

        # All returns are zero
        returns = np.zeros((n_periods, n_strategies))
        weights = np.array([0.6, 0.4])
        strategy_names = ["A", "B"]

        calculator = RiskContributionCalculator()
        metrics = calculator.calculate_portfolio_metrics(
            returns, weights, strategy_names
        )

        # With zero returns, portfolio volatility should be zero
        assert metrics["portfolio_volatility"] == 0.0

        # Risk contributions might be NaN or 0, but should be handled gracefully
        risk_contribs = [
            metrics["risk_contributions"][name]["risk_contribution_pct"]
            for name in strategy_names
        ]

        # Should either be all zeros or properly normalized
        if not all(np.isnan(contrib) for contrib in risk_contribs):
            total = sum(risk_contribs)
            assert np.isclose(total, 1.0, rtol=1e-5) or total == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
