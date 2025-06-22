#!/usr/bin/env node

console.log('Node.js is working');
console.log('Node version:', process.version);
console.log('Working directory:', process.cwd());

// Try to run the CSV test
try {
  import('./tests/csvDataValidation.spec.js')
    .then(() => console.log('Test started'))
    .catch((err) => console.error('Test failed to start:', err));
} catch (error) {
  console.error('Import error:', error);
}
