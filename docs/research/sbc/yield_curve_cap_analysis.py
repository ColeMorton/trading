#!/usr/bin/env python3
"""
SBC Yield Curve Cap Analysis
Investigation of the 95% discount cap and its impact around 600-700 days

This script analyzes why the yield curve levels off around 600 days
and whether this behavior is mathematically sound.
"""

import matplotlib.pyplot as plt
import pandas as pd
from sbc_yield_curve_calculator import SBCYieldCurveCalculator


def analyze_cap_behavior():
    """Analyze where and why the 95% cap kicks in"""

    calculator = SBCYieldCurveCalculator()

    # Generate detailed curve around the cap point
    test_days = list(range(500, 800, 10))  # Around suspected cap point

    results = []
    for days in test_days:
        breakdown = calculator.get_discount_breakdown(days)

        # Calculate what discount would be without cap
        uncapped_discount = (
            breakdown["expected_appreciation"]
            + breakdown["time_premium"]
            + breakdown["risk_premium"]
            + breakdown["market_adjustment"]
        )

        is_capped = uncapped_discount > 9500

        results.append(
            {
                "vesting_days": days,
                "expected_appreciation": breakdown["expected_appreciation"],
                "time_premium": breakdown["time_premium"],
                "risk_premium": breakdown["risk_premium"],
                "market_adjustment": breakdown["market_adjustment"],
                "uncapped_discount": uncapped_discount,
                "final_discount": breakdown["total_discount"],
                "is_capped": is_capped,
                "cap_excess": max(0, uncapped_discount - 9500),
            }
        )

    return pd.DataFrame(results)


def find_exact_cap_point():
    """Find exactly where the cap first kicks in"""

    calculator = SBCYieldCurveCalculator()

    # Binary search for exact cap point
    low_days = 500
    high_days = 800
    tolerance = 1  # 1 day precision

    while high_days - low_days > tolerance:
        mid_days = (low_days + high_days) // 2
        breakdown = calculator.get_discount_breakdown(mid_days)

        uncapped = (
            breakdown["expected_appreciation"]
            + breakdown["time_premium"]
            + breakdown["risk_premium"]
            + breakdown["market_adjustment"]
        )

        if uncapped > 9500:
            high_days = mid_days
        else:
            low_days = mid_days

    return high_days


def analyze_mathematical_components():
    """Analyze which component causes the cap to be hit"""

    calculator = SBCYieldCurveCalculator()

    # Test specific points around cap
    test_points = [600, 650, 700, 750, 1093]

    analysis = []
    for days in test_points:
        expected = calculator.calculate_expected_appreciation(days)
        time_prem = calculator.calculate_time_premium(days)
        risk_prem = calculator.calculate_risk_premium(days)

        analysis.append(
            {
                "days": days,
                "expected_appreciation": expected,
                "time_premium": time_prem,
                "risk_premium": risk_prem,
                "total_uncapped": expected + time_prem + risk_prem,
                "months": days / 30,
                "expected_pct": expected / 100,
                "time_pct": time_prem / 100,
                "risk_pct": risk_prem / 100,
            }
        )

    return pd.DataFrame(analysis)


def calculate_theoretical_max_without_cap():
    """Calculate what the maximum discount would be at 1093 days without cap"""

    calculator = SBCYieldCurveCalculator()

    # Calculate each component at maximum duration
    days_1093 = 1093
    expected = calculator.calculate_expected_appreciation(days_1093)
    time_prem = calculator.calculate_time_premium(days_1093)
    risk_prem = calculator.calculate_risk_premium(days_1093)

    total_uncapped = expected + time_prem + risk_prem

    return {
        "expected_appreciation_bps": expected,
        "time_premium_bps": time_prem,
        "risk_premium_bps": risk_prem,
        "total_uncapped_bps": total_uncapped,
        "total_uncapped_pct": total_uncapped / 100,
        "cap_at_95pct": 9500,
        "excess_over_cap_bps": total_uncapped - 9500,
        "excess_over_cap_pct": (total_uncapped - 9500) / 100,
    }


def create_cap_analysis_visualization():
    """Create visualization showing cap behavior"""

    # Generate analysis data
    cap_df = analyze_cap_behavior()
    exact_cap_point = find_exact_cap_point()
    component_analysis = analyze_mathematical_components()
    theoretical_max = calculate_theoretical_max_without_cap()

    # Create comprehensive figure
    _fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # 1. Capped vs Uncapped Curve
    ax1.plot(
        cap_df["vesting_days"],
        cap_df["uncapped_discount"] / 100,
        "b-",
        linewidth=3,
        label="Uncapped Discount",
    )
    ax1.plot(
        cap_df["vesting_days"],
        cap_df["final_discount"] / 100,
        "r-",
        linewidth=3,
        label="Final Discount (with cap)",
    )
    ax1.axhline(y=95, color="gray", linestyle="--", alpha=0.7, label="95% Cap")
    ax1.axvline(
        x=exact_cap_point,
        color="orange",
        linestyle=":",
        label=f"Cap Point: {exact_cap_point} days",
    )

    ax1.set_xlabel("Vesting Period (Days)")
    ax1.set_ylabel("Discount (%)")
    ax1.set_title("Yield Curve: Capped vs Uncapped Behavior")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Component breakdown around cap point
    cap_region = cap_df[
        (cap_df["vesting_days"] >= 550) & (cap_df["vesting_days"] <= 750)
    ]

    ax2.plot(
        cap_region["vesting_days"],
        cap_region["expected_appreciation"] / 100,
        "g-",
        linewidth=2,
        label="Expected Appreciation",
    )
    ax2.plot(
        cap_region["vesting_days"],
        cap_region["time_premium"] / 100,
        "b-",
        linewidth=2,
        label="Time Premium",
    )
    ax2.plot(
        cap_region["vesting_days"],
        cap_region["risk_premium"] / 100,
        "r-",
        linewidth=2,
        label="Risk Premium",
    )
    ax2.axhline(y=95, color="gray", linestyle="--", alpha=0.7, label="95% Cap")

    ax2.set_xlabel("Vesting Period (Days)")
    ax2.set_ylabel("Component Value (%)")
    ax2.set_title("Component Analysis Around Cap Point")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. Cap excess analysis
    capped_data = cap_df[cap_df["is_capped"]]

    ax3.plot(
        capped_data["vesting_days"],
        capped_data["cap_excess"] / 100,
        "orange",
        linewidth=3,
        label="Excess Over Cap",
    )
    ax3.fill_between(
        capped_data["vesting_days"],
        0,
        capped_data["cap_excess"] / 100,
        alpha=0.3,
        color="orange",
        label="Lost Discount Area",
    )

    ax3.set_xlabel("Vesting Period (Days)")
    ax3.set_ylabel("Excess Discount (%)")
    ax3.set_title("Discount Lost Due to 95% Cap")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 4. Summary statistics
    ax4.axis("off")

    summary_text = f"""
    YIELD CURVE CAP ANALYSIS

    Cap Point Analysis:
    • First hits 95% cap at: {exact_cap_point} days (~{exact_cap_point / 30:.1f} months)
    • Cap level: 95% (9,500 basis points)

    Theoretical Maximum (1093 days):
    • Expected Appreciation: {theoretical_max["expected_appreciation_bps"]:.0f} bps ({theoretical_max["expected_appreciation_bps"] / 100:.1f}%)
    • Time Premium: {theoretical_max["time_premium_bps"]:.0f} bps ({theoretical_max["time_premium_bps"] / 100:.1f}%)
    • Risk Premium: {theoretical_max["risk_premium_bps"]:.0f} bps ({theoretical_max["risk_premium_bps"] / 100:.1f}%)
    • Total Uncapped: {theoretical_max["total_uncapped_bps"]:.0f} bps ({theoretical_max["total_uncapped_pct"]:.1f}%)

    Cap Impact:
    • Excess over cap: {theoretical_max["excess_over_cap_bps"]:.0f} bps ({theoretical_max["excess_over_cap_pct"]:.1f}%)
    • Percentage capped: {theoretical_max["excess_over_cap_bps"] / theoretical_max["total_uncapped_bps"]:.1%}

    Primary Driver:
    • Expected appreciation dominates and would naturally
      exceed 95% around {exact_cap_point} days
    • Cap prevents unrealistic discount levels
    • Maintains economic sustainability
    """

    ax4.text(
        0.05,
        0.95,
        summary_text,
        transform=ax4.transAxes,
        fontsize=11,
        verticalalignment="top",
        fontfamily="monospace",
        bbox={"boxstyle": "round", "facecolor": "lightblue", "alpha": 0.1},
    )

    plt.tight_layout()
    plt.savefig(
        "/Users/colemorton/Projects/trading/sbc_yield_curve_cap_analysis.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.show()

    # Print detailed analysis
    print("SBC Yield Curve Cap Analysis")
    print("=" * 50)
    print(f"Cap first hits at: {exact_cap_point} days")
    print(f"Theoretical max at 1093 days: {theoretical_max['total_uncapped_pct']:.1f}%")
    print(f"Excess over cap: {theoretical_max['excess_over_cap_pct']:.1f}%")
    print("\nComponent Analysis at Key Points:")
    print(component_analysis.round(1))

    return cap_df, exact_cap_point, theoretical_max


def evaluate_cap_rationale():
    """Evaluate whether the 95% cap makes economic sense"""

    theoretical_max = calculate_theoretical_max_without_cap()

    print("\nEconomic Rationale for 95% Cap:")
    print("=" * 40)

    # Without cap, what would maximum discount be?
    max_uncapped = theoretical_max["total_uncapped_pct"]

    print(f"1. Maximum uncapped discount: {max_uncapped:.1f}%")
    print(f"   - This means paying ${100 - max_uncapped:.1f} to get $100 of SBC")
    print(f"   - Effective return: {max_uncapped / (100 - max_uncapped) * 100:.0f}%")

    # Treasury implications
    print("\n2. Treasury safety implications:")
    print(
        f"   - At {max_uncapped:.1f}% discount: Protocol gets ${100 - max_uncapped:.1f}, owes $100 SBC"
    )
    print(
        f"   - WBTC needs to appreciate {100 / (100 - max_uncapped):.1f}x to break even"
    )
    print("   - Historical WBTC 3-year: ~3.4x appreciation")

    if max_uncapped > 95:
        print("   - ⚠️  Uncapped discount exceeds sustainable levels")
        print("   - 95% cap provides safety margin")
    else:
        print("   - ✅ Uncapped discount within reasonable bounds")

    # Market reasonableness
    print("\n3. Market reasonableness:")
    print("   - 95% discount = paying $5 to get $100 of future SBC")
    print("   - This is extreme but not unreasonable for 3-year lock")
    print("   - Cap prevents >95% discounts that could destabilize treasury")


if __name__ == "__main__":
    print("Running SBC Yield Curve Cap Analysis...")
    cap_df, exact_cap_point, theoretical_max = create_cap_analysis_visualization()
    evaluate_cap_rationale()
