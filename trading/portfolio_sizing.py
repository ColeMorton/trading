import yfinance as yf

# Constants
ASSET_1_TICKER = "SPY"
ASSET_2_TICKER = "BTC-USD"
ASSET_1_ALLOCATION = 0.5
ASSET_2_ALLOCATION = 0.5
TOTAL_PORTFOLIO_VALUE = 30000
USE_EMA = True
EMA_PERIOD = 21
USE_LEVERAGE = True
ASSET_1_LEVERAGE = 9.5
ASSET_2_LEVERAGE = 4.7

def get_price_or_ema(ticker, use_ema, ema_period):
    """Fetch the current price or EMA for a given ticker."""
    data = yf.Ticker(ticker).history(period="1mo")
    if use_ema:
        return data['Close'].ewm(span=ema_period, adjust=False).mean().iloc[-1]
    return data['Close'].iloc[-1]

def calculate_effective_portfolio_value(total_value, alloc1, alloc2, lev1, lev2):
    """Calculate the effective portfolio value considering leverage."""
    return total_value / ((alloc1 / lev1) + (alloc2 / lev2))

def calculate_position_size(effective_value, allocation, price):
    """Calculate the position size for an asset."""
    return (effective_value * allocation) / price

def calculate_dollar_value(position_size, price):
    """Calculate the dollar value of a position."""
    return position_size * price

def print_asset_details(ticker, initial_value, position_size, leveraged_value, allocation):
    """Print details for an asset."""
    print(f"\nAsset: {ticker}")
    print(f"  Initial (pre-leverage) value: ${initial_value:.2f}")
    print(f"  Position size: {position_size:.6f}")
    print(f"  Leveraged value: ${leveraged_value:.2f}")
    print(f"  Allocation: {allocation:.2f}%")

def main():
    # Fetch asset prices
    asset_1_price = get_price_or_ema(ASSET_1_TICKER, USE_EMA, EMA_PERIOD)
    asset_2_price = get_price_or_ema(ASSET_2_TICKER, USE_EMA, EMA_PERIOD)

    # Calculate effective portfolio value
    effective_value = calculate_effective_portfolio_value(
        TOTAL_PORTFOLIO_VALUE, ASSET_1_ALLOCATION, ASSET_2_ALLOCATION,
        ASSET_1_LEVERAGE, ASSET_2_LEVERAGE
    )

    # Calculate initial values
    initial_asset_1_value = TOTAL_PORTFOLIO_VALUE * ASSET_1_ALLOCATION
    initial_asset_2_value = TOTAL_PORTFOLIO_VALUE * ASSET_2_ALLOCATION

    # Calculate position sizes
    asset_1_position = calculate_position_size(effective_value, ASSET_1_ALLOCATION, asset_1_price)
    asset_2_position = calculate_position_size(effective_value, ASSET_2_ALLOCATION, asset_2_price)

    # Calculate leveraged values
    asset_1_leveraged_value = calculate_dollar_value(asset_1_position, asset_1_price)
    asset_2_leveraged_value = calculate_dollar_value(asset_2_position, asset_2_price)

    # Calculate total leveraged value
    total_leveraged_value = asset_1_leveraged_value + asset_2_leveraged_value

    # Calculate allocations
    asset_1_allocation = (asset_1_leveraged_value / total_leveraged_value) * 100
    asset_2_allocation = (asset_2_leveraged_value / total_leveraged_value) * 100

    # Print results
    print_asset_details(ASSET_1_TICKER, initial_asset_1_value, asset_1_position, 
                        asset_1_leveraged_value, asset_1_allocation)
    print_asset_details(ASSET_2_TICKER, initial_asset_2_value, asset_2_position, 
                        asset_2_leveraged_value, asset_2_allocation)

    print(f"\nInitial Portfolio Value: ${TOTAL_PORTFOLIO_VALUE:.2f}")
    print(f"Total Leveraged Portfolio Value: ${total_leveraged_value:.2f}")
    print(f"Effective Portfolio Value: ${effective_value:.2f}")

if __name__ == "__main__":
    main()