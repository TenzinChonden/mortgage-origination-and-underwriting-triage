"""
Automated Gherkin Acceptance & Regulatory Compliance Test Suite
Validates BR-01 through BR-05 and FR-01 through NFR-03.
"""

import pytest
from config import PolicyConfig, DEFAULT_POLICY
from rules_engine import canadian_monthly_payment, evaluate_application


def base_prime_application() -> dict:
    """Helper returning a clean prime Track B salaried borrower profile."""
    return {
        "application_id": "TEST-001",
        "province": "ON",
        "employment_type": "Salaried",
        "property_value": 600_000.0,
        "down_payment": 150_000.0,
        "ltv": 0.75,
        "base_loan_amount": 450_000.0,
        "contract_rate": 0.0450,  # MQR = max(4.50% + 2.00%, 5.25%) = 6.50%
        "declared_annual_income": 135_000.0,
        "verified_annual_income": 135_000.0,
        "credit_score": 760,
        "monthly_property_tax": 425.0,
        "monthly_heating": 140.0,
        "monthly_condo_fees": 0.0,
        "monthly_other_debts": 450.0,
        "pipeda_consent_signed": True,
        "fintrac_pep_or_sanctions_hit": False,
        "sof_90day_verified": True,
    }


def test_canadian_semi_annual_compounding():
    """Verify Canadian semi-annual compounding payment math against standard benchmark."""
    # $450,000 at 6.50% nominal (compounded semi-annually) over 25 years = $3,014.20/mo
    pmt = canadian_monthly_payment(principal=450_000.0, annual_nominal_rate=0.065, years=25)
    assert pmt == pytest.approx(3014.20, abs=0.05)


def test_gherkin_scenario_1_track_b_prime_stp_approval():
    """
    Scenario 1: Prime salaried Track B borrower passes MQR stress test, credit >= 680,
    and clean AML/SOF -> Automated Conditional Commitment (< 15 min).
    """
    app = base_prime_application()
    res = evaluate_application(app)

    assert res["track"] == "Track B (Conventional)"
    assert res["cmhc_premium"] == 0.0
    assert res["mqr_rate"] == 0.0650
    assert res["gds_ratio"] < 0.39
    assert res["tds_ratio"] < 0.44
    assert res["routing_decision"] == "STP_APPROVED"
    assert res["reason_codes"] == "OK-STP-PRIME"


def test_gherkin_scenario_2_track_a_tds_breach_routes_to_workbench():
    """
    Scenario 2: High-ratio Track A insured borrower (90% LTV) with elevated monthly debts
    breaches 44% TDS -> Never auto-declined (BR-05); routes to Underwriter Workbench.
    """
    app = base_prime_application()
    app.update(
        {
            "property_value": 500_000.0,
            "down_payment": 50_000.0,
            "ltv": 0.90,
            "base_loan_amount": 450_000.0,
            "verified_annual_income": 115_000.0,
            "declared_annual_income": 115_000.0,
            "monthly_other_debts": 950.0,
        }
    )
    res = evaluate_application(app)

    assert res["track"] == "Track A (Insured)"
    assert res["cmhc_premium"] == round(450_000.0 * 0.0310, 2)  # 3.10% CMHC tier at 90% LTV
    assert res["tds_ratio"] > 0.44
    assert res["routing_decision"] == "UNDERWRITER_WORKBENCH"
    assert "ERR-CMHC-TDS-44" in res["reason_codes"]


def test_gherkin_scenario_3_fintrac_sof_provenance_hold():
    """
    Scenario 3: Down payment >= $10,000 lacking 90-day bank statement provenance
    routes immediately to Compliance Queue with HOLD-AML-SOF.
    """
    app = base_prime_application()
    app["sof_90day_verified"] = False

    res = evaluate_application(app)
    assert res["routing_decision"] == "COMPLIANCE_QUEUE"
    assert "HOLD-AML-SOF" in res["reason_codes"]


def test_ocr_income_variance_boundary_fr03():
    """FR-03: Variance > +/- 2.0% between declared and CRA NOA income triggers exception review."""
    app = base_prime_application()
    app["declared_annual_income"] = 140_000.0  # +3.7% above verified $135k

    res = evaluate_application(app)
    assert res["routing_decision"] == "UNDERWRITER_WORKBENCH"
    assert "ERR-OCR-INC-VAR" in res["reason_codes"]


def test_externalized_policy_config_agility_nfr03():
    """NFR-03: Changing MQR floor in PolicyConfig updates qualification without code edits."""
    strict_policy = PolicyConfig(mqr_floor_rate=0.0975)  # Stress shock to 9.75% floor
    app = base_prime_application()
    res = evaluate_application(app, policy=strict_policy)

    assert res["mqr_rate"] == 0.0975
    assert res["routing_decision"] == "UNDERWRITER_WORKBENCH"
    assert "ERR-B20-GDS-39" in res["reason_codes"]