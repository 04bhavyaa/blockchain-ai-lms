// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract AP2 is Ownable {
    struct Purchase {
        address buyer;
        address token;      // ERC20 token address
        uint256 amount;
        address recipient;  // Platform/instructor
        uint256 courseId;
        bool executed;
        uint256 createdAt;
    }

    mapping(uint256 => Purchase) public purchases;
    mapping(address => bool) public agents; // Authorized AI agents

    event AgentRegistered(address indexed agent);
    event AgentUnregistered(address indexed agent);
    event PurchaseInitiated(uint256 indexed purchaseId, address indexed buyer, uint256 amount, uint256 courseId);
    event PurchaseExecuted(uint256 indexed purchaseId, address indexed agent, address indexed recipient, uint256 amount);

    constructor() Ownable(msg.sender) {}

    // Owner registers AI agent addresses
    function registerAgent(address agent) external onlyOwner {
        agents[agent] = true;
        emit AgentRegistered(agent);
    }

    function unregisterAgent(address agent) external onlyOwner {
        agents[agent] = false;
        emit AgentUnregistered(agent);
    }

    // Buyer deposits tokens into escrow
    function initiatePurchase(
        uint256 purchaseId,
        address token,
        uint256 amount,
        address recipient,
        uint256 courseId
    ) external {
        require(purchases[purchaseId].buyer == address(0), "Purchase already exists");
        require(amount > 0, "Amount must be > 0");

        // Transfer tokens from buyer to this contract (escrow)
        bool ok = IERC20(token).transferFrom(msg.sender, address(this), amount);
        require(ok, "Token transfer failed");

        purchases[purchaseId] = Purchase({
            buyer: msg.sender,
            token: token,
            amount: amount,
            recipient: recipient,
            courseId: courseId,
            executed: false,
            createdAt: block.timestamp
        });

        emit PurchaseInitiated(purchaseId, msg.sender, amount, courseId);
    }

    // Authorized agent executes the purchase
    function executePurchase(uint256 purchaseId) external {
        require(agents[msg.sender], "Not an authorized agent");
        Purchase storage p = purchases[purchaseId];
        require(p.buyer != address(0), "Purchase not found");
        require(!p.executed, "Already executed");
        require(p.amount > 0, "Nothing to transfer");

        p.executed = true;

        // Transfer funds to recipient (platform/instructor)
        bool ok = IERC20(p.token).transfer(p.recipient, p.amount);
        require(ok, "Token transfer to recipient failed");

        emit PurchaseExecuted(purchaseId, msg.sender, p.recipient, p.amount);
    }

    // Emergency withdrawal after 30 days
    function emergencyWithdraw(uint256 purchaseId) external onlyOwner {
        Purchase storage p = purchases[purchaseId];
        require(p.buyer != address(0), "Purchase not found");
        require(!p.executed, "Already executed");
        require(block.timestamp >= p.createdAt + 30 days, "Too early for emergency withdraw");

        uint256 amount = p.amount;
        p.amount = 0;
        p.executed = true;

        bool ok = IERC20(p.token).transfer(owner(), amount);
        require(ok, "Emergency transfer failed");
    }
}
