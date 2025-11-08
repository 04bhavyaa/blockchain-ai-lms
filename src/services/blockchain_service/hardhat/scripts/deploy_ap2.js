// simple Hardhat deploy script for AP2
async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying contracts with the account:', deployer.address);

  const AP2 = await ethers.getContractFactory('AP2');

  // Deploy contract (ethers v6/hardhat-compatible)
  const ap2 = await AP2.deploy();
  // Wait for deployment to finish
  if (typeof ap2.waitForDeployment === 'function') {
    await ap2.waitForDeployment();
  } else if (ap2.deployTransaction) {
    await ap2.deployTransaction.wait();
  }

  // Get deployed address (ethers v6: getAddress())
  let deployedAddress = ap2.address || (typeof ap2.getAddress === 'function' ? await ap2.getAddress() : undefined);
  console.log('AP2 deployed to:', deployedAddress);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
