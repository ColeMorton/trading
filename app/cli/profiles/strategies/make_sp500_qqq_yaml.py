# make_sp500_qqq_yaml.py
# Requires: requests, pandas, pyyaml, lxml
# pip install requests pandas pyyaml lxml beautifulsoup4

import re

import pandas as pd
import requests
import yaml


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


def normalize_to_yahoo(ticker: str) -> str:
    """
    Convert ticker to Yahoo Finance format.
    Example: BRK.B -> BRK-B
    """
    t = ticker.strip().upper()
    t = re.sub(r"[^A-Z0-9.\-]", "", t)
    return t.replace(".", "-")  # Yahoo uses dash instead of dot


def get_sp500_from_wikipedia():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    dfs = pd.read_html(resp.text, flavor="lxml")
    df = None
    for candidate in dfs:
        cols = [str(c).lower() for c in candidate.columns]
        if any("symbol" in c for c in cols):
            df = candidate
            break
    if df is None:
        msg = "Could not parse S&P 500 table from Wikipedia."
        raise RuntimeError(msg)
    symbol_col = next(c for c in df.columns if "symbol" in str(c).lower())
    symbols = df[symbol_col].astype(str).tolist()
    return [normalize_to_yahoo(s) for s in symbols]


def get_qqq_holdings_invesco():
    # Invesco holdings page
    url = "https://www.invesco.com/us/financial-products/etfs/holdings?audienceType=Investor&ticker=QQQ"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    try:
        dfs = pd.read_html(resp.text, flavor="lxml")
    except ValueError:
        msg = "Invesco holdings table not found in HTML (likely JS-rendered)."
        raise RuntimeError(
            msg,
        )
    df = None
    for candidate in dfs:
        cols = [str(c).lower() for c in candidate.columns]
        if any("symbol" in c or "ticker" in c for c in cols):
            df = candidate
            break
    if df is None:
        msg = "Could not parse tickers from Invesco QQQ holdings page."
        raise RuntimeError(msg)
    col_candidates = [
        c
        for c in df.columns
        if "symbol" in str(c).lower() or "ticker" in str(c).lower()
    ]
    if not col_candidates:
        msg = "Ticker column not found in Invesco QQQ holdings table."
        raise RuntimeError(msg)
    symbol_col = col_candidates[0]
    symbols = df[symbol_col].astype(str).tolist()
    return [normalize_to_yahoo(s) for s in symbols]


def get_qqq_holdings_fallback():
    # Fallback: Slickcharts NASDAQ-100
    url = "https://www.slickcharts.com/nasdaq100"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    dfs = pd.read_html(resp.text, flavor="lxml")
    df = dfs[0]
    # Usually first column is rank, second column is company, third is ticker
    # We’ll search for ticker-like values
    tickers = []
    for col in df.columns:
        values = df[col].astype(str).tolist()
        ticker_like = [
            v for v in values if re.fullmatch(r"[A-Za-z0-9.\-]{1,6}", v.strip())
        ]
        if len(ticker_like) > len(df) * 0.5:
            tickers = [normalize_to_yahoo(v) for v in ticker_like]
            break
    if not tickers:
        msg = "Could not parse tickers from Slickcharts fallback."
        raise RuntimeError(msg)
    return tickers


def main():
    sp500 = get_sp500_from_wikipedia()
    try:
        qqq = get_qqq_holdings_invesco()
    except Exception as e:
        print(
            "Warning: Invesco QQQ holdings fetch failed, using Slickcharts fallback. Error:",
            e,
        )
        qqq = get_qqq_holdings_fallback()

    combined = sorted(set(sp500) | set(qqq))
    yaml_output = yaml.safe_dump(combined, sort_keys=False, allow_unicode=True)
    print("# YAML array of unique Yahoo Finance tickers for S&P500 + QQQ holdings\n")
    print(yaml_output)


if __name__ == "__main__":
    main()
