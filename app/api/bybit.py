from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the API key and secret
api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

print("API_KEY:", api_key)
print("API_SECRET:", api_secret)

SYMBOL = 'BIGTIMEUSDT'

# Create a session with the Bybit API
session = HTTP(api_key=api_key, api_secret=api_secret, testnet=True)

def market_order(quantity):
    try:
        # Place a market order to buy
        response = session.place_order(
            category="linear",  # For USDT perpetual contracts
            symbol=SYMBOL,
            side="Buy",
            orderType="Market",  # Market order type
            qty=str(quantity),  # Quantity to buy
            timeInForce="GoodTillCancel"  # Order validity
        )
        print("Order response:", response)
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    quantity_to_buy = 31  # Amount to buy
    print(f"Buying {quantity_to_buy} {SYMBOL}...")
    market_order(quantity_to_buy)