// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract LMSCourseToken is ERC20 {
    constructor() ERC20("LMS Course Token", "LMSCT") {
        _mint(msg.sender, 1000000 ether); // 1M tokens to deployer
    }
}
