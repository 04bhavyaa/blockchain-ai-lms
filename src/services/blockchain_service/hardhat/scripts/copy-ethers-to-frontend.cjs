// Post-install script to copy ethers v5 UMD build to frontend
const fs = require('fs');
const path = require('path');

const source = path.join(__dirname, '../node_modules/ethers5/dist/ethers.umd.min.js');
const targetDir = path.join(__dirname, '../../../../frontend-simple/assets/js/vendor');
const target = path.join(targetDir, 'ethers.umd.min.js');

try {
  // Create vendor directory if it doesn't exist
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
    console.log('✓ Created vendor directory');
  }

  // Copy ethers.js
  if (fs.existsSync(source)) {
    fs.copyFileSync(source, target);
    console.log('✓ Copied ethers v5.7.2 to frontend/assets/js/vendor/');
  } else {
    console.warn('⚠ Warning: ethers5 not found. Run npm install first.');
  }
} catch (error) {
  console.error('✗ Error copying ethers.js:', error.message);
  // Don't fail the install if this fails
  process.exit(0);
}
