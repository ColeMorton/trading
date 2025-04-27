# Strategy Breadth Oscillator Error Resolution Report

## Introduction

This report documents the process of resolving multiple type mismatch errors in the TradingView Pine Script "Strategy Breadth Oscillator" indicator. The original script encountered several type-related errors that prevented successful compilation and execution. This document outlines the step-by-step approach taken to diagnose and fix these issues while maintaining the original functionality.

## Initial Error Analysis

The first error encountered was:

```
Error: Cannot call 'array.size' with argument 'id'='#a0'. An argument of 'simple int' type was used but a 'array<type>' is expected.
```

This occurred in the following code section:

```pine
// Process each strategy from the configuration
int size = array.size(strategy_configs)
for i = 0 to size - 1
```

The error indicated a fundamental issue with how arrays are handled in Pine Script v5. Despite `strategy_configs` being defined as a string array using `array.new_string(0)`, the type system was not correctly recognizing it as an array when passed to `array.size()`.

## Step-by-Step Resolution Process

### Step 1: Addressing array.size() Error

**Initial Approach**: Replace explicit type declaration

```pine
// From:
int size = array.size(strategy_configs)
// To:
size = array.size(strategy_configs)
```

**Reasoning**: The initial hypothesis was that the explicit type declaration might be causing a conflict with the inferred type from `array.size()`. By removing the explicit type declaration, we hoped Pine Script would correctly infer the type.

**Result**: This approach failed, producing the same error.

**Second Approach**: Hardcode the array size

```pine
// From:
int size = array.size(strategy_configs)
// To:
int size = 11  // Hardcoded based on the number of strategies
```

**Reasoning**: Since we knew exactly how many strategies were in the array (11), we could bypass the problematic `array.size()` function altogether by hardcoding this value.

**Result**: This fixed the immediate error but led to a new error with `array.get()`.

### Step 2: Addressing array.get() Error

The next error was:

```
Error: Cannot call 'array.get' with argument 'id'='#a0'. An argument of 'simple int' type was used but a 'array<type>' is expected.
```

This occurred in:

```pine
string config = array.get(strategy_configs, i)
```

**Approach**: Replace array-based configuration with function-based approach

```pine
// Function to get strategy config by index instead of using arrays
getStrategyConfig(index) =>
    if index == 0
        "BTC-USD,SMA,104,105,0"
    else if index == 1
        "BTC-USD,MACD,14,23,13"
    // ... and so on
```

**Reasoning**: Since both `array.size()` and `array.get()` were causing type mismatch errors with the `strategy_configs` array, we eliminated the array altogether and replaced it with a function that returns the configuration string for a given index.

**Result**: This fixed the `array.get()` error but led to string comparison errors.

### Step 3: Addressing String Comparison Errors

The next error was:

```
Error: Cannot call 'operator !=' with argument 'expr1'='#a0'. An argument of 'simple int' type was used but a 'series string' is expected.
```

This occurred in:

```pine
if ticker != tickerInput and ticker != "ALL" and tickerInput != "ALL"
```

**Approach**: Remove ticker comparison

```pine
// All configurations have "BTC-USD" as the ticker and the user can only select "BTC-USD"
// No need to check if the ticker matches
totalApplicableStrategies += 1
```

**Reasoning**: Since all configurations had "BTC-USD" as the ticker and the user could only select "BTC-USD" from the options, the ticker comparison was unnecessary and could be removed entirely.

**Result**: This fixed the string comparison error but led to type mismatch errors with strategy functions.

### Step 4: Addressing Type Mismatch with Strategy Functions

The next error was:

```
Error: Cannot call 'emaCrossSignal' with argument 'shortWindow'='shortWindow'. An argument of 'series int' type was used but a 'simple int' is expected.
```

This occurred in:

```pine
isActive := emaCrossSignal(shortWindow, longWindow)
```

**Initial Approach**: Create separate functions for each parameter type

```pine
getStrategyConfigType(index) => // Returns strategy type
getStrategyConfigShortWindow(index) => // Returns short window
getStrategyConfigLongWindow(index) => // Returns long window
getStrategyConfigSignalWindow(index) => // Returns signal window
```

**Reasoning**: By separating the configuration into type-specific functions, we hoped to ensure that each parameter would have the correct type.

**Result**: This approach still resulted in type mismatch errors.

**Final Approach**: Hardcode each strategy call directly

```pine
// Strategy 8: EMA(5, 68)
totalApplicableStrategies += 1
if emaCrossSignal(5, 68)
    strategiesInPosition += 1
```

**Reasoning**: By directly using literal values in the function calls, we ensured that the functions received parameters of the expected types (simple int) rather than variables that might be inferred as series types.

**Result**: This fixed the type mismatch errors with strategy functions but led to one final error with `hline`.

### Step 5: Addressing hline Type Mismatch

The final error was:

```
Error: Cannot call 'hline' with argument 'price'='totalStrategies'. An argument of 'series int' type was used but a 'input float' is expected.
```

This occurred in:

```pine
hline(totalStrategies, "Max", color=color.new(#787b86, 70), linestyle=hline.style_dotted)
```

**Approach**: Hardcode the maximum value

```pine
hline(11, "Max", color=color.new(#787b86, 70), linestyle=hline.style_dotted)
```

**Reasoning**: Since we knew there were exactly 11 strategies, we could hardcode this value instead of using the `totalStrategies` variable, which was being inferred as a 'series int' type.

**Result**: This fixed the final type mismatch error, allowing the script to compile and run successfully.

## Final Solution

The final solution involved several key changes:

1. **Elimination of Dynamic Array Processing**: Replaced the array-based approach with hardcoded strategy calls directly in the `calculateBreadth()` function.

2. **Direct Literal Values**: Used literal integer values directly in function calls instead of variables to ensure correct type inference.

3. **Simplified Logic**: Removed unnecessary ticker comparison since all strategies were for "BTC-USD".

4. **Hardcoded Constants**: Used hardcoded values for known constants (number of strategies, maximum value for visualization) to avoid type mismatch issues.

The resulting code is more verbose but completely avoids the type mismatch errors that were occurring with the more dynamic approach.

## Lessons Learned

### Pine Script v5 Type System Insights

1. **Type Inference Challenges**: Pine Script v5's type system can sometimes infer types differently than expected, particularly when variables are used across different contexts.

2. **Series vs. Simple Types**: There's a strict distinction between 'series' types and 'simple' types in Pine Script, and functions often expect specific type categories.

3. **Variable Reassignment**: Variables that are reassigned values (especially within functions or loops) may be inferred as 'series' types even if they appear to be simple constants.

### Best Practices for Avoiding Similar Errors

1. **Use Literal Values**: When possible, use literal values directly in function calls rather than variables to avoid type inference issues.

2. **Minimize Variable Reassignment**: Limit the use of the `:=` reassignment operator, which can change type inference.

3. **Hardcode Known Constants**: For values that are known and fixed, hardcoding them can avoid type mismatch issues.

4. **Simplify Logic**: Reduce unnecessary complexity in the code, such as conditional checks that aren't needed.

5. **Understand Function Requirements**: Be aware of the specific type requirements for built-in functions like `hline()`, which may expect 'input' types rather than 'series' types.

By applying these principles, we were able to successfully resolve all type mismatch errors in the Strategy Breadth Oscillator script while maintaining its original functionality.