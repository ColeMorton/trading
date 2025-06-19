const {
  testAdvancedConfigCollapse,
} = require('./advancedConfigAnimation.spec.js');

console.log(
  '🧪 Running Advanced Configuration Animation Test for Sensylate...\n'
);

testAdvancedConfigCollapse()
  .then(() => {
    console.log(
      '\n🎉 Advanced Configuration collapse test completed successfully!'
    );
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n💥 Test failed:', error.message);
    process.exit(1);
  });
