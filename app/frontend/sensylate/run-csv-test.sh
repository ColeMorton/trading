#!/bin/bash
cd /Users/colemorton/Projects/trading/app/frontend/sensylate
echo "Working directory: $(pwd)"
echo "Node version: $(node --version)"
echo "Running CSV Data Validation Test..."
echo "=================================="
node tests/csvDataValidation.spec.js
