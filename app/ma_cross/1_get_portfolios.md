Setting `USE_SCANNER = True` fundamentally changes how the strategy processes tickers and their moving average parameters:

1. **Normal Mode (USE_SCANNER = False)**:
- Uses fixed window ranges for moving averages defined by the WINDOWS parameter
- Analyzes all possible combinations of short and long windows up to the WINDOWS limit
- Performs exhaustive parameter sensitivity analysis for each ticker
- Suitable for deep analysis of individual tickers or small sets of tickers

2. **Scanner Mode (USE_SCANNER = True)**:
- Reads predefined moving average parameters from a scanner list CSV file
- Only analyzes specific MA combinations defined in the scanner list
- Processes multiple tickers more efficiently by avoiding exhaustive parameter testing
- Designed for quick analysis of many tickers with known/preferred MA parameters

Key Differences:

1. **Parameter Selection**:
   - Normal Mode: Tests all possible window combinations (e.g., if WINDOWS=89, tests hundreds of combinations)
   - Scanner Mode: Only tests specific window combinations from the scanner list (e.g., might only test EMA_FAST=12, EMA_SLOW=26)

2. **Data Source**:
   - Normal Mode: Uses tickers defined in config["TICKER"]
   - Scanner Mode: Uses tickers from scanner list CSV file (defined by config["SCANNER_LIST"])

3. **Execution Flow**:
   - Normal Mode: Runs through execute_strategy() in 1_get_portfolios.py
   - Scanner Mode: Runs through process_scanner() in 1_scanner.py

4. **Output Structure**:
   - Normal Mode: Creates detailed portfolio analysis with multiple parameter combinations
   - Scanner Mode: Creates focused results based on specific parameter sets from scanner list

5. **Efficiency**:
   - Normal Mode: More computationally intensive due to testing all parameter combinations
   - Scanner Mode: More efficient as it only tests specific parameter combinations

6. **Use Cases**:
   - Normal Mode: Better for:
     * Parameter optimization
     * Deep analysis of individual tickers
     * Finding optimal MA combinations
   - Scanner Mode: Better for:
     * Screening many tickers quickly
     * Real-time market scanning
     * Testing specific MA combinations across multiple tickers

Important Implementation Note:
- Scanner mode must be executed through 1_scanner.py, not 1_get_portfolios.py
- Setting USE_SCANNER=True in 1_get_portfolios.py will not activate scanner mode as they are separate execution paths
- 1_scanner.py logs to 2_scanner.log while 1_get_portfolios.py logs to 1_get_portfolios.log

Example Usage:
```python
# For scanner mode (using specific MA parameters from CSV):
python 1_scanner.py  # Will automatically set USE_SCANNER=True

# For normal mode (exhaustive parameter analysis):
python 1_get_portfolios.py  # USE_SCANNER setting is ignored
```

The scanner mode essentially provides a more targeted and efficient approach when you already know which MA parameters you want to test, while the normal mode is better suited for comprehensive analysis and parameter optimization.