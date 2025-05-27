"""Simple test to check MA Cross API."""

import requests
import json

# Test the API
url = "http://localhost:8000/api/ma-cross/analyze"
data = {
    "TICKER": "AAPL",
    "WINDOWS": 50,
    "DIRECTION": "Long",
    "STRATEGY_TYPES": ["SMA"],
    "fast_period": 20,
    "slow_period": 50
}

print("Testing MA Cross API...")
print(f"Request: {json.dumps(data, indent=2)}")

try:
    response = requests.post(url, json=data, timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except requests.exceptions.ConnectionError:
    print("Error: API server is not running")
    print("Start the server with: python -m app.api.run")
except Exception as e:
    print(f"Error: {e}")