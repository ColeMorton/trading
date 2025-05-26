#!/usr/bin/env python3
"""
Market Data Scraper using MCP Puppeteer Server
Example of how to use Puppeteer for trading-related web scraping
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

class PuppeteerMarketScraper:
    """
    Example class showing how to use MCP Puppeteer server
    for scraping market data from websites
    """
    
    def __init__(self):
        self.server_process = None
        self.request_id = 0
        
    def start_server(self):
        """Start the MCP Puppeteer server using npx"""
        print("Starting Puppeteer server...")
        self.server_process = subprocess.Popen(
            ["npx", "-y", "@modelcontextprotocol/server-puppeteer"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        time.sleep(5)  # Give server time to start
        print("✅ Puppeteer server started")
        
    def send_request(self, method, params=None):
        """Send request to MCP server"""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self.request_id
        }
        if params:
            request["params"] = params
            
        self.server_process.stdin.write(json.dumps(request) + "\n")
        self.server_process.stdin.flush()
        
        response_line = self.server_process.stdout.readline()
        if response_line:
            return json.loads(response_line)
        return None
        
    def call_tool(self, tool_name, arguments):
        """Call a Puppeteer tool"""
        return self.send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
    def scrape_yahoo_finance(self, symbol):
        """Example: Scrape stock data from Yahoo Finance"""
        print(f"\n📊 Scraping data for {symbol}...")
        
        # Navigate to Yahoo Finance
        url = f"https://finance.yahoo.com/quote/{symbol}"
        nav_response = self.call_tool("puppeteer_navigate", {
            "url": url,
            "launchOptions": {"headless": True}
        })
        
        if nav_response and "result" in nav_response:
            print(f"✅ Navigated to {url}")
            
            # Wait a moment for page to load
            time.sleep(2)
            
            # Extract price data using JavaScript
            price_script = """
            {
                const price = document.querySelector('[data-field="regularMarketPrice"]')?.textContent || 'N/A';
                const change = document.querySelector('[data-field="regularMarketChange"]')?.textContent || 'N/A';
                const changePercent = document.querySelector('[data-field="regularMarketChangePercent"]')?.textContent || 'N/A';
                const volume = document.querySelector('[data-field="regularMarketVolume"]')?.textContent || 'N/A';
                
                JSON.stringify({
                    symbol: '""" + symbol + """',
                    price: price,
                    change: change,
                    changePercent: changePercent,
                    volume: volume,
                    timestamp: new Date().toISOString()
                });
            }
            """
            
            data_response = self.call_tool("puppeteer_evaluate", {
                "script": price_script
            })
            
            if data_response and "result" in data_response:
                result_text = data_response['result'].get('content', [{}])[0].get('text', '{}')
                try:
                    market_data = json.loads(result_text)
                    print("\n📈 Market Data Retrieved:")
                    for key, value in market_data.items():
                        print(f"   {key}: {value}")
                    return market_data
                except:
                    print("❌ Could not parse market data")
                    
            # Take a screenshot for verification
            screenshot_response = self.call_tool("puppeteer_screenshot", {
                "name": f"{symbol}_screenshot",
                "width": 1920,
                "height": 1080
            })
            
            if screenshot_response:
                print(f"📸 Screenshot saved: {symbol}_screenshot")
                
        return None
        
    def scrape_crypto_prices(self, symbols):
        """Example: Scrape multiple crypto prices"""
        results = []
        
        # Navigate to CoinMarketCap
        self.call_tool("puppeteer_navigate", {
            "url": "https://coinmarketcap.com",
            "launchOptions": {"headless": True}
        })
        
        time.sleep(3)
        
        # Extract top crypto prices
        script = """
        {
            const rows = document.querySelectorAll('table tbody tr');
            const data = [];
            
            for (let i = 0; i < Math.min(rows.length, 10); i++) {
                const row = rows[i];
                const name = row.querySelector('.coin-item-name')?.textContent || '';
                const symbol = row.querySelector('.coin-item-symbol')?.textContent || '';
                const price = row.querySelector('.price')?.textContent || '';
                const change = row.querySelector('.change')?.textContent || '';
                
                if (name && price) {
                    data.push({
                        name: name.trim(),
                        symbol: symbol.trim(),
                        price: price.trim(),
                        change24h: change.trim()
                    });
                }
            }
            
            JSON.stringify(data);
        }
        """
        
        response = self.call_tool("puppeteer_evaluate", {"script": script})
        
        if response and "result" in response:
            try:
                crypto_data = json.loads(response['result']['content'][0]['text'])
                print("\n💰 Top Cryptocurrencies:")
                for crypto in crypto_data:
                    print(f"   {crypto['symbol']}: {crypto['price']} ({crypto['change24h']})")
                return crypto_data
            except:
                print("❌ Could not parse crypto data")
                
        return results
        
    def cleanup(self):
        """Shutdown the server"""
        if self.server_process:
            self.server_process.terminate()
            time.sleep(1)
            if self.server_process.poll() is None:
                self.server_process.kill()
            print("\n✅ Puppeteer server stopped")

# Example usage
if __name__ == "__main__":
    scraper = PuppeteerMarketScraper()
    
    try:
        scraper.start_server()
        
        # Scrape stock data
        scraper.scrape_yahoo_finance("AAPL")
        
        # Scrape crypto data
        # scraper.scrape_crypto_prices(["BTC", "ETH", "SOL"])
        
    finally:
        scraper.cleanup()