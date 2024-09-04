import numpy as np
import yfinance as yf

# Define parameters
TOTAL_PORTFOLIO_VALUE = 30000  # Example total portfolio value
ASSET_1_TICKER = "BTC-USD"
ASSET_2_TICKER = "SPY"
ASSET_1_LEVERAGE = 4  # Example leverage factor for Asset 1
ASSET_2_LEVERAGE = 9.5  # Example leverage factor for Asset 2
USE_EMA = False
EMA_PERIOD = 21

# Target ratio between Asset 2 Leveraged value and Asset 1 Leveraged value
# Adjust RATIO in order to get the desired Allocations
RATIO = 0.5

def get_price_or_ema(ticker, use_ema, ema_period):
    """Fetch the current price or EMA for a given ticker."""
    data = yf.Ticker(ticker).history(period="1mo")
    if use_ema:
        return data['Close'].ewm(span=ema_period, adjust=False).mean().iloc[-1]
    return data['Close'].iloc[-1]

def get_intersection_index(x):
    # Calculate Leveraged Values
    leveraged_value_1 = ASSET_1_LEVERAGE * x
    leveraged_value_2 = ASSET_2_LEVERAGE * x

    # Calculate the reversed second line
    reversed_leveraged_value_2 = RATIO * leveraged_value_2[::-1]

    # Find the intersection point by minimizing the absolute difference
    diff = np.abs(leveraged_value_1 - reversed_leveraged_value_2)
    return np.argmin(diff)

def print_asset_details(ticker, initial_value, leverage, position_size, leveraged_value, allocation):
    """Print details for an asset."""
    print(f"\nAsset: {ticker}")
    print(f"  Initial (pre-leverage) value: ${initial_value:.2f}")
    print(f"  Leverage: {leverage:.2f}")
    print(f"  Leveraged value: ${leveraged_value:.2f}")
    print(f"  Position size: {position_size:.6f}")
    print(f"  Allocation: {allocation:.2f}%")

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
    levered_asset_1_value = initial_asset_1_value*ASSET_1_LEVERAGE
    levered_asset_2_value = initial_asset_2_value*ASSET_2_LEVERAGE
    levered_total_value = levered_asset_1_value+levered_asset_2_value
    position_size_asset_1_value = levered_asset_1_value/asset_1_price
    position_size_asset_2_value = levered_asset_2_value/asset_2_price
    allocation_asset_1_value = levered_asset_1_value/levered_total_value*100
    allocation_asset_2_value = levered_asset_2_value/levered_total_value*100

    # Print results
    print_asset_details(ASSET_1_TICKER, initial_asset_1_value, ASSET_1_LEVERAGE, position_size_asset_1_value,
                        levered_asset_1_value, allocation_asset_1_value)
    print_asset_details(ASSET_2_TICKER, initial_asset_2_value, ASSET_2_LEVERAGE, position_size_asset_2_value,
                        levered_asset_2_value, allocation_asset_2_value)
    
    print(f"\nInitial Portfolio Value: ${TOTAL_PORTFOLIO_VALUE:.2f}")
    print(f"Total Leveraged Portfolio Value: ${levered_total_value:.2f}")

if __name__ == "__main__":
    main()