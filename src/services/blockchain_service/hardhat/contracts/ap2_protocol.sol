// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract AP2AgentPurchase {
    event AP2Purchase(address indexed agent, address indexed user, uint256 courseId, uint256 amount, bytes32 payloadHash);
    function purchaseWithAgent(address user, uint256 courseId, uint256 amount, bytes calldata agentSig) external returns (bool) {
        bytes32 payloadHash = keccak256(abi.encodePacked(user, courseId, amount, agentSig));
        emit AP2Purchase(msg.sender, user, courseId, amount, payloadHash);
        return true;
    }
}
