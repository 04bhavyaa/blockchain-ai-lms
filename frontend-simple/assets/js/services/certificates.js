/**
 * Certificate Service
 * Handles certificate fetching, verification, and blockchain interactions
 */

import { API_ENDPOINTS } from '../config/api.js';
import { AuthService } from './auth.js';
import { ContractsService } from '../web3/contracts.js';
import { WalletService } from '../web3/wallet.js';

export const CertificateService = {
    /**
     * Fetch all certificates for the authenticated user
     */
    async getMyCertificates() {
        try {
            const response = await fetch(API_ENDPOINTS.BLOCKCHAIN.MY_CERTIFICATES, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${AuthService.getAccessToken()}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: Failed to fetch certificates`);
            }

            const result = await response.json();
            return result.data || [];
        } catch (error) {
            console.error('Get certificates error:', error);
            throw error;
        }
    },

    /**
     * Issue a new certificate for a completed course
     */
    async issueCertificate(courseId, courseName, completionDate, metadata = {}) {
        try {
            const response = await fetch(API_ENDPOINTS.BLOCKCHAIN.ISSUE_CERTIFICATE, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${AuthService.getAccessToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    course_id: courseId,
                    course_name: courseName,
                    completion_date: completionDate,
                    metadata: metadata
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to issue certificate');
            }

            const result = await response.json();
            return result.data;
        } catch (error) {
            console.error('Issue certificate error:', error);
            throw error;
        }
    },

    /**
     * Verify certificate ownership on blockchain
     */
    async verifyCertificateOnChain(tokenId) {
        try {
            const walletConnected = await WalletService.isWalletConnected();
            if (!walletConnected) {
                throw new Error('Wallet not connected');
            }

            const certData = await ContractsService.verifyCertificate(tokenId);
            
            return {
                isValid: true,
                owner: certData.owner,
                tokenURI: certData.tokenURI,
                verified_at: new Date().toISOString()
            };
        } catch (error) {
            console.error('Verify certificate on-chain error:', error);
            throw error;
        }
    },

    /**
     * Get certificate metadata from tokenURI (IPFS or HTTP)
     */
    async getCertificateMetadata(tokenURI) {
        try {
            // Handle IPFS URLs
            if (tokenURI.startsWith('ipfs://')) {
                const ipfsHash = tokenURI.replace('ipfs://', '');
                tokenURI = `https://ipfs.io/ipfs/${ipfsHash}`;
            }

            const response = await fetch(tokenURI);
            if (!response.ok) {
                throw new Error('Failed to fetch metadata');
            }

            return await response.json();
        } catch (error) {
            console.error('Get metadata error:', error);
            throw error;
        }
    },

    /**
     * Get certificate statistics for the user
     */
    async getCertificateStats() {
        try {
            const certificates = await this.getMyCertificates();
            
            return {
                total: certificates.length,
                minted: certificates.filter(c => c.status === 'minted').length,
                pending: certificates.filter(c => c.status === 'pending' || c.status === 'minting').length,
                failed: certificates.filter(c => c.status === 'failed').length,
                verified: certificates.filter(c => c.status === 'verified').length
            };
        } catch (error) {
            console.error('Get stats error:', error);
            throw error;
        }
    },

    /**
     * Get user's NFT certificates from blockchain
     */
    async getBlockchainCertificates(walletAddress) {
        try {
            const walletConnected = await WalletService.isWalletConnected();
            if (!walletConnected) {
                throw new Error('Wallet not connected');
            }

            const certificates = await ContractsService.getUserCertificates(walletAddress);
            return certificates;
        } catch (error) {
            console.error('Get blockchain certificates error:', error);
            throw error;
        }
    },

    /**
     * Request certificate minting (trigger backend to mint NFT)
     */
    async requestMinting(certificateId) {
        try {
            const response = await fetch(`${API_ENDPOINTS.BLOCKCHAIN.CERTIFICATES}${certificateId}/mint/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${AuthService.getAccessToken()}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to request minting');
            }

            const result = await response.json();
            return result.data;
        } catch (error) {
            console.error('Request minting error:', error);
            throw error;
        }
    },

    /**
     * Download certificate as PDF (placeholder - would integrate with backend)
     */
    async downloadCertificate(certificateId) {
        try {
            // This would call a backend endpoint that generates a PDF
            const response = await fetch(`${API_ENDPOINTS.BLOCKCHAIN.CERTIFICATES}${certificateId}/download/`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${AuthService.getAccessToken()}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to download certificate');
            }

            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `certificate_${certificateId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Download certificate error:', error);
            throw error;
        }
    }
};
