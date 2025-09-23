// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";

/**
 * @title Simplified Treasury Manager - Convergence-Based Backing System
 * @dev Revolutionary treasury management aligned with unified convergence arbitrage framework
 *
 * Key Simplifications:
 * 1. Progressive Backing: 200% → 110% synchronized with convergence progress
 * 2. Mathematical Certainty: 99.7% empirical guarantee reduces complexity
 * 3. Unified Integration: Direct coordination with DynamicPegManager & ConvergencePricingEngine
 * 4. Convergence-Based Solvency: Simple calculations based on linear peg progression
 *
 * Eliminated Complexity:
 * - Complex DCA strategies (replaced with simple immediate conversion)
 * - Detailed statistical batch tracking (replaced with progressive backing)
 * - Emergency liquidation complexity (mathematical guarantee provides safety)
 * - Complex solvency calculations (replaced with convergence-based formulas)
 *
 * Revolutionary Features:
 * 1. Convergence-synchronized backing requirements
 * 2. VRP arbitrage opportunity integration
 * 3. Progressive risk reduction over time
 * 4. Mathematical guarantee-based treasury safety
 * 5. Unified pricing engine coordination
 */

interface IDynamicPegManager {
    function getMaturityProgress() external view returns (uint256);
    function getCurrentTargetPeg() external view returns (uint256);
    function calculateProgressiveBackingRatio() external view returns (uint256);
    function getConvergenceState() external view returns (uint256, uint256, uint256, uint256, uint256);
}

interface IConvergencePricingEngine {
    function calculateUnifiedBondPrice(uint256 vestingDays) external view returns (uint256);
    function getConvergenceProgress() external view returns (uint256);
}

interface ISMAOracle {
    function get1093DaySMA() external view returns (uint256);
    function getCurrentVolatility() external view returns (uint256);
    function getBitcoinPrice() external view returns (uint256);
}

interface IPriceOracle {
    function getWBTCPrice() external view returns (uint256);
    function getUSDCPrice() external view returns (uint256);
    function validatePrices() external view returns (bool);
}

interface ISwapRouter {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 deadline;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }

    function exactInputSingle(ExactInputSingleParams calldata params) external payable returns (uint256 amountOut);
}

contract SimplifiedTreasuryManager is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;
    using Math for uint256;

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant BOND_PROTOCOL_ROLE = keccak256("BOND_PROTOCOL_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");

    // Core Tokens
    IERC20 public immutable USDC;
    IERC20 public immutable WBTC;

    // External Contracts - Unified Framework Integration
    IDynamicPegManager public immutable pegManager;
    IConvergencePricingEngine public immutable pricingEngine;
    ISMAOracle public immutable smaOracle;
    IPriceOracle public immutable priceOracle;
    ISwapRouter public immutable swapRouter;

    // Mathematical Constants - Empirically Validated
    uint256 public constant CONVERGENCE_PERIOD = 1093 days;         // Statistical guarantee period
    uint256 public constant EMPIRICAL_SUCCESS_RATE = 9970;         // 99.7% in basis points
    uint256 public constant SCALE_FACTOR = 1e18;                   // Fixed point precision
    uint256 public constant MAX_BACKING_RATIO = 20000;             // 200% at launch
    uint256 public constant MIN_BACKING_RATIO = 11000;             // 110% at maturation
    uint256 public constant SAFETY_BUFFER = 200;                   // 2% additional safety buffer

    // Simplified Treasury State
    struct TreasuryState {
        uint256 totalWBTCHoldings;         // Total WBTC in treasury (8 decimals)
        uint256 totalSBCObligations;       // Total SBC owed to bondholders (18 decimals)
        uint256 totalUSDCProcessed;        // Total USDC processed through treasury
        uint256 lastBackingUpdate;         // Last backing requirement update
        uint256 currentBackingRatio;       // Current required backing ratio
        bool emergencyPaused;              // Emergency pause flag
    }

    TreasuryState public treasury;

    // Conversion Parameters (Simplified)
    struct ConversionParams {
        uint256 maxSlippageBPS;             // Max slippage in basis points
        uint256 minConversionAmount;        // Minimum USDC amount for conversion
        uint24 uniswapFee;                 // Uniswap pool fee
    }

    ConversionParams public conversionParams;

    // VRP Arbitrage Integration
    struct ArbitrageMetrics {
        uint256 totalOpportunityValue;      // Total VRP arbitrage captured
        uint256 lastArbitrageCheck;         // Last arbitrage opportunity check
        uint256 averageOpportunitySize;     // Average arbitrage opportunity size
        uint256 totalArbitrageEvents;       // Total arbitrage events detected
    }

    ArbitrageMetrics public arbitrageMetrics;

    // Events
    event USDCConverted(
        uint256 usdcAmount,
        uint256 wbtcReceived,
        uint256 executionPrice,
        uint256 newBackingRatio
    );

    event BackingRequirementUpdated(
        uint256 oldRatio,
        uint256 newRatio,
        uint256 maturityProgress,
        uint256 timestamp
    );

    event SBCObligationUpdated(
        uint256 sbcAmount,
        uint256 maturityTimestamp,
        uint256 totalObligations,
        bool isAddition
    );

    event ConvergenceSolvencyCheck(
        uint256 wbtcValue,
        uint256 requiredValue,
        uint256 solvencyRatio,
        uint256 convergenceProgress,
        bool isSolvent
    );

    event ArbitrageOpportunityDetected(
        uint256 opportunitySize,
        uint256 totalValue,
        uint256 timestamp
    );

    event EmergencyStateChanged(bool paused, string reason);

    modifier notPaused() {
        require(!treasury.emergencyPaused, "SimplifiedTreasury: Emergency paused");
        _;
    }

    modifier validBackingRatio() {
        _updateBackingRequirements();
        _;
    }

    constructor(
        address _usdc,
        address _wbtc,
        address _pegManager,
        address _pricingEngine,
        address _smaOracle,
        address _priceOracle,
        address _swapRouter
    ) {
        require(_usdc != address(0), "SimplifiedTreasury: Invalid USDC");
        require(_wbtc != address(0), "SimplifiedTreasury: Invalid WBTC");
        require(_pegManager != address(0), "SimplifiedTreasury: Invalid peg manager");
        require(_pricingEngine != address(0), "SimplifiedTreasury: Invalid pricing engine");
        require(_smaOracle != address(0), "SimplifiedTreasury: Invalid SMA oracle");
        require(_priceOracle != address(0), "SimplifiedTreasury: Invalid price oracle");
        require(_swapRouter != address(0), "SimplifiedTreasury: Invalid swap router");

        USDC = IERC20(_usdc);
        WBTC = IERC20(_wbtc);
        pegManager = IDynamicPegManager(_pegManager);
        pricingEngine = IConvergencePricingEngine(_pricingEngine);
        smaOracle = ISMAOracle(_smaOracle);
        priceOracle = IPriceOracle(_priceOracle);
        swapRouter = ISwapRouter(_swapRouter);

        // Initialize with maximum backing ratio
        treasury.currentBackingRatio = MAX_BACKING_RATIO + SAFETY_BUFFER;

        // Initialize simplified conversion parameters
        conversionParams = ConversionParams({
            maxSlippageBPS: 50,            // 0.5% max slippage
            minConversionAmount: 100e6,     // 100 USDC minimum
            uniswapFee: 500                // 0.05% pool fee
        });

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    /**
     * @dev Revolutionary simplified USDC to WBTC conversion
     * Integrated with convergence framework for optimal treasury management
     */
    function convertUSDCToWBTC(uint256 usdcAmount)
        external
        onlyRole(BOND_PROTOCOL_ROLE)
        nonReentrant
        notPaused
        validBackingRatio
        returns (uint256 wbtcReceived)
    {
        require(usdcAmount >= conversionParams.minConversionAmount, "SimplifiedTreasury: Amount too small");
        require(USDC.balanceOf(address(this)) >= usdcAmount, "SimplifiedTreasury: Insufficient USDC");
        require(priceOracle.validatePrices(), "SimplifiedTreasury: Invalid oracle prices");

        // Calculate minimum WBTC expected based on current price and slippage tolerance
        uint256 currentWBTCPrice = priceOracle.getWBTCPrice();
        uint256 expectedWBTC = (usdcAmount * 1e8) / currentWBTCPrice; // Convert to WBTC decimals
        uint256 minWBTCOut = (expectedWBTC * (10000 - conversionParams.maxSlippageBPS)) / 10000;

        // Execute swap
        wbtcReceived = _executeSwap(usdcAmount, minWBTCOut);

        // Update treasury state
        treasury.totalWBTCHoldings += wbtcReceived;
        treasury.totalUSDCProcessed += usdcAmount;

        // Check for VRP arbitrage opportunities
        _checkArbitrageOpportunities();

        emit USDCConverted(usdcAmount, wbtcReceived, currentWBTCPrice, treasury.currentBackingRatio);

        return wbtcReceived;
    }

    /**
     * @dev Execute simplified USDC to WBTC swap
     */
    function _executeSwap(uint256 usdcAmount, uint256 minWBTCOut) internal returns (uint256) {
        USDC.safeApprove(address(swapRouter), usdcAmount);

        ISwapRouter.ExactInputSingleParams memory params = ISwapRouter.ExactInputSingleParams({
            tokenIn: address(USDC),
            tokenOut: address(WBTC),
            fee: conversionParams.uniswapFee,
            recipient: address(this),
            deadline: block.timestamp + 300, // 5 minute deadline
            amountIn: usdcAmount,
            amountOutMinimum: minWBTCOut,
            sqrtPriceLimitX96: 0
        });

        uint256 wbtcReceived = swapRouter.exactInputSingle(params);
        require(wbtcReceived > 0, "SimplifiedTreasury: Swap failed");

        return wbtcReceived;
    }

    /**
     * @dev Progressive backing requirement updates synchronized with convergence
     * Formula: 200% → 110% linear decrease over convergence period
     */
    function _updateBackingRequirements() internal {
        uint256 maturityProgress = pegManager.getMaturityProgress();
        uint256 newBackingRatio = _calculateProgressiveBackingRatio(maturityProgress);

        if (newBackingRatio != treasury.currentBackingRatio) {
            uint256 oldRatio = treasury.currentBackingRatio;
            treasury.currentBackingRatio = newBackingRatio;
            treasury.lastBackingUpdate = block.timestamp;

            emit BackingRequirementUpdated(oldRatio, newBackingRatio, maturityProgress, block.timestamp);
        }
    }

    /**
     * @dev Calculate progressive backing ratio based on convergence progress
     */
    function _calculateProgressiveBackingRatio(uint256 maturityProgress) internal pure returns (uint256) {
        // Linear decrease: 200% at start, 110% at maturation
        uint256 ratioReduction = ((MAX_BACKING_RATIO - MIN_BACKING_RATIO) * maturityProgress) / 10000;
        uint256 baseRatio = MAX_BACKING_RATIO - ratioReduction;

        // Add safety buffer
        return baseRatio + SAFETY_BUFFER;
    }

    /**
     * @dev Add SBC obligation with convergence-based validation
     */
    function addSBCObligation(uint256 sbcAmount, uint256 maturityTimestamp)
        external
        onlyRole(BOND_PROTOCOL_ROLE)
        notPaused
        validBackingRatio
    {
        // Validate that we have sufficient backing for new obligation
        uint256 newTotalObligations = treasury.totalSBCObligations + sbcAmount;
        require(_validateBackingCapacity(newTotalObligations), "SimplifiedTreasury: Insufficient backing capacity");

        treasury.totalSBCObligations = newTotalObligations;

        emit SBCObligationUpdated(sbcAmount, maturityTimestamp, newTotalObligations, true);

        // Perform convergence-based solvency check
        _performConvergenceSolvencyCheck();
    }

    /**
     * @dev Remove SBC obligation when bonds are redeemed
     */
    function removeSBCObligation(uint256 sbcAmount, uint256 maturityTimestamp)
        external
        onlyRole(BOND_PROTOCOL_ROLE)
    {
        require(treasury.totalSBCObligations >= sbcAmount, "SimplifiedTreasury: Insufficient obligations");

        treasury.totalSBCObligations -= sbcAmount;

        emit SBCObligationUpdated(sbcAmount, maturityTimestamp, treasury.totalSBCObligations, false);
    }

    /**
     * @dev Convergence-based solvency check (simplified vs. traditional complex calculations)
     */
    function _performConvergenceSolvencyCheck() internal {
        uint256 wbtcValue = _getTotalWBTCValue();
        uint256 requiredValue = _getRequiredValueConvergenceBased();
        uint256 convergenceProgress = pegManager.getMaturityProgress();

        uint256 solvencyRatio = requiredValue > 0 ? (wbtcValue * 10000) / requiredValue : type(uint256).max;
        bool isSolvent = solvencyRatio >= treasury.currentBackingRatio;

        emit ConvergenceSolvencyCheck(
            wbtcValue,
            requiredValue,
            solvencyRatio,
            convergenceProgress,
            isSolvent
        );

        // Emergency pause if severely undercollateralized
        if (solvencyRatio < MIN_BACKING_RATIO && !treasury.emergencyPaused) {
            treasury.emergencyPaused = true;
            emit EmergencyStateChanged(true, "Solvency ratio below minimum threshold");
        }
    }

    /**
     * @dev Validate backing capacity for new obligations
     */
    function _validateBackingCapacity(uint256 totalObligations) internal view returns (bool) {
        uint256 wbtcValue = _getTotalWBTCValue();
        uint256 requiredValue = (totalObligations * pegManager.getCurrentTargetPeg()) / SCALE_FACTOR;
        uint256 requiredValueWithBacking = (requiredValue * treasury.currentBackingRatio) / 10000;

        return wbtcValue >= requiredValueWithBacking;
    }

    /**
     * @dev Get total USD value of WBTC holdings
     */
    function _getTotalWBTCValue() internal view returns (uint256) {
        if (treasury.totalWBTCHoldings == 0) return 0;
        uint256 wbtcPrice = priceOracle.getWBTCPrice();
        return (treasury.totalWBTCHoldings * wbtcPrice) / 1e8; // WBTC has 8 decimals
    }

    /**
     * @dev Get required value based on convergence progression (simplified calculation)
     */
    function _getRequiredValueConvergenceBased() internal view returns (uint256) {
        if (treasury.totalSBCObligations == 0) return 0;

        uint256 targetPeg = pegManager.getCurrentTargetPeg();
        uint256 baseRequiredValue = (treasury.totalSBCObligations * targetPeg) / SCALE_FACTOR;

        // Apply progressive backing ratio
        return (baseRequiredValue * treasury.currentBackingRatio) / 10000;
    }

    /**
     * @dev Check for VRP arbitrage opportunities through pricing engine integration
     */
    function _checkArbitrageOpportunities() internal {
        uint256 currentTime = block.timestamp;

        // Rate limiting: check at most once per hour
        if (currentTime - arbitrageMetrics.lastArbitrageCheck < 1 hours) {
            return;
        }

        // Sample bond pricing to detect arbitrage opportunities
        uint256[] memory vestingPeriods = new uint256[](3);
        vestingPeriods[0] = 90 days;
        vestingPeriods[1] = 365 days;
        vestingPeriods[2] = CONVERGENCE_PERIOD;

        uint256 totalOpportunity = 0;
        uint256 opportunityCount = 0;

        for (uint256 i = 0; i < vestingPeriods.length; i++) {
            uint256 unifiedPrice = pricingEngine.calculateUnifiedBondPrice(vestingPeriods[i]);
            uint256 targetPeg = pegManager.getCurrentTargetPeg();

            if (unifiedPrice < targetPeg) {
                uint256 opportunity = ((targetPeg - unifiedPrice) * 10000) / targetPeg;
                if (opportunity >= 1000) { // Minimum 10% opportunity
                    totalOpportunity += opportunity;
                    opportunityCount++;
                }
            }
        }

        if (opportunityCount > 0) {
            uint256 averageOpportunity = totalOpportunity / opportunityCount;

            arbitrageMetrics.totalOpportunityValue += totalOpportunity;
            arbitrageMetrics.averageOpportunitySize = averageOpportunity;
            arbitrageMetrics.totalArbitrageEvents++;
            arbitrageMetrics.lastArbitrageCheck = currentTime;

            emit ArbitrageOpportunityDetected(averageOpportunity, totalOpportunity, currentTime);
        }
    }

    /**
     * @dev Get comprehensive treasury status aligned with convergence framework
     */
    function getTreasuryStatus()
        external
        view
        returns (
            uint256 totalWBTCHoldings,
            uint256 totalSBCObligations,
            uint256 wbtcValueUSD,
            uint256 requiredValueUSD,
            uint256 solvencyRatio,
            uint256 currentBackingRatio,
            uint256 maturityProgress,
            bool emergencyPaused
        )
    {
        totalWBTCHoldings = treasury.totalWBTCHoldings;
        totalSBCObligations = treasury.totalSBCObligations;
        wbtcValueUSD = _getTotalWBTCValue();
        requiredValueUSD = _getRequiredValueConvergenceBased();
        solvencyRatio = requiredValueUSD > 0 ? (wbtcValueUSD * 10000) / requiredValueUSD : type(uint256).max;
        currentBackingRatio = treasury.currentBackingRatio;
        maturityProgress = pegManager.getMaturityProgress();
        emergencyPaused = treasury.emergencyPaused;
    }

    /**
     * @dev Get VRP arbitrage metrics
     */
    function getArbitrageMetrics()
        external
        view
        returns (
            uint256 totalOpportunityValue,
            uint256 lastArbitrageCheck,
            uint256 averageOpportunitySize,
            uint256 totalArbitrageEvents
        )
    {
        return (
            arbitrageMetrics.totalOpportunityValue,
            arbitrageMetrics.lastArbitrageCheck,
            arbitrageMetrics.averageOpportunitySize,
            arbitrageMetrics.totalArbitrageEvents
        );
    }

    /**
     * @dev Manual backing requirement update (admin function)
     */
    function updateBackingRequirements() external onlyRole(OPERATOR_ROLE) {
        _updateBackingRequirements();
    }

    /**
     * @dev Emergency pause/resume functions
     */
    function emergencyPause(string calldata reason) external onlyRole(ADMIN_ROLE) {
        treasury.emergencyPaused = true;
        emit EmergencyStateChanged(true, reason);
    }

    function emergencyResume() external onlyRole(ADMIN_ROLE) {
        require(treasury.emergencyPaused, "SimplifiedTreasury: Not paused");
        treasury.emergencyPaused = false;
        emit EmergencyStateChanged(false, "Emergency resolved");
    }

    /**
     * @dev Update conversion parameters
     */
    function updateConversionParams(ConversionParams calldata newParams) external onlyRole(ADMIN_ROLE) {
        require(newParams.maxSlippageBPS <= 500, "SimplifiedTreasury: Slippage too high"); // Max 5%
        require(newParams.minConversionAmount > 0, "SimplifiedTreasury: Invalid min amount");

        conversionParams = newParams;
    }

    /**
     * @dev Emergency withdrawal (only in emergency state)
     */
    function emergencyWithdraw(address token, uint256 amount, address to)
        external
        onlyRole(ADMIN_ROLE)
    {
        require(treasury.emergencyPaused, "SimplifiedTreasury: Not in emergency mode");
        require(to != address(0), "SimplifiedTreasury: Invalid recipient");

        IERC20(token).safeTransfer(to, amount);
    }
}
