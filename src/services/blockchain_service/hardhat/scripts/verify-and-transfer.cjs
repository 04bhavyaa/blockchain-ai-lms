const hre = require("hardhat");

async function main() {
  const address = "0x01f51c176c23d7f7dcf806197082faf493e151a5";
  const tokenAddress = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
  
  console.log("Checking balance for:", address);
  console.log("Token contract:", tokenAddress);
  console.log("─".repeat(60));
  
  // Simple direct call
  const provider = hre.ethers.provider;
  const data = hre.ethers.AbiCoder.defaultAbiCoder().encode(['address'], [address]);
  const selector = '0x70a08231'; // balanceOf selector
  
  try {
    const result = await provider.call({
      to: tokenAddress,
      data: selector + data.slice(2)
    });
    
    const balance = hre.ethers.AbiCoder.defaultAbiCoder().decode(['uint256'], result)[0];
    console.log("Balance (Wei):", balance.toString());
    console.log("Balance (Tokens):", hre.ethers.formatEther(balance));
    
    if (balance === 0n) {
      console.log("\n❌ Balance is 0! The transfer failed or was reverted.");
      console.log("\nTrying to transfer now...");
      
      const [deployer] = await hre.ethers.getSigners();
      const Token = await hre.ethers.getContractAt("LMSCourseToken", tokenAddress);
      const amount = hre.ethers.parseEther("10000");
      
      const tx = await Token.transfer(address, amount);
      console.log("Transfer TX:", tx.hash);
      await tx.wait();
      console.log("✅ Transfer complete!");
      
      // Check balance again
      const newResult = await provider.call({
        to: tokenAddress,
        data: selector + data.slice(2)
      });
      const newBalance = hre.ethers.AbiCoder.defaultAbiCoder().decode(['uint256'], newResult)[0];
      console.log("New Balance:", hre.ethers.formatEther(newBalance), "LMSCT");
    } else {
      console.log("\n✅ You have tokens!");
    }
  } catch (error) {
    console.error("Error:", error.message);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
