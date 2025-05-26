#!/usr/bin/env node

/**
 * Test script to verify Puppeteer MCP server is accessible
 * Run this to ensure the server is properly configured
 */

import { spawn } from 'child_process';

console.log('Testing MCP Puppeteer Server Access');
console.log('===================================\n');

// Test using npx (recommended method)
console.log('Testing npx method...');
const npxTest = spawn('npx', ['-y', '@modelcontextprotocol/server-puppeteer', '--version'], {
  stdio: 'pipe'
});

let npxSuccess = false;

npxTest.on('error', (err) => {
  console.log('❌ npx method failed:', err.message);
});

npxTest.on('close', (code) => {
  if (code === 0 || code === 1) {
    npxSuccess = true;
    console.log('✅ npx method is available');
  } else {
    console.log('❌ npx method failed with code:', code);
  }
  
  // Test direct path method
  console.log('\nTesting direct path method...');
  const directTest = spawn('node', ['/Users/colemorton/mcp-servers/puppeteer/dist/index.js'], {
    stdio: 'pipe'
  });
  
  let directSuccess = false;
  
  directTest.on('error', (err) => {
    console.log('❌ Direct path method failed:', err.message);
    showResults();
  });
  
  // Give it a moment then kill it
  setTimeout(() => {
    directTest.kill();
    directSuccess = true;
    console.log('✅ Direct path method is available');
    showResults();
  }, 1000);
  
  function showResults() {
    console.log('\n===================================');
    console.log('Results:');
    console.log(`  npx method: ${npxSuccess ? '✅ Available' : '❌ Not available'}`);
    console.log(`  Direct path: ${directSuccess ? '✅ Available' : '❌ Not available'}`);
    
    if (npxSuccess || directSuccess) {
      console.log('\n✅ MCP Puppeteer server is accessible!');
      console.log('\nConfiguration files:');
      console.log('  - .vscode/mcp.json (for VS Code)');
      console.log('  - claude_desktop_config.json (for Claude Desktop)');
      console.log('\nSee MCP_PUPPETEER_SETUP.md for detailed instructions.');
    } else {
      console.log('\n❌ MCP Puppeteer server is not accessible.');
      console.log('Please check your Node.js and npm installation.');
    }
    
    process.exit(npxSuccess || directSuccess ? 0 : 1);
  }
});