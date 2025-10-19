"""
Command Line Interface for Strategy Template Generator

Provides interactive CLI for creating new strategies using templates.
"""

import argparse
import sys

from .config_template import IndicatorType, StrategyType, TemplateConfig
from .generator import StrategyTemplateGenerator


class StrategyTemplateCLI:
    """Command line interface for strategy template generator."""

    def __init__(self):
        self.generator = None
        self._initialize_generator()

    def _initialize_generator(self):
        """Initialize the strategy generator."""
        try:
            self.generator = StrategyTemplateGenerator()
        except ValueError as e:
            print(f"Error: {e}")
            print("Please ensure you're running from the project root directory.")
            sys.exit(1)

    def run(self):
        """Run the CLI application."""
        parser = self._create_parser()
        args = parser.parse_args()

        if hasattr(args, "func"):
            args.func(args)
        else:
            parser.print_help()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description="Strategy Template Generator - Create new trading strategies from templates",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        subparsers = parser.add_subparsers(title="commands", dest="command")

        # Create strategy command
        create_parser = subparsers.add_parser(
            "create", help="Create a new strategy from template"
        )
        self._add_create_arguments(create_parser)
        create_parser.set_defaults(func=self._create_strategy)

        # List strategies command
        list_parser = subparsers.add_parser("list", help="List existing strategies")
        list_parser.set_defaults(func=self._list_strategies)

        # Info command
        info_parser = subparsers.add_parser(
            "info", help="Get information about a strategy"
        )
        info_parser.add_argument("strategy_name", help="Name of the strategy")
        info_parser.set_defaults(func=self._strategy_info)

        # Interactive command
        interactive_parser = subparsers.add_parser(
            "interactive", help="Interactive strategy creation wizard"
        )
        interactive_parser.add_argument(
            "--overwrite", action="store_true", help="Overwrite existing strategy"
        )
        interactive_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be generated without creating files",
        )
        interactive_parser.set_defaults(func=self._interactive_create)

        return parser

    def _add_create_arguments(self, parser: argparse.ArgumentParser):
        """Add arguments for create command."""
        parser.add_argument(
            "strategy_name", help="Name of the strategy (e.g., my_custom_strategy)"
        )

        parser.add_argument(
            "--type",
            choices=[t.value for t in StrategyType],
            default="custom",
            help="Strategy type",
        )

        parser.add_argument(
            "--primary-indicator",
            choices=[i.value for i in IndicatorType],
            default="sma",
            help="Primary technical indicator",
        )

        parser.add_argument(
            "--secondary-indicators",
            nargs="*",
            choices=[i.value for i in IndicatorType],
            default=[],
            help="Secondary technical indicators",
        )

        parser.add_argument(
            "--description",
            default="Custom trading strategy",
            help="Strategy description",
        )

        parser.add_argument("--ticker", default="AAPL", help="Default ticker symbol")

        parser.add_argument(
            "--timeframe",
            default="daily",
            choices=["daily", "hourly", "minute"],
            help="Default timeframe",
        )

        parser.add_argument(
            "--direction",
            default="Long",
            choices=["Long", "Short", "Both"],
            help="Trading direction",
        )

        parser.add_argument(
            "--no-stop-loss", action="store_true", help="Disable stop loss"
        )

        parser.add_argument(
            "--no-take-profit", action="store_true", help="Disable take profit"
        )

        parser.add_argument(
            "--position-sizing",
            choices=["fixed", "percentage", "kelly"],
            default="fixed",
            help="Position sizing method",
        )

        parser.add_argument(
            "--overwrite", action="store_true", help="Overwrite existing strategy"
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be generated without creating files",
        )

    def _create_strategy(self, args):
        """Create a new strategy."""
        try:
            # Validate strategy name
            self.generator.validate_strategy_name(args.strategy_name)

            # Create template configuration
            config = TemplateConfig(
                strategy_name=args.strategy_name,
                strategy_type=StrategyType(args.type),
                description=args.description,
                primary_indicator=IndicatorType(args.primary_indicator),
                secondary_indicators=[
                    IndicatorType(ind) for ind in args.secondary_indicators
                ],
                entry_conditions=self._get_default_entry_conditions(args.type),
                exit_conditions=self._get_default_exit_conditions(args.type),
                stop_loss_enabled=not args.no_stop_loss,
                take_profit_enabled=not args.no_take_profit,
                position_sizing=args.position_sizing,
                default_ticker=args.ticker,
                default_timeframe=args.timeframe,
            )

            # Generate strategy
            if args.dry_run:
                print(f"DRY RUN: Would create strategy '{args.strategy_name}'")
                print(f"Strategy type: {args.type}")
                print(f"Primary indicator: {args.primary_indicator}")
                if args.secondary_indicators:
                    print(
                        f"Secondary indicators: {', '.join(args.secondary_indicators)}"
                    )
                print(f"Description: {args.description}")

                files = self.generator.generate_strategy(config, dry_run=True)
                print(f"\nWould generate {len(files)} files:")
                for file_path in sorted(files.keys()):
                    print(f"  - {file_path}")
            else:
                result = self.generator.generate_strategy(
                    config, overwrite=args.overwrite, dry_run=False
                )

                print(f"✅ Successfully created strategy '{args.strategy_name}'")
                print(f"📁 Location: {result['strategy_path']}")
                print(f"📄 Files created: {result['file_count']}")
                print("\nNext steps:")
                print("1. Review the generated configuration in config_types.py")
                print("2. Customize the strategy logic in tools/strategy_execution.py")
                print(
                    f"3. Run tests: pytest {result['strategy_path']}/test_strategy.py"
                )
                print(
                    f"4. Execute strategy: python {result['strategy_path']}/1_get_portfolios.py"
                )

        except Exception as e:
            print(f"❌ Error creating strategy: {e}")
            sys.exit(1)

    def _list_strategies(self, args):
        """List existing strategies."""
        strategies = self.generator.list_available_strategies()

        if not strategies:
            print("No strategies found.")
            return

        print(f"Found {len(strategies)} strategies:")
        for strategy in strategies:
            print(f"  - {strategy}")

    def _strategy_info(self, args):
        """Get information about a strategy."""
        info = self.generator.get_strategy_info(args.strategy_name)

        if info is None:
            print(f"Strategy '{args.strategy_name}' not found.")
            return

        print(f"Strategy: {info['name']}")
        print(f"Path: {info['path']}")
        print(f"Tools directory: {'✅' if info['tools_dir'] else '❌'}")

        print("\nFiles:")
        for file_info in info["files"]:
            status = "✅" if file_info["exists"] else "❌"
            size = f"({file_info['size']} bytes)" if file_info["exists"] else ""
            print(f"  {status} {file_info['name']} {size}")

        if info["tools_files"]:
            print(f"\nTools files: {', '.join(info['tools_files'])}")

    def _interactive_create(self, args):
        """Interactive strategy creation wizard."""
        print("🚀 Strategy Template Generator - Interactive Mode")
        print("=" * 50)

        try:
            # Get strategy name
            strategy_name = self._prompt_strategy_name()

            # Get strategy type
            strategy_type = self._prompt_strategy_type()

            # Get description
            description = self._prompt_description()

            # Get indicators
            primary_indicator, secondary_indicators = self._prompt_indicators()

            # Get trading settings
            trading_settings = self._prompt_trading_settings()

            # Get risk management
            risk_settings = self._prompt_risk_management()

            # Create configuration
            config = TemplateConfig(
                strategy_name=strategy_name,
                strategy_type=strategy_type,
                description=description,
                primary_indicator=primary_indicator,
                secondary_indicators=secondary_indicators,
                entry_conditions=self._get_default_entry_conditions(
                    strategy_type.value
                ),
                exit_conditions=self._get_default_exit_conditions(strategy_type.value),
                stop_loss_enabled=risk_settings["stop_loss"],
                take_profit_enabled=risk_settings["take_profit"],
                position_sizing=risk_settings["position_sizing"],
                default_ticker=trading_settings["ticker"],
                default_timeframe=trading_settings["timeframe"],
            )

            # Show summary
            self._show_strategy_summary(config)

            # Confirm creation
            if not self._confirm_creation():
                print("Strategy creation cancelled.")
                return

            # Generate strategy
            if args.dry_run:
                files = self.generator.generate_strategy(config, dry_run=True)
                print(f"\nDRY RUN: Would generate {len(files)} files")
                return

            result = self.generator.generate_strategy(
                config, overwrite=args.overwrite, dry_run=False
            )

            print(f"\n✅ Strategy '{strategy_name}' created successfully!")
            print(f"📁 Location: {result['strategy_path']}")
            print(f"📄 Files created: {result['file_count']}")

        except KeyboardInterrupt:
            print("\n\nStrategy creation cancelled.")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)

    def _prompt_strategy_name(self) -> str:
        """Prompt for strategy name."""
        while True:
            name = input("\n📝 Enter strategy name (e.g., my_rsi_strategy): ").strip()

            if not name:
                print("Strategy name cannot be empty.")
                continue

            try:
                self.generator.validate_strategy_name(name)

                # Check if exists
                if self.generator.get_strategy_info(name) is not None:
                    print(f"⚠️  Strategy '{name}' already exists.")
                    continue

                return name
            except ValueError as e:
                print(f"Invalid name: {e}")

    def _prompt_strategy_type(self) -> StrategyType:
        """Prompt for strategy type."""
        print("\n📊 Select strategy type:")
        types = list(StrategyType)
        for i, strategy_type in enumerate(types, 1):
            print(f"  {i}. {strategy_type.value.replace('_', ' ').title()}")

        while True:
            try:
                choice = input(
                    f"\nEnter choice (1-{len(types)}) [default: 7 (Custom)]: "
                ).strip()

                if not choice:
                    return StrategyType.CUSTOM

                index = int(choice) - 1
                if 0 <= index < len(types):
                    return types[index]
                print(f"Please enter a number between 1 and {len(types)}")
            except ValueError:
                print("Please enter a valid number.")

    def _prompt_description(self) -> str:
        """Prompt for strategy description."""
        description = input(
            "\n📋 Enter strategy description [default: Custom trading strategy]: "
        ).strip()
        return description or "Custom trading strategy"

    def _prompt_indicators(self) -> tuple[IndicatorType, list[IndicatorType]]:
        """Prompt for technical indicators."""
        print("\n🔍 Select primary technical indicator:")
        indicators = list(IndicatorType)
        for i, indicator in enumerate(indicators, 1):
            print(f"  {i}. {indicator.value.upper()}")

        while True:
            try:
                choice = input(
                    f"\nEnter choice (1-{len(indicators)}) [default: 1 (SMA)]: "
                ).strip()

                if not choice:
                    primary = IndicatorType.SMA
                else:
                    index = int(choice) - 1
                    if 0 <= index < len(indicators):
                        primary = indicators[index]
                    else:
                        print(f"Please enter a number between 1 and {len(indicators)}")
                        continue
                break
            except ValueError:
                print("Please enter a valid number.")

        # Secondary indicators
        print("\n🔍 Select secondary indicators (optional):")
        print("Enter indicator numbers separated by spaces, or press Enter to skip")
        for i, indicator in enumerate(indicators, 1):
            if indicator != primary:
                print(f"  {i}. {indicator.value.upper()}")

        secondary_input = input("\nSecondary indicators: ").strip()
        secondary = []

        if secondary_input:
            try:
                choices = [int(x) - 1 for x in secondary_input.split()]
                for index in choices:
                    if 0 <= index < len(indicators) and indicators[index] != primary:
                        secondary.append(indicators[index])
            except ValueError:
                print("Invalid input for secondary indicators, skipping.")

        return primary, secondary

    def _prompt_trading_settings(self) -> dict:
        """Prompt for trading settings."""
        print("\n📈 Trading Settings:")

        ticker = input("Default ticker symbol [AAPL]: ").strip().upper() or "AAPL"

        print("Timeframe options:")
        print("  1. Daily")
        print("  2. Hourly")
        print("  3. Minute")

        timeframe_choice = input("Select timeframe (1-3) [1]: ").strip() or "1"
        timeframes = {"1": "daily", "2": "hourly", "3": "minute"}
        timeframe = timeframes.get(timeframe_choice, "daily")

        return {"ticker": ticker, "timeframe": timeframe}

    def _prompt_risk_management(self) -> dict:
        """Prompt for risk management settings."""
        print("\n🛡️  Risk Management Settings:")

        stop_loss = input("Enable stop loss? (y/n) [y]: ").strip().lower()
        stop_loss = stop_loss != "n"

        take_profit = input("Enable take profit? (y/n) [y]: ").strip().lower()
        take_profit = take_profit != "n"

        print("Position sizing options:")
        print("  1. Fixed")
        print("  2. Percentage")
        print("  3. Kelly Criterion")

        sizing_choice = input("Select position sizing (1-3) [1]: ").strip() or "1"
        sizing_map = {"1": "fixed", "2": "percentage", "3": "kelly"}
        position_sizing = sizing_map.get(sizing_choice, "fixed")

        return {
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "position_sizing": position_sizing,
        }

    def _show_strategy_summary(self, config: TemplateConfig):
        """Show strategy configuration summary."""
        print("\n" + "=" * 50)
        print("📋 Strategy Configuration Summary")
        print("=" * 50)
        print(f"Name: {config.strategy_name}")
        print(f"Type: {config.strategy_type.value.replace('_', ' ').title()}")
        print(f"Description: {config.description}")
        print(f"Primary Indicator: {config.primary_indicator.value.upper()}")
        if config.secondary_indicators:
            print(
                f"Secondary Indicators: {', '.join(ind.value.upper() for ind in config.secondary_indicators)}"
            )
        print(f"Default Ticker: {config.default_ticker}")
        print(f"Timeframe: {config.default_timeframe}")
        print(f"Stop Loss: {'✅' if config.stop_loss_enabled else '❌'}")
        print(f"Take Profit: {'✅' if config.take_profit_enabled else '❌'}")
        print(f"Position Sizing: {config.position_sizing.title()}")
        print("=" * 50)

    def _confirm_creation(self) -> bool:
        """Confirm strategy creation."""
        response = input("\n✅ Create this strategy? (y/n) [y]: ").strip().lower()
        return response != "n"

    def _get_default_entry_conditions(self, strategy_type: str) -> list[str]:
        """Get default entry conditions for strategy type."""
        conditions = {
            "moving_average": [
                "Short MA crosses above Long MA (bullish crossover)",
                "Price is above both moving averages",
                "Volume confirmation (optional)",
            ],
            "rsi": [
                "RSI crosses above oversold threshold (e.g., 30)",
                "RSI momentum is positive",
                "Price confirmation with trend",
            ],
            "macd": [
                "MACD line crosses above signal line",
                "MACD histogram is positive",
                "Price is in uptrend",
            ],
            "bollinger_bands": [
                "Price bounces off lower Bollinger Band",
                "RSI is oversold (confirmation)",
                "Volume spike on entry",
            ],
            "stochastic": [
                "Stochastic %K crosses above %D",
                "Both indicators are in oversold region",
                "Price momentum confirmation",
            ],
            "momentum": [
                "Momentum indicator above threshold",
                "Price breaks resistance level",
                "Volume confirmation",
            ],
        }

        return conditions.get(
            strategy_type,
            [
                "Custom entry condition 1",
                "Custom entry condition 2",
                "Custom entry condition 3",
            ],
        )

    def _get_default_exit_conditions(self, strategy_type: str) -> list[str]:
        """Get default exit conditions for strategy type."""
        conditions = {
            "moving_average": [
                "Short MA crosses below Long MA (bearish crossover)",
                "Price falls below stop loss",
                "Take profit target reached",
            ],
            "rsi": [
                "RSI crosses below overbought threshold (e.g., 70)",
                "RSI momentum turns negative",
                "Stop loss or take profit triggered",
            ],
            "macd": [
                "MACD line crosses below signal line",
                "MACD histogram turns negative",
                "Stop loss or take profit triggered",
            ],
            "bollinger_bands": [
                "Price reaches upper Bollinger Band",
                "RSI is overbought (confirmation)",
                "Stop loss or take profit triggered",
            ],
            "stochastic": [
                "Stochastic %K crosses below %D",
                "Both indicators are in overbought region",
                "Stop loss or take profit triggered",
            ],
            "momentum": [
                "Momentum indicator below threshold",
                "Price breaks support level",
                "Stop loss or take profit triggered",
            ],
        }

        return conditions.get(
            strategy_type,
            [
                "Custom exit condition 1",
                "Custom exit condition 2",
                "Custom exit condition 3",
            ],
        )


def main():
    """Main entry point for CLI."""
    cli = StrategyTemplateCLI()
    cli.run()


if __name__ == "__main__":
    main()
