// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";

/**
 * @title SBC Bond Protocol
 * @dev ERC-1155 semi-fungible bond system for SBC token issuance
 *
 * Core Features:
 * - USD-denominated bond pricing
 * - Automatic USDC→WBTC treasury conversion
 * - User-selectable vesting periods (30-1093 days)
 * - Dynamic yield curve pricing
 * - Monthly cohort grouping for semi-fungible bonds
 * - No SBC→WBTC convertibility (backing without arbitrage)
 */

interface ISMAOracle {
    function get1093DaySMA() external view returns (uint256);
    function getLastUpdate() external view returns (uint256);
    function validateIntegrity() external view returns (bool);
}

interface IYieldCurve {
    function getDiscount(uint256 vestingDays) external view returns (uint256);
    function updateMarketParams() external;
}

interface ITreasuryManager {
    function convertUSDCToWBTC(uint256 usdcAmount, uint256 minWBTCReceived) external returns (uint256);
    function addSBCObligation(uint256 sbcAmount, uint256 maturityTimestamp) external;
    function checkSolvency() external view returns (bool solvent, uint256 excessWBTC);
}

interface ISBC {
    function mint(address to, uint256 amount) external;
}

contract SBCBondProtocol is ERC1155, ReentrancyGuard, AccessControl {
    using SafeERC20 for IERC20;
    using Math for uint256;

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");

    // Core tokens and contracts
    IERC20 public immutable USDC;
    ISBC public immutable SBC;
    ISMAOracle public smaOracle;
    IYieldCurve public yieldCurve;
    ITreasuryManager public treasury;

    // Bond parameters
    uint256 public constant MIN_VESTING = 30 days;
    uint256 public constant MAX_VESTING = 1093 days;
    uint256 public constant COHORT_GRANULARITY = 30 days; // Monthly cohorts
    uint256 public constant MIN_BOND_AMOUNT = 100e6; // 100 USDC minimum

    // Protocol state
    bool public protocolActive = true;
    uint256 public totalSBCIssued;
    uint256 public totalUSDCRaised;

    // Bond cohort data (ERC-1155 token IDs)
    struct Cohort {
        uint256 maturityTimestamp;     // When bonds mature
        uint256 totalSBCOwed;          // Total SBC to be issued
        uint256 totalUSDCRaised;       // Total USDC collected
        uint256 averageDiscount;       // Weighted average discount (basis points)
        uint256 averageVestingDays;    // Weighted average vesting period
        bool matured;                  // Has this cohort matured
        mapping(address => uint256) userContributions; // Track user USDC contributions
    }

    mapping(uint256 => Cohort) public cohorts;
    uint256[] public activeCohortIds;
    mapping(uint256 => bool) public cohortExists;

    // Events
    event BondPurchased(
        address indexed buyer,
        uint256 indexed cohortId,
        uint256 sbcAmount,
        uint256 usdcPaid,
        uint256 discount,
        uint256 vestingDays,
        uint256 maturityTimestamp
    );

    event BondRedeemed(
        address indexed redeemer,
        uint256 indexed cohortId,
        uint256 sbcAmount
    );

    event CohortMatured(
        uint256 indexed cohortId,
        uint256 totalSBC,
        uint256 totalUSDC
    );

    event ProtocolParametersUpdated(
        address indexed oracle,
        address indexed yieldCurve,
        address indexed treasury
    );

    event EmergencyPause(bool paused);

    constructor(
        address _usdc,
        address _sbc,
        address _smaOracle,
        address _yieldCurve,
        address _treasury,
        string memory _uri
    ) ERC1155(_uri) {
        require(_usdc != address(0), "Invalid USDC address");
        require(_sbc != address(0), "Invalid SBC address");
        require(_smaOracle != address(0), "Invalid oracle address");
        require(_yieldCurve != address(0), "Invalid yield curve address");
        require(_treasury != address(0), "Invalid treasury address");

        USDC = IERC20(_usdc);
        SBC = ISBC(_sbc);
        smaOracle = ISMAOracle(_smaOracle);
        yieldCurve = IYieldCurve(_yieldCurve);
        treasury = ITreasuryManager(_treasury);

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    /**
     * @dev Purchase bonds with custom vesting period
     * @param usdcAmount Amount of USDC to pay
     * @param vestingDays Number of days until maturity (30-1093)
     * @param maxDiscount Maximum acceptable discount (slippage protection)
     * @param minWBTCFromConversion Minimum WBTC expected from USDC conversion
     */
    function purchaseBond(
        uint256 usdcAmount,
        uint256 vestingDays,
        uint256 maxDiscount,
        uint256 minWBTCFromConversion
    ) external nonReentrant returns (uint256 cohortId) {
        require(protocolActive, "Protocol paused");
        require(vestingDays >= MIN_VESTING && vestingDays <= MAX_VESTING, "Invalid vesting period");
        require(usdcAmount >= MIN_BOND_AMOUNT, "Bond amount too small");

        // Validate oracle integrity
        require(smaOracle.validateIntegrity(), "Oracle integrity check failed");

        // Get current discount from yield curve
        uint256 discount = yieldCurve.getDiscount(vestingDays);
        require(discount <= maxDiscount, "Discount exceeds maximum");

        // Calculate SBC amount based on USD pricing
        uint256 currentSMA = smaOracle.get1093DaySMA(); // In USD (e.g., $60,000)
        require(currentSMA > 0, "Invalid SMA price");

        uint256 discountedPrice = (currentSMA * (10000 - discount)) / 10000;
        uint256 sbcAmount = (usdcAmount * 1e18) / discountedPrice; // SBC has 18 decimals, USDC has 6

        require(sbcAmount > 0, "Invalid SBC amount calculated");

        // Determine cohort (monthly buckets based on maturity)
        uint256 maturityTimestamp = block.timestamp + vestingDays;
        cohortId = getCohortId(maturityTimestamp);

        // Update or create cohort
        Cohort storage cohort = cohorts[cohortId];
        if (!cohortExists[cohortId]) {
            cohort.maturityTimestamp = roundToMonthStart(maturityTimestamp);
            activeCohortIds.push(cohortId);
            cohortExists[cohortId] = true;
        }

        // Update cohort accounting with weighted averages
        uint256 previousTotalUSDC = cohort.totalUSDCRaised;
        uint256 previousTotalSBC = cohort.totalSBCOwed;

        cohort.totalSBCOwed += sbcAmount;
        cohort.totalUSDCRaised += usdcAmount;

        // Calculate weighted average discount
        if (previousTotalUSDC > 0) {
            cohort.averageDiscount = (cohort.averageDiscount * previousTotalUSDC + discount * usdcAmount) / cohort.totalUSDCRaised;
            cohort.averageVestingDays = (cohort.averageVestingDays * previousTotalSBC + vestingDays * sbcAmount) / cohort.totalSBCOwed;
        } else {
            cohort.averageDiscount = discount;
            cohort.averageVestingDays = vestingDays;
        }

        cohort.userContributions[msg.sender] += usdcAmount;

        // Mint semi-fungible bond tokens
        _mint(msg.sender, cohortId, sbcAmount, "");

        // Transfer USDC from user
        USDC.safeTransferFrom(msg.sender, address(this), usdcAmount);

        // Approve and convert USDC to WBTC via treasury
        USDC.safeApprove(address(treasury), usdcAmount);
        treasury.convertUSDCToWBTC(usdcAmount, minWBTCFromConversion);

        // Add SBC obligation to treasury tracking
        treasury.addSBCObligation(sbcAmount, cohort.maturityTimestamp);

        // Update protocol totals
        totalSBCIssued += sbcAmount;
        totalUSDCRaised += usdcAmount;

        emit BondPurchased(
            msg.sender,
            cohortId,
            sbcAmount,
            usdcAmount,
            discount,
            vestingDays,
            cohort.maturityTimestamp
        );

        return cohortId;
    }

    /**
     * @dev Redeem matured bonds for SBC tokens
     * @param cohortId The cohort ID to redeem
     */
    function redeemMaturedBonds(uint256 cohortId) external nonReentrant {
        require(cohortExists[cohortId], "Cohort does not exist");

        Cohort storage cohort = cohorts[cohortId];
        require(block.timestamp >= cohort.maturityTimestamp, "Bonds not yet matured");

        uint256 bondBalance = balanceOf(msg.sender, cohortId);
        require(bondBalance > 0, "No bonds to redeem");

        // Check treasury solvency
        (bool solvent,) = treasury.checkSolvency();
        require(solvent, "Treasury insufficient for redemption");

        // Burn bond tokens
        _burn(msg.sender, cohortId, bondBalance);

        // Mint and transfer SBC to user
        SBC.mint(msg.sender, bondBalance);

        // Mark cohort as matured if this is first redemption
        if (!cohort.matured) {
            cohort.matured = true;
            emit CohortMatured(cohortId, cohort.totalSBCOwed, cohort.totalUSDCRaised);
        }

        emit BondRedeemed(msg.sender, cohortId, bondBalance);
    }

    /**
     * @dev Batch redeem multiple cohorts
     * @param cohortIds Array of cohort IDs to redeem
     */
    function batchRedeemBonds(uint256[] calldata cohortIds) external {
        for (uint256 i = 0; i < cohortIds.length; i++) {
            if (balanceOf(msg.sender, cohortIds[i]) > 0) {
                redeemMaturedBonds(cohortIds[i]);
            }
        }
    }

    /**
     * @dev Get cohort ID from maturity timestamp (monthly buckets)
     */
    function getCohortId(uint256 timestamp) public pure returns (uint256) {
        return timestamp / COHORT_GRANULARITY; // 30-day buckets
    }

    /**
     * @dev Round timestamp to start of month bucket
     */
    function roundToMonthStart(uint256 timestamp) public pure returns (uint256) {
        return (timestamp / COHORT_GRANULARITY) * COHORT_GRANULARITY;
    }

    /**
     * @dev Get comprehensive user bond information
     */
    function getUserBonds(address user) external view returns (
        uint256[] memory cohortIds,
        uint256[] memory bondAmounts,
        uint256[] memory maturities,
        uint256[] memory discounts,
        bool[] memory matured
    ) {
        uint256 count = activeCohortIds.length;
        uint256[] memory tempCohortIds = new uint256[](count);
        uint256[] memory tempBondAmounts = new uint256[](count);
        uint256[] memory tempMaturities = new uint256[](count);
        uint256[] memory tempDiscounts = new uint256[](count);
        bool[] memory tempMatured = new bool[](count);

        uint256 validCount = 0;
        for (uint256 i = 0; i < count; i++) {
            uint256 cohortId = activeCohortIds[i];
            uint256 balance = balanceOf(user, cohortId);
            if (balance > 0) {
                tempCohortIds[validCount] = cohortId;
                tempBondAmounts[validCount] = balance;
                tempMaturities[validCount] = cohorts[cohortId].maturityTimestamp;
                tempDiscounts[validCount] = cohorts[cohortId].averageDiscount;
                tempMatured[validCount] = cohorts[cohortId].matured;
                validCount++;
            }
        }

        // Resize arrays to actual count
        cohortIds = new uint256[](validCount);
        bondAmounts = new uint256[](validCount);
        maturities = new uint256[](validCount);
        discounts = new uint256[](validCount);
        matured = new bool[](validCount);

        for (uint256 i = 0; i < validCount; i++) {
            cohortIds[i] = tempCohortIds[i];
            bondAmounts[i] = tempBondAmounts[i];
            maturities[i] = tempMaturities[i];
            discounts[i] = tempDiscounts[i];
            matured[i] = tempMatured[i];
        }
    }

    /**
     * @dev Get cohort information
     */
    function getCohortInfo(uint256 cohortId) external view returns (
        uint256 maturityTimestamp,
        uint256 totalSBCOwed,
        uint256 totalUSDCRaised,
        uint256 averageDiscount,
        uint256 averageVestingDays,
        bool matured
    ) {
        require(cohortExists[cohortId], "Cohort does not exist");
        Cohort storage cohort = cohorts[cohortId];

        return (
            cohort.maturityTimestamp,
            cohort.totalSBCOwed,
            cohort.totalUSDCRaised,
            cohort.averageDiscount,
            cohort.averageVestingDays,
            cohort.matured
        );
    }

    /**
     * @dev Preview bond purchase calculation
     */
    function previewBondPurchase(
        uint256 usdcAmount,
        uint256 vestingDays
    ) external view returns (
        uint256 sbcAmount,
        uint256 discount,
        uint256 cohortId,
        uint256 maturityTimestamp
    ) {
        require(vestingDays >= MIN_VESTING && vestingDays <= MAX_VESTING, "Invalid vesting period");

        discount = yieldCurve.getDiscount(vestingDays);
        uint256 currentSMA = smaOracle.get1093DaySMA();
        uint256 discountedPrice = (currentSMA * (10000 - discount)) / 10000;
        sbcAmount = (usdcAmount * 1e18) / discountedPrice;

        maturityTimestamp = block.timestamp + vestingDays;
        cohortId = getCohortId(maturityTimestamp);
        maturityTimestamp = roundToMonthStart(maturityTimestamp);
    }

    /**
     * @dev Get protocol statistics
     */
    function getProtocolStats() external view returns (
        uint256 totalSBCIssued_,
        uint256 totalUSDCRaised_,
        uint256 activeCohorts,
        uint256 currentSMA,
        bool treasurySolvent
    ) {
        totalSBCIssued_ = totalSBCIssued;
        totalUSDCRaised_ = totalUSDCRaised;
        activeCohorts = activeCohortIds.length;
        currentSMA = smaOracle.get1093DaySMA();
        (treasurySolvent,) = treasury.checkSolvency();
    }

    // Admin functions

    /**
     * @dev Update protocol contracts
     */
    function updateProtocolContracts(
        address newOracle,
        address newYieldCurve,
        address newTreasury
    ) external onlyRole(ADMIN_ROLE) {
        if (newOracle != address(0)) {
            smaOracle = ISMAOracle(newOracle);
        }
        if (newYieldCurve != address(0)) {
            yieldCurve = IYieldCurve(newYieldCurve);
        }
        if (newTreasury != address(0)) {
            treasury = ITreasuryManager(newTreasury);
        }

        emit ProtocolParametersUpdated(newOracle, newYieldCurve, newTreasury);
    }

    /**
     * @dev Emergency pause mechanism
     */
    function setProtocolActive(bool active) external onlyRole(ADMIN_ROLE) {
        protocolActive = active;
        emit EmergencyPause(!active);
    }

    /**
     * @dev Update URI for metadata
     */
    function setURI(string memory newURI) external onlyRole(ADMIN_ROLE) {
        _setURI(newURI);
    }

    // View functions for bond trading/secondary markets

    /**
     * @dev Calculate current bond value based on time to maturity
     */
    function getCurrentBondValue(uint256 cohortId) external view returns (uint256) {
        require(cohortExists[cohortId], "Cohort does not exist");

        Cohort storage cohort = cohorts[cohortId];
        if (cohort.matured || block.timestamp >= cohort.maturityTimestamp) {
            return smaOracle.get1093DaySMA(); // Full value at maturity
        }

        uint256 timeToMaturity = cohort.maturityTimestamp - block.timestamp;
        uint256 remainingDays = timeToMaturity / 1 days;

        // Calculate present value based on remaining time
        uint256 currentDiscount = yieldCurve.getDiscount(remainingDays);
        uint256 currentSMA = smaOracle.get1093DaySMA();

        return (currentSMA * (10000 - currentDiscount)) / 10000;
    }

    /**
     * @dev Get all active cohort IDs
     */
    function getActiveCohortIds() external view returns (uint256[] memory) {
        return activeCohortIds;
    }
}
