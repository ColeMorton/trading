#!/usr/bin/env python3
"""
Automatic Updater for Strategy Breadth Pine Script

This script automatically updates the Strategy Breadth Pine script
when the source CSV file changes. It runs the generator script and
integrates the generated configuration into the Pine script.
"""

import os
import sys
import subprocess
import re
from datetime import datetime
import shutil

def run_generator(csv_path, ticker_filter=None):
    """
    Run the strategy configuration generator and return the path to the generated file.
    
    Args:
        csv_path: Path to the CSV file
        ticker_filter: Optional ticker filter
        
    Returns:
        Path to the generated configuration file
    """
    cmd = ["python", "tradingview/generate_strategy_config.py", csv_path]
    if ticker_filter:
        cmd.append(ticker_filter)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Extract the output file path
            output_line = [line for line in result.stdout.strip().split('\n') if "Configuration saved to" in line]
            if output_line:
                return output_line[0].split("Configuration saved to ")[-1].strip()
        else:
            print("Error executing generator:")
            print(result.stderr)
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def extract_section(file_path, start_marker, end_marker):
    """
    Extract a section from a file between two marker lines.
    
    Args:
        file_path: Path to the file
        start_marker: Start marker line
        end_marker: End marker line
        
    Returns:
        The extracted section as a list of lines
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    section = []
    in_section = False
    
    for line in lines:
        if start_marker in line:
            in_section = True
            continue
        elif end_marker in line:
            break
        
        if in_section:
            section.append(line)
    
    return section

def update_pine_script(pine_script_path, config_file_path):
    """
    Update the Pine script with the generated configuration.
    
    Args:
        pine_script_path: Path to the Pine script
        config_file_path: Path to the generated configuration file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create a backup of the original Pine script
        backup_path = f"{pine_script_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        shutil.copy2(pine_script_path, backup_path)
        print(f"Created backup: {backup_path}")
        
        # Extract sections from the configuration file
        config_section = extract_section(
            config_file_path,
            "// Strategy configuration array",
            "// ================ Ticker Selection"
        )
        
        ticker_section = extract_section(
            config_file_path,
            "// ================ Ticker Selection",
            "// ================ Dynamic Calculation Function"
        )
        
        calc_section = extract_section(
            config_file_path,
            "// ================ Dynamic Calculation Function",
            "// End of file"  # This might need adjustment
        )
        
        # Read the Pine script
        with open(pine_script_path, 'r') as f:
            pine_lines = f.readlines()
        
        # Update the Pine script
        new_pine_lines = []
        skip_section = False
        
        for line in pine_lines:
            # Handle strategy configuration section
            if "// ================ Strategy Configuration" in line:
                new_pine_lines.append(line)
                new_pine_lines.extend(config_section)
                skip_section = True
                continue
            elif "// ================ Dynamic Strategy Processing" in line:
                new_pine_lines.append(line)
                new_pine_lines.extend(calc_section)
                skip_section = True
                continue
            elif "// Ticker selection for filtering strategies" in line:
                # Replace the ticker selection line and the next line
                new_pine_lines.extend(ticker_section)
                skip_section = True
                continue
            elif any(marker in line for marker in [
                "array.push(strategy_configs",
                "calculateBreadth() =>",
                "tickerInput = input.string"
            ]):
                # Skip lines that are part of sections we're replacing
                if skip_section:
                    continue
            else:
                # End of section
                skip_section = False
            
            new_pine_lines.append(line)
        
        # Write the updated Pine script
        with open(pine_script_path, 'w') as f:
            f.writelines(new_pine_lines)
        
        print(f"Updated Pine script: {pine_script_path}")
        return True
    
    except Exception as e:
        print(f"Error updating Pine script: {e}")
        return False

def main():
    """Main function to update the Pine script."""
    if len(sys.argv) < 3:
        print("Usage: python update_strategy_breadth.py <csv_file_path> <pine_script_path> [ticker_filter]")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    pine_script_path = sys.argv[2]
    ticker_filter = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    if not os.path.exists(pine_script_path):
        print(f"Error: Pine script not found: {pine_script_path}")
        sys.exit(1)
    
    # Run the generator
    print(f"Generating configuration from {csv_path}...")
    config_file_path = run_generator(csv_path, ticker_filter)
    
    if not config_file_path or not os.path.exists(config_file_path):
        print("Error: Failed to generate configuration file.")
        sys.exit(1)
    
    # Update the Pine script
    print(f"Updating Pine script {pine_script_path}...")
    if update_pine_script(pine_script_path, config_file_path):
        print("Pine script updated successfully!")
    else:
        print("Failed to update Pine script.")
        sys.exit(1)

if __name__ == "__main__":
    main()