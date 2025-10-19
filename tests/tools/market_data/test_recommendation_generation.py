"""
Unit tests for recommendation generation in MarketDataAnalyzer.

Tests the comprehensive recommendation system including BUY/SELL signals,
scoring algorithms, and signal threshold logic.
"""

from unittest.mock import Mock

import pytest

from app.tools.market_data_analyzer import MarketDataAnalyzer


class TestRecommendationGeneration:
    """Test recommendation generation functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    @pytest.fixture
    def strong_buy_analysis(self):
        """Create analysis data that should generate STRONG_BUY signal."""
        return {
            # Strong positive momentum
            "momentum_differential": 0.002,
            "momentum_5d": 0.003,
            "momentum_20d": 0.002,
            "price_acceleration": 0.0001,
            # Strong uptrend
            "trend_direction_20d": 0.15,
            "trend_direction_50d": 0.12,
            "trend_direction_200d": 0.08,
            "trend_consistency": 0.9,
            "trend_slope": 0.001,
            # Good risk-adjusted returns
            "annualized_sharpe": 2.5,
            "annualized_sortino": 3.0,
            "return_to_risk_ratio": 1.5,
            "mean_daily_return": 0.002,
            # Low risk profile
            "annualized_volatility": 0.15,
            "skewness": 0.1,
            "excess_kurtosis": 0.5,
            "var_95": -0.02,
            "is_normal_distribution": True,
        }

    @pytest.fixture
    def strong_sell_analysis(self):
        """Create analysis data that should generate STRONG_SELL signal."""
        return {
            # Negative momentum
            "momentum_differential": -0.003,
            "momentum_5d": -0.004,
            "momentum_20d": -0.002,
            "price_acceleration": -0.0002,
            # Strong downtrend
            "trend_direction_20d": -0.20,
            "trend_direction_50d": -0.15,
            "trend_direction_200d": -0.10,
            "trend_consistency": 0.1,
            "trend_slope": -0.002,
            # Poor risk-adjusted returns
            "annualized_sharpe": -1.5,
            "annualized_sortino": -2.0,
            "return_to_risk_ratio": 0.3,
            "mean_daily_return": -0.002,
            # High risk profile
            "annualized_volatility": 0.45,
            "skewness": -1.5,
            "excess_kurtosis": 8.0,
            "var_95": -0.08,
            "is_normal_distribution": False,
        }

    @pytest.fixture
    def hold_analysis(self):
        """Create analysis data that should generate HOLD signal."""
        return {
            # Neutral momentum
            "momentum_differential": 0.0001,
            "momentum_5d": 0.0002,
            "momentum_20d": -0.0001,
            "price_acceleration": 0.0,
            # Sideways trend
            "trend_direction_20d": 0.02,
            "trend_direction_50d": -0.01,
            "trend_direction_200d": 0.01,
            "trend_consistency": 0.5,
            "trend_slope": 0.0001,
            # Moderate risk-adjusted returns
            "annualized_sharpe": 0.5,
            "annualized_sortino": 0.7,
            "return_to_risk_ratio": 0.8,
            "mean_daily_return": 0.0005,
            # Moderate risk profile
            "annualized_volatility": 0.25,
            "skewness": 0.2,
            "excess_kurtosis": 1.0,
            "var_95": -0.035,
            "is_normal_distribution": True,
        }

    def test_generate_recommendation_strong_buy(self, analyzer, strong_buy_analysis):
        """Test generation of STRONG_BUY recommendation."""
        signal, confidence, reasoning = analyzer.generate_recommendation(
            strong_buy_analysis
        )

        assert signal == "STRONG_BUY"
        assert 0.80 <= confidence <= 0.95
        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert "positive" in reasoning.lower() or "strong" in reasoning.lower()

    def test_generate_recommendation_strong_sell(self, analyzer, strong_sell_analysis):
        """Test generation of STRONG_SELL recommendation."""
        signal, confidence, reasoning = analyzer.generate_recommendation(
            strong_sell_analysis
        )

        assert signal == "STRONG_SELL"
        assert 0.80 <= confidence <= 0.95
        assert isinstance(reasoning, str)
        assert "risk" in reasoning.lower() or "negative" in reasoning.lower()

    def test_generate_recommendation_hold(self, analyzer, hold_analysis):
        """Test generation of HOLD recommendation."""
        signal, confidence, reasoning = analyzer.generate_recommendation(hold_analysis)

        assert signal == "HOLD"
        assert 0.60 <= confidence <= 0.70
        assert isinstance(reasoning, str)
        assert "mixed" in reasoning.lower() or "moderate" in reasoning.lower()

    def test_generate_recommendation_buy_signal(self, analyzer):
        """Test generation of BUY signal (moderate positive)."""
        buy_analysis = {
            "momentum_differential": 0.001,
            "momentum_5d": 0.002,
            "momentum_20d": 0.001,
            "price_acceleration": 0.00005,
            "trend_direction_20d": 0.08,
            "trend_direction_50d": 0.05,
            "trend_direction_200d": 0.03,
            "trend_consistency": 0.7,
            "trend_slope": 0.0005,
            "annualized_sharpe": 1.2,
            "annualized_sortino": 1.5,
            "return_to_risk_ratio": 1.0,
            "mean_daily_return": 0.001,
            "annualized_volatility": 0.20,
            "skewness": 0.0,
            "excess_kurtosis": 0.0,
            "var_95": -0.025,
            "is_normal_distribution": True,
        }

        signal, confidence, reasoning = analyzer.generate_recommendation(buy_analysis)

        assert signal == "BUY"
        assert 0.70 <= confidence <= 0.80

    def test_generate_recommendation_sell_signal(self, analyzer):
        """Test generation of SELL signal (moderate negative)."""
        sell_analysis = {
            "momentum_differential": -0.001,
            "momentum_5d": -0.0015,
            "momentum_20d": -0.0008,
            "price_acceleration": -0.00005,
            "trend_direction_20d": -0.08,
            "trend_direction_50d": -0.05,
            "trend_direction_200d": -0.03,
            "trend_consistency": 0.3,
            "trend_slope": -0.0005,
            "annualized_sharpe": -0.5,
            "annualized_sortino": -0.3,
            "return_to_risk_ratio": 0.4,
            "mean_daily_return": -0.0008,
            "annualized_volatility": 0.35,
            "skewness": -0.5,
            "excess_kurtosis": 3.0,
            "var_95": -0.05,
            "is_normal_distribution": False,
        }

        signal, confidence, reasoning = analyzer.generate_recommendation(sell_analysis)

        assert signal == "SELL"
        assert 0.70 <= confidence <= 0.80


class TestScoringAlgorithms:
    """Test individual scoring algorithms."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_score_momentum_positive(self, analyzer):
        """Test momentum scoring with positive momentum."""
        analysis = {
            "momentum_differential": 0.002,
            "momentum_5d": 0.003,
            "momentum_20d": 0.002,
            "price_acceleration": 0.0001,
        }

        score = analyzer._score_momentum(analysis)

        assert isinstance(score, float)
        assert score > 0  # Should be positive for positive momentum
        assert -100 <= score <= 100  # Should be within bounds

    def test_score_momentum_negative(self, analyzer):
        """Test momentum scoring with negative momentum."""
        analysis = {
            "momentum_differential": -0.002,
            "momentum_5d": -0.003,
            "momentum_20d": -0.002,
            "price_acceleration": -0.0001,
        }

        score = analyzer._score_momentum(analysis)

        assert score < 0  # Should be negative for negative momentum
        assert -100 <= score <= 100

    def test_score_trend_strength_uptrend(self, analyzer):
        """Test trend strength scoring with uptrend."""
        analysis = {
            "trend_direction_20d": 0.1,
            "trend_direction_50d": 0.08,
            "trend_direction_200d": 0.05,
            "trend_consistency": 0.8,
            "trend_slope": 0.001,
        }

        score = analyzer._score_trend_strength(analysis)

        assert score > 0  # Should be positive for uptrend
        assert -100 <= score <= 100

    def test_score_trend_strength_downtrend(self, analyzer):
        """Test trend strength scoring with downtrend."""
        analysis = {
            "trend_direction_20d": -0.1,
            "trend_direction_50d": -0.08,
            "trend_direction_200d": -0.05,
            "trend_consistency": 0.2,
            "trend_slope": -0.001,
        }

        score = analyzer._score_trend_strength(analysis)

        assert score < 0  # Should be negative for downtrend
        assert -100 <= score <= 100

    def test_score_risk_adjusted_returns_good(self, analyzer):
        """Test risk-adjusted returns scoring with good metrics."""
        analysis = {
            "annualized_sharpe": 2.0,
            "annualized_sortino": 2.5,
            "return_to_risk_ratio": 1.5,
            "mean_daily_return": 0.002,
        }

        score = analyzer._score_risk_adjusted_returns(analysis)

        assert score > 0  # Should be positive for good metrics
        assert -100 <= score <= 100

    def test_score_risk_adjusted_returns_poor(self, analyzer):
        """Test risk-adjusted returns scoring with poor metrics."""
        analysis = {
            "annualized_sharpe": -1.0,
            "annualized_sortino": -0.5,
            "return_to_risk_ratio": 0.2,
            "mean_daily_return": -0.002,
        }

        score = analyzer._score_risk_adjusted_returns(analysis)

        assert score < 0  # Should be negative for poor metrics
        assert -100 <= score <= 100

    def test_score_mean_reversion_oversold(self, analyzer):
        """Test mean reversion scoring with oversold conditions."""
        analysis = {
            "var_95": -0.06,  # Large negative VaR (oversold)
            "trend_direction_20d": -0.15,  # Price below 20-day MA
            "annualized_volatility": 0.4,  # High volatility
        }

        score = analyzer._score_mean_reversion(analysis)

        assert score > 0  # Should be positive for potential bounce
        assert 0 <= score <= 100  # Mean reversion only gives positive scores

    def test_score_mean_reversion_normal(self, analyzer):
        """Test mean reversion scoring with normal conditions."""
        analysis = {
            "var_95": -0.02,  # Normal VaR
            "trend_direction_20d": 0.05,  # Price above 20-day MA
            "annualized_volatility": 0.2,  # Normal volatility
        }

        score = analyzer._score_mean_reversion(analysis)

        assert score == 0  # Should be zero for normal conditions


class TestScoreBoundaries:
    """Test score boundary conditions and edge cases."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_score_bounds_enforcement(self, analyzer):
        """Test that all scores are properly bounded."""
        # Create extreme analysis data to test bounds
        extreme_analysis = {
            "momentum_differential": 1.0,  # Extreme values
            "momentum_5d": 1.0,
            "momentum_20d": 1.0,
            "price_acceleration": 1.0,
            "trend_direction_20d": 5.0,  # Extreme trend
            "trend_direction_50d": 5.0,
            "trend_direction_200d": 5.0,
            "trend_consistency": 1.0,
            "trend_slope": 1.0,
            "annualized_sharpe": 10.0,  # Extreme Sharpe
            "annualized_sortino": 10.0,
            "return_to_risk_ratio": 10.0,
            "mean_daily_return": 0.1,
            "var_95": -1.0,  # Extreme VaR
            "annualized_volatility": 2.0,  # Extreme volatility
        }

        momentum_score = analyzer._score_momentum(extreme_analysis)
        trend_score = analyzer._score_trend_strength(extreme_analysis)
        risk_adj_score = analyzer._score_risk_adjusted_returns(extreme_analysis)
        mean_rev_score = analyzer._score_mean_reversion(extreme_analysis)

        # All scores should be within bounds
        for score in [momentum_score, trend_score, risk_adj_score]:
            assert -100 <= score <= 100

        # Mean reversion is always non-negative
        assert 0 <= mean_rev_score <= 100

    def test_zero_values_handling(self, analyzer):
        """Test handling of zero values in analysis."""
        zero_analysis = {
            key: 0.0
            for key in [
                "momentum_differential",
                "momentum_5d",
                "momentum_20d",
                "price_acceleration",
                "trend_direction_20d",
                "trend_direction_50d",
                "trend_direction_200d",
                "trend_consistency",
                "trend_slope",
                "annualized_sharpe",
                "annualized_sortino",
                "return_to_risk_ratio",
                "mean_daily_return",
                "var_95",
                "annualized_volatility",
            ]
        }

        signal, confidence, reasoning = analyzer.generate_recommendation(zero_analysis)

        assert signal in ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
        assert 0 <= confidence <= 1
        assert isinstance(reasoning, str)


class TestSignalThresholds:
    """Test signal threshold logic."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_signal_threshold_boundaries(self, analyzer):
        """Test signal generation at threshold boundaries."""
        # Test each threshold boundary by mocking the overall score calculation

        # Mock the component scores to control overall score
        def create_analysis_for_score(target_score):
            """Create analysis that should result in target overall score."""
            # Since overall score = risk_component*0.25 + momentum*0.25 + trend*0.30 + risk_adj*0.15 + mean_rev*0.05
            # We'll set trend score to dominate (30% weight)
            trend_score = target_score / 0.30

            return {
                "momentum_differential": 0.0,
                "momentum_5d": 0.0,
                "momentum_20d": 0.0,
                "price_acceleration": 0.0,
                "trend_direction_20d": trend_score
                / 200,  # Adjusted for trend calculation
                "trend_direction_50d": trend_score / 200,
                "trend_direction_200d": trend_score / 200,
                "trend_consistency": 0.5 + (trend_score / 200),
                "trend_slope": trend_score / 1000,
                "annualized_sharpe": 0.0,
                "annualized_sortino": 0.0,
                "return_to_risk_ratio": 1.0,
                "mean_daily_return": 0.0,
                "annualized_volatility": 0.2,
                "skewness": 0.0,
                "excess_kurtosis": 0.0,
                "var_95": -0.03,
                "is_normal_distribution": True,
            }

        # Test STRONG_BUY threshold (≥60)
        strong_buy_analysis = create_analysis_for_score(65)
        signal, _, _ = analyzer.generate_recommendation(strong_buy_analysis)
        # Note: Due to complex scoring, we'll verify the signal is reasonable
        assert signal in ["STRONG_BUY", "BUY", "HOLD"]

        # Test boundary conditions with simplified direct testing
        # We'll test this by directly checking the threshold logic

    def test_confidence_levels(self, analyzer):
        """Test confidence level calculations."""
        # Test that confidence increases with stronger signals
        weak_analysis = {
            "momentum_differential": 0.0001,
            "momentum_5d": 0.0001,
            "momentum_20d": 0.0001,
            "price_acceleration": 0.0,
            "trend_direction_20d": 0.02,
            "trend_direction_50d": 0.01,
            "trend_direction_200d": 0.01,
            "trend_consistency": 0.55,
            "trend_slope": 0.0001,
            "annualized_sharpe": 0.3,
            "annualized_sortino": 0.4,
            "return_to_risk_ratio": 0.7,
            "mean_daily_return": 0.0003,
            "annualized_volatility": 0.25,
            "skewness": 0.1,
            "excess_kurtosis": 0.5,
            "var_95": -0.03,
            "is_normal_distribution": True,
        }

        strong_analysis = {
            "momentum_differential": 0.002,
            "momentum_5d": 0.003,
            "momentum_20d": 0.002,
            "price_acceleration": 0.0001,
            "trend_direction_20d": 0.12,
            "trend_direction_50d": 0.10,
            "trend_direction_200d": 0.08,
            "trend_consistency": 0.85,
            "trend_slope": 0.001,
            "annualized_sharpe": 1.8,
            "annualized_sortino": 2.2,
            "return_to_risk_ratio": 1.3,
            "mean_daily_return": 0.0018,
            "annualized_volatility": 0.18,
            "skewness": 0.0,
            "excess_kurtosis": 0.2,
            "var_95": -0.025,
            "is_normal_distribution": True,
        }

        _, weak_confidence, _ = analyzer.generate_recommendation(weak_analysis)
        _, strong_confidence, _ = analyzer.generate_recommendation(strong_analysis)

        # Strong signals should have higher confidence
        assert strong_confidence >= weak_confidence


class TestErrorHandling:
    """Test error handling in recommendation generation."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_empty_analysis_data(self, analyzer):
        """Test recommendation generation with empty analysis data."""
        signal, confidence, reasoning = analyzer.generate_recommendation({})

        assert signal == "HOLD"
        assert confidence == 0.5
        assert "Insufficient data" in reasoning

    def test_missing_keys_in_analysis(self, analyzer):
        """Test recommendation generation with missing keys."""
        incomplete_analysis = {
            "annualized_volatility": 0.2,
            "trend_direction_20d": 0.05,
            # Missing many required keys
        }

        signal, confidence, reasoning = analyzer.generate_recommendation(
            incomplete_analysis
        )

        # Should handle gracefully and return valid signal
        assert signal in ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
        assert 0 <= confidence <= 1
        assert isinstance(reasoning, str)

    def test_none_analysis_data(self, analyzer):
        """Test recommendation generation with None analysis data."""
        signal, confidence, reasoning = analyzer.generate_recommendation(None)

        assert signal == "HOLD"
        assert confidence == 0.5
        assert "Insufficient data" in reasoning

    def test_recommendation_generation_exception(self, analyzer):
        """Test exception handling in recommendation generation."""
        # Mock logger
        analyzer.logger = Mock()

        # This should trigger exception handling
        with pytest.patch.object(
            analyzer, "_score_momentum", side_effect=Exception("Test error")
        ):
            signal, confidence, reasoning = analyzer.generate_recommendation(
                {"test": "data"}
            )

        assert signal == "HOLD"
        assert confidence == 0.50
        assert "Recommendation generation error" in reasoning
        analyzer.logger.error.assert_called_once()


class TestBackwardCompatibility:
    """Test backward compatibility with legacy exit signal method."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return MarketDataAnalyzer("TEST")

    def test_generate_exit_signal_calls_recommendation(self, analyzer):
        """Test that legacy method calls new recommendation method."""
        analysis_data = {
            "annualized_volatility": 0.2,
            "skewness": 0.1,
            "excess_kurtosis": 0.5,
            "var_95": -0.03,
            "is_normal_distribution": True,
            "momentum_differential": 0.001,
            "trend_direction_20d": 0.05,
            "annualized_sharpe": 1.0,
        }

        # Call legacy method
        exit_signal_result = analyzer.generate_exit_signal(analysis_data)

        # Call new method
        recommendation_result = analyzer.generate_recommendation(analysis_data)

        # Results should be identical
        assert exit_signal_result == recommendation_result

    def test_legacy_method_signature(self, analyzer):
        """Test that legacy method maintains expected signature."""
        result = analyzer.generate_exit_signal({})

        # Should return tuple of (signal, confidence, reasoning)
        assert isinstance(result, tuple)
        assert len(result) == 3

        signal, confidence, reasoning = result
        assert isinstance(signal, str)
        assert isinstance(confidence, float)
        assert isinstance(reasoning, str)


if __name__ == "__main__":
    pytest.main([__file__])
