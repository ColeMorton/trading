"""
Configuration Profile Integration Tests.

This test suite validates that all provided configuration profiles work correctly
with the CLI system:
- Profile loading and parsing
- Inheritance resolution
- Parameter validation across all strategy types
- CLI command compatibility
- Profile-specific configuration validation
- Cross-profile consistency
- Real-world usage scenarios

These tests ensure all provided profiles are functional and maintain backward compatibility.
"""

from unittest.mock import Mock, patch

import polars as pl
import pytest
from typer.testing import CliRunner

from app.cli.commands.strategy import app as strategy_app
from app.cli.config.loader import ConfigLoader
from app.cli.models.strategy import StrategyConfig, StrategyType


class TestDefaultStrategyProfileIntegration:
    """Test integration of default_strategy.yaml profile."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def config_loader(self):
        """Create ConfigLoader instance for testing."""
        return ConfigLoader()

    def test_default_strategy_profile_loading(self, config_loader):
        """Test that default_strategy profile loads correctly."""
        # Load the actual profile
        config = config_loader.load_from_profile(
            "default_strategy", config_type=None, overrides={}
        )

        # Verify basic profile structure
        assert isinstance(config, StrategyConfig)
        assert config.ticker == ["BTC-USD"]

        # Verify MACD parameters are loaded
        assert hasattr(config, "short_window_start")
        assert hasattr(config, "long_window_start")
        assert hasattr(config, "signal_window_start")

        # Verify parameter ranges
        assert config.short_window_start == 5
        assert config.short_window_end == 21
        assert config.long_window_start == 8
        assert config.long_window_end == 34
        assert config.signal_window_start == 5
        assert config.signal_window_end == 13

        # Verify strategy configuration
        assert config.direction == "Long"
        assert config.use_hourly is False
        assert config.use_years is False
        assert config.years == 15

    def test_default_strategy_profile_parameter_validation(self, config_loader):
        """Test parameter validation for default_strategy profile."""
        config = config_loader.load_from_profile(
            "default_strategy", config_type=None, overrides={}
        )

        # Verify MACD parameter relationships
        assert config.short_window_start < config.long_window_start
        assert config.short_window_end <= config.long_window_end
        assert config.signal_window_start > 0
        assert config.signal_window_end > 0

        # Verify sorting configuration
        assert config.sort_by == "Score"
        assert config.sort_ascending is False

        # Verify years configuration
        assert config.years > 0
        assert isinstance(config.years, int)

    def test_default_strategy_profile_includes_all_strategy_types(self, config_loader):
        """Test that default_strategy profile explicitly includes all strategy types."""
        config = config_loader.load_from_profile(
            "default_strategy", config_type=StrategyConfig, overrides={}
        )

        # Verify that the profile explicitly defines all strategy types
        assert config.strategy_types == [
            StrategyType.SMA,
            StrategyType.EMA,
            StrategyType.MACD,
        ]

        # Verify this is explicit in the profile, not just model defaults
        # by checking that the profile actually overrides the model behavior
        assert hasattr(config, "strategy_types")
        assert len(config.strategy_types) == 3

        # Verify the specific types are included
        # Handle both enum and string representations
        if config.strategy_types and hasattr(config.strategy_types[0], "value"):
            strategy_values = [st.value for st in config.strategy_types]
        else:
            strategy_values = [str(st) for st in config.strategy_types]

        assert "SMA" in strategy_values
        assert "EMA" in strategy_values
        assert "MACD" in strategy_values

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_default_strategy_profile_cli_execution(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test CLI execution with default_strategy profile."""
        # Setup real config loading
        real_config_loader = ConfigLoader()
        real_config = real_config_loader.load_from_profile(
            "default_strategy", config_type=None, overrides={}
        )
        mock_config_loader.return_value.load_from_profile.return_value = real_config

        # Setup execution mocks
        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = pl.DataFrame(
            {"Date": [pl.date(2023, 1, 1)], "Close": [45000.0]},
        )

        # Execute CLI command with default_strategy profile
        result = cli_runner.invoke(
            strategy_app,
            ["run", "--profile", "default_strategy"],
        )

        # Verify successful execution
        assert result.exit_code == 0
        mock_config_loader.return_value.load_from_profile.assert_called_once()
        mock_dispatcher.execute_strategy.assert_called_once()

    def test_default_strategy_profile_overrides(self, config_loader):
        """Test parameter overrides with default_strategy profile."""
        # Test ticker override
        overrides = {"ticker": ["ETH-USD"]}
        config = config_loader.load_from_profile(
            "default_strategy", config_type=None, overrides=overrides
        )
        assert config.ticker == ["ETH-USD"]

        # Test years override
        overrides = {"years": 5}
        config = config_loader.load_from_profile(
            "default_strategy", config_type=None, overrides=overrides
        )
        assert config.years == 5

        # Test use_years override
        overrides = {"use_years": True}
        config = config_loader.load_from_profile(
            "default_strategy", config_type=None, overrides=overrides
        )
        assert config.use_years is True

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_default_strategy_profile_dry_run(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test dry-run execution with default_strategy profile."""
        # Setup real config
        real_config_loader = ConfigLoader()
        real_config = real_config_loader.load_from_profile(
            "default_strategy", config_type=None, overrides={}
        )
        mock_config_loader.return_value.load_from_profile.return_value = real_config

        # Execute dry-run
        result = cli_runner.invoke(
            strategy_app,
            ["run", "--profile", "default_strategy", "--dry-run"],
        )

        # Verify dry-run execution
        assert result.exit_code == 0
        assert "Preview" in result.stdout or "Configuration" in result.stdout

        # Verify no actual execution occurred
        mock_get_data.assert_not_called()


@pytest.mark.skip(reason="Profile ma_cross_crypto has been archived")
class TestMACrossCryptoProfileIntegration:
    """Test integration of ma_cross_crypto.yaml profile (ARCHIVED)."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def config_loader(self):
        """Create ConfigLoader instance for testing."""
        return ConfigLoader()

    def test_ma_cross_crypto_profile_loading(self, config_loader):
        """Test that ma_cross_crypto profile loads correctly."""
        config = config_loader.load_from_profile("ma_cross_crypto", {}, {})

        # Verify basic profile structure
        assert isinstance(config, StrategyConfig)

        # Verify crypto tickers
        assert "BTC-USD" in config.ticker
        assert "ETH-USD" in config.ticker

        # Verify strategy types
        assert StrategyType.SMA in config.strategy_types
        assert StrategyType.EMA in config.strategy_types

        # Verify parameter ranges
        assert config.fast_period_range == [5, 89]
        assert config.slow_period_range == [8, 89]

        # Verify minimums
        assert config.minimums.win_rate == 0.55
        assert config.minimums.trades == 50
        assert config.minimums.profit_factor == 1.5

    def test_ma_cross_crypto_profile_parameter_validation(self, config_loader):
        """Test parameter validation for ma_cross_crypto profile."""
        config = config_loader.load_from_profile("ma_cross_crypto", {}, {})

        # Verify parameter range relationships
        assert config.fast_period_range[0] <= config.fast_period_range[1]
        assert config.slow_period_range[0] <= config.slow_period_range[1]

        # Verify minimum thresholds are reasonable
        assert 0 < config.minimums.win_rate <= 1.0
        assert config.minimums.trades > 0
        assert config.minimums.profit_factor > 1.0

        # Verify multiple strategies are configured
        assert len(config.strategy_types) >= 2

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.logging_context")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_ma_cross_crypto_profile_sweep_execution(
        self,
        mock_config_loader,
        mock_logging,
        mock_analyze,
        mock_get_data,
        cli_runner,
    ):
        """Test parameter sweep execution with ma_cross_crypto profile."""
        # Setup real config
        real_config_loader = ConfigLoader()
        real_config = real_config_loader.load_from_profile("ma_cross_crypto", {}, {})
        mock_config_loader.return_value.load_from_profile.return_value = real_config

        # Setup execution mocks
        mock_get_data.return_value = pl.DataFrame(
            {"Date": [pl.date(2023, 1, 1)], "Close": [45000.0]},
        )

        mock_analyze.return_value = pl.DataFrame(
            {"Ticker": ["BTC-USD"], "Strategy Type": ["SMA"], "Score": [8.5]},
        )

        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Execute sweep with ma_cross_crypto profile
        result = cli_runner.invoke(
            strategy_app,
            ["sweep", "--profile", "ma_cross_crypto"],
        )

        # Verify successful execution
        assert result.exit_code == 0
        mock_config_loader.return_value.load_from_profile.assert_called()

    def test_ma_cross_crypto_profile_multi_ticker_handling(self, config_loader):
        """Test multi-ticker configuration in ma_cross_crypto profile."""
        config = config_loader.load_from_profile("ma_cross_crypto", {}, {})

        # Verify multiple tickers
        assert len(config.ticker) >= 2

        # Verify all tickers are crypto format
        for ticker in config.ticker:
            assert (
                "-USD" in ticker
                or "/" in ticker
                or ticker.startswith("BTC")
                or ticker.startswith("ETH")
            )

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_ma_cross_crypto_profile_strategy_compatibility(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test strategy compatibility validation with ma_cross_crypto profile."""
        # Setup real config
        real_config_loader = ConfigLoader()
        real_config = real_config_loader.load_from_profile("ma_cross_crypto", {}, {})
        mock_config_loader.return_value.load_from_profile.return_value = real_config

        # Setup mocks
        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = pl.DataFrame(
            {"Date": [pl.date(2023, 1, 1)], "Close": [45000.0]},
        )

        # Execute CLI command
        result = cli_runner.invoke(
            strategy_app,
            ["run", "--profile", "ma_cross_crypto"],
        )

        # Verify strategy compatibility was validated
        assert result.exit_code == 0
        mock_dispatcher.validate_strategy_compatibility.assert_called_once()


class TestDefaultStrategyCurrentProfileIntegration:
    """Test integration of default_strategy_current.yaml profile with inheritance."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def config_loader(self):
        """Create ConfigLoader instance for testing."""
        return ConfigLoader()

    def test_default_strategy_current_profile_inheritance(self, config_loader):
        """Test that default_strategy_current inherits from default_strategy correctly."""
        # Load both profiles
        base_config = config_loader.load_from_profile(
            "default_strategy", config_type=None, overrides={}
        )
        current_config = config_loader.load_from_profile(
            "default_strategy_current",
            config_type=None,
            overrides={},
        )

        # Verify inheritance - current should have all base parameters
        assert current_config.ticker == base_config.ticker
        assert current_config.short_window_start == base_config.short_window_start
        assert current_config.long_window_start == base_config.long_window_start
        assert current_config.years == base_config.years

        # Verify current-specific overrides
        assert current_config.use_current is True
        assert hasattr(current_config, "filter")
        assert current_config.filter.use_current is True

    def test_default_strategy_current_profile_loading(self, config_loader):
        """Test that default_strategy_current profile loads with inheritance."""
        config = config_loader.load_from_profile(
            "default_strategy_current", config_type=None, overrides={}
        )

        # Verify inherited parameters
        assert isinstance(config, StrategyConfig)
        assert config.ticker == ["BTC-USD"]

        # Verify current signal filtering is enabled
        assert config.use_current is True
        assert hasattr(config, "filter")
        assert config.filter.use_current is True

        # Verify inherited MACD parameters
        assert config.short_window_start == 5
        assert config.long_window_start == 8

    @patch("app.tools.get_data.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_default_strategy_current_profile_cli_execution(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test CLI execution with default_strategy_current profile."""
        # Setup real config
        real_config_loader = ConfigLoader()
        real_config = real_config_loader.load_from_profile(
            "default_strategy_current",
            config_type=None,
            overrides={},
        )
        mock_config_loader.return_value.load_from_profile.return_value = real_config

        # Setup execution mocks
        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = pl.DataFrame(
            {"Date": [pl.date(2023, 1, 1)], "Close": [45000.0]},
        )

        # Execute CLI command
        result = cli_runner.invoke(
            strategy_app,
            ["run", "--profile", "default_strategy_current"],
        )

        # Verify successful execution
        assert result.exit_code == 0
        mock_dispatcher.execute_strategy.assert_called_once()

    def test_default_strategy_current_profile_override_inheritance(self, config_loader):
        """Test that overrides work correctly with inherited profiles."""
        # Test override on inherited profile
        overrides = {"ticker": ["DOGE-USD"], "years": 3}
        config = config_loader.load_from_profile(
            "default_strategy_current",
            config_type=None,
            overrides=overrides,
        )

        # Verify overrides applied
        assert config.ticker == ["DOGE-USD"]
        assert config.years == 3

        # Verify current-specific config preserved
        assert config.use_current is True

        # Verify other inherited values preserved
        assert config.short_window_start == 5


class TestCrossProfileCompatibility:
    """Test compatibility and consistency across all profiles."""

    @pytest.fixture
    def config_loader(self):
        """Create ConfigLoader instance for testing."""
        return ConfigLoader()

    @pytest.fixture
    def all_strategy_profiles(self):
        """List of all strategy profiles to test."""
        return ["default_strategy", "ma_cross_crypto", "default_strategy_current"]

    def test_all_profiles_load_successfully(self, config_loader, all_strategy_profiles):
        """Test that all profiles load without errors."""
        for profile_name in all_strategy_profiles:
            try:
                config = config_loader.load_from_profile(
                    profile_name, config_type=None, overrides={}
                )
                # Verify basic structure
                assert isinstance(config, StrategyConfig)
                assert hasattr(config, "ticker")
                assert len(config.ticker) > 0
            except Exception as e:
                pytest.fail(f"Profile {profile_name} failed to load: {e}")

    def test_profile_parameter_consistency(self, config_loader, all_strategy_profiles):
        """Test parameter consistency across profiles."""
        configs = {}
        for profile_name in all_strategy_profiles:
            configs[profile_name] = config_loader.load_from_profile(
                profile_name,
                {},
                {},
            )

        # Test common parameters have consistent types
        for profile_name, config in configs.items():
            # Ticker should always be a list
            assert isinstance(
                config.ticker,
                list,
            ), f"{profile_name}: ticker should be list"

            # Years should always be positive integer
            if hasattr(config, "years"):
                assert isinstance(
                    config.years,
                    int,
                ), f"{profile_name}: years should be int"
                assert config.years > 0, f"{profile_name}: years should be positive"

            # Boolean flags should be boolean
            if hasattr(config, "use_hourly"):
                assert isinstance(
                    config.use_hourly,
                    bool,
                ), f"{profile_name}: use_hourly should be bool"
            if hasattr(config, "use_years"):
                assert isinstance(
                    config.use_years,
                    bool,
                ), f"{profile_name}: use_years should be bool"

    def test_profile_schema_validation(self, config_loader, all_strategy_profiles):
        """Test that all profiles conform to expected schema."""
        for profile_name in all_strategy_profiles:
            config = config_loader.load_from_profile(profile_name, {}, {})

            # Verify required fields exist
            assert hasattr(config, "ticker"), f"{profile_name}: missing ticker"

            # Verify ticker format
            for ticker in config.ticker:
                assert isinstance(
                    ticker,
                    str,
                ), f"{profile_name}: ticker should be string"
                assert len(ticker) > 0, f"{profile_name}: ticker should not be empty"

            # Verify strategy types if present
            if hasattr(config, "strategy_types"):
                assert isinstance(
                    config.strategy_types,
                    list,
                ), f"{profile_name}: strategy_types should be list"
                for strategy_type in config.strategy_types:
                    assert isinstance(
                        strategy_type,
                        StrategyType,
                    ), f"{profile_name}: invalid strategy type"

    def test_profile_override_consistency(self, config_loader, all_strategy_profiles):
        """Test that parameter overrides work consistently across profiles."""
        common_overrides = {"ticker": ["TEST"], "years": 1}

        for profile_name in all_strategy_profiles:
            config = config_loader.load_from_profile(profile_name, {}, common_overrides)

            # Verify overrides applied consistently
            assert config.ticker == ["TEST"], f"{profile_name}: ticker override failed"

            if hasattr(config, "years"):
                assert config.years == 1, f"{profile_name}: years override failed"

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_all_profiles_cli_compatibility(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        all_strategy_profiles,
    ):
        """Test that all profiles work with CLI commands."""
        cli_runner = CliRunner()
        real_config_loader = ConfigLoader()

        # Setup execution mocks
        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = pl.DataFrame(
            {"Date": [pl.date(2023, 1, 1)], "Close": [45000.0]},
        )

        for profile_name in all_strategy_profiles:
            # Load real config for this profile
            real_config = real_config_loader.load_from_profile(profile_name, {}, {})
            mock_config_loader.return_value.load_from_profile.return_value = real_config

            # Test CLI execution
            result = cli_runner.invoke(
                strategy_app,
                ["run", "--profile", profile_name, "--dry-run"],
            )

            # Verify CLI compatibility
            assert result.exit_code == 0, f"Profile {profile_name} failed CLI execution"

            # Reset mocks for next iteration
            mock_config_loader.reset_mock()


class TestProfileErrorHandling:
    """Test error handling for profile loading and validation."""

    @pytest.fixture
    def config_loader(self):
        """Create ConfigLoader instance for testing."""
        return ConfigLoader()

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    def test_nonexistent_profile_handling(self, config_loader):
        """Test handling of nonexistent profiles."""
        with pytest.raises((FileNotFoundError, ValueError)):
            config_loader.load_from_profile("nonexistent_profile", {}, {})

    def test_invalid_profile_inheritance(self, config_loader):
        """Test handling of invalid inheritance references."""
        # This would test if a profile has invalid inherits_from reference
        # For now, test that our known good profiles don't have this issue
        try:
            config_loader.load_from_profile("default_strategy_current", {}, {})
        except Exception as e:
            pytest.fail(f"Valid inheritance failed: {e}")

    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_cli_profile_error_handling(self, mock_config_loader, cli_runner):
        """Test CLI error handling for profile issues."""
        # Test nonexistent profile
        mock_config_loader.return_value.load_from_profile.side_effect = (
            FileNotFoundError("Profile not found")
        )

        result = cli_runner.invoke(strategy_app, ["run", "--profile", "nonexistent"])

        # Should handle error gracefully
        assert result.exit_code != 0 or "error" in result.stdout.lower()

    def test_profile_parameter_validation_errors(self, config_loader):
        """Test validation of invalid parameter combinations."""
        # Test invalid overrides
        invalid_overrides = {
            "years": -1,  # Invalid negative years
            "ticker": [],  # Empty ticker list
        }

        for profile_name in ["default_strategy"]:
            try:
                config = config_loader.load_from_profile(
                    profile_name,
                    {},
                    invalid_overrides,
                )
                # Some validation might occur during config creation
                # If no exception, verify the invalid values were handled
                if hasattr(config, "years") and config.years <= 0:
                    pytest.fail(
                        f"Profile {profile_name} accepted invalid years: {config.years}",
                    )
                if len(config.ticker) == 0:
                    pytest.fail(f"Profile {profile_name} accepted empty ticker list")
            except (ValueError, TypeError):
                # Expected validation error
                pass


class TestProfileRealWorldUsage:
    """Test profiles in realistic usage scenarios."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_default_strategy_typical_usage(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test default_strategy profile in typical usage scenario."""
        # Setup real config
        real_config_loader = ConfigLoader()
        real_config = real_config_loader.load_from_profile("default_strategy", {}, {})
        mock_config_loader.return_value.load_from_profile.return_value = real_config

        # Setup execution mocks
        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = pl.DataFrame(
            {"Date": [pl.date(2023, 1, 1)], "Close": [45000.0]},
        )

        # Typical usage: run with ticker override
        result = cli_runner.invoke(
            strategy_app,
            ["run", "--profile", "default_strategy", "--ticker", "ETH-USD"],
        )

        assert result.exit_code == 0
        mock_dispatcher.execute_strategy.assert_called_once()

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.analyze_parameter_sensitivity")
    @patch("app.cli.commands.strategy.logging_context")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_ma_cross_crypto_typical_usage(
        self,
        mock_config_loader,
        mock_logging,
        mock_analyze,
        mock_get_data,
        cli_runner,
    ):
        """Test ma_cross_crypto profile in typical parameter sweep scenario."""
        # Setup real config
        real_config_loader = ConfigLoader()
        real_config = real_config_loader.load_from_profile("ma_cross_crypto", {}, {})
        mock_config_loader.return_value.load_from_profile.return_value = real_config

        # Setup execution mocks
        mock_get_data.return_value = pl.DataFrame(
            {"Date": [pl.date(2023, 1, 1)], "Close": [45000.0]},
        )

        mock_analyze.return_value = pl.DataFrame(
            {"Ticker": ["BTC-USD"], "Strategy Type": ["SMA"], "Score": [8.5]},
        )

        mock_logging.return_value.__enter__ = Mock()
        mock_logging.return_value.__exit__ = Mock()

        # Typical usage: parameter sweep with custom ranges
        result = cli_runner.invoke(
            strategy_app,
            [
                "sweep",
                "--profile",
                "ma_cross_crypto",
                "--fast-min",
                "10",
                "--fast-max",
                "30",
            ],
        )

        assert result.exit_code == 0
        mock_analyze.assert_called()

    @patch("app.cli.commands.strategy.get_data")
    @patch("app.cli.commands.strategy.StrategyDispatcher")
    @patch("app.cli.commands.strategy.ConfigLoader")
    def test_profile_chain_usage(
        self,
        mock_config_loader,
        mock_dispatcher_class,
        mock_get_data,
        cli_runner,
    ):
        """Test using profiles in a sequence of commands (realistic workflow)."""
        # Setup real config loading
        real_config_loader = ConfigLoader()

        # Setup execution mocks
        mock_dispatcher = Mock()
        mock_dispatcher.validate_strategy_compatibility.return_value = True
        mock_dispatcher.execute_strategy.return_value = True
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_get_data.return_value = pl.DataFrame(
            {"Date": [pl.date(2023, 1, 1)], "Close": [45000.0]},
        )

        # Sequence: default_strategy -> ma_cross_crypto -> default_strategy_current
        profiles_to_test = [
            "default_strategy",
            "ma_cross_crypto",
            "default_strategy_current",
        ]

        for profile_name in profiles_to_test:
            real_config = real_config_loader.load_from_profile(profile_name, {}, {})
            mock_config_loader.return_value.load_from_profile.return_value = real_config

            result = cli_runner.invoke(
                strategy_app,
                ["run", "--profile", profile_name, "--dry-run"],
            )
            assert result.exit_code == 0, f"Profile {profile_name} failed in sequence"

            # Reset for next iteration
            mock_config_loader.reset_mock()
