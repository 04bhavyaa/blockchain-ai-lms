// import { ethers } from "ethers";
// export async function connectWallet() {
//     if (!window.ethereum) { throw new Error('MetaMask required'); }
//     await window.ethereum.request({ method: 'eth_requestAccounts' });
//     return new ethers.providers.Web3Provider(window.ethereum);
// }
// export async function getAccount(provider) {
//     const accounts = await provider.listAccounts();
//     return accounts[0];
// }
// // Approve and purchase functions omitted for brevity, but use erc20 contract ABI, signer, and send tx.

import { ethers } from "ethers";
export async function connectWallet() {
    if (!window.ethereum) throw new Error('MetaMask required');
    await window.ethereum.request({ method: 'eth_requestAccounts' });
    return new ethers.providers.Web3Provider(window.ethereum);
}
export async function getAccount(provider) {
    const accounts = await provider.listAccounts();
    return accounts[0];
}
