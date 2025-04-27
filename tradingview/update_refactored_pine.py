#!/usr/bin/env python3
"""
Update Strategy Breadth Refactored Pine Script

This script updates the strategy_breadth_refactored.pine file with the latest
strategies from the CSV file, following the best practices identified in the
error resolution process.
"""

import os
import sys
import subprocess
from datetime import datetime

def main():
    """Main function to update the refactored Pine script."""
    # Default paths
    csv_path = "csv/strategies/BTC_d_20250427.csv"
    pine_script_path = "tradingview/strategy_breadth_refactored.pine"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    if len(sys.argv) > 2:
        pine_script_path = sys.argv[2]
    
    # Check if files exist
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    if not os.path.exists(pine_script_path):
        print(f"Error: Pine script not found: {pine_script_path}")
        sys.exit(1)
    
    # Create a backup of the original Pine script
    backup_path = f"{pine_script_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        with open(pine_script_path, 'r') as f_in, open(backup_path, 'w') as f_out:
            f_out.write(f_in.read())
        print(f"Created backup: {backup_path}")
    except Exception as e:
        print(f"Error creating backup: {e}")
        sys.exit(1)
    
    # Run the hardcoded generator to update the Pine script
    print(f"Updating {pine_script_path} with strategies from {csv_path}...")
    cmd = ["python", "tradingview/generate_hardcoded_config.py", csv_path, pine_script_path]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Update successful!")
            print(result.stdout)
        else:
            print("Error updating Pine script:")
            print(result.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Exception: {e}")
        sys.exit(1)
    
    print(f"\nThe {pine_script_path} file has been updated with the latest strategies from {csv_path}.")
    print("You can now upload the updated script to TradingView.")

if __name__ == "__main__":
    main()