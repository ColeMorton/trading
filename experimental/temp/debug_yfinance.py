import yfinance as yf
import requests
import sys

print("=== YFINANCE DEBUG ===")
print(f"yfinance version: {yf.__version__}")

# Test 1: Check if we can reach Yahoo Finance
print("\n1. Testing Yahoo Finance connectivity...")
try:
    response = requests.get("https://finance.yahoo.com", timeout=5)
    print(f"   ✓ Yahoo Finance is reachable (status: {response.status_code})")
except Exception as e:
    print(f"   ✗ Cannot reach Yahoo Finance: {e}")

# Test 2: Try different methods to get BTC-USD
print("\n2. Testing BTC-USD with different methods...")

# Method A: Direct download
print("\n   Method A: yf.download()")
try:
    data = yf.download("BTC-USD", period="1d", progress=False)
    print(f"   Result: {len(data)} rows")
    if not data.empty:
        print(f"   Latest: {data.index[-1]} - Close: ${data['Close'].iloc[-1]:.2f}")
except Exception as e:
    print(f"   Error: {e}")

# Method B: Ticker with different parameters
print("\n   Method B: Ticker.history()")
try:
    ticker = yf.Ticker("BTC-USD")
    
    # Try with interval parameter
    hist = ticker.history(period="1mo", interval="1d")
    print(f"   Result: {len(hist)} rows")
    if not hist.empty:
        print(f"   Latest: {hist.index[-1]} - Close: ${hist['Close'].iloc[-1]:.2f}")
except Exception as e:
    print(f"   Error: {e}")

# Method C: Try with a known working ticker first
print("\n3. Testing with AAPL as control...")
try:
    aapl = yf.Ticker("AAPL")
    hist = aapl.history(period="1mo")
    print(f"   AAPL Result: {len(hist)} rows")
    if not hist.empty:
        print(f"   Latest: {hist.index[-1]} - Close: ${hist['Close'].iloc[-1]:.2f}")
except Exception as e:
    print(f"   AAPL Error: {e}")

# Test 3: Check session and headers
print("\n4. Checking yfinance session...")
try:
    ticker = yf.Ticker("BTC-USD")
    print(f"   Session exists: {ticker._base.session is not None}")
    
    # Try to get raw data
    print("\n5. Attempting raw data fetch...")
    from yfinance import shared
    shared._ERRORS = {}
    
    # Force a fresh download
    ticker = yf.Ticker("BTC-USD")
    ticker._history_metadata = None
    
    # Try with auto_adjust
    hist = ticker.history(period="1d", auto_adjust=True, actions=False)
    print(f"   Raw fetch result: {len(hist)} rows")
    
except Exception as e:
    print(f"   Session error: {e}")

# Print any shared errors
if hasattr(yf, 'shared') and hasattr(yf.shared, '_ERRORS'):
    if yf.shared._ERRORS:
        print("\n6. Shared errors:")
        for symbol, error in yf.shared._ERRORS.items():
            print(f"   {symbol}: {error}")