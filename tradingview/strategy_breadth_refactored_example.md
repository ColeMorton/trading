# Strategy Breadth Pine Script Refactoring Example

This document provides a before-and-after comparison of the Strategy Breadth Pine script to illustrate the benefits of the proposed refactoring approach.

## Current Implementation (Before)

The current implementation has hardcoded strategy parameters and individual blocks for each strategy:

```pine
// ================ Apply Strategies ================
calculateBreadth() =>
    int strategiesInPosition = 0
    
    // SMA Strategy 1: 104, 105
    shortSMA1 = checkParameter(104, "Short SMA Window")
    longSMA1 = checkParameter(105, "Long SMA Window")
    if smaCrossSignal(shortSMA1, longSMA1)
        strategiesInPosition += 1
    
    // SMA Strategy 2: 26, 38
    shortSMA2 = checkParameter(26, "Short SMA Window")
    longSMA2 = checkParameter(38, "Long SMA Window")
    if smaCrossSignal(shortSMA2, longSMA2)
        strategiesInPosition += 1
        
    // ... more strategies ...
    
    // MACD Strategy 3: 3, 15, 3
    macdShort3 = checkParameter(3, "MACD Short Window")
    macdLong3 = checkParameter(15, "MACD Long Window")
    macdSignal3 = checkParameter(3, "MACD Signal Window")
    if macdSignal(macdShort3, macdLong3, macdSignal3)
        strategiesInPosition += 1
    
    strategiesInPosition
```

## Refactored Implementation (After)

The refactored implementation uses a configuration array with ticker information and a dynamic processing function:

```pine
//@version=5
indicator("BTC Strategy Breadth Oscillator", shorttitle="StgyBreadth", overlay=false)

// Description:
// This indicator calculates how many strategies from a predefined collection
// are currently in a bullish position. It functions as a breadth oscillator that shows
// market sentiment based on multiple strategies simultaneously.

// ================ Main Configuration ================
var int totalStrategies = 11  // This will be dynamically updated based on applicable strategies
var float lowerBand = 0.0     // Minimum oscillator value
var float upperBand = 11.0    // Maximum oscillator value (total strategies)

// Default Colors
color bullColor = color.new(#26c6da, 0)
color bearColor = color.new(#7e57c2, 0)
color neutralColor = color.new(#3179f5, 0)

// Optional user inputs for time frame selection
timeframeInput = input.timeframe("D", "Strategy Timeframe", options=["H", "D", "W", "M"])

// Ticker selection for filtering strategies
tickerInput = input.string("BTC-USD", "Ticker for Strategies", options=["ALL", "BTC-USD", "ETH-USD", "SOL-USD"])

// ================ Strategy Functions ================

// Function to calculate SMA Crossover signal
smaCrossSignal(shortWindow, longWindow) =>
    shortSMA = ta.sma(close, shortWindow)
    longSMA = ta.sma(close, longWindow)
    
    // Current state
    crossUp = shortSMA > longSMA
    
    // Return the signal (true if bullish)
    crossUp

// Function to calculate EMA Crossover signal
emaCrossSignal(shortWindow, longWindow) =>
    shortEMA = ta.ema(close, shortWindow)
    longEMA = ta.ema(close, longWindow)
    
    // Current state
    crossUp = shortEMA > longEMA
    
    // Return the signal (true if bullish)
    crossUp

// Function to calculate MACD signal
macdSignal(shortWindow, longWindow, signalWindow) =>
    [macdLine, signalLine, _] = ta.macd(close, shortWindow, longWindow, signalWindow)
    
    // Current state
    crossUp = macdLine > signalLine
    
    // Return the signal (true if bullish)
    crossUp

// ================ Error Handling Function ================
checkParameter(param, paramName) =>
    if param <= 0
        runtime.error("Invalid " + paramName + ": " + str.tostring(param) + ". Must be positive.")
        0
    else
        param

// ================ Strategy Configuration ================
// Strategy configuration array - Auto-generated from CSV
// Source: csv/strategies/BTC_d_20250427.csv
// Generated: 2025-04-27 09:14:00
// Total strategies: 11
// Strategies for BTC-USD: 11

var strategy_configs = array.new_string(0)

array.push(strategy_configs, "BTC-USD,SMA,104,105,0")
array.push(strategy_configs, "BTC-USD,MACD,14,23,13")
array.push(strategy_configs, "BTC-USD,SMA,26,38,0")
array.push(strategy_configs, "BTC-USD,SMA,27,29,0")
array.push(strategy_configs, "BTC-USD,SMA,76,78,0")
array.push(strategy_configs, "BTC-USD,SMA,11,36,0")
array.push(strategy_configs, "BTC-USD,MACD,18,29,18")
array.push(strategy_configs, "BTC-USD,SMA,8,44,0")
array.push(strategy_configs, "BTC-USD,EMA,5,68,0")
array.push(strategy_configs, "BTC-USD,SMA,3,47,0")
array.push(strategy_configs, "BTC-USD,MACD,3,15,3")

// ================ Dynamic Strategy Processing ================
calculateBreadth() =>
    int strategiesInPosition = 0
    int totalApplicableStrategies = 0
    
    // Process each strategy from the configuration
    for i = 0 to array.size(strategy_configs) - 1
        config = array.get(strategy_configs, i)
        string[] params = str.split(config, ",")
        
        // Extract ticker and parameters
        string ticker = params[0]
        
        // Skip if not matching the current ticker and not set to "ALL"
        if ticker != tickerInput and ticker != "ALL" and tickerInput != "ALL"
            continue
            
        totalApplicableStrategies += 1
        string type = params[1]
        int shortWindow = str.toint(params[2])
        int longWindow = str.toint(params[3])
        int signalWindow = str.toint(params[4])
        
        // Check parameters
        shortWindow := checkParameter(shortWindow, "Short Window")
        longWindow := checkParameter(longWindow, "Long Window")
        signalWindow := checkParameter(signalWindow, "Signal Window")
        
        // Process based on strategy type
        bool isActive = false
        if type == "SMA"
            isActive := smaCrossSignal(shortWindow, longWindow)
        else if type == "EMA"
            isActive := emaCrossSignal(shortWindow, longWindow)
        else if type == "MACD"
            isActive := macdSignal(shortWindow, longWindow, signalWindow)
            
        if isActive
            strategiesInPosition += 1
    
    // Update the total strategies variable based on applicable strategies
    totalStrategies := totalApplicableStrategies
    
    strategiesInPosition

// Request data using the specified timeframe
[strategiesActive] = request.security(syminfo.tickerid, timeframeInput, [calculateBreadth()])

// ... rest of the script remains the same ...
```

## Key Differences and Benefits

### 1. Centralized Configuration with Ticker Support

**Before**: Each strategy's parameters were scattered throughout the code in separate blocks with no ticker information.

**After**: All strategy parameters are centralized in a single configuration array that includes ticker information, making it easy to see all strategies at once and update them in one place.

### 2. Dynamic Processing with Ticker Filtering

**Before**: Each strategy required its own block of code with parameter checking and signal calculation.

**After**: A single function processes all strategies based on their type, parameters, and ticker, eliminating code duplication and supporting filtering by ticker.

### 3. Automated Updates with Ticker Support

**Before**: Adding, removing, or modifying strategies required manual code changes in multiple places.

**After**: The configuration can be automatically generated from the CSV file using the provided Python script, ensuring the Pine script stays in sync with the source data and supports strategies for multiple assets.

### 4. Ticker Selection

**Before**: The script was hardcoded for a single set of strategies with no way to switch between different assets.

**After**: The script includes a ticker selection input that allows users to switch between different assets' strategies or view all strategies at once.

### 5. Dynamic Total Strategies

**Before**: The total number of strategies was fixed at 11.

**After**: The total number of strategies is dynamically updated based on the applicable strategies for the selected ticker, ensuring accurate percentage calculations.

### 6. Extensibility

**Before**: Adding a new strategy type or supporting a new asset would require significant code changes.

**After**: New strategy types and assets can be added by simply extending the configuration array and processing function, following the Open/Closed principle.

### 7. Maintainability

**Before**: The code was harder to maintain due to duplication, scattered logic, and lack of asset-specific support.

**After**: The code is more maintainable with clear separation of configuration and processing logic, and support for multiple assets.

## Implementation Steps

To implement this refactoring:

1. Replace the hardcoded strategy definitions with the generated configuration array that includes ticker information
2. Add the ticker selection input to allow users to switch between different assets' strategies
3. Replace the `calculateBreadth()` function with the dynamic calculation function that supports ticker filtering
4. Update the `totalStrategies` variable to be dynamically updated based on applicable strategies
5. Test the refactored script to ensure it produces the same results as the original

This refactoring significantly improves the maintainability of the Pine script while preserving its functionality, making it much easier to update when the source CSV file changes and supporting strategies for multiple assets.