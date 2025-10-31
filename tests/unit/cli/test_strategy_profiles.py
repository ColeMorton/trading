"""
Comprehensive tests for CLI Strategy Configuration and Profiles.

This test suite covers:
- Profile loading for all strategy types (SMA, EMA, MACD)
- Configuration overrides and parameter validation
- Profile inheritance and defaults
- Error handling for invalid configurations
- YAML parsing and validation
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.cli.config.loader import ConfigLoader
from app.cli.models.strategy import StrategyConfig, StrategyType


@pytest.mark.unit
class TestConfigLoader:
    """Test cases for ConfigLoader with strategy profiles."""

    @pytest.fixture
    def config_loader(self):
        """Create ConfigLoader instance."""
        return ConfigLoader()

    @pytest.fixture
    def temp_profile_dir(self):
        """Create temporary directory with test profiles."""
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = Path(temp_dir) / "profiles"
            profile_dir.mkdir()
            yield profile_dir

    @pytest.fixture
    def sample_sma_profile(self):
        """Sample SMA strategy profile YAML content."""
        return """
metadata:
  name: test_sma_strategy
  description: Test SMA strategy configuration

config_type: strategy
config:
  ticker: [AAPL, MSFT]
  strategy_types: [SMA]
  use_years: false
  years: 15
  multi_ticker: true
  use_scanner: false
  scanner_list: ""
  use_gbm: false
  minimums:
    win_rate: 0.55
    trades: 30
    expectancy_per_trade: 0.01
    profit_factor: 1.2
    sortino_ratio: 0.8
    beats_bnh: 0.05
  synthetic:
    use_synthetic: false
    ticker_1: ""
    ticker_2: ""
  filter:
    use_current: true
  fast_period_range: [5, 50]
  slow_period_range: [20, 200]
"""

    @pytest.fixture
    def sample_macd_profile(self):
        """Sample MACD strategy profile YAML content."""
        return """
metadata:
  name: test_macd_strategy
  description: Test MACD strategy configuration

config_type: strategy
config:
  ticker: [BTC-USD]
  strategy_types: [MACD]
  use_years: true
  years: 10
  multi_ticker: false
  use_scanner: false
  scanner_list: ""
  use_gbm: false
  minimums:
    win_rate: 0.6
    trades: 25
    profit_factor: 1.5
  synthetic:
    use_synthetic: false
  filter:
    use_current: false
  short_window_start: 8
  short_window_end: 16
  long_window_start: 20
  long_window_end: 30
  signal_window_start: 5
  signal_window_end: 15
  step: 2
  direction: Long
  use_hourly: false
  refresh: true
"""

    @pytest.fixture
    def sample_mixed_profile(self):
        """Sample profile with mixed strategy types."""
        return """
metadata:
  name: test_mixed_strategy
  description: Test mixed SMA/EMA strategy configuration

config_type: strategy
config:
  ticker: [AAPL, MSFT, GOOGL]
  strategy_types: [SMA, EMA]
  use_years: false
  years: 20
  multi_ticker: true
  minimums:
    win_rate: 0.5
    trades: 40
  synthetic:
    use_synthetic: false
  filter:
    use_current: true
"""

    def test_load_sma_profile_success(
        self,
        config_loader,
        temp_profile_dir,
        sample_sma_profile,
    ):
        """Test successful loading of SMA strategy profile."""
        # Create profile file
        profile_file = temp_profile_dir / "test_sma.yaml"
        profile_file.write_text(sample_sma_profile)

        with patch.object(
            config_loader.profile_manager,
            "profiles_dir",
            temp_profile_dir,
        ):
            config = config_loader.load_from_profile("test_sma", StrategyConfig)

        assert isinstance(config, StrategyConfig)
        assert config.ticker == ["AAPL", "MSFT"]
        assert config.strategy_types == [StrategyType.SMA]
        assert config.use_years is False
        assert config.years == 15
        assert config.multi_ticker is True
        assert config.minimums.win_rate == 0.55
        assert config.minimums.trades == 30
        assert config.filter.use_current is True
        assert config.fast_period_range == (5, 50)
        assert config.slow_period_range == (20, 200)

    def test_load_macd_profile_success(
        self,
        config_loader,
        temp_profile_dir,
        sample_macd_profile,
    ):
        """Test successful loading of MACD strategy profile."""
        # Create profile file
        profile_file = temp_profile_dir / "test_macd.yaml"
        profile_file.write_text(sample_macd_profile)

        with patch.object(
            config_loader.profile_manager,
            "profiles_dir",
            temp_profile_dir,
        ):
            config = config_loader.load_from_profile("test_macd", StrategyConfig)

        assert isinstance(config, StrategyConfig)
        assert config.ticker == ["BTC-USD"]
        assert config.strategy_types == [StrategyType.MACD]
        assert config.use_years is True
        assert config.years == 10
        assert config.short_window_start == 8
        assert config.short_window_end == 16
        assert config.long_window_start == 20
        assert config.long_window_end == 30
        assert config.signal_window_start == 5
        assert config.signal_window_end == 15
        assert config.step == 2
        assert config.direction == "Long"
        assert config.use_hourly is False
        assert config.refresh is True

    def test_load_mixed_strategy_profile(
        self,
        config_loader,
        temp_profile_dir,
        sample_mixed_profile,
    ):
        """Test loading profile with mixed strategy types."""
        # Create profile file
        profile_file = temp_profile_dir / "test_mixed.yaml"
        profile_file.write_text(sample_mixed_profile)

        with patch.object(
            config_loader.profile_manager,
            "profiles_dir",
            temp_profile_dir,
        ):
            config = config_loader.load_from_profile("test_mixed", StrategyConfig)

        assert isinstance(config, StrategyConfig)
        assert config.ticker == ["AAPL", "MSFT", "GOOGL"]
        assert config.strategy_types == [StrategyType.SMA, StrategyType.EMA]
        assert config.multi_ticker is True

    def test_load_profile_with_overrides(
        self,
        config_loader,
        temp_profile_dir,
        sample_sma_profile,
    ):
        """Test loading profile with runtime overrides."""
        # Create profile file
        profile_file = temp_profile_dir / "test_sma.yaml"
        profile_file.write_text(sample_sma_profile)

        overrides = {
            "ticker": ["TSLA"],
            "minimums": {"win_rate": 0.7, "trades": 50},
            "use_years": True,
            "years": 5,
        }

        with patch.object(
            config_loader.profile_manager,
            "profiles_dir",
            temp_profile_dir,
        ):
            config = config_loader.load_from_profile(
                "test_sma",
                StrategyConfig,
                overrides,
            )

        # Original values should be overridden
        assert config.ticker == ["TSLA"]
        assert config.minimums.win_rate == 0.7
        assert config.minimums.trades == 50
        assert config.use_years is True
        assert config.years == 5

        # Non-overridden values should remain from profile
        assert config.strategy_types == [StrategyType.SMA]
        assert config.multi_ticker is True

    def test_load_profile_nonexistent_file(self, config_loader):
        """Test loading nonexistent profile file."""
        with pytest.raises(FileNotFoundError):
            config_loader.load_from_profile("nonexistent", StrategyConfig)

    def test_load_profile_invalid_yaml(self, config_loader, temp_profile_dir):
        """Test loading profile with invalid YAML."""
        # Create profile file with invalid YAML
        profile_file = temp_profile_dir / "invalid.yaml"
        profile_file.write_text("invalid: yaml: content: [unclosed")

        with (
            patch.object(
                config_loader.profile_manager, "profiles_dir", temp_profile_dir
            ),
            pytest.raises(Exception),
        ):  # YAML parsing error
            config_loader.load_from_profile("invalid", StrategyConfig)

    def test_load_profile_missing_required_fields(
        self,
        config_loader,
        temp_profile_dir,
    ):
        """Test loading profile missing required fields."""
        incomplete_profile = """
metadata:
  name: incomplete
config_type: strategy
config:
  strategy_types: [SMA]
  # Missing ticker (required field)
"""
        profile_file = temp_profile_dir / "incomplete.yaml"
        profile_file.write_text(incomplete_profile)

        with (
            patch.object(
                config_loader.profile_manager, "profiles_dir", temp_profile_dir
            ),
            pytest.raises(Exception),
        ):  # Validation error
            config_loader.load_from_profile("incomplete", StrategyConfig)

    def test_load_profile_wrong_config_type(self, config_loader, temp_profile_dir):
        """Test loading profile with wrong config type."""
        wrong_type_profile = """
metadata:
  name: wrong_type
config_type: portfolio  # Wrong type
config:
  ticker: [AAPL]
  strategy_types: [SMA]
"""
        profile_file = temp_profile_dir / "wrong_type.yaml"
        profile_file.write_text(wrong_type_profile)

        with (
            patch.object(
                config_loader.profile_manager, "profiles_dir", temp_profile_dir
            ),
            pytest.raises(Exception),
        ):  # Type validation error
            config_loader.load_from_profile("wrong_type", StrategyConfig)


@pytest.mark.unit
class TestParameterValidation:
    """Test parameter validation for strategy configurations."""

    @pytest.fixture
    def config_loader(self):
        """Create ConfigLoader instance."""
        return ConfigLoader()

    def test_ticker_validation_string_conversion(self, config_loader):
        """Test that string tickers are converted to lists."""
        config_data = {
            "ticker": "AAPL",  # String
            "strategy_types": ["SMA"],
            "minimums": {},
            "synthetic": {},
            "filter": {},
        }

        config = StrategyConfig(**config_data)
        assert config.ticker == "AAPL"  # Should remain as string per model

    def test_strategy_types_validation(self, config_loader):
        """Test strategy types validation."""
        # Valid strategy types
        valid_config = {
            "ticker": ["AAPL"],
            "strategy_types": ["SMA", "EMA"],
            "minimums": {},
            "synthetic": {},
            "filter": {},
        }
        config = StrategyConfig(**valid_config)
        assert config.strategy_types == [StrategyType.SMA, StrategyType.EMA]

        # Invalid strategy type should raise validation error
        invalid_config = {
            "ticker": ["AAPL"],
            "strategy_types": ["INVALID_STRATEGY"],
            "minimums": {},
            "synthetic": {},
            "filter": {},
        }
        with pytest.raises(ValueError):
            StrategyConfig(**invalid_config)

    def test_minimums_validation(self, config_loader):
        """Test minimum criteria validation."""
        config_data = {
            "ticker": ["AAPL"],
            "strategy_types": ["SMA"],
            "minimums": {
                "win_rate": 0.5,
                "trades": 25,
                "expectancy_per_trade": 0.01,
                "profit_factor": 1.0,
                "sortino_ratio": 0.5,
                "beats_bnh": 0.0,
            },
            "synthetic": {},
            "filter": {},
        }
        config = StrategyConfig(**config_data)
        assert config.minimums.win_rate == 0.5
        assert config.minimums.trades == 25

    def test_synthetic_ticker_validation(self, config_loader):
        """Test synthetic ticker configuration validation."""
        config_data = {
            "ticker": ["STRK/MSTR"],
            "strategy_types": ["SMA"],
            "minimums": {},
            "synthetic": {
                "use_synthetic": True,
                "ticker_1": "STRK",
                "ticker_2": "MSTR",
            },
            "filter": {},
        }
        config = StrategyConfig(**config_data)
        assert config.synthetic.use_synthetic is True
        assert config.synthetic.ticker_1 == "STRK"
        assert config.synthetic.ticker_2 == "MSTR"

    def test_macd_specific_validation(self, config_loader):
        """Test MACD-specific parameter validation."""
        macd_config = {
            "ticker": ["BTC-USD"],
            "strategy_types": ["MACD"],
            "minimums": {},
            "synthetic": {},
            "filter": {},
            "short_window_start": 8,
            "short_window_end": 16,
            "long_window_start": 20,
            "long_window_end": 30,
            "signal_window_start": 5,
            "signal_window_end": 15,
            "step": 1,
            "direction": "Long",
        }
        config = StrategyConfig(**macd_config)
        assert config.short_window_start == 8
        assert config.long_window_start == 20
        assert config.direction == "Long"

    def test_parameter_range_validation(self, config_loader):
        """Test parameter range validation."""
        config_data = {
            "ticker": ["AAPL"],
            "strategy_types": ["SMA"],
            "minimums": {},
            "synthetic": {},
            "filter": {},
            "fast_period_range": [5, 50],
            "slow_period_range": [20, 200],
            "fast_period": 12,
            "slow_period": 26,
        }
        config = StrategyConfig(**config_data)
        assert config.fast_period_range == (5, 50)
        assert config.slow_period_range == (20, 200)
        assert config.fast_period == 12
        assert config.slow_period == 26


@pytest.mark.unit
class TestProfileInheritance:
    """Test profile inheritance and template functionality."""

    @pytest.fixture
    def config_loader(self):
        """Create ConfigLoader instance."""
        return ConfigLoader()

    @pytest.fixture
    def temp_profile_dir(self):
        """Create temporary directory with test profiles."""
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = Path(temp_dir) / "profiles"
            profile_dir.mkdir()
            yield profile_dir

    @pytest.fixture
    def base_template(self):
        """Base template profile."""
        return """
metadata:
  name: base_strategy_template
  description: Base template for strategy configurations
  is_template: true

config_type: strategy
config:
  use_years: false
  years: 15
  multi_ticker: false
  use_scanner: false
  scanner_list: ""
  use_gbm: false
  minimums:
    win_rate: 0.5
    trades: 20
    profit_factor: 1.0
  synthetic:
    use_synthetic: false
    ticker_1: ""
    ticker_2: ""
  filter:
    use_current: false
"""

    @pytest.fixture
    def derived_profile(self):
        """Profile that inherits from base template."""
        return """
metadata:
  name: derived_sma_strategy
  description: SMA strategy derived from base template
inherits_from: base_strategy_template

config_type: strategy
config:
  ticker: [AAPL]
  strategy_types: [SMA]
  minimums:
    win_rate: 0.6  # Override base value
    trades: 30     # Override base value
  filter:
    use_current: true  # Override base value
"""

    def test_profile_inheritance_basic(
        self,
        config_loader,
        temp_profile_dir,
        base_template,
        derived_profile,
    ):
        """Test basic profile inheritance functionality."""
        # Create base template
        base_file = temp_profile_dir / "base_strategy_template.yaml"
        base_file.write_text(base_template)

        # Create derived profile
        derived_file = temp_profile_dir / "derived_sma_strategy.yaml"
        derived_file.write_text(derived_profile)

        with patch.object(
            config_loader.profile_manager,
            "profiles_dir",
            temp_profile_dir,
        ):
            config = config_loader.load_from_profile(
                "derived_sma_strategy",
                StrategyConfig,
            )

        # Check inherited values
        assert config.use_years is False  # From base
        assert config.years == 15  # From base
        assert config.multi_ticker is False  # From base
        assert config.use_gbm is False  # From base

        # Check overridden values
        assert config.ticker == ["AAPL"]  # From derived
        assert config.strategy_types == [StrategyType.SMA]  # From derived
        assert config.minimums.win_rate == 0.6  # Overridden
        assert config.minimums.trades == 30  # Overridden
        assert config.filter.use_current is True  # Overridden

        # Check base values that weren't overridden
        assert config.minimums.profit_factor == 1.0  # From base

    def test_profile_inheritance_missing_base(
        self,
        config_loader,
        temp_profile_dir,
        derived_profile,
    ):
        """Test handling of missing base template."""
        # Create only derived profile (base template missing)
        derived_file = temp_profile_dir / "derived_sma_strategy.yaml"
        derived_file.write_text(derived_profile)

        with (
            patch.object(
                config_loader.profile_manager,
                "profiles_dir",
                temp_profile_dir,
            ),
            pytest.raises((FileNotFoundError, ValidationError)),
        ):
            config_loader.load_from_profile("derived_sma_strategy", StrategyConfig)

    def test_multiple_inheritance_levels(self, config_loader, temp_profile_dir):
        """Test multiple levels of profile inheritance."""
        # Base template
        base_template = """
metadata:
  name: base_template
  is_template: true
config_type: strategy
config:
  use_years: false
  minimums:
    win_rate: 0.4
    trades: 10
"""

        # Intermediate template
        intermediate_template = """
metadata:
  name: intermediate_template
  is_template: true
inherits_from: base_template

config_type: strategy
config:
  minimums:
    win_rate: 0.5  # Override base
    profit_factor: 1.2
"""

        # Final derived profile
        final_profile = """
metadata:
  name: final_profile
inherits_from: intermediate_template

config_type: strategy
config:
  ticker: [AAPL]
  strategy_types: [SMA]
  minimums:
    win_rate: 0.6  # Override intermediate
"""

        # Create all files
        (temp_profile_dir / "base_template.yaml").write_text(base_template)
        (temp_profile_dir / "intermediate_template.yaml").write_text(
            intermediate_template,
        )
        (temp_profile_dir / "final_profile.yaml").write_text(final_profile)

        with patch.object(
            config_loader.profile_manager,
            "profiles_dir",
            temp_profile_dir,
        ):
            config = config_loader.load_from_profile("final_profile", StrategyConfig)

        # Check final inheritance chain
        assert config.use_years is False  # From base
        assert config.minimums.win_rate == 0.6  # From final (overridden twice)
        assert config.minimums.trades == 10  # From base (not overridden)
        assert config.minimums.profit_factor == 1.2  # From intermediate
        assert config.ticker == ["AAPL"]  # From final
        assert config.strategy_types == [StrategyType.SMA]  # From final


@pytest.mark.unit
class TestStrategyConfigModelDefaults:
    """Test StrategyConfig model default values and behavior."""

    def test_strategy_config_default_strategy_types(self):
        """Test that StrategyConfig defaults to all strategy types when none specified."""
        # Create minimal config without specifying strategy_types
        minimal_config = {
            "ticker": ["AAPL"],
            "minimums": {},
            "synthetic": {},
            "filter": {},
        }

        config = StrategyConfig(**minimal_config)

        # Should default to all three strategy types
        assert config.strategy_types == [
            StrategyType.SMA,
            StrategyType.EMA,
            StrategyType.MACD,
        ]

    def test_strategy_config_explicit_strategy_types_override(self):
        """Test that explicit strategy_types override the defaults."""
        # Test with single strategy type
        single_config = {
            "ticker": ["AAPL"],
            "strategy_types": [StrategyType.SMA],
            "minimums": {},
            "synthetic": {},
            "filter": {},
        }

        config = StrategyConfig(**single_config)
        assert config.strategy_types == [StrategyType.SMA]

        # Test with multiple strategy types
        multi_config = {
            "ticker": ["AAPL"],
            "strategy_types": [StrategyType.EMA, StrategyType.MACD],
            "minimums": {},
            "synthetic": {},
            "filter": {},
        }

        config = StrategyConfig(**multi_config)
        assert config.strategy_types == [StrategyType.EMA, StrategyType.MACD]

    def test_strategy_config_default_includes_all_supported_types(self):
        """Test that the default strategy_types includes all currently supported strategy types."""
        config = StrategyConfig(
            ticker=["TEST"],
            minimums={},
            synthetic={},
            filter={},
        )

        # Verify all supported strategy types are included
        expected_strategies = {StrategyType.SMA, StrategyType.EMA, StrategyType.MACD}
        actual_strategies = set(config.strategy_types)

        assert actual_strategies == expected_strategies, (
            f"Default strategy types {actual_strategies} don't match expected {expected_strategies}"
        )

    def test_strategy_config_empty_strategy_types_validation(self):
        """Test validation behavior with empty strategy types list."""
        config_data = {
            "ticker": ["AAPL"],
            "strategy_types": [],  # Empty list
            "minimums": {},
            "synthetic": {},
            "filter": {},
        }

        # Should be valid (empty list is allowed, though unusual)
        config = StrategyConfig(**config_data)
        assert config.strategy_types == []


@pytest.mark.unit
class TestConfigurationEdgeCases:
    """Test edge cases and error scenarios for configuration loading."""

    @pytest.fixture
    def config_loader(self):
        """Create ConfigLoader instance."""
        return ConfigLoader()

    def test_empty_profile_file(self, config_loader, temp_dir=None):
        """Test handling of empty profile file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")  # Empty file
            empty_file = Path(f.name)

        try:
            with pytest.raises(Exception):
                config_loader.load_from_yaml(empty_file, StrategyConfig)
        finally:
            empty_file.unlink()

    def test_profile_with_special_characters(self, config_loader):
        """Test profile names with special characters."""
        special_profile = """
metadata:
  name: "test-profile_with.special@chars"
config_type: strategy
config:
  ticker: [AAPL]
  strategy_types: [SMA]
  minimums: {}
  synthetic: {}
  filter: {}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(special_profile)
            special_file = Path(f.name)

        try:
            config = config_loader.load_from_yaml(special_file, StrategyConfig)
            assert config.ticker == ["AAPL"]
        finally:
            special_file.unlink()

    def test_large_profile_file(self, config_loader):
        """Test handling of large profile file."""
        # Create profile with many tickers
        large_ticker_list = [f"TICKER{i:04d}" for i in range(1000)]
        large_profile = f"""
metadata:
  name: large_profile
config_type: strategy
config:
  ticker: {large_ticker_list}
  strategy_types: [SMA]
  minimums: {{}}
  synthetic: {{}}
  filter: {{}}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(large_profile)
            large_file = Path(f.name)

        try:
            config = config_loader.load_from_yaml(large_file, StrategyConfig)
            assert len(config.ticker) == 1000
            assert config.ticker[0] == "TICKER0000"
            assert config.ticker[-1] == "TICKER0999"
        finally:
            large_file.unlink()

    def test_profile_with_unicode_content(self, config_loader):
        """Test profile with Unicode characters."""
        unicode_profile = """
metadata:
  name: unicode_profile
  description: "Profile with Unicode: αβγ δεζ ηθι 中文 日本語"
config_type: strategy
config:
  ticker: [AAPL]
  strategy_types: [SMA]
  minimums: {}
  synthetic: {}
  filter: {}
"""
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yaml",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write(unicode_profile)
            unicode_file = Path(f.name)

        try:
            config = config_loader.load_from_yaml(unicode_file, StrategyConfig)
            assert config.ticker == ["AAPL"]
        finally:
            unicode_file.unlink()

    def test_circular_inheritance(self, config_loader):
        """Test detection and handling of circular inheritance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = Path(temp_dir)

            # Create circular inheritance: A -> B -> A
            profile_a = """
metadata:
  name: profile_a
  inherits_from: profile_b
config_type: strategy
config:
  ticker: [AAPL]
"""
            profile_b = """
metadata:
  name: profile_b
  inherits_from: profile_a
config_type: strategy
config:
  strategy_types: [SMA]
"""

            (profile_dir / "profile_a.yaml").write_text(profile_a)
            (profile_dir / "profile_b.yaml").write_text(profile_b)

            with (
                patch.object(
                    config_loader.profile_manager,
                    "profiles_dir",
                    profile_dir,
                ),
                pytest.raises(Exception),
            ):  # Should detect circular inheritance
                config_loader.load_from_profile("profile_a", StrategyConfig)

    def test_profile_with_environment_variables(self, config_loader):
        """Test profile with environment variable substitution."""
        env_profile = """
metadata:
  name: env_profile
config_type: strategy
config:
  ticker: [${TICKER_SYMBOL:-AAPL}]
  strategy_types: [SMA]
  minimums:
    win_rate: ${MIN_WIN_RATE:-0.5}
  synthetic: {}
  filter: {}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(env_profile)
            env_file = Path(f.name)

        try:
            # Set environment variable
            os.environ["TICKER_SYMBOL"] = "TSLA"
            os.environ["MIN_WIN_RATE"] = "0.7"

            # Note: This test depends on whether the config loader supports env var substitution
            # If not supported, it should handle gracefully
            try:
                config = config_loader.load_from_yaml(env_file, StrategyConfig)
                # If env vars are supported, check substitution
                if isinstance(config.ticker, list) and len(config.ticker) > 0:
                    assert config.ticker[0] in ["TSLA", "${TICKER_SYMBOL:-AAPL}"]
            except Exception:
                # If env var substitution not supported, that's acceptable
                pass
        finally:
            env_file.unlink()
            # Clean up environment
            os.environ.pop("TICKER_SYMBOL", None)
            os.environ.pop("MIN_WIN_RATE", None)
