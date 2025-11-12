/**
 * Smart Contract Interaction Module
 * Handles all blockchain interactions using ethers.js v6
 * Requires: ethers.js v6 loaded via CDN
 * <script src="https://cdn.jsdelivr.net/npm/ethers@6/dist/ethers.umd.min.js"></script>
 */

/**
 * Get ethers provider and signer from MetaMask
 */
async function getProviderAndSigner() {
    if (!window.ethereum) {
        throw new Error('MetaMask not installed. Please install MetaMask extension.');
    }
    
    const provider = new ethers.BrowserProvider(window.ethereum);
    await provider.send("eth_requestAccounts", []); // Request accounts
    const signer = await provider.getSigner();
    
    return { provider, signer };
}

/**
 * Check if on correct network (Hardhat localhost)
 */
async function checkNetwork() {
    try {
        const { provider } = await getProviderAndSigner();
        const network = await provider.getNetwork();
        const chainId = '0x' + network.chainId.toString(16);
        
        if (chainId !== window.WEB3_CONFIG.NETWORK.chainId) {
            throw new Error(`Wrong network. Please switch to ${window.WEB3_CONFIG.NETWORK.name}`);
        }
        
        return true;
    } catch (error) {
        console.error('Network check failed:', error);
        throw error;
    }
}

/**
 * Get user's token balance
 */
async function getTokenBalance(userAddress) {
    try {
        const { provider } = await getProviderAndSigner();
        const tokenContract = new ethers.Contract(
            window.WEB3_CONFIG.CONTRACTS.TOKEN.address,
            window.ERC20_ABI,
            provider
        );
        
        const balance = await tokenContract.balanceOf(userAddress);
        const decimals = await tokenContract.decimals();
        
        return ethers.formatUnits(balance, decimals);
    } catch (error) {
        console.error('Error getting token balance:', error);
        return '0';
    }
}

/**
 * Check token allowance
 */
async function checkAllowance(ownerAddress, spenderAddress) {
    try {
        const { provider } = await getProviderAndSigner();
        const tokenContract = new ethers.Contract(
            window.WEB3_CONFIG.CONTRACTS.TOKEN.address,
            window.ERC20_ABI,
            provider
        );
        
        const allowance = await tokenContract.allowance(ownerAddress, spenderAddress);
        const decimals = await tokenContract.decimals();
        
        return ethers.formatUnits(allowance, decimals);
    } catch (error) {
        console.error('Error checking allowance:', error);
        return '0';
    }
}

/**
 * Approve ERC20 tokens for spending
 * @param {string} spenderAddress - Address that can spend tokens
 * @param {string} amount - Amount to approve (in token units, e.g., "100")
 * @returns {Promise<object>} Transaction receipt
 */
async function approveERC20(spenderAddress, amount) {
    try {
        await checkNetwork();
        const { signer } = await getProviderAndSigner();
        
        const tokenContract = new ethers.Contract(
            window.WEB3_CONFIG.CONTRACTS.TOKEN.address,
            window.ERC20_ABI,
            signer
        );
        
        // Get decimals
        const decimals = await tokenContract.decimals();
        
        // Parse amount to Wei equivalent
        const amountWei = ethers.parseUnits(amount.toString(), decimals);
        
        console.log(`Approving ${amount} tokens (${amountWei.toString()} wei) for ${spenderAddress}`);
        
        // Send transaction
        const tx = await tokenContract.approve(spenderAddress, amountWei);
        console.log('Approval transaction sent:', tx.hash);
        
        // Wait for confirmation
        const receipt = await tx.wait();
        console.log('Approval confirmed:', receipt);
        
        return receipt;
    } catch (error) {
        console.error('Error approving tokens:', error);
        throw error;
    }
}

/**
 * Transfer ERC20 tokens
 * @param {string} toAddress - Recipient address
 * @param {string} amount - Amount to transfer
 * @returns {Promise<object>} Transaction receipt
 */
async function transferERC20(toAddress, amount) {
    try {
        await checkNetwork();
        const { signer } = await getProviderAndSigner();
        
        const tokenContract = new ethers.Contract(
            window.WEB3_CONFIG.CONTRACTS.TOKEN.address,
            window.ERC20_ABI,
            signer
        );
        
        const decimals = await tokenContract.decimals();
        const amountWei = ethers.parseUnits(amount.toString(), decimals);
        
        const tx = await tokenContract.transfer(toAddress, amountWei);
        const receipt = await tx.wait();
        
        return receipt;
    } catch (error) {
        console.error('Error transferring tokens:', error);
        throw error;
    }
}

/**
 * Get user's certificate NFTs
 * @param {string} userAddress - User's wallet address
 * @returns {Promise<number>} Number of certificates owned
 */
async function getCertificateBalance(userAddress) {
    try {
        const { provider } = await getProviderAndSigner();
        const certificateContract = new ethers.Contract(
            window.WEB3_CONFIG.CONTRACTS.CERTIFICATE.address,
            window.ERC721_ABI,
            provider
        );
        
        const balance = await certificateContract.balanceOf(userAddress);
        return balance.toString();
    } catch (error) {
        console.error('Error getting certificate balance:', error);
        return '0';
    }
}

/**
 * Add Hardhat localhost network to MetaMask
 */
async function addHardhatNetwork() {
    try {
        await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [{
                chainId: window.WEB3_CONFIG.NETWORK.chainId,
                chainName: window.WEB3_CONFIG.NETWORK.name,
                nativeCurrency: window.WEB3_CONFIG.NETWORK.currency,
                rpcUrls: [window.WEB3_CONFIG.NETWORK.rpcUrl]
            }]
        });
        
        return true;
    } catch (error) {
        console.error('Error adding network:', error);
        throw error;
    }
}

/**
 * Switch to Hardhat localhost network
 */
async function switchToHardhatNetwork() {
    try {
        await window.ethereum.request({
            method: 'wallet_switchEthereumChain',
            params: [{ chainId: window.WEB3_CONFIG.NETWORK.chainId }],
        });
        
        return true;
    } catch (error) {
        // Network not added, try adding it
        if (error.code === 4902) {
            return await addHardhatNetwork();
        }
        
        console.error('Error switching network:', error);
        throw error;
    }
}

// Export all functions to window.contracts
window.contracts = {
    getProviderAndSigner,
    checkNetwork,
    getTokenBalance,
    checkAllowance,
    approveERC20,
    transferERC20,
    getCertificateBalance,
    addHardhatNetwork,
    switchToHardhatNetwork
};

console.log('✅ Contracts module loaded');
