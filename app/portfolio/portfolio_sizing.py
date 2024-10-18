import numpy as np
import yfinance as yf
import scipy.stats as st

# Define parameters
TOTAL_PORTFOLIO_VALUE = 8000  # target 1
# TOTAL_PORTFOLIO_VALUE = 10000  # target 2
# TOTAL_PORTFOLIO_VALUE = 11000  # target 3
ASSET_1_TICKER = "BTC-USD"
ASSET_2_TICKER = "SPY"
ASSET_1_LEVERAGE = 7  # Example leverage factor for Asset 1
ASSET_2_LEVERAGE = 7  # Example leverage factor for Asset 2
USE_EMA = False
EMA_PERIOD = 21
ASSET_1_ALLOCATION = 45.97 # Target allocation for Asset 1 (as a percentage)
VAR_CONFIDENCE_LEVELS = [0.95, 0.99]

TOTAL_PORTFOLIO_VALUE = 6500  # target
ASSET_1_TICKER = "BTC-USD"
ASSET_2_TICKER = "SOL-USD"
ASSET_1_LEVERAGE = 7  # Example leverage factor for Asset 1
ASSET_2_LEVERAGE = 2  # Example leverage factor for Asset 2
USE_EMA = False
EMA_PERIOD = 21
ASSET_1_ALLOCATION = 50 # Target allocation for Asset 1 (as a percentage)
VAR_CONFIDENCE_LEVELS = [0.95, 0.99]

def get_price_or_ema(ticker, use_ema, ema_period):
    """Fetch the current price or EMA for a given ticker."""
    data = yf.Ticker(ticker).history(period="1mo")
    if use_ema:
        return data['Close'].ewm(span=ema_period, adjust=False).mean().iloc[-1]
    return data['Close'].iloc[-1]

def calculate_var_cvar(returns, confidence_levels=[0.95, 0.99]):
    """Calculate VaR and CVaR for given set of returns at multiple confidence levels."""
    results = {}
    for cl in confidence_levels:
        var_threshold = np.percentile(returns, (1 - cl) * 100)
        cvar_threshold = returns[returns <= var_threshold].mean()
        results[cl] = (var_threshold, cvar_threshold)
    return results

def get_returns(ticker):
    """Fetch historical returns for a given ticker."""
    data = yf.Ticker(ticker).history(period="1y")  # 1 year of historical data
    returns = data['Close'].pct_change().dropna()  # Calculate daily returns
    return returns

def get_intersection_index(x):
    # Calculate Leveraged Values
    leveraged_value_1 = ASSET_1_LEVERAGE * x
    leveraged_value_2 = ASSET_2_LEVERAGE * x

    # Calculate RATIO based on ASSET_1_ALLOCATION
    ratio = ASSET_1_ALLOCATION / (100 - ASSET_1_ALLOCATION)

    # Calculate the reversed second line
    reversed_leveraged_value_2 = ratio * leveraged_value_2[::-1]

    # Find the intersection point by minimizing the absolute difference
    diff = np.abs(leveraged_value_1 - reversed_leveraged_value_2)
    return np.argmin(diff)

def print_asset_details(ticker, initial_value, leverage, position_size, leveraged_value, allocation, var_cvar_results):
    """Print details for an asset."""
    print(f"\nAsset: {ticker}")
    print(f"  Initial (pre-leverage) value: ${initial_value:.2f}")
    print(f"  Leverage: {leverage:.2f}")
    print(f"  Leveraged value: ${leveraged_value:.2f}")
    print(f"  Position size: {position_size:.6f}")
    print(f"  Allocation: {allocation:.2f}%")
    
    for cl, (var, cvar) in var_cvar_results.items():
        print(f"  VaR Monetary Loss ({cl*100:.0f}%): ${abs(var*leveraged_value):.2f}")
        print(f"  CVaR Monetary Loss ({cl*100:.0f}%): ${abs(cvar*leveraged_value):.2f}")

def main():
    # Fetch asset prices
    asset_1_price = get_price_or_ema(ASSET_1_TICKER, USE_EMA, EMA_PERIOD)
    asset_2_price = get_price_or_ema(ASSET_2_TICKER, USE_EMA, EMA_PERIOD)

    # Generate x-axis values (from 0 to TOTAL_PORTFOLIO_VALUE, divided into 1000 points)
    x = np.linspace(0, TOTAL_PORTFOLIO_VALUE, 1000)

    # Get intersection index
    intersection_index = get_intersection_index(x)

    initial_asset_1_value = x[intersection_index]
    initial_asset_2_value = TOTAL_PORTFOLIO_VALUE - initial_asset_1_value
    levered_asset_1_value = initial_asset_1_value * ASSET_1_LEVERAGE
    levered_asset_2_value = initial_asset_2_value * ASSET_2_LEVERAGE
    levered_total_value = levered_asset_1_value + levered_asset_2_value
    position_size_asset_1_value = levered_asset_1_value / asset_1_price
    position_size_asset_2_value = levered_asset_2_value / asset_2_price
    allocation_asset_1_value = levered_asset_1_value / levered_total_value * 100
    allocation_asset_2_value = levered_asset_2_value / levered_total_value * 100

    # Get returns for VaR and CVaR calculations
    returns_asset_1 = get_returns(ASSET_1_TICKER)
    returns_asset_2 = get_returns(ASSET_2_TICKER)
    
    # Calculate VaR and CVaR for both assets at both confidence levels
    var_cvar_asset_1 = calculate_var_cvar(returns_asset_1, VAR_CONFIDENCE_LEVELS)
    var_cvar_asset_2 = calculate_var_cvar(returns_asset_2, VAR_CONFIDENCE_LEVELS)

    # Print results
    print_asset_details(ASSET_1_TICKER, initial_asset_1_value, ASSET_1_LEVERAGE, position_size_asset_1_value,
                        levered_asset_1_value, allocation_asset_1_value, var_cvar_asset_1)
    
    print_asset_details(ASSET_2_TICKER, initial_asset_2_value, ASSET_2_LEVERAGE, position_size_asset_2_value,
                        levered_asset_2_value, allocation_asset_2_value, var_cvar_asset_2)
    
    print(f"\nInitial Portfolio Value: ${TOTAL_PORTFOLIO_VALUE:.2f}")
    print(f"Total Leveraged Portfolio Value: ${levered_total_value:.2f}")

if __name__ == "__main__":
    main()