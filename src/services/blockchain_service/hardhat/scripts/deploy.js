import hre from "hardhat";
import fs from "fs";

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("\n🚀 Deploying contracts with account:", deployer.address);
  console.log("Balance:", hre.ethers.formatEther(await hre.ethers.provider.getBalance(deployer.address)), "ETH\n");

  // 1. Deploy ERC20 Token
  console.log("📝 Deploying ERC20 Token...");
  const ERC20 = await hre.ethers.getContractFactory("LMSCourseToken");
  const erc20 = await ERC20.deploy();
  await erc20.waitForDeployment();
  const erc20Address = await erc20.getAddress();
  console.log("✅ Token deployed to:", erc20Address);

  // 2. Deploy ERC721 Certificate NFT
  console.log("\n📝 Deploying ERC721 Certificate NFT...");
  const ERC721 = await hre.ethers.getContractFactory("LMSCertificateNFT");
  const erc721 = await ERC721.deploy();
  await erc721.waitForDeployment();
  const erc721Address = await erc721.getAddress();
  console.log("✅ Certificate deployed to:", erc721Address);

  // 3. Deploy AP2 Protocol
  console.log("\n📝 Deploying AP2 Protocol...");
  const AP2 = await hre.ethers.getContractFactory("AP2");
  const ap2 = await AP2.deploy();
  await ap2.waitForDeployment();
  const ap2Address = await ap2.getAddress();
  console.log("✅ AP2 deployed to:", ap2Address);

  // 4. Register backend as authorized agent
  console.log("\n📝 Registering backend agent in AP2...");
  const backendAgentAddress = deployer.address; // Or specific agent address
  const registerTx = await ap2.registerAgent(backendAgentAddress);
  await registerTx.wait();
  console.log("✅ Agent registered:", backendAgentAddress);

  // 5. Mint test tokens to additional accounts (localhost only)
  if (hre.network.name === "localhost") {
    console.log("\n📝 Minting test tokens to accounts...");
    const testAccounts = [
      "0x70997970C51812dc3A010C7d01b50e0d17dc79C8", // Account #1
      "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC", // Account #2
      "0x90F79bf6EB2c4f870365E785982E1f101E93b906"  // Account #3
    ];
    
    for (const account of testAccounts) {
      const tx = await erc20.transfer(account, hre.ethers.parseEther("10000"));
      await tx.wait();
      console.log(`   💰 Minted 10,000 tokens to ${account}`);
    }
  }

  // 6. Save deployment info
  const deployment = {
    network: hre.network.name,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    contracts: {
      token: erc20Address,
      certificate: erc721Address,
      ap2: ap2Address
    }
  };

  const filename = `deployment-${hre.network.name}.json`;
  fs.writeFileSync(filename, JSON.stringify(deployment, null, 2));

  // 7. Print summary
  console.log("\n" + "=".repeat(60));
  console.log("✨ Deployment Complete!");
  console.log("=".repeat(60));
  console.log("\n📋 Contract Addresses:");
  console.log(`   Token:       ${erc20Address}`);
  console.log(`   Certificate: ${erc721Address}`);
  console.log(`   AP2:         ${ap2Address}`);
  console.log(`\n📄 Saved to: ${filename}`);
  console.log("\n🔧 Add to .env:");
  console.log(`TOKEN_CONTRACT_ADDRESS=${erc20Address}`);
  console.log(`CERTIFICATE_CONTRACT_ADDRESS=${erc721Address}`);
  console.log(`AP2_CONTRACT_ADDRESS=${ap2Address}\n`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
