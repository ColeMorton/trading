# S&P 100 constituents as of Dec 2024, excluding stocks that appear in QQQ
# Arrays are roughly equal in size

sp100_group1 = [
    "JNJ",  # Johnson & Johnson
    "JPM",  # JPMorgan Chase
    "V",  # Visa
    "XOM",  # Exxon Mobil
    "MA",  # Mastercard
    "UNH",  # UnitedHealth Group
    "WMT",  # Walmart
    "BAC",  # Bank of America
    "PG",  # Procter & Gamble
]

sp100_group2 = [
    "CVX",  # Chevron
    "LLY",  # Eli Lilly
    "HD",  # Home Depot
    "MRK",  # Merck
    "ABBV",  # AbbVie
    "KO",  # Coca-Cola
    "MCD",  # McDonald's
    "ACN",  # Accenture
    "TMO",  # Thermo Fisher Scientific
]

sp100_group3 = [
    "DHR",  # Danaher
    "ABT",  # Abbott Laboratories
    "WFC",  # Wells Fargo
    "CRM",  # Salesforce
    "NEE",  # NextEra Energy
    "LIN",  # Linde
    "BMY",  # Bristol Myers Squibb
    "PM",  # Philip Morris
    "UPS",  # United Parcel Service
]

sp100_group4 = [
    "CVS",  # CVS Health
    "RTX",  # RTX Corporation
    "MS",  # Morgan Stanley
    "BA",  # Boeing
    "BLK",  # BlackRock
    "CAT",  # Caterpillar
    "SPGI",  # S&P Global
    "DE",  # Deere & Company
    "UNP",  # Union Pacific
]

sp100_group5 = [
    "GS",  # Goldman Sachs
    "AMT",  # American Tower
    "DUK",  # Duke Energy
    "IBM",  # IBM
    "C",  # Citigroup
    "ELV",  # Elevance Health
    "SCHW",  # Charles Schwab
    "AXP",  # American Express
    "PNC",  # PNC Financial Services
]

sp100_group6 = [
    "SO",  # Southern Company
    "GE",  # General Electric
    "TJX",  # TJX Companies
    "MMC",  # Marsh & McLennan
    "LOW",  # Lowe's
    "SLB",  # Schlumberger
    "CI",  # Cigna
    "NOC",  # Northrop Grumman
    "MO",  # Altria Group
]

# All groups in a list for easy access
sp100_groups = [
    sp100_group1,
    sp100_group2,
    sp100_group3,
    sp100_group4,
    sp100_group5,
    sp100_group6,
]

# Verification set for checking overlaps
sp100_all_tickers = set()
for group in sp100_groups:
    sp100_all_tickers.update(group)

# Number of unique tickers
total_sp100_exclusive = len(
    sp100_all_tickers
)  # Should be 54 stocks after removing QQQ overlaps
