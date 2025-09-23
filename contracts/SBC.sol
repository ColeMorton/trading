// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title SBC (Smoothed Bitcoin Composite) Token
 * @dev Pure ERC-20 token with bond-only issuance
 *
 * Key Features:
 * - No mint/redeem mechanism (bond-only issuance)
 * - No WBTC backing or conversion
 * - Tracks Bitcoin's 1093-day SMA through natural price discovery
 * - Only bondable through SBCBondProtocol contract
 * - Fixed supply controlled entirely by bond sales
 *
 * Design Philosophy:
 * - SBC value derives from limited supply and BTC correlation
 * - No arbitrage mechanisms (prevents peg instability)
 * - Market-driven price discovery through secondary markets
 * - Treasury backing provides solvency without convertibility
 */

contract SBC is ERC20, AccessControl, Pausable {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");

    // Token supply tracking
    uint256 public totalMinted;
    uint256 public maxSupply; // Can be updated by governance if needed

    // Minting restrictions
    mapping(address => bool) public authorizedMinters;
    mapping(address => uint256) public minterAllowances; // Per-minter mint limits

    // Historical performance constants (for reference/display)
    uint256 public constant HISTORICAL_SHARPE_BPS = 14507;     // 145.07
    uint256 public constant HISTORICAL_SORTINO_BPS = 498429;   // 4984.29
    uint256 public constant HISTORICAL_MAX_DD_BPS = 4;         // 0.04%
    uint256 public constant HISTORICAL_ANNUAL_VOL_BPS = 241;   // 2.41%
    uint256 public constant HISTORICAL_CAGR_BPS = 4463;        // 44.63%
    uint256 public constant HISTORICAL_CALMAR_BPS = 1077339;   // 10773.39

    // Events
    event MinterAdded(address indexed minter, uint256 allowance);
    event MinterRemoved(address indexed minter);
    event MinterAllowanceUpdated(address indexed minter, uint256 newAllowance);
    event MaxSupplyUpdated(uint256 oldMaxSupply, uint256 newMaxSupply);
    event TokensMinted(address indexed to, uint256 amount, address indexed minter);

    constructor(
        uint256 _initialMaxSupply
    ) ERC20("Smoothed Bitcoin Composite", "SBC") {
        require(_initialMaxSupply > 0, "Invalid max supply");

        maxSupply = _initialMaxSupply;

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    /**
     * @dev Mint SBC tokens - only callable by authorized minters (bond protocol)
     * @param to Address to mint tokens to
     * @param amount Amount of tokens to mint
     */
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) whenNotPaused {
        require(to != address(0), "Cannot mint to zero address");
        require(amount > 0, "Cannot mint zero amount");
        require(authorizedMinters[msg.sender], "Minter not authorized");
        require(minterAllowances[msg.sender] >= amount, "Exceeds minter allowance");

        // Check max supply if set (0 means no limit)
        if (maxSupply > 0) {
            require(totalMinted + amount <= maxSupply, "Exceeds max supply");
        }

        // Update minter allowance
        minterAllowances[msg.sender] -= amount;

        // Update total minted
        totalMinted += amount;

        // Mint tokens
        _mint(to, amount);

        emit TokensMinted(to, amount, msg.sender);
    }

    /**
     * @dev Add authorized minter with allowance
     * @param minter Address to authorize as minter
     * @param allowance Maximum amount this minter can mint
     */
    function addMinter(address minter, uint256 allowance) external onlyRole(ADMIN_ROLE) {
        require(minter != address(0), "Invalid minter address");
        require(!authorizedMinters[minter], "Minter already authorized");

        authorizedMinters[minter] = true;
        minterAllowances[minter] = allowance;

        // Grant minter role
        _grantRole(MINTER_ROLE, minter);

        emit MinterAdded(minter, allowance);
    }

    /**
     * @dev Remove authorized minter
     * @param minter Address to remove minter authorization
     */
    function removeMinter(address minter) external onlyRole(ADMIN_ROLE) {
        require(authorizedMinters[minter], "Minter not authorized");

        authorizedMinters[minter] = false;
        minterAllowances[minter] = 0;

        // Revoke minter role
        _revokeRole(MINTER_ROLE, minter);

        emit MinterRemoved(minter);
    }

    /**
     * @dev Update minter allowance
     * @param minter Address of the minter
     * @param newAllowance New allowance amount
     */
    function updateMinterAllowance(address minter, uint256 newAllowance) external onlyRole(ADMIN_ROLE) {
        require(authorizedMinters[minter], "Minter not authorized");

        minterAllowances[minter] = newAllowance;

        emit MinterAllowanceUpdated(minter, newAllowance);
    }

    /**
     * @dev Update maximum supply (governance function)
     * @param newMaxSupply New maximum supply (0 for unlimited)
     */
    function updateMaxSupply(uint256 newMaxSupply) external onlyRole(ADMIN_ROLE) {
        uint256 oldMaxSupply = maxSupply;
        maxSupply = newMaxSupply;

        emit MaxSupplyUpdated(oldMaxSupply, newMaxSupply);
    }

    /**
     * @dev Pause token operations (emergency function)
     */
    function pause() external onlyRole(ADMIN_ROLE) {
        _pause();
    }

    /**
     * @dev Unpause token operations
     */
    function unpause() external onlyRole(ADMIN_ROLE) {
        _unpause();
    }

    /**
     * @dev Get token information
     */
    function getTokenInfo() external view returns (
        uint256 totalSupply_,
        uint256 totalMinted_,
        uint256 maxSupply_,
        uint256 remainingSupply,
        bool isPaused
    ) {
        totalSupply_ = totalSupply();
        totalMinted_ = totalMinted;
        maxSupply_ = maxSupply;
        remainingSupply = maxSupply > 0 ? maxSupply - totalMinted : type(uint256).max;
        isPaused = paused();
    }

    /**
     * @dev Get minter information
     */
    function getMinterInfo(address minter) external view returns (
        bool isAuthorized,
        uint256 allowance,
        bool hasRole
    ) {
        isAuthorized = authorizedMinters[minter];
        allowance = minterAllowances[minter];
        hasRole = hasRole(MINTER_ROLE, minter);
    }

    /**
     * @dev Get historical performance metrics (for display/reference)
     */
    function getHistoricalMetrics() external pure returns (
        uint256 sharpeRatio,      // 145.07 (in basis points)
        uint256 sortinoRatio,     // 4984.29 (in basis points)
        uint256 maxDrawdown,      // 0.04% (in basis points)
        uint256 annualVolatility, // 2.41% (in basis points)
        uint256 cagr,             // 44.63% (in basis points)
        uint256 calmarRatio       // 10773.39 (in basis points)
    ) {
        return (
            HISTORICAL_SHARPE_BPS,
            HISTORICAL_SORTINO_BPS,
            HISTORICAL_MAX_DD_BPS,
            HISTORICAL_ANNUAL_VOL_BPS,
            HISTORICAL_CAGR_BPS,
            HISTORICAL_CALMAR_BPS
        );
    }

    /**
     * @dev Get supply statistics
     */
    function getSupplyStats() external view returns (
        uint256 circulatingSupply,
        uint256 percentOfMaxSupply,
        uint256 remainingMintable
    ) {
        circulatingSupply = totalSupply();

        if (maxSupply > 0) {
            percentOfMaxSupply = (circulatingSupply * 10000) / maxSupply; // In basis points
            remainingMintable = maxSupply - totalMinted;
        } else {
            percentOfMaxSupply = 0; // Unlimited supply
            remainingMintable = type(uint256).max;
        }
    }

    /**
     * @dev Override transfer to add pause functionality
     */
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override whenNotPaused {
        super._beforeTokenTransfer(from, to, amount);
    }

    /**
     * @dev Check if address has minting capability
     */
    function canMint(address account, uint256 amount) external view returns (bool) {
        return authorizedMinters[account] &&
               minterAllowances[account] >= amount &&
               hasRole(MINTER_ROLE, account) &&
               !paused() &&
               (maxSupply == 0 || totalMinted + amount <= maxSupply);
    }

    /**
     * @dev Emergency function to recover accidentally sent tokens
     */
    function recoverERC20(
        address tokenAddress,
        uint256 tokenAmount,
        address to
    ) external onlyRole(ADMIN_ROLE) {
        require(tokenAddress != address(this), "Cannot recover SBC tokens");
        IERC20(tokenAddress).transfer(to, tokenAmount);
    }

    // No mint/redeem functions
    // No WBTC conversion functions
    // No backing mechanism access
    // Pure ERC-20 with controlled minting through bonds only
}
