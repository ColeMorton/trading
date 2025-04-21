# Implementation Plan: Enhanced Return Distribution Analysis for Options

## Overview
This plan outlines the steps to enhance the return distribution analysis by adding a custom visualization for the specific days to expiry and incorporating option delta metrics for more accurate risk assessment of covered call strategies.

## 1. Add Configuration Parameters

Add the following parameters at the top of the file around line 13:

```python
# Option strategy parameters
INCLUDE_OPTION_STRATEGY = True  # Toggle to enable/disable option strategy analysis
DELTA = 0.14                    # Current option delta
DAYS_TO_EXPIRY = 11             # Days until option expiration
STRIKE_DISTANCE = 9.73          # Strike price distance above current price (%)
```

## 2. Create Custom Period Returns Function

Add a new function after the `calculate_returns` function:

```python
def calculate_custom_period_returns(data, days):
    """
    Calculate returns for a custom period of days.
    
    Args:
        data (pd.DataFrame): Price data with Close prices
        days (int): Number of days for the return calculation
        
    Returns:
        pd.Series: Series of returns for the specified period
    """
    log(f"Calculating returns for custom period: {days} days")
    data_copy = data.copy()
    data_copy.loc[:, 'Return'] = data_copy.Close.pct_change()
    
    # For crypto which trades 7 days a week
    if "-USD" in TICKER:
        returns = data_copy['Return'].rolling(window=days).sum().dropna()
    # For stocks which trade 5 days a week
    else:
        # Approximate trading days
        trading_days = int(days * 5/7)
        returns = data_copy['Return'].rolling(window=trading_days).sum().dropna()
    
    if returns.empty:
        log("No valid returns calculated for custom period.", "error")
        raise ValueError(f"No valid returns calculated for {days}-day period.")
    
    log(f"Custom {days}-day returns calculated successfully.")
    return returns
```

## 3. Create Market vs Historical Probability Comparison Function

Add a new function after the `calculate_var` function:

```python
def compare_probabilities(returns, strike_return, delta):
    """
    Compare historical probability with market-implied probability.
    
    Args:
        returns (pd.Series): Series of returns
        strike_return (float): Return percentage for the strike price
        delta (float): Option delta representing market-implied probability
        
    Returns:
        tuple: (historical_probability, market_implied_probability, difference)
    """
    log(f"Comparing probabilities for strike return: {strike_return:.2%}")
    
    # Calculate historical probability of exceeding the strike return
    historical_probability = 100 - percentileofscore(returns, strike_return)
    
    # Market-implied probability from delta
    market_implied_probability = delta * 100
    
    # Calculate difference
    difference = market_implied_probability - historical_probability
    
    log(f"Historical probability: {historical_probability:.2f}%, Market-implied: {market_implied_probability:.2f}%")
    return historical_probability, market_implied_probability, difference
```

## 4. Enhance the Plot Return Distribution Function

Modify the `plot_return_distribution` function to include an optional parameter for strike analysis:

```python
def plot_return_distribution(returns, var_95, var_99, ticker, timeframe, ax, current_return, 
                            strike_analysis=None):
    """
    Plot the return distribution with VaR lines and additional statistics.
    
    Args:
        returns (pd.Series): Series of returns
        var_95 (float): 95% Value at Risk
        var_99 (float): 99% Value at Risk
        ticker (str): Ticker symbol
        timeframe (str): Timeframe of the returns
        ax (matplotlib.axes): Axes to plot on
        current_return (float): Current return
        strike_analysis (tuple, optional): Tuple containing (strike_return, historical_prob, 
                                          market_prob, difference)
    """
    # Existing code...
    
    # Add strike analysis if provided
    if strike_analysis is not None:
        strike_return, historical_prob, market_prob, difference = strike_analysis
        
        # Add strike line
        ax.axvline(x=strike_return, color='magenta', linestyle='--', linewidth=2, 
                  label=f'Strike (+{strike_return*100:.2f}%): {historical_prob:.2f}% hist vs {market_prob:.2f}% implied')
        
        # Add comparison text
        risk_assessment = "Market overpricing risk" if difference > 0 else "Market underpricing risk"
        
        # Calculate additional metrics
        expected_return = np.mean(returns)
        probability_above_zero = 100 - percentileofscore(returns, 0)
        max_profit_probability = 100 - historical_prob
        
        # Add text box with metrics
        ax.text(0.99, 0.80,
                f'Market-Historical Diff: {difference:.2f}%\n' +
                f'{risk_assessment}\n' +
                f'Expected Return: {expected_return:.2%}\n' +
                f'Prob. of Positive Return: {probability_above_zero:.2f}%\n' +
                f'Prob. of Max Profit: {max_profit_probability:.2f}%',
                transform=ax.transAxes, verticalalignment='top', horizontalalignment='right',
                fontsize=8, bbox=dict(facecolor='white', alpha=0.7))
    
    # Rest of existing code...
```

## 5. Modify the Main Function with Toggle Feature

Update the main function to include the custom timeframe and option analysis, using the toggle parameter:

```python
def main():
    """Main function to execute the return distribution analysis."""
    log("Starting return distribution analysis.")
    
    # Fetch asset price data
    data = fetch_data(TICKER)
    
    # Determine plot layout based on whether option strategy is included
    if INCLUDE_OPTION_STRATEGY:
        log("Including option strategy analysis.")
        fig, axs = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'{TICKER} Return Distributions with Option Strategy Analysis', fontsize=16)
    else:
        fig, axs = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'{TICKER} Return Distributions', fontsize=16)
    
    # Standard timeframes
    timeframes = ['2W', 'W', '3D', 'D']
    
    # Process standard timeframes
    for i, (timeframe, ax) in enumerate(zip(timeframes, axs.flatten())):
        # Get the last adjusted close price and the one before the resampled period
        current_close = data.Close.iloc[-1]

        # Standard trading days logic
        if timeframe == '3D':
            previous_close = data.Close.iloc[-4]  # 3 days before (plus 1 to account for pct_change offset)

        # Check if the ticker contains "-USD"
        if "-USD" in TICKER:
            # Use 7 trading days for W and 14 trading days for 2W
            if timeframe == 'W':
                previous_close = data.Close.iloc[-8]  # 7 trading days ago
            elif timeframe == '2W':
                previous_close = data.Close.iloc[-15] # 14 trading days ago
        else:
            if timeframe == 'W':
                previous_close = data.Close.iloc[-6]  # 5 trading days ago
            elif timeframe == '2W':
                previous_close = data.Close.iloc[-11] # 10 trading days ago

        # Calculate the current return
        current_return = (current_close - previous_close) / previous_close

        returns = calculate_returns(data, timeframe)
        var_95, var_99 = calculate_var(returns)
        plot_return_distribution(returns, var_95, var_99, TICKER, timeframe, ax, current_return)
    
    # Add option strategy analysis if enabled
    if INCLUDE_OPTION_STRATEGY:
        # Calculate strike return
        strike_return = STRIKE_DISTANCE / 100
        
        # Add custom timeframe for days to expiry
        custom_ax = axs.flatten()[4]
        custom_timeframe = f"{DAYS_TO_EXPIRY}D"
        
        # Calculate custom period returns
        custom_returns = calculate_custom_period_returns(data, DAYS_TO_EXPIRY)
        
        # Calculate VaR for custom period
        custom_var_95, custom_var_99 = calculate_var(custom_returns)
        
        # Calculate current return for custom period
        if "-USD" in TICKER:
            previous_close = data.Close.iloc[-DAYS_TO_EXPIRY-1]
        else:
            # Approximate trading days
            trading_days = int(DAYS_TO_EXPIRY * 5/7)
            previous_close = data.Close.iloc[-trading_days-1]
        
        current_close = data.Close.iloc[-1]
        custom_current_return = (current_close - previous_close) / previous_close
        
        # Compare probabilities
        historical_prob, market_prob, difference = compare_probabilities(
            custom_returns, strike_return, DELTA)
        
        # Plot custom period with strike analysis
        plot_return_distribution(
            custom_returns, custom_var_95, custom_var_99, TICKER, custom_timeframe, 
            custom_ax, custom_current_return, 
            strike_analysis=(strike_return, historical_prob, market_prob, difference)
        )
        
        # Add summary in the last subplot
        summary_ax = axs.flatten()[5]
        summary_ax.axis('off')
        summary_ax.text(0.5, 0.95, "Option Strategy Summary", 
                       ha='center', va='top', fontsize=14, fontweight='bold')
        
        # Create a summary table
        table_data = [
            ["Parameter", "Value"],
            ["Ticker", TICKER],
            ["Days to Expiry", str(DAYS_TO_EXPIRY)],
            ["Strike Distance", f"+{STRIKE_DISTANCE:.2f}%"],
            ["Option Delta", str(DELTA)],
            ["Historical Probability", f"{historical_prob:.2f}%"],
            ["Market-Implied Probability", f"{market_prob:.2f}%"],
            ["Probability Difference", f"{difference:.2f}%"],
            ["Risk Assessment", "Market overpricing risk" if difference > 0 else "Market underpricing risk"],
            ["Expected Return", f"{np.mean(custom_returns):.2%}"],
            ["Max Profit Probability", f"{100-historical_prob:.2f}%"]
        ]
        
        table = summary_ax.table(cellText=table_data, loc='center', cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)
        
        # Print option strategy diagnostic information
        print(f"\nOption Strategy Analysis:")
        print(f"Strike Distance: +{STRIKE_DISTANCE:.2f}%")
        print(f"Days to Expiry: {DAYS_TO_EXPIRY}")
        print(f"Historical Probability of Exceeding Strike: {historical_prob:.2f}%")
        print(f"Market-Implied Probability (Delta): {market_prob:.2f}%")
        print(f"Difference: {difference:.2f}%")
    
    plt.tight_layout()
    plt.show()
    
    # Print some diagnostic information
    print(f"\nTotal days of data: {len(data)}")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")
    
    log("Return distribution analysis completed.")
    log_close()
```

## 6. Implementation Steps

1. Add the configuration parameters with the toggle feature (INCLUDE_OPTION_STRATEGY) around line 13
2. Implement the `calculate_custom_period_returns` function
3. Implement the `compare_probabilities` function
4. Enhance the `plot_return_distribution` function with the strike analysis parameter
5. Modify the `main` function to include conditional logic based on the toggle parameter

## 7. Expected Outcome

When INCLUDE_OPTION_STRATEGY = True:
1. The visualization will include 6 panels (3x2 grid):
   - Standard timeframe distributions (2W, W, 3D, D)
   - Custom distribution for days to expiry
   - Summary panel with key metrics
2. Option strategy analysis will be included in the output

When INCLUDE_OPTION_STRATEGY = False:
1. The visualization will include only 4 panels (2x2 grid) with standard timeframes
2. No option strategy analysis will be performed or displayed

This toggle feature allows the user to easily switch between the standard return distribution analysis and the enhanced version with option strategy analysis without modifying the code.

## 8. Visualization Example

With INCLUDE_OPTION_STRATEGY = True:
```
+-------------------+-------------------+
|     2W Returns    |     W Returns     |
+-------------------+-------------------+
|     3D Returns    |     D Returns     |
+-------------------+-------------------+
| Custom 11D Returns|  Strategy Summary |
+-------------------+-------------------+
```

With INCLUDE_OPTION_STRATEGY = False:
```
+-------------------+-------------------+
|     2W Returns    |     W Returns     |
+-------------------+-------------------+
|     3D Returns    |     D Returns     |
+-------------------+-------------------+
```

The toggle provides flexibility to run the analysis with or without the option strategy component, depending on the user's needs.