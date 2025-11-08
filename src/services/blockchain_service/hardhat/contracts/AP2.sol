// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title AP2 - Agent Payment Protocol (minimal example)
 * @notice This contract provides a simple escrow and agent-execution pattern.
 * - Buyers deposit ERC20 tokens into escrow for a course purchase
 * - Registered agents may execute the purchase, releasing funds to recipient and emitting events
 * - Owner may register/unregister agents
 *
 * NOTE: This is a minimal educational example and not production-ready.
 */
contract AP2 is Ownable {
    /**
     * Ensure Ownable base gets initialized with deployer as owner for OpenZeppelin versions
     * where Ownable requires an initialOwner constructor argument.
     */
    constructor() Ownable(msg.sender) {}
    struct Purchase {
        address buyer;
        address token; // ERC20 token used for payment
        uint256 amount;
        address recipient; // funds receiver (instructor/platform)
        uint256 courseId;
        bool executed;
        uint256 createdAt;
    }

    mapping(uint256 => Purchase) public purchases;
    mapping(address => bool) public agents;

    event AgentRegistered(address indexed agent);
    event AgentUnregistered(address indexed agent);
    event PurchaseInitiated(uint256 indexed purchaseId, address indexed buyer, uint256 amount, uint256 courseId);
    event PurchaseExecuted(uint256 indexed purchaseId, address indexed agent, address indexed recipient, uint256 amount);

    modifier onlyAgent() {
        require(agents[msg.sender], "Not an authorized agent");
        _;
    }

    function registerAgent(address agent) external onlyOwner {
        agents[agent] = true;
        emit AgentRegistered(agent);
    }

    function unregisterAgent(address agent) external onlyOwner {
        agents[agent] = false;
        emit AgentUnregistered(agent);
    }

    /**
     * @notice Buyer must call ERC20.approve(AP2_address, amount) before calling this function
     */
    function initiatePurchase(uint256 purchaseId, address token, uint256 amount, address recipient, uint256 courseId) external {
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

    /**
     * @notice Authorized agent executes the purchase: transfers escrowed tokens to recipient
     */
    function executePurchase(uint256 purchaseId) external onlyAgent {
        Purchase storage p = purchases[purchaseId];
        require(p.buyer != address(0), "Purchase not found");
        require(!p.executed, "Already executed");
        require(p.amount > 0, "Nothing to transfer");

        p.executed = true;

        // Transfer funds to recipient
        bool ok = IERC20(p.token).transfer(p.recipient, p.amount);
        require(ok, "Token transfer to recipient failed");

        emit PurchaseExecuted(purchaseId, msg.sender, p.recipient, p.amount);
    }

    /**
     * @notice Owner can retrieve stuck tokens after a long timeout (emergency)
     */
    function emergencyWithdraw(uint256 purchaseId) external onlyOwner {
        Purchase storage p = purchases[purchaseId];
        require(p.buyer != address(0), "Purchase not found");
        require(!p.executed, "Already executed");
        // simple safety: require >30 days passed
        require(block.timestamp > p.createdAt + 30 days, "Too early for emergency withdraw");

        uint256 amount = p.amount;
        p.amount = 0;
        p.executed = true;

        bool ok = IERC20(p.token).transfer(owner(), amount);
        require(ok, "Emergency transfer failed");
    }
}
