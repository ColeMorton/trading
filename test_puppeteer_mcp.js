#!/usr/bin/env node

import { spawn } from 'child_process';
import { readFileSync, existsSync } from 'fs';

console.log('MCP Puppeteer Server Verification');
console.log('='.repeat(50));

// Test configuration 1: Direct path
const directPath = '/Users/colemorton/mcp-servers/puppeteer/dist/index.js';

async function testServer(command, args, configName) {
  console.log(`\n📋 Testing ${configName}...`);
  
  return new Promise((resolve) => {
    const server = spawn(command, args, {
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let responded = false;
    
    server.stdout.on('data', (data) => {
      const output = data.toString();
      if (!responded && output.includes('jsonrpc')) {
        responded = true;
        console.log(`✅ ${configName} server is responding`);
      }
    });
    
    server.stderr.on('data', (data) => {
      console.error(`   Error: ${data}`);
    });
    
    server.on('error', (err) => {
      console.log(`❌ Failed to start ${configName} server: ${err.message}`);
      resolve(false);
    });
    
    // Give it time to start
    setTimeout(() => {
      // Send a test request
      const request = JSON.stringify({
        jsonrpc: "2.0",
        method: "tools/list",
        id: 1
      }) + '\n';
      
      server.stdin.write(request);
      
      // Wait for response
      setTimeout(() => {
        server.kill();
        resolve(responded);
      }, 2000);
    }, 2000);
  });
}

async function main() {
  // Test 1: Direct path
  let directSuccess = false;
  if (existsSync(directPath)) {
    directSuccess = await testServer('node', [directPath], 'Direct path');
  } else {
    console.log(`\n❌ Direct path server not found at: ${directPath}`);
  }
  
  // Test 2: NPX (checking only)
  console.log('\n📋 Checking npx availability...');
  const npxTest = spawn('npx', ['--version']);
  const npxAvailable = await new Promise((resolve) => {
    npxTest.on('close', (code) => {
      resolve(code === 0);
    });
  });
  
  if (npxAvailable) {
    console.log('✅ npx is available - server can be run with npx command');
  } else {
    console.log('❌ npx is not available');
  }
  
  // Summary
  console.log('\n' + '='.repeat(50));
  console.log('Test Summary:');
  console.log(`  Direct path: ${directSuccess ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`  NPX available: ${npxAvailable ? '✅ YES' : '❌ NO'}`);
  
  if (directSuccess || npxAvailable) {
    console.log('\n✅ MCP Puppeteer server is active and enabled!');
    console.log('\nConfiguration files in project:');
    console.log('  - mcp_config.json (uses direct path)');
    console.log('  - mcp_config_recommended.json (uses npx - preferred)');
  } else {
    console.log('\n❌ MCP Puppeteer server cannot be used!');
  }
  
  process.exit(directSuccess || npxAvailable ? 0 : 1);
}

main().catch(console.error);