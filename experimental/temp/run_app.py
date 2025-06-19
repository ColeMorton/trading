#!/usr/bin/env python
"""
Simple wrapper to run the Flask app without the reloader
which can cause issues with yfinance
"""
from app import app, find_available_port

if __name__ == "__main__":
    port = find_available_port()
    print(f"Starting server on port {port}")
    # Run without reloader to avoid yfinance caching issues
    app.run(debug=False, port=port, use_reloader=False)
