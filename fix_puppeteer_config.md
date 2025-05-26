# Fix for Puppeteer Server Error

## Problem
The error shows that the system is looking for Puppeteer at the old location:
```
/Users/colemorton/Projects/trading/mcp_puppeteer/dist/index.js
```

## Solution

### Option 1: Use NPX Method (Recommended)

Update your configuration to use npx instead of a direct path:

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "env": {
        "PUPPETEER_LAUNCH_OPTIONS": "{ \"headless\": false }"
      }
    }
  }
}
```

### Option 2: Create Symbolic Link (Quick Fix)

If you need the old path to work, create a symbolic link:

```bash
# Create the old directory structure
mkdir -p /Users/colemorton/Projects/trading/mcp_puppeteer

# Create symbolic link to the new location
ln -s /Users/colemorton/mcp-servers/puppeteer/dist /Users/colemorton/Projects/trading/mcp_puppeteer/dist
```

### Option 3: Use the Correct Configuration File

Make sure you're using one of these updated configuration files:
- `mcp_config.json` - Now updated to use npx
- `mcp_config_recommended.json` - Already uses npx
- `.vscode/mcp.json` - For VS Code, uses npx

## Verification

Test the npx method directly:
```bash
npx -y @modelcontextprotocol/server-puppeteer
```

This should start the server without any path issues.

## For Claude Desktop

Use the configuration in `claude_desktop_config.json` which already uses the npx method.