#!/usr/bin/env python3
"""
Statistical Performance Divergence System - Simplified Interface Demo

This demonstrates the dramatically simplified interface where you only need
to specify TWO parameters:
1. PORTFOLIO - the filename (e.g., "risk_on.csv")
2. USE_TRADE_HISTORY - whether to use trade history (True) or equity curves (False)

Files are automatically located:
- Portfolio: ./data/raw/strategies/{portfolio}
- Trade History: ./data/raw/positions/{portfolio} (same filename)
"""

import asyncio
import logging
from pathlib import Path


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

from app.tools.config.statistical_analysis_config import StatisticalAnalysisConfig
from app.tools.portfolio_analyzer import PortfolioStatisticalAnalyzer, analyze_portfolio


async def demo_simplified_interface():
    """Demonstrate the simplified two-parameter interface."""

    print("=" * 70)
    print("STATISTICAL PERFORMANCE DIVERGENCE SYSTEM")
    print("Simplified Interface Demo")
    print("=" * 70)

    # Example portfolios to analyze
    portfolios = [
        ("risk_on.csv", True),  # Use trade history
        ("conservative.csv", True),  # Use trade history
        ("momentum.csv", False),  # Use equity curves
        ("value.csv", False),  # Use equity curves
    ]

    for portfolio_name, use_trade_history in portfolios:
        print(f"\n📊 Analyzing Portfolio: {portfolio_name}")
        print(
            f"   Data Source: {'Trade History' if use_trade_history else 'Equity Curves'}",
        )
        print("-" * 50)

        try:
            # Method 1: Using the analyzer class
            analyzer = PortfolioStatisticalAnalyzer(
                portfolio=portfolio_name,
                use_trade_history=use_trade_history,
            )

            # Show file paths that will be used
            config = analyzer.config
            print(f"   Portfolio file: {config.get_portfolio_file_path()}")
            if use_trade_history:
                print(f"   Trade history:  {config.get_trade_history_file_path()}")

            # Check if files exist
            portfolio_exists = config.get_portfolio_file_path().exists()
            trade_history_exists = (
                config.get_trade_history_file_path().exists()
                if use_trade_history
                else True
            )

            print(f"   Portfolio exists: {'✅' if portfolio_exists else '❌'}")
            if use_trade_history:
                print(
                    f"   Trade history exists: {'✅' if trade_history_exists else '❌'}",
                )

            if portfolio_exists and (trade_history_exists or config.FALLBACK_TO_EQUITY):
                # Perform analysis
                results = await analyzer.analyze()
                summary = analyzer.get_summary_report(results)

                # Display results
                print("\n   Results:")
                print(f"   - Total strategies: {summary['total_strategies']}")
                print(f"   - Immediate exits: {summary['immediate_exits']}")
                print(f"   - Strong sells: {summary['strong_sells']}")
                print(f"   - Holds: {summary['holds']}")
                print(f"   - High confidence: {summary['high_confidence_analyses']}")
                print(f"   - Confidence rate: {summary['confidence_rate']:.1%}")

                # Show individual signals
                exit_signals = analyzer.get_exit_signals(results)
                exit_immediately = [
                    name
                    for name, signal in exit_signals.items()
                    if signal == "EXIT_IMMEDIATELY"
                ]
                if exit_immediately:
                    print(f"   - EXIT IMMEDIATELY: {', '.join(exit_immediately[:3])}")
                    if len(exit_immediately) > 3:
                        print(f"     ... and {len(exit_immediately) - 3} more")
            else:
                print("   ⚠️  Required files not found - skipping analysis")

        except Exception as e:
            print(f"   ❌ Error: {e}")


async def demo_quick_analysis():
    """Demonstrate the one-line analysis function."""

    print("\n" + "=" * 70)
    print("QUICK ANALYSIS FUNCTION DEMO")
    print("=" * 70)

    # One-line portfolio analysis
    try:
        print("\n🚀 Quick analysis of 'risk_on.csv' with trade history...")

        # This is literally all you need:
        _results, summary = await analyze_portfolio(
            "risk_on.csv",
            use_trade_history=True,
        )

        print("✅ Analysis complete!")
        print(f"   Portfolio: {summary['portfolio']}")
        print(f"   Strategies analyzed: {summary['total_strategies']}")
        print(f"   Signal distribution: {summary['signal_distribution']}")

    except FileNotFoundError as e:
        print(f"⚠️  File not found: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_configuration():
    """Demonstrate the simplified configuration interface."""

    print("\n" + "=" * 70)
    print("CONFIGURATION INTERFACE DEMO")
    print("=" * 70)

    # Show how simple the configuration is
    print("\n📝 Creating configurations:")

    # Method 1: Simple interface
    config1 = StatisticalAnalysisConfig.create("risk_on.csv", use_trade_history=True)
    print(
        f"   Config 1: {config1.PORTFOLIO} (trade history: {config1.USE_TRADE_HISTORY})",
    )

    # Method 2: Quick config for different scenarios
    config2 = StatisticalAnalysisConfig.create(
        "conservative.csv",
        use_trade_history=False,
    )
    print(
        f"   Config 2: {config2.PORTFOLIO} (trade history: {config2.USE_TRADE_HISTORY})",
    )

    # Show automatic path resolution
    print("\n📂 Automatic path resolution:")
    print(f"   Portfolio path: {config1.get_portfolio_file_path()}")
    print(f"   Trade history path: {config1.get_trade_history_file_path()}")

    # Show what the old complex interface looked like vs new simple interface
    print("\n🔄 Interface Comparison:")
    print("   OLD (complex): StatisticalAnalysisService(config=SPDSConfig(")
    print("      USE_TRADE_HISTORY=True,")
    print("      TRADE_HISTORY_PATH='./data/raw/positions/',")
    print("      PERCENTILE_THRESHOLD=95,")
    print("      DUAL_LAYER_THRESHOLD=0.85,")
    print("      ... 20+ more parameters")
    print("   ))")
    print()
    print(
        "   NEW (simple): PortfolioStatisticalAnalyzer('risk_on.csv', use_trade_history=True)",
    )


def create_demo_portfolio_files():
    """Create demo portfolio files for testing."""

    print("\n📁 Creating demo portfolio files...")

    # Ensure directories exist
    Path("./data/raw/strategies/").mkdir(parents=True, exist_ok=True)
    Path("./data/raw/positions/").mkdir(parents=True, exist_ok=True)

    # Demo portfolio CSV content
    demo_portfolios = {
        "risk_on.csv": """strategy_name,ticker,allocation,risk_level
AAPL_SMA_20_50,AAPL,0.15,medium
TSLA_EMA_12_26,TSLA,0.12,high
NVDA_SMA_15_35,NVDA,0.10,high
MSFT_EMA_21_50,MSFT,0.08,low""",
        "conservative.csv": """strategy_name,ticker,allocation,risk_level
SPY_SMA_50_200,SPY,0.25,low
VTI_EMA_20_60,VTI,0.20,low
BND_SMA_10_30,BND,0.15,very_low
GLD_EMA_15_45,GLD,0.10,medium""",
        "momentum.csv": """strategy_name,ticker,allocation,risk_level
QQQ_MACD_12_26,QQQ,0.20,medium
ARKK_RSI_14,ARKK,0.15,high
TQQQ_MOMENTUM,TQQQ,0.10,very_high
SOXL_BREAKOUT,SOXL,0.08,very_high""",
    }

    # Create portfolio files
    for filename, content in demo_portfolios.items():
        filepath = Path(f"./data/raw/strategies/{filename}")
        with open(filepath, "w") as f:
            f.write(content)
        print(f"   Created: {filepath}")

    # Demo trade history (simplified)
    demo_trade_history = """strategy_name,ticker,entry_date,exit_date,return,mfe,mae,duration_days,trade_quality
AAPL_SMA_20_50,AAPL,2024-01-15,2024-02-28,0.187,0.234,0.057,44,excellent
TSLA_EMA_12_26,TSLA,2024-02-01,2024-03-15,0.143,0.189,0.034,43,good
NVDA_SMA_15_35,NVDA,2024-03-01,2024-04-12,0.312,0.387,0.089,42,excellent"""

    # Create trade history file
    trade_history_path = Path("./data/raw/positions/risk_on.csv")
    with open(trade_history_path, "w") as f:
        f.write(demo_trade_history)
    print(f"   Created: {trade_history_path}")

    print("✅ Demo files created!")


async def main():
    """Run all demos."""

    print("🎯 Statistical Performance Divergence System")
    print("   Simplified Interface - Two Parameter Solution")
    print("   Portfolio-Centric Analysis")
    print()

    # Show the simplified configuration interface
    demo_configuration()

    # Create demo files for testing
    create_demo_portfolio_files()

    # Demonstrate the simplified analyzer interface
    await demo_simplified_interface()

    # Demonstrate the one-line analysis function
    await demo_quick_analysis()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✅ The interface has been dramatically simplified to TWO parameters:")
    print("   1. PORTFOLIO - filename (e.g., 'risk_on.csv')")
    print("   2. USE_TRADE_HISTORY - True (trade history) or False (equity curves)")
    print()
    print("📂 File locations are automatic:")
    print("   - Portfolios: ./data/raw/strategies/{portfolio}")
    print("   - Trade History: ./data/raw/positions/{portfolio}")
    print("   - Return Distributions: ./data/raw/reports/return_distribution/")
    print()
    print("🚀 Usage is now incredibly simple:")
    print("   analyzer = PortfolioStatisticalAnalyzer('risk_on.csv', True)")
    print("   results = await analyzer.analyze()")
    print()
    print("   # Or even simpler:")
    print("   results, summary = await analyze_portfolio('risk_on.csv', True)")


if __name__ == "__main__":
    asyncio.run(main())
