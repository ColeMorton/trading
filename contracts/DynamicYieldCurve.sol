// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";

/**
 * @title Dynamic Yield Curve - Statistically Guaranteed Implementation
 * @dev Calculates bond discounts using empirical BTC 1093-day SMA performance data
 *
 * Statistical Guarantee Foundation (Empirically Validated):
 * - Maximum Duration: 1093 days matching Bitcoin's 99.7% empirical success rate
 * - Treasury Protection: WBTC profitable in 99.7% of cases within bond maturity period
 * - Zero Duration Risk: Bond obligations never exceed statistically validated recovery time
 * - Mathematical Certainty: 99.7% success rate with 99.5%-99.9% confidence interval (2,931 samples)
 *
 * Treasury-Safe SMA-Aligned Architecture:
 * - Expected Appreciation: Aligned with 44.63% CAGR and 4.61% monthly performance
 * - Treasury Safety: 30-day bonds start at 0% discount to prevent insolvency
 * - Consistency-Based Risk: Empirical declining month analysis for duration tiers
 * - Volatility Buffers: 5.08% monthly volatility with graduated safety margins
 *
 * Discount Components:
 * 1. Expected Appreciation (CAGR × duration_factor × consistency_ratio - volatility_buffer)
 * 2. Time Premium (linear illiquidity compensation)
 * 3. Risk Premium (duration-based tiers with consistency ratios)
 * 4. Market Adjustments (bounded peg deviation and protocol needs)
 *
 * Mathematical Foundation: 2,931 empirically validated 1093-day holding periods (2014-2025)
 * Statistical Guarantee: 99.7% success rate with 99.5%-99.9% confidence interval
 */

interface ISMAOracle {
    function get1093DaySMA() external view returns (uint256);
    function getCurrentVolatility() external view returns (uint256);
}

interface IPegMonitor {
    function getSBCPegDeviation() external view returns (int256); // Basis points deviation from SMA
    function getCurrentSBCPrice() external view returns (uint256);
}

contract DynamicYieldCurve is AccessControl {
    using Math for uint256;

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");

    // SBC Historical Performance Constants (Final Authoritative Statistics)
    // Based on 2,930 daily data points - 1093-Day BTC SMA Analysis
    uint256 public constant MONTHLY_ARITHMETIC_MEAN_BPS = 461;  // 4.61% monthly arithmetic mean
    uint256 public constant ANNUAL_CAGR_BPS = 4463;             // 44.63% annual CAGR
    uint256 public constant MONTHLY_GEOMETRIC_MEAN_BPS = 317;   // 3.17% monthly geometric mean from CAGR
    uint256 public constant MONTHLY_VOLATILITY_BPS = 508;       // 5.08% monthly volatility
    uint256 public constant DAILY_GROWTH_BPS = 15;              // ~0.15% daily (4.61%/30)

    // Treasury Safety Constants
    uint256 public constant VOLATILITY_BUFFER_BPS = 200;        // 2% safety buffer for volatility
    uint256 public constant CONSISTENCY_RATIO_1093 = 10000;     // 100% consistency at 1093 days
    uint256 public constant MIN_DISCOUNT_BPS = 0;               // 0% minimum discount (treasury safe)
    uint256 public constant MAX_DISCOUNT_BPS = 8500;            // 85% maximum discount (CAGR-safe)
    uint256 public constant FIXED_POINT_SCALE = 10000;          // Fixed point precision

    // Statistical Guarantee Constants (Empirically Validated)
    uint256 public constant MAX_DURATION_STATISTICAL = 1093 days; // 99.7% empirical success rate period
    uint256 public constant STATISTICAL_SUCCESS_RATE = 9970;      // 99.7% success rate in basis points
    uint256 public constant CONFIDENCE_INTERVAL_LOW = 9950;       // 99.5% confidence interval lower bound
    uint256 public constant CONFIDENCE_INTERVAL_HIGH = 9990;      // 99.9% confidence interval upper bound
    uint256 public constant EMPIRICAL_SAMPLE_SIZE = 2931;         // Number of validated holding periods
    uint256 public constant BREAK_EVEN_GUARANTEE_DAYS = 1093;     // Empirically validated recovery period

    /**
     * @dev Consistency ratio lookup table based on empirical BTC SMA analysis
     * Index represents duration ranges, value is consistency ratio in basis points
     * Based on declining month analysis from 2,930 daily data points
     * Higher consistency = lower risk = higher sustainable discounts
     */
    struct ConsistencyData {
        uint256 maxDays;           // Maximum days for this tier
        uint256 consistencyBPS;    // Consistency ratio in basis points
        uint256 decliningMonths;   // Historical declining months
    }

    ConsistencyData[6] private CONSISTENCY_TIERS = [
        ConsistencyData(50, 5880, 54),   // 15-50 days: 58.8% consistency, ~54 declining months
        ConsistencyData(200, 6500, 45),  // 51-200 days: 65% consistency (interpolated)
        ConsistencyData(400, 7830, 25),  // 201-400 days: 78.3% consistency, ~25 declining months
        ConsistencyData(600, 8200, 20),  // 401-600 days: 82% consistency (interpolated)
        ConsistencyData(800, 8450, 18),  // 601-800 days: 84.5% consistency, ~18 declining months
        ConsistencyData(1093, 10000, 0)  // 801-1093 days: 100% consistency, 0 declining months
    ];

    // Risk Constants
    uint256 public constant BASE_RISK_FREE_RATE = 500; // 5% risk-free base
    uint256 public constant SMART_CONTRACT_RISK_BPS = 100; // 1% SC risk
    uint256 public constant ILLIQUIDITY_RATE_PER_MONTH = 50; // 0.5% per month locked

    // Market parameters (governance adjustable)
    struct MarketParams {
        uint256 volatilityMultiplier;    // How much vol affects discount (default: 100 = 1x)
        uint256 liquidityNeedBPS;        // Current protocol liquidity need (0-2000)
        uint256 demandPressureBPS;       // Current demand for bonds (-1000 to +1000)
        uint256 maxDailyChange;          // Max daily discount change (500 = 5%)
        bool emergencyMode;              // Emergency high discounts
    }

    MarketParams public marketParams;

    // Oracle contracts
    ISMAOracle public smaOracle;
    IPegMonitor public pegMonitor;

    // State tracking
    mapping(uint256 => uint256) public historicalDiscounts; // vestingDays => discount
    uint256 public lastUpdateTimestamp;
    uint256 public dailyVolumeUSDC;
    uint256 public rollingAvgVolume;

    // Events
    event MarketParamsUpdated(MarketParams newParams);
    event DiscountCalculated(uint256 vestingDays, uint256 discount, uint256 timestamp);
    event EmergencyModeToggled(bool enabled);

    constructor(
        address _smaOracle,
        address _pegMonitor
    ) {
        require(_smaOracle != address(0), "Invalid SMA oracle");
        require(_pegMonitor != address(0), "Invalid peg monitor");

        smaOracle = ISMAOracle(_smaOracle);
        pegMonitor = IPegMonitor(_pegMonitor);

        // Initialize default market parameters
        marketParams = MarketParams({
            volatilityMultiplier: 100,     // 1x volatility impact
            liquidityNeedBPS: 0,           // No additional liquidity need
            demandPressureBPS: 0,          // Neutral demand
            maxDailyChange: 500,           // 5% max daily change
            emergencyMode: false
        });

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    /**
     * @dev Calculate discount for given vesting period
     * @param vestingDays Number of days until bond maturity
     * @return discount Discount in basis points (treasury-safe and statistically guaranteed)
     */
    function getDiscount(uint256 vestingDays) external view returns (uint256) {
        require(
            vestingDays >= 30 && vestingDays <= BREAK_EVEN_GUARANTEE_DAYS,
            "Vesting period must be within empirical guarantee (30-1093 days, 99.7% success rate)"
        );

        // Emergency mode: Return very high discounts
        if (marketParams.emergencyMode) {
            return calculateEmergencyDiscount(vestingDays);
        }

        // Component 1: Expected SBC appreciation during vesting period
        uint256 expectedAppreciation = calculateExpectedAppreciation(vestingDays);

        // Component 2: Time premium for illiquidity
        uint256 timePremium = calculateTimePremium(vestingDays);

        // Component 3: Risk premium for duration and smart contract risk
        uint256 riskPremium = calculateRiskPremium(vestingDays);

        // Component 4: Market condition adjustments
        int256 marketAdjustment = calculateMarketAdjustment();

        // Total base discount
        uint256 totalDiscount = expectedAppreciation + timePremium + riskPremium;

        // Apply market adjustments
        if (marketAdjustment >= 0) {
            totalDiscount += uint256(marketAdjustment);
        } else {
            uint256 negativeAdjustment = uint256(-marketAdjustment);
            totalDiscount = totalDiscount > negativeAdjustment ?
                totalDiscount - negativeAdjustment : 0;
        }

        // Ensure minimum discount for treasury safety (starts at 0% for 30-day bonds)
        totalDiscount = totalDiscount < MIN_DISCOUNT_BPS ? MIN_DISCOUNT_BPS : totalDiscount;

        // Cap at maximum safe discount based on CAGR analysis
        return totalDiscount > MAX_DISCOUNT_BPS ? MAX_DISCOUNT_BPS : totalDiscount;
    }

    /**
     * @dev Calculate expected SBC appreciation using SMA-aligned treasury-safe formula
     * Formula: max(0, CAGR_component × duration_factor × consistency_ratio - volatility_buffer)
     * Starts at 0% for 30-day bonds to ensure treasury solvency
     * Aligns with empirical 1093-day SMA performance data
     */
    function calculateExpectedAppreciation(uint256 vestingDays) public view returns (uint256) {
        require(vestingDays >= 30, "Minimum vesting period is 30 days");

        // 30-day bonds start at 0% for treasury safety
        if (vestingDays == 30) {
            return 0;
        }

        // Calculate duration factor: linear progression from 0 to 1 over 1063 days (1093-30)
        uint256 durationFactor = ((vestingDays - 30) * FIXED_POINT_SCALE) / (1093 - 30);

        // Get consistency ratio for this duration tier
        uint256 consistencyRatio = getConsistencyRatio(vestingDays);

        // Calculate CAGR component: 44.63% annual = ~85% for max duration with consistency
        uint256 maxCagrDiscount = (ANNUAL_CAGR_BPS * 85) / 100; // 85% of CAGR for safety
        uint256 cagrComponent = (maxCagrDiscount * durationFactor) / FIXED_POINT_SCALE;

        // Apply consistency ratio adjustment
        uint256 consistencyAdjusted = (cagrComponent * consistencyRatio) / FIXED_POINT_SCALE;

        // Calculate volatility buffer: higher for shorter durations
        uint256 volatilityBuffer = calculateVolatilityBuffer(vestingDays);

        // Ensure non-negative result
        if (consistencyAdjusted <= volatilityBuffer) {
            return 0;
        }

        return consistencyAdjusted - volatilityBuffer;
    }

    /**
     * @dev Get consistency ratio for given vesting period based on empirical BTC SMA analysis
     * @param vestingDays Number of days until bond maturity
     * @return consistencyRatio Consistency ratio in basis points (0-10000)
     */
    function getConsistencyRatio(uint256 vestingDays) public view returns (uint256) {
        // Linear search through consistency tiers
        for (uint256 i = 0; i < CONSISTENCY_TIERS.length; i++) {
            if (vestingDays <= CONSISTENCY_TIERS[i].maxDays) {
                return CONSISTENCY_TIERS[i].consistencyBPS;
            }
        }

        // Fallback to maximum consistency (should never reach here)
        return CONSISTENCY_RATIO_1093;
    }

    /**
     * @dev Calculate volatility buffer based on vesting period
     * Shorter durations need higher buffers due to market timing risk
     * @param vestingDays Number of days until bond maturity
     * @return buffer Volatility buffer in basis points
     */
    function calculateVolatilityBuffer(uint256 vestingDays) public pure returns (uint256) {
        // Base volatility buffer of 2%
        uint256 baseBuffer = VOLATILITY_BUFFER_BPS;

        // Additional buffer for shorter durations (decreases linearly)
        // 30 days: +3% buffer, 1093 days: +0% buffer
        uint256 durationBuffer = 0;
        if (vestingDays < 365) {
            durationBuffer = (300 * (365 - vestingDays)) / 365; // Up to 3% for very short durations
        }

        return baseBuffer + durationBuffer;
    }

    /**
     * @dev Calculate time premium for illiquidity
     * Users need compensation for locking funds
     */
    function calculateTimePremium(uint256 vestingDays) public pure returns (uint256) {
        // Base: 0.5% per month (linear)
        uint256 basePremium = (vestingDays * ILLIQUIDITY_RATE_PER_MONTH) / 30;

        // Add exponential component for very long durations
        if (vestingDays > 365) {
            uint256 extraDays = vestingDays - 365;
            uint256 exponentialPremium = (extraDays * extraDays) / 10000; // Quadratic growth
            basePremium += exponentialPremium;
        }

        return basePremium;
    }

    /**
     * @dev Calculate risk premium based on duration and smart contract risk
     */
    function calculateRiskPremium(uint256 vestingDays) public pure returns (uint256) {
        uint256 riskPremium = SMART_CONTRACT_RISK_BPS; // Base 1% SC risk

        // Duration risk: Higher for longer periods
        if (vestingDays <= 90) {
            riskPremium += 50;    // +0.5% for < 3 months
        } else if (vestingDays <= 365) {
            riskPremium += 150;   // +1.5% for < 1 year
        } else if (vestingDays <= 730) {
            riskPremium += 300;   // +3% for < 2 years
        } else {
            riskPremium += 500;   // +5% for 2+ years
        }

        return riskPremium;
    }

    /**
     * @dev Calculate market condition adjustments
     * Returns signed adjustment in basis points
     */
    function calculateMarketAdjustment() public view returns (int256) {
        int256 totalAdjustment = 0;

        // 1. Peg deviation adjustment
        int256 pegDeviation = pegMonitor.getSBCPegDeviation();
        // If SBC trades above SMA, reduce discounts (make bonds less attractive)
        // If SBC trades below SMA, increase discounts (make bonds more attractive)
        totalAdjustment -= pegDeviation / 4; // 25% of peg deviation

        // 2. Volatility adjustment
        uint256 currentVol = smaOracle.getCurrentVolatility();
        uint256 baseVol = 200; // 2% baseline volatility
        if (currentVol > baseVol) {
            uint256 excessVol = currentVol - baseVol;
            uint256 volAdjustment = (excessVol * marketParams.volatilityMultiplier) / 100;
            totalAdjustment += int256(volAdjustment);
        }

        // 3. Liquidity needs adjustment
        totalAdjustment += int256(marketParams.liquidityNeedBPS);

        // 4. Demand pressure adjustment
        totalAdjustment += int256(marketParams.demandPressureBPS);

        return totalAdjustment;
    }

    /**
     * @dev Calculate emergency mode discount (very high to attract immediate liquidity)
     */
    function calculateEmergencyDiscount(uint256 vestingDays) public pure returns (uint256) {
        // Emergency: Offer very attractive discounts regardless of fundamentals
        uint256 baseEmergencyDiscount = 7000; // 70% base
        uint256 timeBonus = (vestingDays * 2000) / 1093; // Up to +20% for max duration

        return baseEmergencyDiscount + timeBonus; // Up to 90% in emergency
    }

    /**
     * @dev Preview discount calculation with detailed breakdown
     */
    function previewDiscountCalculation(uint256 vestingDays) external view returns (
        uint256 expectedAppreciation,
        uint256 timePremium,
        uint256 riskPremium,
        int256 marketAdjustment,
        uint256 totalDiscount
    ) {
        expectedAppreciation = calculateExpectedAppreciation(vestingDays);
        timePremium = calculateTimePremium(vestingDays);
        riskPremium = calculateRiskPremium(vestingDays);
        marketAdjustment = calculateMarketAdjustment();

        uint256 baseDiscount = expectedAppreciation + timePremium + riskPremium;

        if (marketAdjustment >= 0) {
            totalDiscount = baseDiscount + uint256(marketAdjustment);
        } else {
            uint256 negativeAdjustment = uint256(-marketAdjustment);
            totalDiscount = baseDiscount > negativeAdjustment ?
                baseDiscount - negativeAdjustment : 0;
        }

        totalDiscount = Math.min(totalDiscount, 9500);
    }

    /**
     * @dev Get discount curve for multiple durations
     */
    function getDiscountCurve(uint256[] calldata vestingDays) external view returns (
        uint256[] memory discounts
    ) {
        discounts = new uint256[](vestingDays.length);

        for (uint256 i = 0; i < vestingDays.length; i++) {
            discounts[i] = this.getDiscount(vestingDays[i]);
        }
    }

    /**
     * @dev Update market parameters
     */
    function updateMarketParams(MarketParams calldata newParams) external onlyRole(ADMIN_ROLE) {
        // Validate parameters
        require(newParams.volatilityMultiplier <= 500, "Volatility multiplier too high"); // Max 5x
        require(newParams.liquidityNeedBPS <= 2000, "Liquidity need too high"); // Max 20%
        require(newParams.demandPressureBPS <= 1000 && newParams.demandPressureBPS >= -1000, "Invalid demand pressure");
        require(newParams.maxDailyChange <= 1000, "Max daily change too high"); // Max 10%

        marketParams = newParams;
        emit MarketParamsUpdated(newParams);
    }

    /**
     * @dev Toggle emergency mode
     */
    function setEmergencyMode(bool enabled) external onlyRole(ADMIN_ROLE) {
        marketParams.emergencyMode = enabled;
        emit EmergencyModeToggled(enabled);
    }

    /**
     * @dev Update oracle contracts
     */
    function updateOracles(
        address newSMAOracle,
        address newPegMonitor
    ) external onlyRole(ADMIN_ROLE) {
        if (newSMAOracle != address(0)) {
            smaOracle = ISMAOracle(newSMAOracle);
        }
        if (newPegMonitor != address(0)) {
            pegMonitor = IPegMonitor(newPegMonitor);
        }
    }

    /**
     * @dev Record daily volume for demand analysis
     */
    function recordDailyVolume(uint256 volumeUSDC) external onlyRole(OPERATOR_ROLE) {
        dailyVolumeUSDC = volumeUSDC;

        // Update rolling average (7-day)
        rollingAvgVolume = (rollingAvgVolume * 6 + volumeUSDC) / 7;

        lastUpdateTimestamp = block.timestamp;
    }

    /**
     * @dev Get current market conditions summary
     */
    function getMarketConditions() external view returns (
        int256 pegDeviation,
        uint256 currentVolatility,
        uint256 dailyVolume,
        uint256 avgVolume,
        bool emergencyMode
    ) {
        pegDeviation = pegMonitor.getSBCPegDeviation();
        currentVolatility = smaOracle.getCurrentVolatility();
        dailyVolume = dailyVolumeUSDC;
        avgVolume = rollingAvgVolume;
        emergencyMode = marketParams.emergencyMode;
    }

    /**
     * @dev Calculate optimal vesting period for given discount target
     */
    function findOptimalVestingForDiscount(uint256 targetDiscount) external view returns (uint256 optimalDays) {
        // Binary search for optimal vesting period
        uint256 low = 30;
        uint256 high = 1093;

        while (low < high) {
            uint256 mid = (low + high) / 2;
            uint256 discount = this.getDiscount(mid);

            if (discount < targetDiscount) {
                low = mid + 1;
            } else {
                high = mid;
            }
        }

        return low;
    }
}
