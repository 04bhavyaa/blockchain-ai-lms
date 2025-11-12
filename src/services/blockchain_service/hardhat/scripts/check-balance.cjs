// Check LMSCT token balance for an address
const hre = require("hardhat");

async function main() {
  const addressToCheck = process.argv[2] || "0x01f51c176c23d7f7dcf806197082faf493e151a5";
  
  console.log("Checking LMSCT balance for:", addressToCheck);
  console.log("─".repeat(60));
  
  // Get the deployed token contract
  const tokenAddress = "0xa513E6E4b8f2a923D98304ec87F64353C4D5C853";
  const LMSToken = await hre.ethers.getContractAt("LMSCourseToken", tokenAddress);
  
  try {
    // Simple balance check
    const provider = hre.ethers.provider;
    const iface = new hre.ethers.Interface([
      'function balanceOf(address) view returns (uint256)',
      'function symbol() view returns (string)',
      'function decimals() view returns (uint8)'
    ]);
    
    // Get balance
    const balanceData = iface.encodeFunctionData('balanceOf', [addressToCheck]);
    const balanceResult = await provider.call({ to: tokenAddress, data: balanceData });
    const balance = iface.decodeFunctionResult('balanceOf', balanceResult)[0];
    
    console.log("Balance (raw):", balance.toString());
    console.log("Balance:", hre.ethers.formatEther(balance), "LMSCT");
    
    if (balance > 0n) {
      console.log("\n✅ You have tokens!");
      console.log("   Token Address:", tokenAddress);
      console.log("   Symbol: LMSCT");
      console.log("   Decimals: 18");
      console.log("\n   If MetaMask shows 0, try:");
      console.log("   1. Remove the token from MetaMask");
      console.log("   2. Re-import it");
      console.log("   3. Switch networks and back");
      console.log("   4. Restart MetaMask");
    } else {
      console.log("\n❌ No tokens found.");
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
