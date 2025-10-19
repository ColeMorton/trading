"""Tests for seasonality JSON and CSV export functionality.

CRITICAL: These tests verify that exported data is correctly structured
and contains all required fields for downstream analysis.
"""

from datetime import datetime
import json

import pandas as pd


def get_service_class():
    """Late import to avoid circular dependency."""
    from app.tools.services.seasonality_service import SeasonalityService

    return SeasonalityService


def get_config_class():
    """Late import to avoid circular dependency."""
    from app.cli.models.seasonality import SeasonalityConfig

    return SeasonalityConfig


def get_result_class():
    """Late import to avoid circular dependency."""
    from app.cli.models.seasonality import SeasonalityResult

    return SeasonalityResult


def get_pattern_class():
    """Late import to avoid circular dependency."""
    from app.cli.models.seasonality import SeasonalityPattern

    return SeasonalityPattern


def get_pattern_type():
    """Late import to avoid circular dependency."""
    from app.cli.models.seasonality import PatternType

    return PatternType


class TestJSONExportStructure:
    """Test JSON export structure and content."""

    def test_json_file_created(self, tmp_path, standard_5yr_data):
        """Test that JSON file is created."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup
        config = SeasonalityConfig(tickers=["TEST"], output_format="json")
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        standard_5yr_data.to_csv(price_file)

        # Analyze (which calls _save_result -> _export_json)
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

        # Assert JSON file exists
        json_file = service.output_dir / "TEST_seasonality.json"
        assert json_file.exists()

    def test_json_has_required_sections(self, tmp_path, standard_5yr_data):
        """CRITICAL: Test that JSON has all required top-level sections."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup
        config = SeasonalityConfig(tickers=["TEST"])
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        standard_5yr_data.to_csv(price_file)

        # Analyze and export
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

        # Load JSON
        json_file = service.output_dir / "TEST_seasonality.json"
        with open(json_file) as f:
            data = json.load(f)

        # Assert required sections present
        assert "meta" in data
        assert "summary_statistics" in data
        assert "monthly_patterns" in data
        assert "weekly_patterns" in data
        assert "quarterly_patterns" in data
        assert "week_of_year_patterns" in data
        assert "day_of_month_patterns" in data

    def test_json_meta_section_complete(self, tmp_path, standard_5yr_data):
        """Test that meta section contains all required fields."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup
        config = SeasonalityConfig(tickers=["TEST"])
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        standard_5yr_data.to_csv(price_file)

        # Analyze and export
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

        # Load JSON
        json_file = service.output_dir / "TEST_seasonality.json"
        with open(json_file) as f:
            data = json.load(f)

        # Assert meta fields
        meta = data["meta"]
        assert meta["ticker"] == "TEST"
        assert "analysis_date" in meta
        assert "data_period" in meta
        assert "configuration" in meta

        # Data period fields
        assert "start" in meta["data_period"]
        assert "end" in meta["data_period"]
        assert "years" in meta["data_period"]
        assert "trading_days" in meta["data_period"]

        # Configuration fields
        assert "confidence_level" in meta["configuration"]
        assert "detrended" in meta["configuration"]
        assert "min_sample_size" in meta["configuration"]

    def test_json_summary_statistics_complete(self, tmp_path, standard_5yr_data):
        """Test that summary statistics section is complete."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup
        config = SeasonalityConfig(tickers=["TEST"])
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        standard_5yr_data.to_csv(price_file)

        # Analyze and export
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

        # Load JSON
        json_file = service.output_dir / "TEST_seasonality.json"
        with open(json_file) as f:
            data = json.load(f)

        # Assert summary statistics
        summary = data["summary_statistics"]
        assert "seasonal_strength" in summary
        assert "overall_consistency" in summary
        assert "best_month" in summary
        assert "worst_month" in summary
        assert "best_day" in summary
        assert "worst_day" in summary

    def test_json_pattern_arrays_populated(self, tmp_path, standard_5yr_data):
        """Test that pattern arrays contain data."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup
        config = SeasonalityConfig(tickers=["TEST"])
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        standard_5yr_data.to_csv(price_file)

        # Analyze and export
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

        # Load JSON
        json_file = service.output_dir / "TEST_seasonality.json"
        with open(json_file) as f:
            data = json.load(f)

        # Monthly patterns should have 12 entries
        assert isinstance(data["monthly_patterns"], list)
        assert len(data["monthly_patterns"]) == 12

        # Weekly patterns should have 5 entries
        assert isinstance(data["weekly_patterns"], list)
        assert len(data["weekly_patterns"]) == 5

        # Quarterly patterns should have 4 entries
        assert isinstance(data["quarterly_patterns"], list)
        assert len(data["quarterly_patterns"]) == 4


class TestJSONPatternFields:
    """Test that individual pattern fields are correctly exported."""

    def test_pattern_has_all_fields(self, tmp_path, standard_5yr_data):
        """Test that each pattern in JSON has all required fields."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup
        config = SeasonalityConfig(tickers=["TEST"])
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        standard_5yr_data.to_csv(price_file)

        # Analyze and export
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

        # Load JSON
        json_file = service.output_dir / "TEST_seasonality.json"
        with open(json_file) as f:
            data = json.load(f)

        # Check first monthly pattern
        if data["monthly_patterns"]:
            pattern = data["monthly_patterns"][0]

            # Required fields
            assert "period" in pattern
            assert "avg_return_pct" in pattern
            assert "std_dev_pct" in pattern
            assert "win_rate" in pattern
            assert "sample_size" in pattern
            assert "statistical_significance" in pattern

            # Optional fields (should exist even if None)
            assert "sharpe_ratio" in pattern
            assert "sortino_ratio" in pattern
            assert "max_drawdown_pct" in pattern
            assert "p_value" in pattern
            assert "confidence_interval" in pattern
            assert "consistency_score" in pattern
            assert "skewness" in pattern
            assert "kurtosis" in pattern

    def test_numeric_precision_4_decimals(self, tmp_path, standard_5yr_data):
        """CRITICAL: Test that numeric values are rounded to 4 decimals."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup
        config = SeasonalityConfig(tickers=["TEST"])
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        standard_5yr_data.to_csv(price_file)

        # Analyze and export
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

        # Load JSON
        json_file = service.output_dir / "TEST_seasonality.json"
        with open(json_file) as f:
            data = json.load(f)

        # Check precision on summary statistics
        strength = data["summary_statistics"]["seasonal_strength"]
        # Count decimal places
        if isinstance(strength, float):
            str_val = str(strength)
            if "." in str_val:
                decimals = len(str_val.split(".")[1])
                assert decimals <= 4

    def test_week_of_year_sorted_by_period_number(self, tmp_path, standard_5yr_data):
        """CRITICAL: Test that week_of_year patterns are sorted by period_number."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup
        config = SeasonalityConfig(tickers=["TEST"])
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        standard_5yr_data.to_csv(price_file)

        # Analyze and export
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

        # Load JSON
        json_file = service.output_dir / "TEST_seasonality.json"
        with open(json_file) as f:
            data = json.load(f)

        # Check week_of_year is sorted
        week_patterns = data["week_of_year_patterns"]
        if len(week_patterns) > 1:
            period_numbers = [
                p.get("period_number") for p in week_patterns if p.get("period_number")
            ]

            # Should be in ascending order
            for i in range(len(period_numbers) - 1):
                assert period_numbers[i] < period_numbers[i + 1]


class TestCSVExportStructure:
    """Test CSV export structure and content."""

    def test_csv_file_created(self, tmp_path, standard_5yr_data):
        """Test that CSV file is created."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup
        config = SeasonalityConfig(tickers=["TEST"], output_format="csv")
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        standard_5yr_data.to_csv(price_file)

        # Analyze and export
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

        # Assert CSV file exists
        csv_file = service.output_dir / "TEST_seasonality.csv"
        assert csv_file.exists()

    def test_csv_has_all_columns(self, tmp_path, standard_5yr_data):
        """Test that CSV export includes all columns."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup
        config = SeasonalityConfig(tickers=["TEST"], output_format="csv")
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        standard_5yr_data.to_csv(price_file)

        # Analyze and export
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

        # Load CSV
        csv_file = service.output_dir / "TEST_seasonality.csv"
        df = pd.read_csv(csv_file)

        # Check required columns
        expected_columns = [
            "Pattern_Type",
            "Period",
            "Period_Number",
            "Average_Return",
            "Std_Dev",
            "Win_Rate",
            "Sample_Size",
            "Sharpe_Ratio",
            "Sortino_Ratio",
            "Max_Drawdown",
            "Consistency_Score",
            "Statistical_Significance",
            "P_Value",
            "CI_Lower",
            "CI_Upper",
            "Skewness",
            "Kurtosis",
        ]

        for col in expected_columns:
            assert col in df.columns

    def test_csv_no_duplicate_rows(self, tmp_path, standard_5yr_data):
        """CRITICAL: Test that CSV doesn't have duplicate rows (bug we fixed)."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup
        config = SeasonalityConfig(tickers=["TEST"], output_format="csv")
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        standard_5yr_data.to_csv(price_file)

        # Analyze and export
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

        # Load CSV
        csv_file = service.output_dir / "TEST_seasonality.csv"
        df = pd.read_csv(csv_file)

        # Check for duplicates
        # Count rows for each pattern type + period combination
        duplicates = df.duplicated(subset=["Pattern_Type", "Period"], keep=False)

        # Should have NO duplicates
        assert duplicates.sum() == 0

        # Monthly patterns should have exactly 12 rows
        monthly_rows = df[df["Pattern_Type"] == "Monthly"]
        assert len(monthly_rows) == 12

    def test_csv_monthly_patterns_unique(self, tmp_path, standard_5yr_data):
        """Test that each month appears exactly once in CSV."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup
        config = SeasonalityConfig(tickers=["TEST"], output_format="csv")
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        standard_5yr_data.to_csv(price_file)

        # Analyze and export
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

        # Load CSV
        csv_file = service.output_dir / "TEST_seasonality.csv"
        df = pd.read_csv(csv_file)

        # Filter to monthly patterns
        monthly = df[df["Pattern_Type"] == "Monthly"]

        # Each month should appear exactly once
        month_counts = monthly["Period"].value_counts()
        assert all(count == 1 for count in month_counts.values)


class TestJSONvsCSVConsistency:
    """Test that JSON and CSV exports contain the same data."""

    def test_json_and_csv_pattern_counts_match(self, tmp_path, standard_5yr_data):
        """Test that JSON and CSV have the same number of patterns."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup
        config = SeasonalityConfig(tickers=["TEST"], output_format="both")
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        standard_5yr_data.to_csv(price_file)

        # Analyze and export
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

        # Load both files
        json_file = service.output_dir / "TEST_seasonality.json"
        csv_file = service.output_dir / "TEST_seasonality.csv"

        with open(json_file) as f:
            json_data = json.load(f)

        csv_data = pd.read_csv(csv_file)

        # Count patterns in JSON
        json_monthly_count = len(json_data["monthly_patterns"])
        json_weekly_count = len(json_data["weekly_patterns"])
        json_quarterly_count = len(json_data["quarterly_patterns"])

        # Count patterns in CSV
        csv_monthly_count = len(csv_data[csv_data["Pattern_Type"] == "Monthly"])
        csv_weekly_count = len(csv_data[csv_data["Pattern_Type"] == "Weekly"])
        csv_quarterly_count = len(csv_data[csv_data["Pattern_Type"] == "Quarterly"])

        # Counts should match
        assert json_monthly_count == csv_monthly_count
        assert json_weekly_count == csv_weekly_count
        assert json_quarterly_count == csv_quarterly_count

    def test_json_and_csv_values_match(self, tmp_path, standard_5yr_data):
        """Test that JSON and CSV contain the same values for patterns."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup
        config = SeasonalityConfig(tickers=["TEST"], output_format="both")
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        standard_5yr_data.to_csv(price_file)

        # Analyze and export
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

        # Load both files
        json_file = service.output_dir / "TEST_seasonality.json"
        csv_file = service.output_dir / "TEST_seasonality.csv"

        with open(json_file) as f:
            json_data = json.load(f)

        csv_data = pd.read_csv(csv_file)

        # Compare January data from both
        json_jan = next(
            (p for p in json_data["monthly_patterns"] if p["period"] == "January"), None
        )
        csv_jan = csv_data[
            (csv_data["Pattern_Type"] == "Monthly") & (csv_data["Period"] == "January")
        ]

        if json_jan and not csv_jan.empty:
            # Compare key metrics (allowing for rounding)
            csv_row = csv_jan.iloc[0]

            assert abs(json_jan["avg_return_pct"] - csv_row["Average_Return"]) < 0.01
            assert abs(json_jan["win_rate"] - csv_row["Win_Rate"]) < 0.01
            assert json_jan["sample_size"] == csv_row["Sample_Size"]


class TestExportEdgeCases:
    """Test export handling of edge cases."""

    def test_export_with_no_patterns(self, tmp_path, few_samples_data):
        """Test export when no patterns meet min_sample_size."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()

        # Setup with very high min_sample_size
        config = SeasonalityConfig(tickers=["TEST"], min_sample_size=1000)
        service = SeasonalityService(config)
        service.prices_dir = tmp_path / "prices"
        service.output_dir = tmp_path / "seasonality"
        service.prices_dir.mkdir(parents=True, exist_ok=True)
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Save test data
        price_file = service.prices_dir / "TEST_D.csv"
        few_samples_data.to_csv(price_file)

        # Analyze and export
        result = service._analyze_ticker("TEST")
        if result:
            service._save_result(result)

            # JSON should still be created
            json_file = service.output_dir / "TEST_seasonality.json"
            assert json_file.exists()

            with open(json_file) as f:
                data = json.load(f)

            # Pattern arrays should be empty
            assert data["monthly_patterns"] == []

    def test_export_handles_none_values(self, tmp_path):
        """Test that None values in patterns are handled correctly in export."""
        SeasonalityConfig = get_config_class()
        SeasonalityService = get_service_class()
        SeasonalityPattern = get_pattern_class()
        PatternType = get_pattern_type()
        SeasonalityResult = get_result_class()

        # Create a result with patterns that have None values
        patterns = [
            SeasonalityPattern(
                pattern_type=PatternType.MONTHLY,
                period="January",
                average_return=1.5,
                std_dev=3.2,
                win_rate=0.65,
                sample_size=120,
                statistical_significance=0.95,
                # Leave optional fields as None
                p_value=None,
                sharpe_ratio=None,
                sortino_ratio=None,
            )
        ]

        SeasonalityResult = get_result_class()

        result = SeasonalityResult(
            ticker="TEST",
            data_start_date=datetime(2020, 1, 1),
            data_end_date=datetime(2025, 1, 1),
            total_periods=1260,
            patterns=patterns,
            overall_seasonal_strength=0.5,
        )

        # Setup service
        config = SeasonalityConfig(tickers=["TEST"])
        service = SeasonalityService(config)
        service.output_dir = tmp_path / "seasonality"
        service.output_dir.mkdir(parents=True, exist_ok=True)

        # Export
        service._export_json(result)

        # Load and verify None values are handled
        json_file = service.output_dir / "TEST_seasonality.json"
        with open(json_file) as f:
            data = json.load(f)

        # None values should be null in JSON
        pattern_data = data["monthly_patterns"][0]
        assert pattern_data["p_value"] is None
        assert pattern_data["sharpe_ratio"] is None
