# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Application
```bash
# Start the Flask server (automatically finds available port)
python app.py

# The server will start on port 5000-5100 (first available)
```

### Testing
```bash
# Run Puppeteer UI tests (ensure Flask server is running first)
npm test

# The tests are configured to use port 5001 by default
# Server typically starts on port 5001 (first available port)
```

### Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for testing)
npm install
```

## Architecture

This is a stock price visualization web application with:

1. **Backend (Flask)**: 
   - `app.py` - Main Flask application with yfinance integration
   - Endpoint `/api/ticker-history` accepts POST with ticker symbol
   - Implements fallback strategies for fetching data (period="1mo" → period="max" → yf.download())
   - Auto-finds available port to avoid conflicts

2. **Frontend**: 
   - Single-page application in `templates/index.html`
   - Chart.js for price visualization
   - Dark theme with purple gradient accents
   - Real-time loading states and error handling

3. **Testing**:
   - Puppeteer-based UI tests in `test.js`
   - Tests cover: page load, UI elements, data fetching, error handling, keyboard shortcuts
   - Configured for localhost:5001 by default

## Key Implementation Details

- The app has multiple versions (`app.py`, `app_fixed.py`, `app_simple.py`) - use `app.py` as the primary version
- yfinance error handling includes clearing shared._ERRORS and trying multiple fetch methods
- Frontend expects data in format: `{date, open, high, low, close, volume}`
- All API responses follow consistent JSON structure with `success` flag