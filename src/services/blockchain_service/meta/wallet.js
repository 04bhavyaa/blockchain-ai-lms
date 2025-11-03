// import { connectWallet, getAccount } from "./metamask";
// export async function requestWallet() { return await connectWallet(); }
// export async function getWalletAddress(provider) { return await getAccount(provider); }

import { connectWallet, getAccount } from "./metamask";
export async function requestWallet() { return await connectWallet(); }
export async function getWalletAddress(provider) { return await getAccount(provider); }
