import hre from "hardhat";

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);

  // Deploy ERC20 Token
  const ERC20 = await hre.ethers.getContractFactory("LMSCourseToken");
  const erc20 = await ERC20.deploy();
  await erc20.waitForDeployment();
  const erc20Address = await erc20.getAddress();
  console.log("ERC20 deployed:", erc20Address);

  // Deploy ERC721 NFT
  const ERC721 = await hre.ethers.getContractFactory("LMSCertificateNFT");
  const erc721 = await ERC721.deploy();
  await erc721.waitForDeployment();
  const erc721Address = await erc721.getAddress();
  console.log("ERC721 deployed:", erc721Address);

  // Deploy AP2 Protocol
  const AP2 = await hre.ethers.getContractFactory("AP2AgentPurchase");
  const ap2 = await AP2.deploy();
  await ap2.waitForDeployment();
  const ap2Address = await ap2.getAddress();
  console.log("AP2 protocol deployed:", ap2Address);

  // Save deployment addresses for frontend usage
  const deploymentAddresses = {
    erc20: erc20Address,
    erc721: erc721Address,
    ap2: ap2Address
  };
  console.log("\nDeployment Summary:", deploymentAddresses);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
