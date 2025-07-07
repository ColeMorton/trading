#!/usr/bin/env python3
"""
Trade History Close Live Signal - Usage Examples

This script demonstrates various ways to use the trade_history_close_live_signal
command for generating comprehensive sell signal reports.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str):
    """Run a command and display results"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print("\nOutput:")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("Stderr:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")


def main():
    """Run examples of the trade_history_close_live_signal command"""

    print("🎯 Trade History Close Live Signal - Usage Examples")
    print("Demonstrating comprehensive sell signal analysis capabilities")

    # Example 1: List all available strategies
    run_command(
        [
            sys.executable,
            "-m",
            "app.tools.trade_history_close_live_signal",
            "--list-strategies",
        ],
        "List all available strategies with signal classifications",
    )

    # Example 2: Health check
    run_command(
        [
            sys.executable,
            "-m",
            "app.tools.trade_history_close_live_signal",
            "--health-check",
        ],
        "Perform comprehensive system health check",
    )

    # Example 3: Generate markdown report for SELL signal strategy
    run_command(
        [
            sys.executable,
            "-m",
            "app.tools.trade_history_close_live_signal",
            "--strategy",
            "MA_SMA_78_82",
            "--output",
            "/tmp/MA_sell_analysis.md",
        ],
        "Generate comprehensive sell signal report for MA strategy (SELL signal)",
    )

    # Example 4: Generate JSON report for CRWD with enhanced analysis
    run_command(
        [
            sys.executable,
            "-m",
            "app.tools.trade_history_close_live_signal",
            "--strategy",
            "CRWD_EMA_5_21",
            "--format",
            "json",
            "--current-price",
            "245.50",
            "--market-condition",
            "bearish",
            "--output",
            "/tmp/CRWD_enhanced_analysis.json",
        ],
        "Generate JSON report with market condition and current price",
    )

    # Example 5: Generate report for HOLD signal strategy
    run_command(
        [
            sys.executable,
            "-m",
            "app.tools.trade_history_close_live_signal",
            "--strategy",
            "QCOM_SMA_49_66",
            "--include-raw-data",
            "--output",
            "/tmp/QCOM_hold_analysis.md",
        ],
        "Generate detailed report for HOLD signal strategy with raw data",
    )

    # Example 6: Quick analysis to stdout
    run_command(
        [
            sys.executable,
            "-m",
            "app.tools.trade_history_close_live_signal",
            "--strategy",
            "AMD_SMA_7_45",
        ],
        "Quick analysis output to console (stdout)",
    )

    # Example 7: Data validation
    run_command(
        [
            sys.executable,
            "-m",
            "app.tools.trade_history_close_live_signal",
            "--validate-data",
        ],
        "Validate data integrity across all SPDS export sources",
    )

    print(f"\n{'='*60}")
    print("✅ All examples completed!")
    print("📁 Generated reports saved to /tmp/")
    print("🔍 Check the output files for comprehensive analysis results")
    print(f"{'='*60}")

    # Display generated files
    print("\n📄 Generated Files:")
    output_files = [
        "/tmp/MA_sell_analysis.md",
        "/tmp/CRWD_enhanced_analysis.json",
        "/tmp/QCOM_hold_analysis.md",
    ]

    for file_path in output_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"  ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"  ❌ {file_path} (not found)")


if __name__ == "__main__":
    main()
