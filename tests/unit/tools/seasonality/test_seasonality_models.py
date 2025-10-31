"""Tests for seasonality data models.

CRITICAL: These tests verify Pydantic model validation to prevent
invalid configurations and data structures.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError


def get_models():
    """Late import to avoid circular dependency."""
    from app.cli.models.seasonality import (
        PatternType,
        SeasonalityConfig,
        SeasonalityPattern,
        SeasonalityResult,
    )

    return PatternType, SeasonalityPattern, SeasonalityResult, SeasonalityConfig


@pytest.mark.unit
class TestPatternTypeEnum:
    """Test PatternType enum."""

    def test_all_pattern_types_defined(self):
        """Test that all expected pattern types are defined."""
        pattern_type_cls, _, _, _ = get_models()

        expected_types = {"Monthly", "Weekly", "Quarterly", "DayOfMonth", "WeekOfYear"}

        actual_types = {pt.value for pt in pattern_type_cls}

        assert actual_types == expected_types

    def test_pattern_type_string_values(self):
        """Test pattern type string values are correct."""
        pattern_type_cls, _, _, _ = get_models()

        assert pattern_type_cls.MONTHLY.value == "Monthly"
        assert pattern_type_cls.WEEKLY.value == "Weekly"
        assert pattern_type_cls.QUARTERLY.value == "Quarterly"
        assert pattern_type_cls.DAY_OF_MONTH.value == "DayOfMonth"
        assert pattern_type_cls.WEEK_OF_YEAR.value == "WeekOfYear"


@pytest.mark.unit
class TestSeasonalityPatternModel:
    """Test SeasonalityPattern model validation."""

    def test_pattern_creation_with_all_fields(self):
        """Test creating pattern with all fields."""
        pattern_type_cls, pattern_cls, _, _ = get_models()

        pattern = pattern_cls(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            average_return=1.5,
            std_dev=3.2,
            win_rate=0.65,
            sample_size=120,
            statistical_significance=0.95,
            p_value=0.02,
            confidence_interval_lower=0.5,
            confidence_interval_upper=2.5,
            sharpe_ratio=0.47,
            sortino_ratio=0.65,
            max_drawdown=-5.2,
            consistency_score=0.65,
            skewness=0.3,
            kurtosis=1.2,
            period_number=1,
        )

        assert pattern.pattern_type == pattern_type_cls.MONTHLY
        assert pattern.period == "January"
        assert pattern.average_return == 1.5
        assert pattern.sharpe_ratio == 0.47

    def test_pattern_optional_fields_can_be_none(self):
        """Test that optional fields can be None."""
        pattern_type_cls, pattern_cls, _, _ = get_models()

        pattern = pattern_cls(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            average_return=1.5,
            std_dev=3.2,
            win_rate=0.65,
            sample_size=120,
            statistical_significance=0.95,
            # All optional fields omitted
        )

        assert pattern.p_value is None
        assert pattern.confidence_interval_lower is None
        assert pattern.confidence_interval_upper is None
        assert pattern.sharpe_ratio is None
        assert pattern.sortino_ratio is None
        assert pattern.max_drawdown is None
        assert pattern.consistency_score is None
        assert pattern.skewness is None
        assert pattern.kurtosis is None
        assert pattern.period_number is None

    def test_pattern_serialization_to_dict(self):
        """Test pattern serialization to dictionary."""
        pattern_type_cls, pattern_cls, _, _ = get_models()

        pattern = pattern_cls(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            average_return=1.5,
            std_dev=3.2,
            win_rate=0.65,
            sample_size=120,
            statistical_significance=0.95,
            sharpe_ratio=0.47,
        )

        data = pattern.model_dump()

        assert isinstance(data, dict)
        assert data["pattern_type"] == "Monthly"
        assert data["period"] == "January"
        assert data["sharpe_ratio"] == 0.47

    def test_pattern_json_serialization(self):
        """Test pattern can be serialized to JSON."""
        pattern_type_cls, pattern_cls, _, _ = get_models()

        pattern = pattern_cls(
            pattern_type=pattern_type_cls.MONTHLY,
            period="January",
            average_return=1.5,
            std_dev=3.2,
            win_rate=0.65,
            sample_size=120,
            statistical_significance=0.95,
        )

        json_str = pattern.model_dump_json()

        assert isinstance(json_str, str)
        assert "January" in json_str
        assert "Monthly" in json_str


@pytest.mark.unit
class TestSeasonalityConfigModel:
    """Test SeasonalityConfig model validation."""

    def test_config_defaults(self):
        """Test that default values are applied correctly."""
        _, _, _, config_cls = get_models()

        config = config_cls()

        assert config.min_years == 3.0
        assert config.confidence_level == 0.95
        assert config.output_format == "csv"
        assert config.detrend_data is True
        assert config.min_sample_size == 10
        assert config.time_period_days == 1

    def test_config_custom_values(self):
        """Test configuration with custom values."""
        _, _, _, config_cls = get_models()

        config = config_cls(
            tickers=["AAPL", "MSFT"],
            min_years=5.0,
            confidence_level=0.99,
            output_format="json",
            detrend_data=False,
            min_sample_size=20,
            time_period_days=5,
        )

        assert config.tickers == ["AAPL", "MSFT"]
        assert config.min_years == 5.0
        assert config.confidence_level == 0.99
        assert config.output_format == "json"
        assert config.detrend_data is False
        assert config.min_sample_size == 20
        assert config.time_period_days == 5

    def test_confidence_level_validation_rejects_invalid(self):
        """CRITICAL: Test that invalid confidence levels are rejected."""
        _, _, _, config_cls = get_models()

        # Test values outside (0, 1)
        with pytest.raises(ValidationError):
            config_cls(confidence_level=0.0)

        with pytest.raises(ValidationError):
            config_cls(confidence_level=1.0)

        with pytest.raises(ValidationError):
            config_cls(confidence_level=1.5)

        with pytest.raises(ValidationError):
            config_cls(confidence_level=-0.5)

    def test_confidence_level_validation_accepts_valid(self):
        """Test that valid confidence levels are accepted."""
        _, _, _, config_cls = get_models()

        # Valid values
        config_95 = config_cls(confidence_level=0.95)
        assert config_95.confidence_level == 0.95

        config_99 = config_cls(confidence_level=0.99)
        assert config_99.confidence_level == 0.99

        config_90 = config_cls(confidence_level=0.90)
        assert config_90.confidence_level == 0.90

    def test_min_years_validation_rejects_invalid(self):
        """CRITICAL: Test that invalid min_years are rejected."""
        _, _, _, config_cls = get_models()

        with pytest.raises(ValidationError):
            config_cls(min_years=0)

        with pytest.raises(ValidationError):
            config_cls(min_years=-1)

    def test_min_years_validation_accepts_valid(self):
        """Test that valid min_years are accepted."""
        _, _, _, config_cls = get_models()

        config = config_cls(min_years=5.5)
        assert config.min_years == 5.5

    def test_output_format_validation_rejects_invalid(self):
        """Test that invalid output formats are rejected."""
        _, _, _, config_cls = get_models()

        with pytest.raises(ValidationError):
            config_cls(output_format="xml")

        with pytest.raises(ValidationError):
            config_cls(output_format="txt")

    def test_output_format_validation_accepts_valid(self):
        """Test that valid output formats are accepted."""
        _, _, _, config_cls = get_models()

        config_csv = config_cls(output_format="csv")
        assert config_csv.output_format == "csv"

        config_json = config_cls(output_format="json")
        assert config_json.output_format == "json"

        # Should handle case-insensitive
        config_upper = config_cls(output_format="CSV")
        assert config_upper.output_format == "csv"

    def test_time_period_days_validation_rejects_invalid(self):
        """Test that invalid time_period_days are rejected."""
        _, _, _, config_cls = get_models()

        with pytest.raises(ValidationError):
            config_cls(time_period_days=0)

        with pytest.raises(ValidationError):
            config_cls(time_period_days=-1)

        with pytest.raises(ValidationError):
            config_cls(time_period_days=366)

    def test_time_period_days_validation_accepts_valid(self):
        """Test that valid time_period_days are accepted."""
        _, _, _, config_cls = get_models()

        config_1 = config_cls(time_period_days=1)
        assert config_1.time_period_days == 1

        config_30 = config_cls(time_period_days=30)
        assert config_30.time_period_days == 30

        config_365 = config_cls(time_period_days=365)
        assert config_365.time_period_days == 365


@pytest.mark.unit
class TestSeasonalityResultModel:
    """Test SeasonalityResult model."""

    def test_result_creation_with_patterns(self):
        """Test creating result with patterns."""
        pattern_type_cls, pattern_cls, result_cls, _ = get_models()

        patterns = [
            pattern_cls(
                pattern_type=pattern_type_cls.MONTHLY,
                period="January",
                average_return=1.5,
                std_dev=3.2,
                win_rate=0.65,
                sample_size=120,
                statistical_significance=0.95,
            ),
            pattern_cls(
                pattern_type=pattern_type_cls.WEEKLY,
                period="Monday",
                average_return=0.5,
                std_dev=2.1,
                win_rate=0.55,
                sample_size=250,
                statistical_significance=0.85,
            ),
        ]

        result = result_cls(
            ticker="AAPL",
            data_start_date=datetime(2020, 1, 1),
            data_end_date=datetime(2025, 1, 1),
            total_periods=1260,
            patterns=patterns,
            overall_seasonal_strength=0.6,
            strongest_pattern=patterns[0],
        )

        assert result.ticker == "AAPL"
        assert len(result.patterns) == 2
        assert result.strongest_pattern == patterns[0]

    def test_result_strongest_pattern_can_be_none(self):
        """Test that strongest_pattern can be None."""
        _, _, result_cls, _ = get_models()

        result = result_cls(
            ticker="AAPL",
            data_start_date=datetime(2020, 1, 1),
            data_end_date=datetime(2025, 1, 1),
            total_periods=1260,
            patterns=[],
            overall_seasonal_strength=0.0,
            strongest_pattern=None,
        )

        assert result.strongest_pattern is None

    def test_result_metadata_dictionary(self):
        """Test that metadata dictionary works."""
        _, _, result_cls, _ = get_models()

        result = result_cls(
            ticker="AAPL",
            data_start_date=datetime(2020, 1, 1),
            data_end_date=datetime(2025, 1, 1),
            total_periods=1260,
            patterns=[],
            overall_seasonal_strength=0.5,
            metadata={"years_of_data": 5.0, "detrended": True, "custom_field": "test"},
        )

        assert result.metadata["years_of_data"] == 5.0
        assert result.metadata["detrended"] is True
        assert result.metadata["custom_field"] == "test"

    def test_result_analysis_date_auto_populated(self):
        """Test that analysis_date is automatically populated."""
        _, _, result_cls, _ = get_models()

        result = result_cls(
            ticker="AAPL",
            data_start_date=datetime(2020, 1, 1),
            data_end_date=datetime(2025, 1, 1),
            total_periods=1260,
            patterns=[],
            overall_seasonal_strength=0.5,
        )

        # analysis_date should be set automatically
        assert result.analysis_date is not None
        assert isinstance(result.analysis_date, datetime)
