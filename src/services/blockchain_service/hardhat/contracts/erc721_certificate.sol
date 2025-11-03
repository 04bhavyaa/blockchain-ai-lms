// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
contract LMSCertificateNFT is ERC721URIStorage {
    address public admin;
    uint256 public nextTokenId;
    constructor() ERC721("LMS Certificate NFT", "LMSCNFT") { admin = msg.sender; }
    function mintCertificate(address to, string memory tokenURI) external returns (uint256) {
        require(msg.sender == admin, "Admin only");
        uint256 tokenId = nextTokenId++;
        _mint(to, tokenId);
        _setTokenURI(tokenId, tokenURI);
        return tokenId;
    }
}
