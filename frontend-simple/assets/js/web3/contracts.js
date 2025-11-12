import { WEB3_CONFIG, loadABI } from '../config/web3_config.js';
import { WalletService } from './wallet.js';
import { showAlert } from '../utils/utils.js';

export const ContractsService = {
    // Get LMS token balance
    async getTokenBalance(walletAddress) {
        try {
            const erc20ABI = await loadABI('ERC20');
            if (!erc20ABI) {
                throw new Error('Failed to load ERC20 ABI');
            }

            const contract = new window.ethers.Contract(
                WEB3_CONFIG.CONTRACTS.LMS_TOKEN,
                erc20ABI,
                new window.ethers.providers.Web3Provider(window.ethereum)
            );

            const balance = await contract.balanceOf(walletAddress);
            const decimals = await contract.decimals();
            
            // Convert to human-readable format
            const balanceFormatted = window.ethers.utils.formatUnits(balance, decimals);
            return parseFloat(balanceFormatted);
        } catch (error) {
            console.error('Get token balance error:', error);
            throw error;
        }
    },

    // Transfer LMS tokens
    async transferTokens(toAddress, amount) {
        try {
            const erc20ABI = await loadABI('ERC20');
            if (!erc20ABI) {
                throw new Error('Failed to load ERC20 ABI');
            }

            const provider = new window.ethers.providers.Web3Provider(window.ethereum);
            const signer = provider.getSigner();

            const contract = new window.ethers.Contract(
                WEB3_CONFIG.CONTRACTS.LMS_TOKEN,
                erc20ABI,
                signer
            );

            const decimals = await contract.decimals();
            const amountInWei = window.ethers.utils.parseUnits(amount.toString(), decimals);

            const tx = await contract.transfer(toAddress, amountInWei);
            showAlert('info', 'Transaction submitted. Waiting for confirmation...');

            const receipt = await tx.wait();
            showAlert('success', `Transfer successful! Tx: ${receipt.transactionHash}`);
            
            return receipt;
        } catch (error) {
            console.error('Transfer tokens error:', error);
            showAlert('error', error.message);
            throw error;
        }
    },

    // Get user's NFT certificates
    async getUserCertificates(walletAddress) {
        try {
            const erc721ABI = await loadABI('ERC721');
            if (!erc721ABI) {
                throw new Error('Failed to load ERC721 ABI');
            }

            const contract = new window.ethers.Contract(
                WEB3_CONFIG.CONTRACTS.CERTIFICATE_NFT,
                erc721ABI,
                new window.ethers.providers.Web3Provider(window.ethereum)
            );

            const balance = await contract.balanceOf(walletAddress);
            const certificates = [];

            // Get all token IDs owned by user
            for (let i = 0; i < balance; i++) {
                const tokenId = await contract.tokenOfOwnerByIndex(walletAddress, i);
                const tokenURI = await contract.tokenURI(tokenId);
                
                certificates.push({
                    tokenId: tokenId.toString(),
                    tokenURI: tokenURI,
                });
            }

            return certificates;
        } catch (error) {
            console.error('Get certificates error:', error);
            throw error;
        }
    },

    // Verify certificate ownership
    async verifyCertificate(tokenId) {
        try {
            const erc721ABI = await loadABI('ERC721');
            if (!erc721ABI) {
                throw new Error('Failed to load ERC721 ABI');
            }

            const contract = new window.ethers.Contract(
                WEB3_CONFIG.CONTRACTS.CERTIFICATE_NFT,
                erc721ABI,
                new window.ethers.providers.Web3Provider(window.ethereum)
            );

            const owner = await contract.ownerOf(tokenId);
            const tokenURI = await contract.tokenURI(tokenId);

            return {
                owner: owner,
                tokenURI: tokenURI,
            };
        } catch (error) {
            console.error('Verify certificate error:', error);
            throw error;
        }
    },

    // Approve token spending (for AP2 payments)
    async approveTokenSpending(spenderAddress, amount) {
        try {
            const erc20ABI = await loadABI('ERC20');
            if (!erc20ABI) {
                throw new Error('Failed to load ERC20 ABI');
            }

            const provider = new window.ethers.providers.Web3Provider(window.ethereum);
            const signer = provider.getSigner();

            const contract = new window.ethers.Contract(
                WEB3_CONFIG.CONTRACTS.LMS_TOKEN,
                erc20ABI,
                signer
            );

            const decimals = await contract.decimals();
            const amountInWei = window.ethers.utils.parseUnits(amount.toString(), decimals);

            const tx = await contract.approve(spenderAddress, amountInWei);
            showAlert('info', 'Approval submitted. Waiting for confirmation...');

            const receipt = await tx.wait();
            showAlert('success', 'Token spending approved!');
            
            return receipt;
        } catch (error) {
            console.error('Approve token spending error:', error);
            showAlert('error', error.message);
            throw error;
        }
    },

    // Check token allowance
    async checkAllowance(ownerAddress, spenderAddress) {
        try {
            const erc20ABI = await loadABI('ERC20');
            if (!erc20ABI) {
                throw new Error('Failed to load ERC20 ABI');
            }

            const contract = new window.ethers.Contract(
                WEB3_CONFIG.CONTRACTS.LMS_TOKEN,
                erc20ABI,
                new window.ethers.providers.Web3Provider(window.ethereum)
            );

            const allowance = await contract.allowance(ownerAddress, spenderAddress);
            const decimals = await contract.decimals();
            
            const allowanceFormatted = window.ethers.utils.formatUnits(allowance, decimals);
            return parseFloat(allowanceFormatted);
        } catch (error) {
            console.error('Check allowance error:', error);
            throw error;
        }
    },
};
