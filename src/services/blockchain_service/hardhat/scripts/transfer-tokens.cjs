// Transfer LMS tokens from deployer to test account
const hre = require("hardhat");

async function main() {
  // Get recipient address from command line argument
  const recipientAddress = process.argv[2];
  
  if (!recipientAddress) {
    console.error("❌ Please provide recipient address as argument");
    console.log("Usage: node scripts/transfer-tokens.cjs <your-metamask-address>");
    console.log("Example: node scripts/transfer-tokens.cjs 0x1234567890abcdef...");
    process.exit(1);
  }

  // Get the deployed token contract
  const tokenAddress = "0xa513E6E4b8f2a923D98304ec87F64353C4D5C853";
  const LMSToken = await hre.ethers.getContractAt("LMSCourseToken", tokenAddress);
  
  // Transfer 10,000 LMSCT tokens
  const amount = hre.ethers.parseEther("10000");
  
  console.log("Transferring 10,000 LMSCT tokens...");
  console.log("From:", (await hre.ethers.provider.getSigner(0)).address);
  console.log("To:", recipientAddress);
  
  const tx = await LMSToken.transfer(recipientAddress, amount);
  await tx.wait();
  
  console.log("✅ Transfer successful!");
  console.log("Transaction hash:", tx.hash);
  console.log("\n📋 Now import token in MetaMask:");
  console.log("  Token Address:", tokenAddress);
  console.log("  Symbol: LMSCT");
  console.log("  Decimals: 18");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
