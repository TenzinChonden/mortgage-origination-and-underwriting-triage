"""
Externalized OSFI Guideline B-20, CMHC & FINTRAC Underwriting Rules Engine
Maple Crest Bank — Retail Mortgage Origination & Underwriting Triage
"""

from typing import Dict, Any, List
import pandas as pd
from config import PolicyConfig, DEFAULT_POLICY


def canadian_monthly_payment(principal: float, annual_nominal_rate: float, years: int = 25) -> float:
    """
    Calculates monthly mortgage payment using Canadian semi-annual compounding.
    Formula: r_monthly = (1 + r_nominal / 2) ** (2 / 12) - 1
    """
    if principal <= 0:
        return 0.0
    if annual_nominal_rate <= 0:
        return principal / (years * 12)

    effective_monthly_rate = (1.0 + annual_nominal_rate / 2.0) ** (2.0 / 12.0) - 1.0
    n_payments = years * 12
    payment = principal * (
        effective_monthly_rate * (1.0 + effective_monthly_rate) ** n_payments
    ) / ((1.0 + effective_monthly_rate) ** n_payments - 1.0)
    return round(payment, 2)


def get_cmhc_premium_rate(ltv: float, policy: PolicyConfig = DEFAULT_POLICY) -> float:
    """Returns CMHC insurance premium rate for high-ratio mortgages (LTV > 80%)."""
    if ltv <= policy.insured_ltv_threshold:
        return 0.0
    for upper_ltv, rate in policy.cmhc_premium_tiers:
        if ltv <= upper_ltv:
            return rate
    raise ValueError(f"LTV {ltv:.2%} exceeds maximum allowable cap of {policy.max_ltv_cap:.0%}")


def evaluate_application(row: Dict[str, Any], policy: PolicyConfig = DEFAULT_POLICY) -> Dict[str, Any]:
    """
    Evaluates a single mortgage application against OSFI B-20, CMHC, FINTRAC, and PIPEDA rules.
    Enforces BR-05: Zero automated declines; non-STP files route to human queues with reason codes.
    """
    reason_codes: List[str] = []

    # 1. Track A (Insured) vs. Track B (Conventional) & CMHC Capitalization
    ltv = float(row["ltv"])
    property_value = float(row["property_value"])
    base_loan = float(row["base_loan_amount"])

    if ltv > policy.insured_ltv_threshold:
        track = "Track A (Insured)"
        if property_value > policy.insured_price_cap or ltv > policy.max_ltv_cap:
            reason_codes.append("ERR-CMHC-CAP-1.5M")
            cmhc_rate = 0.0
        else:
            cmhc_rate = get_cmhc_premium_rate(ltv, policy)
    else:
        track = "Track B (Conventional)"
        cmhc_rate = 0.0

    cmhc_premium = round(base_loan * cmhc_rate, 2)
    total_insured_loan = round(base_loan + cmhc_premium, 2)

    # 2. OSFI B-20 Minimum Qualifying Rate (MQR) & Stressed P&I
    contract_rate = float(row["contract_rate"])
    mqr_rate = round(max(contract_rate + policy.mqr_buffer_spread, policy.mqr_floor_rate), 4)
    stressed_monthly_pi = canadian_monthly_payment(
        total_insured_loan, mqr_rate, policy.default_amortization_years
    )

    # 3. GDS & TDS Ratio Calculation (using verified CRA NOA/T4 income)
    verified_income = float(row["verified_annual_income"])
    declared_income = float(row["declared_annual_income"])
    gross_monthly_income = verified_income / 12.0

    monthly_housing_costs = (
        stressed_monthly_pi
        + float(row["monthly_property_tax"])
        + float(row["monthly_heating"])
        + 0.50 * float(row["monthly_condo_fees"])
    )
    monthly_total_debt = monthly_housing_costs + float(row["monthly_other_debts"])

    gds_ratio = round(monthly_housing_costs / gross_monthly_income, 4)
    tds_ratio = round(monthly_total_debt / gross_monthly_income, 4)

    # 4. Regulatory & Policy Rule Checks
    # BR-04: PIPEDA Consent & FINTRAC AML / 90-Day Source-of-Funds Provenance
    if not bool(row["pipeda_consent_signed"]):
        reason_codes.append("HOLD-PIPEDA-CONSENT")

    aml_flag = False
    if bool(row["fintrac_pep_or_sanctions_hit"]):
        reason_codes.append("HOLD-FINTRAC-PEP")
        aml_flag = True

    if float(row["down_payment"]) >= policy.sof_provenance_threshold and not bool(row["sof_90day_verified"]):
        reason_codes.append("HOLD-AML-SOF")
        aml_flag = True

    # FR-03: OCR Income Variance Check (+/- 2.0% tolerance)
    income_variance = abs(declared_income - verified_income) / verified_income
    if income_variance > policy.ocr_income_tolerance:
        reason_codes.append("ERR-OCR-INC-VAR")

    # BR-02 / BR-03: Credit Score Thresholds
    credit_score = int(row["credit_score"])
    if credit_score < policy.hard_min_credit_score:
        reason_codes.append("ERR-CREDIT-SUB600")
    elif credit_score < policy.prime_min_credit_score:
        reason_codes.append("ERR-CREDIT-680")

    # BR-01 / BR-02 / BR-03: GDS / TDS Cap Checks
    max_gds = policy.track_a_max_gds if track.startswith("Track A") else policy.track_b_max_gds
    max_tds = policy.track_a_max_tds if track.startswith("Track A") else policy.track_b_max_tds

    if gds_ratio > max_gds:
        reason_codes.append("ERR-B20-GDS-39")
    if tds_ratio > max_tds:
        reason_codes.append("ERR-CMHC-TDS-44" if track.startswith("Track A") else "ERR-B20-TDS-44")

    # Employment Type Check: Self-employed T1 General / 2-yr avg requires underwriter validation
    if str(row["employment_type"]) == "Self-Employed":
        reason_codes.append("REV-SELF-EMP")

    # 5. Deterministic Routing Outcome (BR-05: No Automated Declines)
    if aml_flag:
        routing_decision = "COMPLIANCE_QUEUE"
        sla_target = "<= 2 Business Days"
    elif len(reason_codes) > 0:
        routing_decision = "UNDERWRITER_WORKBENCH"
        sla_target = "<= 2 Business Days"
    else:
        routing_decision = "STP_APPROVED"
        sla_target = "< 15 Minutes"
        reason_codes.append("OK-STP-PRIME")

    return {
        "track": track,
        "cmhc_premium": cmhc_premium,
        "total_insured_loan": total_insured_loan,
        "mqr_rate": mqr_rate,
        "stressed_monthly_pi": stressed_monthly_pi,
        "gds_ratio": gds_ratio,
        "tds_ratio": tds_ratio,
        "income_variance": round(income_variance, 4),
        "routing_decision": routing_decision,
        "sla_target": sla_target,
        "reason_codes": "|".join(reason_codes),
    }


def run_batch_triage(
    input_path: str = "data/synthetic_applications.csv",
    output_path: str = "data/triaged_applications.csv",
    policy: PolicyConfig = DEFAULT_POLICY,
) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    results = df.apply(lambda r: evaluate_application(r.to_dict(), policy), axis=1, result_type="expand")
    triaged_df = pd.concat([df, results], axis=1)
    triaged_df.to_csv(output_path, index=False)

    # Print executive triage summary
    total = len(triaged_df)
    stp_count = (triaged_df["routing_decision"] == "STP_APPROVED").sum()
    uw_count = (triaged_df["routing_decision"] == "UNDERWRITER_WORKBENCH").sum()
    comp_count = (triaged_df["routing_decision"] == "COMPLIANCE_QUEUE").sum()

    salaried_df = triaged_df[triaged_df["employment_type"] == "Salaried"]
    salaried_stp = (salaried_df["routing_decision"] == "STP_APPROVED").sum() / len(salaried_df)

    print(f"Triaged {total:,} applications -> {output_path}")
    print(f"  - STP Approved (< 15m):        {stp_count:,} ({stp_count/total:.1%}) [Salaried STP: {salaried_stp:.1%}]")
    print(f"  - Underwriter Workbench (<=2d): {uw_count:,} ({uw_count/total:.1%})")
    print(f"  - Compliance Queue (<=2d):      {comp_count:,} ({comp_count/total:.1%})")
    return triaged_df


if __name__ == "__main__":
    run_batch_triage()