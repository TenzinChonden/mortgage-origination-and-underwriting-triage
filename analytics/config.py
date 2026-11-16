"""
Externalized Regulatory & Underwriting Policy Configuration (NFR-03 / ADR-02)
Maple Crest Bank — Retail Mortgage Origination & Underwriting Triage
"""

from dataclasses import dataclass
from typing import Tuple, List


@dataclass(frozen=True)
class PolicyConfig:
    # --- OSFI Guideline B-20 Minimum Qualifying Rate (MQR) ---
    mqr_floor_rate: float = 0.0525          # 5.25% benchmark floor
    mqr_buffer_spread: float = 0.0200       # +2.00% over contract rate
    default_amortization_years: int = 25    # Standard 25-year amortization

    # --- Track A (Insured: LTV > 80%) vs. Track B (Conventional: LTV <= 80%) ---
    insured_ltv_threshold: float = 0.80     # > 80% requires mortgage default insurance
    max_ltv_cap: float = 0.95               # Max 95% LTV under Canadian rules
    insured_price_cap: float = 1_500_000.0  # $1.5M CAD purchase price cap for insured mortgages

    # --- Debt Service Ratio Caps (GDS / TDS) ---
    track_a_max_gds: float = 0.39           # CMHC Insured max GDS: 39.0%
    track_a_max_tds: float = 0.44           # CMHC Insured max TDS: 44.0%
    track_b_max_gds: float = 0.39           # Maple Crest Prime Conventional GDS: 39.0%
    track_b_max_tds: float = 0.44           # Maple Crest Prime Conventional TDS: 44.0%

    # --- Credit & Income Verification Thresholds ---
    prime_min_credit_score: int = 680       # Minimum credit score for STP prime track
    hard_min_credit_score: int = 600        # Below 600 routes immediately to senior review
    ocr_income_tolerance: float = 0.02      # +/- 2.0% variance allowed between declared & NOA/T4

    # --- FINTRAC AML & Source-of-Funds (SOF) Provenance ---
    sof_provenance_threshold: float = 10_000.0  # Down payments >= $10k require 90-day provenance

    # --- CMHC Tiered Insurance Premium Rates (by LTV upper bound) ---
    # Standard single-premium rates applied to base loan amount
    cmhc_premium_tiers: Tuple[Tuple[float, float], ...] = (
        (0.65, 0.0060),  # Up to 65% LTV: 0.60%
        (0.75, 0.0170),  # 65.01% - 75% LTV: 1.70%
        (0.80, 0.0240),  # 75.01% - 80% LTV: 2.40%
        (0.85, 0.0280),  # 80.01% - 85% LTV: 2.80%
        (0.90, 0.0310),  # 85.01% - 90% LTV: 3.10%
        (0.95, 0.0400),  # 90.01% - 95% LTV: 4.00%
    )

    # --- Operational & Financial Simulation Constants (Baseline vs. Target) ---
    annual_intake_volume: int = 8_400
    baseline_sla_days: float = 6.0
    target_stp_sla_minutes: float = 12.0
    target_exception_sla_days: float = 1.5
    baseline_abandonment_rate: float = 0.140
    target_abandonment_rate: float = 0.055
    avg_net_margin_per_funded_loan: float = 4_850.0  # CAD lifetime net contribution per loan
    implementation_cost_cad: float = 1_200_000.0


DEFAULT_POLICY = PolicyConfig()

PROVINCES: List[str] = ["ON", "BC", "AB", "QC", "MB", "SK", "NS", "NB"]
PROVINCE_WEIGHTS: List[float] = [0.42, 0.18, 0.16, 0.12, 0.04, 0.03, 0.03, 0.02]