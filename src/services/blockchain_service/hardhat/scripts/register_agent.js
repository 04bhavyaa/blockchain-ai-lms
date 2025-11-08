// Hardhat script to register an agent address in AP2 contract
async function main() {
  const [deployer] = await ethers.getSigners();
  const ap2Address = process.env.AP2_ADDRESS || '';
  const agentToRegister = process.env.AGENT_ADDRESS || '';

  if (!ap2Address || !agentToRegister) {
    console.error('Please set AP2_ADDRESS and AGENT_ADDRESS environment variables');
    return;
  }

  const ap2 = await ethers.getContractAt('AP2', ap2Address);
  const tx = await ap2.registerAgent(agentToRegister);
  await tx.wait();
  console.log('Agent registered:', agentToRegister);
}

main().catch((err) => { console.error(err); process.exit(1); });
