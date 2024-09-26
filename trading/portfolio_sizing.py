import numpy as np
import yfinance as yf
import scipy.stats as st

# Define parameters
TOTAL_PORTFOLIO_VALUE = 8500  # target 1
# TOTAL_PORTFOLIO_VALUE = 9750  # target 2
# TOTAL_PORTFOLIO_VALUE = 11000  # target 3
ASSET_1_TICKER = "BTC-USD"
ASSET_2_TICKER = "SPY"
ASSET_1_LEVERAGE = 7  # Example leverage factor for Asset 1
ASSET_2_LEVERAGE = 7  # Example leverage factor for Asset 2
USE_EMA = False
EMA_PERIOD = 21
ASSET_1_ALLOCATION = 40.41 # Target allocation for Asset 1 (as a percentage)
VAR_CONFIDENCE_LEVEL = 0.95

# TOTAL_PORTFOLIO_VALUE = 6500  # target
# ASSET_1_TICKER = "BTC-USD"
# ASSET_2_TICKER = "SOL-USD"
# ASSET_1_LEVERAGE = 6  # Example leverage factor for Asset 1
# ASSET_2_LEVERAGE = 5  # Example leverage factor for Asset 2
# USE_EMA = False
# EMA_PERIOD = 21
# ASSET_1_ALLOCATION = 40.41 # Target allocation for Asset 1 (as a percentage)
# VAR_CONFIDENCE_LEVEL = 0.95

def get_price_or_ema(ticker, use_ema, ema_period):
    """Fetch the current price or EMA for a given ticker."""
    data = yf.Ticker(ticker).history(period="1mo")
    if use_ema:
        return data['Close'].ewm(span=ema_period, adjust=False).mean().iloc[-1]
    return data['Close'].iloc[-1]

def calculate_var_cvar(returns, confidence_level=0.95):
    """Calculate VaR and CVaR for a given set of returns."""
    var_threshold = np.percentile(returns, (1 - confidence_level) * 100)
    cvar_threshold = returns[returns <= var_threshold].mean()
    return var_threshold, cvar_threshold

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

def print_asset_details(ticker, initial_value, leverage, position_size, leveraged_value, allocation, var_pct, cvar_pct, var_monetary, cvar_monetary):
    """Print details for an asset."""
    print(f"\nAsset: {ticker}")
    print(f"  Initial (pre-leverage) value: ${initial_value:.2f}")
    print(f"  Leverage: {leverage:.2f}")
    print(f"  Leveraged value: ${leveraged_value:.2f}")
    print(f"  Position size (Target): {position_size:.6f}")
    print(f"  Position size (Daily): {position_size*0.764:.6f}")
    print(f"  Position size (Hourly): {position_size*0.236:.6f}")
    print(f"  Allocation: {allocation:.2f}%")
    print(f"  VaR (95%): {var_pct:.4f}%")
    print(f"  CVaR (95%): {cvar_pct:.4f}%")
    print(f"  VaR Monetary Loss (95%): ${var_monetary:.2f}")
    print(f"  CVaR Monetary Loss (95%): ${cvar_monetary:.2f}")

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
    
    # Calculate VaR and CVaR for both assets (in percentage)
    var_asset_1_pct, cvar_asset_1_pct = calculate_var_cvar(returns_asset_1, VAR_CONFIDENCE_LEVEL)
    var_asset_2_pct, cvar_asset_2_pct = calculate_var_cvar(returns_asset_2, VAR_CONFIDENCE_LEVEL)

    # Convert VaR and CVaR percentages to monetary losses
    var_asset_1_monetary = var_asset_1_pct * levered_asset_1_value
    cvar_asset_1_monetary = cvar_asset_1_pct * levered_asset_1_value
    var_asset_2_monetary = var_asset_2_pct * levered_asset_2_value
    cvar_asset_2_monetary = cvar_asset_2_pct * levered_asset_2_value

    # Print results
    print_asset_details(ASSET_1_TICKER, initial_asset_1_value, ASSET_1_LEVERAGE, position_size_asset_1_value,
                        levered_asset_1_value, allocation_asset_1_value, 
                        var_asset_1_pct * 100, cvar_asset_1_pct * 100,  # Convert to percentage
                        var_asset_1_monetary, cvar_asset_1_monetary)
    
    print_asset_details(ASSET_2_TICKER, initial_asset_2_value, ASSET_2_LEVERAGE, position_size_asset_2_value,
                        levered_asset_2_value, allocation_asset_2_value, 
                        var_asset_2_pct * 100, cvar_asset_2_pct * 100,  # Convert to percentage
                        var_asset_2_monetary, cvar_asset_2_monetary)
    
    print(f"\nInitial Portfolio Value: ${TOTAL_PORTFOLIO_VALUE:.2f}")
    print(f"Total Leveraged Portfolio Value: ${levered_total_value:.2f}")

if __name__ == "__main__":
    main()
