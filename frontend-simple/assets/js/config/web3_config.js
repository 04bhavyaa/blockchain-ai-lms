// Web3 Configuration for localhost/Hardhat network

const WEB3_CONFIG = {
    // Network Configuration (Hardhat localhost)
    NETWORK: {
        CHAIN_ID: '0x7a69', // 31337 in hex (Hardhat default)
        CHAIN_ID_DECIMAL: 31337,
        NETWORK_NAME: 'Hardhat Local',
        RPC_URL: 'http://127.0.0.1:8545',
        CURRENCY_SYMBOL: 'ETH',
        CURRENCY_DECIMALS: 18,
        BLOCK_EXPLORER: null, // No block explorer for localhost
    },

    // Contract Addresses (from deployment-localhost.json)
    CONTRACTS: {
        LMS_TOKEN: '0x5fbdb2315678afecb367f032d93f642f64180aa3', 
        CERTIFICATE_NFT: '0xe7f1725e7734ce288f8367e1bb143e90bb3f0512', 
        AP2_PAYMENT: '0x9fe46736679d2d9a65f0992f2272de9f3c7fa6e0', 
    },

    // Token Configuration
    TOKEN: {
        NAME: 'LMS Token',
        SYMBOL: 'LMS',
        DECIMALS: 18,
    },

    // Gas Settings
    GAS: {
        LIMIT: 300000,
        PRICE: null, // Let MetaMask estimate
    },
};

// ABI Paths
const ABI_PATHS = {
    ERC20: '/public/abis/LMSCourseToken.json',
    ERC721: '/public/abis/LMSCertificateNFT.json',
    AP2: '/public/abis/AP2.json',
};

// Load ABIs from files
async function loadABI(abiName) {
    try {
        const response = await fetch(ABI_PATHS[abiName]);
        if (!response.ok) {
            throw new Error(`Failed to load ${abiName} ABI`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error loading ${abiName} ABI:`, error);
        return null;
    }
}

export { WEB3_CONFIG, ABI_PATHS, loadABI };
