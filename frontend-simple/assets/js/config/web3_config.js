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
        LMS_TOKEN: '0xa513E6E4b8f2a923D98304ec87F64353C4D5C853', 
        CERTIFICATE_NFT: '0x2279B7A0a67DB372996a5FaB50D91eAA73d2eBe6', 
        AP2_PAYMENT: '0x8A791620dd6260079BF849Dc5567aDC3F2FdC318', 
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
        const data = await response.json();
        
        // Handle Hardhat artifact format (has 'abi' property)
        if (data.abi) {
            return data.abi;
        }
        
        // Assume it's already an ABI array
        return data;
    } catch (error) {
        console.error(`Error loading ${abiName} ABI:`, error);
        return null;
    }
}

export { WEB3_CONFIG, ABI_PATHS, loadABI };
