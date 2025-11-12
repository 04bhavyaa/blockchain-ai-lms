/**
 * Web3 Configuration for Localhost Hardhat
 * Contract addresses from deploy.js output
 */
window.WEB3_CONFIG = {
    // Network Configuration
    NETWORK: {
        name: 'Hardhat Localhost',
        chainId: '0x7a69', // 31337 in hex
        rpcUrl: 'http://localhost:8545',
        currency: {
            name: 'ETH',
            symbol: 'ETH',
            decimals: 18
        }
    },
    
    // Contract Addresses (from your deploy.js output)
    CONTRACTS: {
        TOKEN: {
            address: '0x5fbdb2315678afecb367f032d93f642f64180aa3',
            name: 'LMSCourseToken',
            symbol: 'LMSCT'
        },
        CERTIFICATE: {
            address: '0xe7f1725e7734ce288f8367e1bb143e90bb3f0512',
            name: 'LMSCertificateNFT',
            symbol: 'LMSCNFT'
        },
        AP2: {
            address: '0x9fe46736679d2d9a65f0992f2272de9f3c7fa6e0',
            name: 'AP2'
        }
    },
    
    // Platform Treasury (Account #0 from Hardhat)
    TREASURY_ADDRESS: '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266',
    
    // Test Accounts (for demo/testing)
    TEST_ACCOUNTS: [
        {
            address: '0x70997970C51812dc3A010C7d01b50e0d17dc79C8',
            privateKey: '0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d',
            balance: '10000 ETH',
            tokens: '10000 LMSCT'
        },
        {
            address: '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC',
            privateKey: '0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a',
            balance: '10000 ETH',
            tokens: '10000 LMSCT'
        },
        {
            address: '0x90F79bf6EB2c4f870365E785982E1f101E93b906',
            privateKey: '0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6',
            balance: '10000 ETH',
            tokens: '10000 LMSCT'
        }
    ]
};

// Minimal ERC20 ABI (balanceOf, approve, transfer, allowance)
window.ERC20_ABI = [
    "function balanceOf(address owner) view returns (uint256)",
    "function approve(address spender, uint256 amount) returns (bool)",
    "function transfer(address to, uint256 amount) returns (bool)",
    "function allowance(address owner, address spender) view returns (uint256)",
    "function decimals() view returns (uint8)",
    "function symbol() view returns (string)",
    "event Transfer(address indexed from, address indexed to, uint256 value)",
    "event Approval(address indexed owner, address indexed spender, uint256 value)"
];

// Minimal ERC721 ABI (for certificates)
window.ERC721_ABI = [
    "function balanceOf(address owner) view returns (uint256)",
    "function ownerOf(uint256 tokenId) view returns (address)",
    "function tokenURI(uint256 tokenId) view returns (string)",
    "event Transfer(address indexed from, address indexed to, uint256 indexed tokenId)"
];
