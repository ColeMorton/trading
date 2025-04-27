# Strategy Generator Adaptation Guide

## Overview

This document provides guidance on how to adapt the Python generator scripts to work with the new hardcoded approach for the Strategy Breadth Oscillator. The original generator scripts were designed to create a dynamic, array-based configuration, but due to Pine Script type system limitations, the implementation now uses hardcoded strategy calls.

## Original Generator Scripts

The original implementation included the following generator scripts:

1. `generate_strategy_config.py`: Generates the Pine script configuration from a CSV file
2. `test_strategy_generator.py`: Tests the generator with different CSV files
3. `update_strategy_breadth.py`: Updates the Pine script with the generated configuration
4. `update_strategy_breadth.sh`: Shell script for the update process

## Adaptation Options

There are several options for adapting these scripts to work with the new hardcoded approach:

### Option 1: Generate Hardcoded Strategy Blocks

Modify the generator scripts to output hardcoded strategy blocks instead of array-based configuration:

```python
def generate_hardcoded_strategies(csv_path, ticker_filter=None):
    """
    Generate hardcoded strategy blocks from CSV file.
    
    Args:
        csv_path: Path to the CSV file containing strategy parameters
        ticker_filter: Optional ticker symbol to filter strategies
        
    Returns:
        A string containing hardcoded strategy blocks for the calculateBreadth() function
    """
    strategies = []
    
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for i, row in enumerate(reader):
            ticker = row.get('Ticker', 'ALL')
            
            # Skip if ticker filter is provided and doesn't match
            if ticker_filter and ticker != ticker_filter:
                continue
                
            strategy_type = row.get('Strategy Type', '')
            short_window = row.get('Short Window', '')
            long_window = row.get('Long Window', '')
            signal_window = row.get('Signal Window', '0')
            
            # Skip rows with missing data
            if not all([strategy_type, short_window, long_window]):
                continue
                
            # Create hardcoded strategy block
            if strategy_type == 'SMA':
                strategy_block = f"""
    // Strategy {i}: SMA({short_window}, {long_window})
    totalApplicableStrategies += 1
    if smaCrossSignal({short_window}, {long_window})
        strategiesInPosition += 1
"""
            elif strategy_type == 'EMA':
                strategy_block = f"""
    // Strategy {i}: EMA({short_window}, {long_window})
    totalApplicableStrategies += 1
    if emaCrossSignal({short_window}, {long_window})
        strategiesInPosition += 1
"""
            elif strategy_type == 'MACD':
                strategy_block = f"""
    // Strategy {i}: MACD({short_window}, {long_window}, {signal_window})
    totalApplicableStrategies += 1
    if macdSignal({short_window}, {long_window}, {signal_window})
        strategiesInPosition += 1
"""
            strategies.append(strategy_block)
    
    return "".join(strategies)
```

### Option 2: Template-Based Approach

Create a template for the Pine script with placeholders for the strategy blocks:

```python
def generate_pine_script_from_template(csv_path, template_path, output_path, ticker_filter=None):
    """
    Generate Pine script from template and CSV file.
    
    Args:
        csv_path: Path to the CSV file containing strategy parameters
        template_path: Path to the Pine script template
        output_path: Path to save the generated Pine script
        ticker_filter: Optional ticker symbol to filter strategies
    """
    # Generate hardcoded strategy blocks
    strategy_blocks = generate_hardcoded_strategies(csv_path, ticker_filter)
    
    # Count strategies
    strategy_count = strategy_blocks.count('totalApplicableStrategies += 1')
    
    # Read template
    with open(template_path, 'r') as f:
        template = f.read()
    
    # Replace placeholders
    pine_script = template.replace('{{STRATEGY_BLOCKS}}', strategy_blocks)
    pine_script = pine_script.replace('{{STRATEGY_COUNT}}', str(strategy_count))
    
    # Write output
    with open(output_path, 'w') as f:
        f.write(pine_script)
```

### Option 3: Interactive Update Tool

Create an interactive tool that guides the user through updating the Pine script:

```python
def interactive_update(csv_path, pine_script_path, ticker_filter=None):
    """
    Interactive tool to update the Pine script with strategies from CSV file.
    
    Args:
        csv_path: Path to the CSV file containing strategy parameters
        pine_script_path: Path to the Pine script
        ticker_filter: Optional ticker symbol to filter strategies
    """
    # Read strategies from CSV
    strategies = read_strategies_from_csv(csv_path, ticker_filter)
    
    # Display strategies
    print(f"Found {len(strategies)} strategies in {csv_path}")
    for i, strategy in enumerate(strategies):
        print(f"{i+1}. {strategy['type']}({strategy['short_window']}, {strategy['long_window']}{', ' + strategy['signal_window'] if strategy['type'] == 'MACD' else ''})")
    
    # Generate hardcoded strategy blocks
    strategy_blocks = generate_hardcoded_strategies(csv_path, ticker_filter)
    
    # Display instructions
    print("\nTo update the Pine script:")
    print(f"1. Open {pine_script_path}")
    print("2. Replace the strategy blocks in the calculateBreadth() function with:")
    print(strategy_blocks)
    print(f"3. Update the hline(11, \"Max\", ...) call to hline({len(strategies)}, \"Max\", ...)")
    
    # Ask if user wants to automatically update
    choice = input("\nDo you want to automatically update the Pine script? (y/n): ")
    if choice.lower() == 'y':
        # Read Pine script
        with open(pine_script_path, 'r') as f:
            pine_script = f.read()
        
        # Find and replace strategy blocks
        start_marker = "calculateBreadth() =>"
        end_marker = "// Return both the active strategies and the total applicable strategies"
        
        start_index = pine_script.find(start_marker)
        if start_index == -1:
            print("Error: Could not find calculateBreadth() function in Pine script")
            return
        
        start_index = pine_script.find("\n", start_index) + 1
        
        end_index = pine_script.find(end_marker, start_index)
        if end_index == -1:
            print("Error: Could not find end marker in Pine script")
            return
        
        # Replace strategy blocks
        new_pine_script = pine_script[:start_index]
        new_pine_script += "    int strategiesInPosition = 0\n"
        new_pine_script += "    int totalApplicableStrategies = 0\n"
        new_pine_script += "    \n"
        new_pine_script += "    // Process each strategy directly with hardcoded parameters\n"
        new_pine_script += strategy_blocks
        new_pine_script += pine_script[end_index:]
        
        # Replace hline value
        new_pine_script = new_pine_script.replace('hline(11, "Max"', f'hline({len(strategies)}, "Max"')
        
        # Write updated Pine script
        with open(pine_script_path, 'w') as f:
            f.write(new_pine_script)
        
        print(f"\nPine script updated successfully: {pine_script_path}")
```

## Recommended Approach

The recommended approach is a combination of Options 2 and 3:

1. Create a template-based generator for new Pine scripts
2. Provide an interactive update tool for existing Pine scripts

This approach offers the following benefits:

1. **Flexibility**: Users can choose to generate a new script or update an existing one
2. **Guidance**: The interactive tool provides clear instructions for manual updates
3. **Automation**: The template-based generator automates the creation of new scripts
4. **Safety**: The interactive tool can create backups before making changes

## Implementation Steps

1. Create a Pine script template with placeholders for strategy blocks and count
2. Implement the `generate_hardcoded_strategies` function to create strategy blocks from CSV
3. Implement the `generate_pine_script_from_template` function for new scripts
4. Implement the `interactive_update` function for existing scripts
5. Update the shell script to support both approaches

## Example Template

```pine
//@version=5
indicator("BTC Strategy Breadth Oscillator", shorttitle="StgyBreadth", overlay=false)

// Description:
// This indicator calculates how many strategies from a predefined collection
// are currently in a bullish position. It functions as a breadth oscillator that shows
// market sentiment based on multiple strategies simultaneously.

// ================ Main Configuration ================
var int totalStrategies = {{STRATEGY_COUNT}}  // Total number of strategies
var float lowerBand = 0.0     // Minimum oscillator value
var float upperBand = {{STRATEGY_COUNT}}.0    // Maximum oscillator value (total strategies)

// ... rest of the script ...

// ================ Dynamic Strategy Processing ================
calculateBreadth() =>
    int strategiesInPosition = 0
    int totalApplicableStrategies = 0
    
    // Process each strategy directly with hardcoded parameters
{{STRATEGY_BLOCKS}}
    
    // Return both the active strategies and the total applicable strategies
    [strategiesInPosition, totalApplicableStrategies]

// ... rest of the script ...

// Plot range bands
hline(0, "Min", color=color.new(#787b86, 70), linestyle=hline.style_dotted)
hline({{STRATEGY_COUNT}}, "Max", color=color.new(#787b86, 70), linestyle=hline.style_dotted)

// ... rest of the script ...
```

## Conclusion

While the new hardcoded approach requires more manual intervention than the original dynamic approach, these adapted generator scripts can still provide significant assistance in maintaining the Strategy Breadth Oscillator. By generating hardcoded strategy blocks and providing clear guidance for updates, they help ensure that the Pine script remains maintainable and error-free.