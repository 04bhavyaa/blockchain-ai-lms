/*
 * Contract interaction helpers using ethers v5 (UMD)
 * Exposes simple functions: approveERC20, transferERC20, mintNFT
 * Requires ethers to be loaded on the page via CDN: https://cdn.jsdelivr.net/npm/ethers@5.7.2/dist/ethers.umd.min.js
 */

async function loadAbi(name) {
    const resp = await fetch(`/abis/${name}.json`);
    if (!resp.ok) throw new Error('ABI not found: ' + name);
    return resp.json();
}

async function getProviderAndSigner() {
    if (!window.ethereum) throw new Error('MetaMask is not available');
    const provider = new ethers.providers.Web3Provider(window.ethereum);
    // Request accounts if not already granted
    await provider.send('eth_requestAccounts', []);
    const signer = provider.getSigner();
    return { provider, signer };
}

async function approveERC20(tokenAddress, abiName, spender, amount) {
    const abiJson = await loadAbi(abiName);
    const abi = abiJson.abi || abiJson;
    const { signer } = await getProviderAndSigner();
    const token = new ethers.Contract(tokenAddress, abi, signer);

    // Try to read decimals, fall back to 18
    let decimals = 18;
    try { decimals = await token.decimals(); } catch (e) { /* ignore */ }
    const amountParsed = ethers.utils.parseUnits(String(amount), decimals);

    const tx = await token.approve(spender, amountParsed);
    return tx; // caller should await tx.wait() for receipt
}

async function transferERC20(tokenAddress, abiName, to, amount) {
    const abiJson = await loadAbi(abiName);
    const abi = abiJson.abi || abiJson;
    const { signer } = await getProviderAndSigner();
    const token = new ethers.Contract(tokenAddress, abi, signer);
    let decimals = 18;
    try { decimals = await token.decimals(); } catch (e) { /* ignore */ }
    const amountParsed = ethers.utils.parseUnits(String(amount), decimals);
    const tx = await token.transfer(to, amountParsed);
    return tx;
}

async function mintNFT(nftAddress, abiName, to, tokenURI) {
    const abiJson = await loadAbi(abiName);
    const abi = abiJson.abi || abiJson;
    const { signer } = await getProviderAndSigner();
    const nft = new ethers.Contract(nftAddress, abi, signer);
    // Assume a mint(to, tokenURI) or safeMint variant exists; this will fail if ABI differs
    if (nft.mint) {
        return nft.mint(to, tokenURI);
    }
    if (nft.safeMint) {
        return nft.safeMint(to, tokenURI);
    }
    throw new Error('NFT contract does not expose mint/safeMint');
}

// Expose helpers globally
window.contracts = {
    loadAbi,
    approveERC20,
    transferERC20,
    mintNFT,
};
