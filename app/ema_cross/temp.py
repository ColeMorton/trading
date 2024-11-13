import pandas as pd

# Step 1: Read the SCANNER.csv file
scanner_df = pd.read_csv('app/ema_cross/SCANNER.csv')
scanner_tickers = scanner_df['TICKER'].tolist()

# Step 2: Define the current QQQ tickers (as of latest data)
qqq_tickers = [
    'ADBE', 'AMD', 'ABNB', 'GOOGL', 'GOOG', 'AMZN', 'AMGN', 'AAPL',
    'ADI', 'ADSK', 'ALGN', 'AVGO', 'BIIB', 'BKNG', 'BKR', 'CDNS',
    'COST', 'CPRT', 'CRWD', 'CSCO', 'CSX', 'DDOG', 'DLTR', 'DOCN',
    'DOCU', 'EA', 'ENPH', 'EXC', 'FANG', 'FAST', 'FCX', 'FISV',
    'FMX', 'GILD', 'GFS', 'HON', 'INTC', 'INTU', 'JD', 'KLAC',
    'LRCX', 'MAR', 'MDLZ', 'META', 'MELI', 'MNST', 'MRNA',
    'MRVL', 'MSFT', 'NFLX', 'NVDA', 'NXPI', 'ON', 'ORLY',
    'PANW', 'PAYX', 'PEP', 'PDD', 'QCOM', 'REGN',
    'ROST', 'SBUX', 'SNPS', 'TEAM', 'TMUS',
    # Add other tickers as needed
]

# Step 3: Generate the final list excluding SCANNER tickers
final_tickers = [ticker for ticker in qqq_tickers if ticker not in scanner_tickers]

# Output the final list
print(final_tickers)