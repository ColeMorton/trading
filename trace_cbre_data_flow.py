#!/usr/bin/env python3
"""
CBRE Data Flow Tracing Script
Phase 1 Implementation: Trace where 4 metric types get reduced to 1

This script simulates the data flow from portfolios_filtered to aggregation
to identify the exact location where data reduction occurs.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.strategies.tools.summary_processing import export_summary_results
from app.tools.get_config import get_config


def create_mock_cbre_portfolios():
    """
    Create mock CBRE portfolio data with 4 metric types for the same configuration.
    This simulates what should be coming from portfolios_filtered CSV.
    """
    base_portfolio = {
        "Ticker": "CBRE",
        "Strategy Type": "SMA",
        "Short Window": 35,
        "Long Window": 50,
        "Signal Window": 0,
        "Signal Entry": True,
        "Signal Exit": False,
        "Total Open Trades": 1,
        "Total Trades": 56,
        "Score": 1.518242394931097,
        "Win Rate [%]": 58.18181818181818,
        "Profit Factor": 2.338158140795567,
        "Expectancy per Trade": 8.239056161437892,
        "Sortino Ratio": 1.3222294815079676,
        "Beats BNH [%]": 0.606137644708798,
        "Total Return [%]": 3191.005915014437,
        "Benchmark Return [%]": 1986.757439828879,
        "Max Gross Exposure [%]": 100.0,
        "Total Fees Paid": 1659.7642366012012,
        "Max Drawdown [%]": 31.736685078735093,
        "Max Drawdown Duration": "1216 days 00:00:00",
        "Total Closed Trades": 55,
        "Best Trade [%]": 92.68948013538161,
        "Worst Trade [%]": -18.937826934938894,
        "Avg Winning Trade [%]": 18.436605589383863,
        "Avg Losing Trade [%]": -5.9488386948347625,
        "Expectancy": 580.7812583508094,
        "Sharpe Ratio": 0.8516114620789481,
        "Calmar Ratio": 0.8605988169848027,
        "Omega Ratio": 1.1849690013526852,
        "Allocation [%]": 2.78,  # This should be reduced to None for analysis exports
    }

    # Create 4 portfolios with different metric types for the same configuration
    portfolios = []
    metric_types = [
        "Most Calmar Ratio",
        "Most Expectancy",
        "Median Max Drawdown Duration",
        "Least Max Drawdown [%]",
    ]

    for metric_type in metric_types:
        portfolio = base_portfolio.copy()
        portfolio["Metric Type"] = metric_type
        portfolios.append(portfolio)

    return portfolios


def mock_log(message, level="info"):
    """Mock logging function that prints with level prefix"""
    print(f"[{level.upper()}] {message}")


def trace_cbre_data_flow():
    """
    Trace the CBRE data flow through the export pipeline with enhanced logging.
    """
    print("=" * 80)
    print("🔍 PHASE 1 DATA FLOW TRACING: CBRE Portfolio Aggregation")
    print("=" * 80)

    # Create mock CBRE portfolios (simulating portfolios_filtered input)
    mock_portfolios = create_mock_cbre_portfolios()
    print(f"✅ Created {len(mock_portfolios)} mock CBRE portfolios with metric types:")
    for i, p in enumerate(mock_portfolios):
        print(f"   {i+1}. {p['Metric Type']}")

    # Get configuration
    config = get_config({})

    # Test portfolios_best export which should use aggregation
    print("\n🚀 Testing portfolios_best export with aggregation...")
    try:
        from app.tools.strategy.export_portfolios import export_portfolios

        # Configure for portfolios_best export (this should trigger aggregation)
        config["USE_MA"] = False

        success_df, success = export_portfolios(
            portfolios=mock_portfolios,
            config=config,
            export_type="portfolios_best",
            csv_filename="cbre_aggregation_test",
            log=mock_log,
        )
        print(f"\n📊 Export completed with success={success}")
    except Exception as e:
        print(f"\n❌ Export failed with error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    trace_cbre_data_flow()
