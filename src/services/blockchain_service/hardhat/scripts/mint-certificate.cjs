/**
 * Mint NFT Certificate Script
 * Usage: node scripts/mint-certificate.cjs <recipient_address> <token_uri>
 */

const hre = require("hardhat");

async function main() {
    const args = process.argv.slice(2);
    
    if (args.length < 2) {
        console.error("Usage: node scripts/mint-certificate.cjs <recipient_address> <token_uri>");
        console.error("Example: node scripts/mint-certificate.cjs 0x123... https://ipfs.io/ipfs/QmX...");
        process.exit(1);
    }

    const recipientAddress = args[0];
    const tokenURI = args[1];

    console.log("Minting NFT Certificate...");
    console.log("Recipient:", recipientAddress);
    console.log("Token URI:", tokenURI);

    // Get the deployed certificate contract address from deployment
    const fs = require('fs');
    const path = require('path');
    
    let certificateAddress;
    try {
        const deploymentPath = path.join(__dirname, '../deployments/localhost.json');
        if (fs.existsSync(deploymentPath)) {
            const deployment = JSON.parse(fs.readFileSync(deploymentPath, 'utf8'));
            certificateAddress = deployment.LMSCertificateNFT;
        }
    } catch (error) {
        console.warn("Could not read deployment file, will use hardcoded address");
    }

    // Fallback to hardcoded address
    if (!certificateAddress) {
        certificateAddress = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512";
    }

    console.log("Certificate Contract:", certificateAddress);

    // Get the contract
    const CertificateNFT = await hre.ethers.getContractFactory("LMSCertificateNFT");
    const certificate = await CertificateNFT.attach(certificateAddress);

    // Get signer (deployer/admin)
    const [signer] = await hre.ethers.getSigners();
    console.log("Admin/Signer:", signer.address);

    try {
        // Mint the certificate
        const tx = await certificate.mintCertificate(recipientAddress, tokenURI);
        console.log("Transaction sent:", tx.hash);
        
        const receipt = await tx.wait();
        console.log("Transaction confirmed in block:", receipt.blockNumber);

        // Get the token ID from the Transfer event
        const transferEvent = receipt.events?.find(e => e.event === 'Transfer');
        const tokenId = transferEvent?.args?.tokenId || transferEvent?.args?.[2];

        console.log("\n✅ Certificate Minted Successfully!");
        console.log("Token ID:", tokenId?.toString());
        console.log("Owner:", recipientAddress);
        console.log("Token URI:", tokenURI);
        console.log("Transaction Hash:", tx.hash);

        // Output JSON for programmatic parsing
        console.log("\nJSON_OUTPUT:", JSON.stringify({
            success: true,
            tokenId: tokenId?.toString(),
            owner: recipientAddress,
            tokenURI: tokenURI,
            transactionHash: tx.hash,
            contractAddress: certificateAddress,
            blockNumber: receipt.blockNumber
        }));

    } catch (error) {
        console.error("\n❌ Minting Failed!");
        console.error("Error:", error.message);
        
        // Output JSON error for programmatic parsing
        console.log("\nJSON_OUTPUT:", JSON.stringify({
            success: false,
            error: error.message
        }));
        
        process.exit(1);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
