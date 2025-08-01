#!/usr/bin/env python3
"""
Debug script to trace MACD strategy routing and export flow
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import importlib.util
import sys

# Import the MACD module directly
spec = importlib.util.spec_from_file_location(
    "macd_portfolios",
    project_root / "app" / "strategies" / "macd" / "1_get_portfolios.py",
)
macd_portfolios = importlib.util.module_from_spec(spec)
spec.loader.exec_module(macd_portfolios)
# from app.strategies.macd.config_types import DEFAULT_CONFIG  # Removed - using inline config
from app.tools.setup_logging import setup_logging


def test_macd_routing():
    """Test MACD strategy routing and export flow"""
    print("=== MACD Routing Debug Test ===")

    # Setup test config - inline configuration
    test_config = {
        "TICKER": "TSLA",
        "SHORT_WINDOW_START": 8,
        "SHORT_WINDOW_END": 12,
        "LONG_WINDOW_START": 21,
        "LONG_WINDOW_END": 26,
        "SIGNAL_WINDOW_START": 9,
        "SIGNAL_WINDOW_END": 9,
        "DIRECTION": "Long",
        "USE_CURRENT": True,
        "USE_HOURLY": False,
        "USE_YEARS": False,
        "YEARS": 15,
        "STEP": 1,
        "BASE_DIR": ".",
        "REFRESH": True
    }

    print(f"Test config strategy types: {test_config.get('STRATEGY_TYPES', 'Not set')}")
    print(f"Test config direction: {test_config.get('DIRECTION', 'Not set')}")

    # Setup logging
    log, log_close, _, _ = setup_logging(
        module_name="debug_macd", log_file="debug_macd_routing.log"
    )

    try:
        print("Starting MACD analysis...")
        result = macd_portfolios.run(test_config)
        print(f"MACD analysis result: {result}")

        # Check what files were created
        import os

        base_path = "/Users/colemorton/Projects/trading/data/raw"

        portfolios_path = f"{base_path}/portfolios/"
        filtered_path = f"{base_path}/portfolios_filtered/"
        best_path = f"{base_path}/portfolios_best/"

        print("\n=== File System Check ===")

        # Check base portfolios
        if os.path.exists(portfolios_path):
            base_files = [
                f for f in os.listdir(portfolios_path) if "TSLA" in f and "MACD" in f
            ]
            print(f"Base portfolios: {base_files}")
        else:
            print("Base portfolios directory doesn't exist")

        # Check filtered portfolios
        if os.path.exists(filtered_path):
            filtered_files = [
                f for f in os.listdir(filtered_path) if "TSLA" in f and "MACD" in f
            ]
            print(f"Filtered portfolios: {filtered_files}")
        else:
            print("Filtered portfolios directory doesn't exist")

        # Check best portfolios
        if os.path.exists(best_path):
            best_files = [
                f for f in os.listdir(best_path) if "TSLA" in f and "MACD" in f
            ]
            print(f"Best portfolios: {best_files}")
        else:
            print("Best portfolios directory doesn't exist")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback

        traceback.print_exc()
    finally:
        log_close()

    # Also check the log file
    print("\n=== Log File Check ===")
    log_path = "/Users/colemorton/Projects/trading/debug_macd_routing.log"
    try:
        with open(log_path, "r") as f:
            log_content = f.read()
            print("Key log entries:")
            for line in log_content.split("\n"):
                if any(
                    keyword in line.lower()
                    for keyword in ["processing", "filter", "export", "error", "macd"]
                ):
                    print(f"  {line}")
    except FileNotFoundError:
        print("Log file not found")


if __name__ == "__main__":
    test_macd_routing()
