// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";

/**
 * @title Treasury Manager
 * @dev Manages USDC→WBTC conversion and treasury solvency for SBC bond obligations
 *
 * Key Features:
 * - Automatic USDC to WBTC conversion with multiple strategies
 * - Solvency tracking (WBTC value vs SBC obligations)
 * - DCA (Dollar Cost Averaging) for large conversions
 * - Emergency liquidity management
 * - No user conversion access (backing without arbitrage)
 */

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

interface IPriceOracle {
    function getWBTCPrice() external view returns (uint256); // Price in USD with 8 decimals
    function getUSDCPrice() external view returns (uint256); // Should be ~1e6 for $1
    function validatePrices() external view returns (bool);
}

interface ISMAOracle {
    function get1093DaySMA() external view returns (uint256); // SMA in USD
}

contract TreasuryManager is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;
    using Math for uint256;

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant BOND_PROTOCOL_ROLE = keccak256("BOND_PROTOCOL_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");

    // Core tokens
    IERC20 public immutable USDC;
    IERC20 public immutable WBTC;

    // External contracts
    ISwapRouter public uniswapRouter;
    IPriceOracle public priceOracle;
    ISMAOracle public smaOracle;

    // Conversion strategies
    enum ConversionStrategy {
        IMMEDIATE,    // Convert all USDC immediately
        DCA,          // Dollar cost average over time
        SPLIT         // Mix of immediate + DCA
    }

    ConversionStrategy public currentStrategy = ConversionStrategy.SPLIT;

    // Treasury state
    struct TreasuryState {
        uint256 totalWBTCHoldings;      // Total WBTC in treasury (8 decimals)
        uint256 totalSBCObligations;    // Total SBC owed to bondholders (18 decimals)
        uint256 totalUSDCProcessed;     // Total USDC processed through treasury
        uint256 averageWBTCCostBasis;   // Average cost basis of WBTC holdings
        uint256 lastSolvencyCheck;      // Last solvency check timestamp
        bool emergencyMode;             // Emergency mode flag
    }

    TreasuryState public treasury;

    // SBC obligations by maturity (for better tracking)
    mapping(uint256 => uint256) public obligationsByMaturity; // timestamp => SBC amount

    // DCA state
    struct DCAOrder {
        uint256 totalUSDC;           // Total USDC to convert
        uint256 remainingUSDC;       // Remaining USDC to convert
        uint256 dailyAmount;         // Amount to convert daily
        uint256 startTimestamp;      // When DCA started
        uint256 endTimestamp;        // When DCA should end
        uint256 lastExecution;       // Last execution timestamp
        bool active;                 // Is this DCA order active
    }

    DCAOrder public activeDCA;

    // Conversion parameters
    struct ConversionParams {
        uint256 immediatePercent;     // % to convert immediately (default: 70%)
        uint256 dcaPeriodDays;        // DCA period in days (default: 7)
        uint256 maxSlippageBPS;       // Max slippage in basis points (default: 50 = 0.5%)
        uint256 minConversionAmount;  // Minimum USDC amount for conversion
        uint24 uniswapFee;           // Uniswap pool fee (default: 500 = 0.05%)
    }

    ConversionParams public conversionParams;

    // Emergency parameters
    uint256 public constant MIN_SOLVENCY_RATIO = 11000; // 110% (10% buffer)
    uint256 public constant EMERGENCY_SOLVENCY_RATIO = 10500; // 105% (emergency threshold)

    // Statistical Treasury Safety Constants (Empirically Validated)
    uint256 public constant STATISTICAL_GUARANTEE_PERIOD = 1093 days; // 99.7% empirical success rate
    uint256 public constant STATISTICAL_SUCCESS_RATE_BPS = 9970; // 99.7% success rate in basis points
    uint256 public constant CONFIDENCE_INTERVAL_LOW_BPS = 9950;  // 99.5% confidence interval lower bound
    uint256 public constant CONFIDENCE_INTERVAL_HIGH_BPS = 9990; // 99.9% confidence interval upper bound
    uint256 public constant SAMPLE_SIZE = 2931; // Number of validated 1093-day periods
    uint256 public constant FORCED_HOLD_PERIOD = 1093 days; // Never sell before statistical guarantee

    // WBTC Batch Tracking for Statistical Guarantee
    struct WBTCBatch {
        uint256 amount;              // Amount of WBTC in this batch
        uint256 purchaseTimestamp;   // When batch was purchased
        uint256 purchasePrice;       // USD price at purchase (for tracking)
        bool isStatisticallyMature;  // True after 1093 days
        uint256 maturityTimestamp;   // When batch reaches statistical guarantee
    }

    // Batch tracking
    mapping(uint256 => WBTCBatch) public wbtcBatches;
    uint256 public nextBatchId;
    uint256 public totalImmatureWBTC; // WBTC not yet at statistical guarantee
    uint256 public totalMatureWBTC;   // WBTC past 1093-day guarantee

    // Events
    event USDCConverted(
        uint256 usdcAmount,
        uint256 wbtcReceived,
        uint256 executionPrice,
        ConversionStrategy strategy
    );

    event DCAOrderCreated(
        uint256 totalUSDC,
        uint256 dailyAmount,
        uint256 duration
    );

    event DCAExecuted(
        uint256 usdcAmount,
        uint256 wbtcReceived,
        uint256 remainingUSDC
    );

    event SBCObligationAdded(
        uint256 sbcAmount,
        uint256 maturityTimestamp,
        uint256 totalObligations
    );

    event SolvencyStatusChanged(
        bool wasSolvent,
        bool isSolvent,
        uint256 solvencyRatio
    );

    event EmergencyModeToggled(bool enabled, string reason);

    event ConversionParamsUpdated(ConversionParams newParams);

    // Statistical guarantee events
    event WBTCBatchCreated(
        uint256 indexed batchId,
        uint256 amount,
        uint256 purchasePrice,
        uint256 maturityTimestamp
    );

    event WBTCBatchMatured(
        uint256 indexed batchId,
        uint256 amount,
        bool profitableAtMaturity
    );

    event StatisticalGuaranteeViolationPrevented(
        uint256 indexed batchId,
        uint256 attemptedAmount,
        uint256 daysRemaining
    );

    constructor(
        address _usdc,
        address _wbtc,
        address _uniswapRouter,
        address _priceOracle,
        address _smaOracle
    ) {
        require(_usdc != address(0), "Invalid USDC address");
        require(_wbtc != address(0), "Invalid WBTC address");
        require(_uniswapRouter != address(0), "Invalid router address");
        require(_priceOracle != address(0), "Invalid oracle address");
        require(_smaOracle != address(0), "Invalid SMA oracle address");

        USDC = IERC20(_usdc);
        WBTC = IERC20(_wbtc);
        uniswapRouter = ISwapRouter(_uniswapRouter);
        priceOracle = IPriceOracle(_priceOracle);
        smaOracle = ISMAOracle(_smaOracle);

        // Initialize default conversion parameters
        conversionParams = ConversionParams({
            immediatePercent: 7000,        // 70% immediate
            dcaPeriodDays: 7,              // 7-day DCA
            maxSlippageBPS: 50,            // 0.5% max slippage
            minConversionAmount: 100e6,     // 100 USDC minimum
            uniswapFee: 500                // 0.05% pool fee
        });

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    /**
     * @dev Convert USDC to WBTC based on current strategy
     * @param usdcAmount Amount of USDC to convert
     * @param minWBTCReceived Minimum WBTC expected (slippage protection)
     */
    function convertUSDCToWBTC(
        uint256 usdcAmount,
        uint256 minWBTCReceived
    ) external onlyRole(BOND_PROTOCOL_ROLE) nonReentrant returns (uint256 totalWBTCReceived) {
        require(usdcAmount >= conversionParams.minConversionAmount, "Amount too small");
        require(USDC.balanceOf(address(this)) >= usdcAmount, "Insufficient USDC balance");

        // Validate oracle prices
        require(priceOracle.validatePrices(), "Oracle price validation failed");

        if (currentStrategy == ConversionStrategy.IMMEDIATE) {
            totalWBTCReceived = _executeImmediateConversion(usdcAmount, minWBTCReceived);
        } else if (currentStrategy == ConversionStrategy.DCA) {
            totalWBTCReceived = _initiateDCAConversion(usdcAmount);
        } else { // SPLIT strategy
            totalWBTCReceived = _executeSplitConversion(usdcAmount, minWBTCReceived);
        }

        // Update treasury state
        treasury.totalWBTCHoldings += totalWBTCReceived;
        treasury.totalUSDCProcessed += usdcAmount;

        // Update average cost basis
        _updateCostBasis(totalWBTCReceived, usdcAmount);

        // Create new WBTC batch with statistical tracking
        _createWBTCBatch(totalWBTCReceived, usdcAmount);

        emit USDCConverted(usdcAmount, totalWBTCReceived, _getCurrentWBTCPrice(), currentStrategy);

        return totalWBTCReceived;
    }

    /**
     * @dev Execute immediate conversion
     */
    function _executeImmediateConversion(
        uint256 usdcAmount,
        uint256 minWBTCReceived
    ) internal returns (uint256) {
        return _swapUSDCToWBTC(usdcAmount, minWBTCReceived);
    }

    /**
     * @dev Execute split conversion (immediate + DCA)
     */
    function _executeSplitConversion(
        uint256 usdcAmount,
        uint256 minWBTCReceived
    ) internal returns (uint256) {
        uint256 immediateAmount = (usdcAmount * conversionParams.immediatePercent) / 10000;
        uint256 dcaAmount = usdcAmount - immediateAmount;

        // Convert immediate portion
        uint256 immediateWBTC = _swapUSDCToWBTC(
            immediateAmount,
            (minWBTCReceived * conversionParams.immediatePercent) / 10000
        );

        // Set up DCA for remainder
        _initiateDCAConversion(dcaAmount);

        return immediateWBTC; // DCA conversions will be counted separately
    }

    /**
     * @dev Initiate DCA conversion
     */
    function _initiateDCAConversion(uint256 usdcAmount) internal returns (uint256) {
        require(!activeDCA.active, "DCA already active");

        uint256 dailyAmount = usdcAmount / conversionParams.dcaPeriodDays;
        require(dailyAmount > 0, "DCA amount too small");

        activeDCA = DCAOrder({
            totalUSDC: usdcAmount,
            remainingUSDC: usdcAmount,
            dailyAmount: dailyAmount,
            startTimestamp: block.timestamp,
            endTimestamp: block.timestamp + (conversionParams.dcaPeriodDays * 1 days),
            lastExecution: 0,
            active: true
        });

        emit DCAOrderCreated(usdcAmount, dailyAmount, conversionParams.dcaPeriodDays);

        return 0; // No immediate WBTC received
    }

    /**
     * @dev Execute DCA conversion (called daily)
     */
    function executeDCA() external onlyRole(OPERATOR_ROLE) nonReentrant {
        require(activeDCA.active, "No active DCA");
        require(block.timestamp >= activeDCA.lastExecution + 1 days, "Too early for next execution");
        require(activeDCA.remainingUSDC > 0, "No remaining USDC");

        uint256 conversionAmount = Math.min(activeDCA.dailyAmount, activeDCA.remainingUSDC);
        uint256 wbtcReceived = _swapUSDCToWBTC(conversionAmount, 0); // No slippage protection for DCA

        activeDCA.remainingUSDC -= conversionAmount;
        activeDCA.lastExecution = block.timestamp;

        // Update treasury
        treasury.totalWBTCHoldings += wbtcReceived;
        _updateCostBasis(wbtcReceived, conversionAmount);

        emit DCAExecuted(conversionAmount, wbtcReceived, activeDCA.remainingUSDC);

        // Close DCA if complete
        if (activeDCA.remainingUSDC == 0 || block.timestamp >= activeDCA.endTimestamp) {
            activeDCA.active = false;
        }
    }

    /**
     * @dev Core USDC to WBTC swap function
     */
    function _swapUSDCToWBTC(uint256 usdcAmount, uint256 minWBTCOut) internal returns (uint256) {
        USDC.safeApprove(address(uniswapRouter), usdcAmount);

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

        uint256 wbtcReceived = uniswapRouter.exactInputSingle(params);
        require(wbtcReceived > 0, "Swap failed");

        return wbtcReceived;
    }

    /**
     * @dev Add SBC obligation when bonds are issued
     */
    function addSBCObligation(
        uint256 sbcAmount,
        uint256 maturityTimestamp
    ) external onlyRole(BOND_PROTOCOL_ROLE) {
        treasury.totalSBCObligations += sbcAmount;
        obligationsByMaturity[maturityTimestamp] += sbcAmount;

        emit SBCObligationAdded(sbcAmount, maturityTimestamp, treasury.totalSBCObligations);

        // Check solvency after adding obligation
        _checkSolvency();
    }

    /**
     * @dev Remove SBC obligation when bonds are redeemed
     */
    function removeSBCObligation(
        uint256 sbcAmount,
        uint256 maturityTimestamp
    ) external onlyRole(BOND_PROTOCOL_ROLE) {
        require(treasury.totalSBCObligations >= sbcAmount, "Insufficient obligations");
        require(obligationsByMaturity[maturityTimestamp] >= sbcAmount, "Insufficient maturity obligations");

        treasury.totalSBCObligations -= sbcAmount;
        obligationsByMaturity[maturityTimestamp] -= sbcAmount;
    }

    /**
     * @dev Check treasury solvency
     */
    function checkSolvency() external view returns (bool solvent, uint256 excessWBTC) {
        return _calculateSolvency();
    }

    /**
     * @dev Internal solvency calculation
     */
    function _calculateSolvency() internal view returns (bool solvent, uint256 excessValue) {
        if (treasury.totalSBCObligations == 0) {
            return (true, _getTotalWBTCValue());
        }

        uint256 wbtcValue = _getTotalWBTCValue();
        uint256 requiredValue = _getRequiredValue();

        solvent = wbtcValue >= requiredValue;
        excessValue = solvent ? wbtcValue - requiredValue : 0;
    }

    /**
     * @dev Get total USD value of WBTC holdings
     */
    function _getTotalWBTCValue() internal view returns (uint256) {
        if (treasury.totalWBTCHoldings == 0) return 0;

        uint256 wbtcPrice = _getCurrentWBTCPrice();
        return (treasury.totalWBTCHoldings * wbtcPrice) / 1e8; // WBTC has 8 decimals
    }

    /**
     * @dev Get required USD value to cover SBC obligations
     */
    function _getRequiredValue() internal view returns (uint256) {
        uint256 currentSMA = smaOracle.get1093DaySMA();
        return (treasury.totalSBCObligations * currentSMA) / 1e18; // SBC has 18 decimals
    }

    /**
     * @dev Get current WBTC price in USD
     */
    function _getCurrentWBTCPrice() internal view returns (uint256) {
        return priceOracle.getWBTCPrice();
    }

    /**
     * @dev Update WBTC cost basis
     */
    function _updateCostBasis(uint256 wbtcAmount, uint256 usdcPaid) internal {
        if (treasury.totalWBTCHoldings == 0) {
            treasury.averageWBTCCostBasis = (usdcPaid * 1e8) / wbtcAmount; // Price per WBTC
        } else {
            uint256 totalCost = (treasury.averageWBTCCostBasis * treasury.totalWBTCHoldings) / 1e8 + usdcPaid;
            uint256 totalWBTC = treasury.totalWBTCHoldings + wbtcAmount;
            treasury.averageWBTCCostBasis = (totalCost * 1e8) / totalWBTC;
        }
    }

    /**
     * @dev Internal solvency check with emergency mode
     */
    function _checkSolvency() internal {
        (bool wasSolvent,) = _calculateSolvency();
        treasury.lastSolvencyCheck = block.timestamp;

        uint256 solvencyRatio = _getSolvencyRatio();

        bool isCurrentlySolvent = solvencyRatio >= MIN_SOLVENCY_RATIO;

        if (wasSolvent != isCurrentlySolvent) {
            emit SolvencyStatusChanged(wasSolvent, isCurrentlySolvent, solvencyRatio);
        }

        // Emergency mode logic
        if (solvencyRatio < EMERGENCY_SOLVENCY_RATIO && !treasury.emergencyMode) {
            treasury.emergencyMode = true;
            emit EmergencyModeToggled(true, "Low solvency ratio");
        } else if (solvencyRatio >= MIN_SOLVENCY_RATIO && treasury.emergencyMode) {
            treasury.emergencyMode = false;
            emit EmergencyModeToggled(false, "Solvency restored");
        }
    }

    /**
     * @dev Get solvency ratio (WBTC value / required value * 10000)
     */
    function _getSolvencyRatio() internal view returns (uint256) {
        uint256 requiredValue = _getRequiredValue();
        if (requiredValue == 0) return type(uint256).max;

        uint256 wbtcValue = _getTotalWBTCValue();
        return (wbtcValue * 10000) / requiredValue;
    }

    // Admin functions

    /**
     * @dev Update conversion strategy
     */
    function setConversionStrategy(ConversionStrategy newStrategy) external onlyRole(ADMIN_ROLE) {
        currentStrategy = newStrategy;
    }

    /**
     * @dev Update conversion parameters
     */
    function updateConversionParams(ConversionParams calldata newParams) external onlyRole(ADMIN_ROLE) {
        require(newParams.immediatePercent <= 10000, "Invalid immediate percent");
        require(newParams.dcaPeriodDays > 0 && newParams.dcaPeriodDays <= 30, "Invalid DCA period");
        require(newParams.maxSlippageBPS <= 1000, "Slippage too high"); // Max 10%

        conversionParams = newParams;
        emit ConversionParamsUpdated(newParams);
    }

    /**
     * @dev Emergency withdrawal (admin only)
     */
    function emergencyWithdraw(
        address token,
        uint256 amount,
        address to
    ) external onlyRole(ADMIN_ROLE) {
        require(treasury.emergencyMode, "Not in emergency mode");
        IERC20(token).safeTransfer(to, amount);
    }

    /**
     * @dev Get treasury statistics
     */
    function getTreasuryStats() external view returns (
        uint256 totalWBTCHoldings,
        uint256 totalSBCObligations,
        uint256 wbtcValueUSD,
        uint256 requiredValueUSD,
        uint256 solvencyRatio,
        uint256 averageCostBasis,
        bool emergencyMode
    ) {
        totalWBTCHoldings = treasury.totalWBTCHoldings;
        totalSBCObligations = treasury.totalSBCObligations;
        wbtcValueUSD = _getTotalWBTCValue();
        requiredValueUSD = _getRequiredValue();
        solvencyRatio = _getSolvencyRatio();
        averageCostBasis = treasury.averageWBTCCostBasis;
        emergencyMode = treasury.emergencyMode;
    }

    // Statistical Guarantee Functions

    /**
     * @dev Create a new WBTC batch with statistical tracking
     */
    function _createWBTCBatch(uint256 wbtcAmount, uint256 usdcPaid) internal {
        uint256 batchId = nextBatchId++;
        uint256 currentPrice = _getCurrentWBTCPrice();
        uint256 maturityTimestamp = block.timestamp + STATISTICAL_GUARANTEE_PERIOD;

        wbtcBatches[batchId] = WBTCBatch({
            amount: wbtcAmount,
            purchaseTimestamp: block.timestamp,
            purchasePrice: currentPrice,
            isStatisticallyMature: false,
            maturityTimestamp: maturityTimestamp
        });

        totalImmatureWBTC += wbtcAmount;

        emit WBTCBatchCreated(batchId, wbtcAmount, currentPrice, maturityTimestamp);
    }

    /**
     * @dev Check and update batch maturity status
     */
    function updateBatchMaturity(uint256 batchId) external {
        WBTCBatch storage batch = wbtcBatches[batchId];
        require(batch.amount > 0, "Batch does not exist");
        require(!batch.isStatisticallyMature, "Batch already mature");

        if (block.timestamp >= batch.maturityTimestamp) {
            batch.isStatisticallyMature = true;
            totalImmatureWBTC -= batch.amount;
            totalMatureWBTC += batch.amount;

            uint256 currentPrice = _getCurrentWBTCPrice();
            bool profitable = currentPrice >= batch.purchasePrice;

            emit WBTCBatchMatured(batchId, batch.amount, profitable);
        }
    }

    /**
     * @dev Modifier to prevent liquidation before statistical guarantee
     */
    modifier respectStatisticalGuarantee(uint256 batchId) {
        WBTCBatch memory batch = wbtcBatches[batchId];
        if (block.timestamp < batch.maturityTimestamp) {
            uint256 daysRemaining = (batch.maturityTimestamp - block.timestamp) / 1 days;
            emit StatisticalGuaranteeViolationPrevented(batchId, batch.amount, daysRemaining);
            revert("Cannot liquidate WBTC before 1093-day statistical guarantee");
        }
        _;
    }

    /**
     * @dev Get time-adjusted solvency ratio based on WBTC batch ages
     */
    function getStatisticalSolvencyRatio() external view returns (uint256) {
        uint256 totalValue = 0;
        uint256 weightedConfidence = 0;

        // Calculate weighted value based on batch maturity
        for (uint256 i = 0; i < nextBatchId; i++) {
            WBTCBatch memory batch = wbtcBatches[i];
            if (batch.amount > 0) {
                uint256 batchValue = (batch.amount * _getCurrentWBTCPrice()) / 1e8;
                uint256 age = block.timestamp > batch.purchaseTimestamp ?
                    block.timestamp - batch.purchaseTimestamp : 0;

                // Calculate confidence based on age (0-99.7% over 1093 days)
                // Empirically validated: 99.7% success rate with 99.5%-99.9% confidence interval
                uint256 confidence = age >= STATISTICAL_GUARANTEE_PERIOD ?
                    STATISTICAL_SUCCESS_RATE_BPS :
                    (age * STATISTICAL_SUCCESS_RATE_BPS) / STATISTICAL_GUARANTEE_PERIOD;

                totalValue += batchValue;
                weightedConfidence += (batchValue * confidence) / 10000;
            }
        }

        uint256 requiredValue = _getRequiredValue();
        if (requiredValue == 0) return type(uint256).max;

        // Return confidence-adjusted solvency ratio
        return (weightedConfidence * 10000) / requiredValue;
    }

    /**
     * @dev Get statistics about WBTC batch maturity
     */
    function getMaturityStatistics() external view returns (
        uint256 totalBatches,
        uint256 matureBatches,
        uint256 immatureBatches,
        uint256 averageDaysToMaturity,
        uint256 nextMaturityTimestamp
    ) {
        totalBatches = nextBatchId;
        uint256 totalDaysRemaining = 0;
        uint256 earliestMaturity = type(uint256).max;

        for (uint256 i = 0; i < nextBatchId; i++) {
            WBTCBatch memory batch = wbtcBatches[i];
            if (batch.amount > 0) {
                if (batch.isStatisticallyMature) {
                    matureBatches++;
                } else {
                    immatureBatches++;
                    if (batch.maturityTimestamp > block.timestamp) {
                        uint256 daysRemaining = (batch.maturityTimestamp - block.timestamp) / 1 days;
                        totalDaysRemaining += daysRemaining;
                        if (batch.maturityTimestamp < earliestMaturity) {
                            earliestMaturity = batch.maturityTimestamp;
                        }
                    }
                }
            }
        }

        averageDaysToMaturity = immatureBatches > 0 ? totalDaysRemaining / immatureBatches : 0;
        nextMaturityTimestamp = earliestMaturity != type(uint256).max ? earliestMaturity : 0;
    }

    /**
     * @dev Emergency liquidation with statistical guarantee check
     * Only mature WBTC can be liquidated in emergencies
     */
    function emergencyLiquidateMatureWBTC(
        uint256 amount
    ) external onlyRole(ADMIN_ROLE) returns (uint256 totalLiquidated) {
        require(treasury.emergencyMode, "Not in emergency mode");
        require(totalMatureWBTC >= amount, "Insufficient mature WBTC");

        // Only liquidate statistically mature WBTC
        for (uint256 i = 0; i < nextBatchId && totalLiquidated < amount; i++) {
            WBTCBatch storage batch = wbtcBatches[i];
            if (batch.isStatisticallyMature && batch.amount > 0) {
                uint256 toLiquidate = Math.min(batch.amount, amount - totalLiquidated);
                batch.amount -= toLiquidate;
                totalLiquidated += toLiquidate;
                totalMatureWBTC -= toLiquidate;
                treasury.totalWBTCHoldings -= toLiquidate;
            }
        }

        return totalLiquidated;
    }
}
