# MCP Puppeteer Server Setup Guide

This guide explains how to enable the MCP Puppeteer server for both the trading project and Claude Desktop (Roo).

## Installation Status

✅ **Puppeteer Server Installed**: Located at `~/mcp-servers/puppeteer/`

## Configuration Files

### 1. For VS Code (Trading Project)

**Location**: `/Users/colemorton/Projects/trading/.vscode/mcp.json`

This configuration enables both the trading API and Puppeteer servers within VS Code.

### 2. For Claude Desktop (Roo)

**Location**: Copy the content from `claude_desktop_config.json` to Claude Desktop's settings

To configure Claude Desktop:
1. Open Claude Desktop
2. Go to Settings → Developer → MCP Servers
3. Add the configuration from `claude_desktop_config.json`

### 3. Alternative Configurations

- `mcp_config.json` - Uses direct path to installed server
- `mcp_config_recommended.json` - Uses npx (recommended)

## Available Puppeteer Tools

Once configured, you'll have access to these browser automation tools:

1. **puppeteer_navigate** - Navigate to any URL
2. **puppeteer_screenshot** - Capture screenshots
3. **puppeteer_click** - Click elements on pages
4. **puppeteer_fill** - Fill out form fields
5. **puppeteer_select** - Select dropdown options
6. **puppeteer_hover** - Hover over elements
7. **puppeteer_evaluate** - Execute JavaScript in browser

## Testing the Setup

### Quick Test (VS Code)
1. Open VS Code in the trading project
2. Open the MCP panel
3. You should see "puppeteer" and "trading-api" servers listed

### Quick Test (Claude Desktop)
1. After adding the configuration, restart Claude Desktop
2. In a new conversation, the Puppeteer tools should be available

### Manual Test
Run this command to verify the server works:
```bash
npx -y @modelcontextprotocol/server-puppeteer
```

## Troubleshooting

### If Puppeteer server doesn't appear:
1. Ensure Node.js is installed: `node --version`
2. Ensure npx is available: `npx --version`
3. Check the configuration file syntax
4. Restart VS Code or Claude Desktop

### For VS Code:
- Make sure you have the MCP extension installed
- Check that `.vscode/mcp.json` is properly formatted

### For Claude Desktop:
- Ensure the configuration is added to the correct section in settings
- The Python path must be absolute for the trading-api server

## Benefits

- **Browser Automation**: Automate web scraping, testing, and interactions
- **Screenshots**: Capture visual data from websites
- **Data Collection**: Extract information from web pages
- **Testing**: Automated testing of web applications

## Security Notes

- The Puppeteer server runs with `headless: false` to show the browser window
- Be cautious when navigating to untrusted websites
- The server has access to your local file system