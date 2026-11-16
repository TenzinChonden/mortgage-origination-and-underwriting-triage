"""
Synthetic Canadian Residential Mortgage Intake Generator
Generates ~8,400 realistic applications calibrated to Maple Crest Bank's baseline portfolio.
"""

import os
import numpy as np
import pandas as pd
from config import DEFAULT_POLICY, PROVINCES, PROVINCE_WEIGHTS


def generate_mortgage_applications(
    n_records: int = DEFAULT_POLICY.annual_intake_volume,
    seed: int = 42,
    output_path: str = "data/synthetic_applications.csv",
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    app_ids = [f"MCB-2026-{i:05d}" for i in range(1, n_records + 1)]
    provinces = rng.choice(PROVINCES, size=n_records, p=PROVINCE_WEIGHTS)

    # Employment type: 78% Salaried (T4/NOA), 22% Self-Employed (T1 General / 2-yr avg)
    employment_type = rng.choice(["Salaried", "Self-Employed"], size=n_records, p=[0.76, 0.24])

    # Property values calibrated around ~$615K CAD (yielding ~$485K avg loan)
    # Slightly higher medians in ON and BC
    prov_multiplier = np.where(np.isin(provinces, ["ON", "BC"]), 1.22, 0.88)
    base_home_value = rng.lognormal(mean=13.22, sigma=0.35, size=n_records) * prov_multiplier
    property_value = np.clip(np.round(base_home_value, -3), 220_000, 2_400_000)

    # LTV distribution: ~58% Conventional (<=80%), ~42% Insured (>80% up to 95%)
    is_high_ratio = rng.random(n_records) < 0.42
    ltv_conventional = rng.uniform(0.50, 0.80, size=n_records)
    ltv_insured = rng.uniform(0.801, 0.95, size=n_records)
    ltv = np.round(np.where(is_high_ratio, ltv_insured, ltv_conventional), 4)

    # Cap insured purchases at $1.5M or adjust LTV down to 80% for expensive properties
    over_insured_cap = (property_value > DEFAULT_POLICY.insured_price_cap) & (ltv > 0.80)
    ltv = np.where(over_insured_cap, 0.80, ltv)

    base_loan_amount = np.round(property_value * ltv, 2)
    down_payment = np.round(property_value - base_loan_amount, 2)

    # Contract interest rate (5-year fixed/variable distribution around 4.35% - 5.45%)
    contract_rate = np.round(rng.normal(loc=0.0465, scale=0.0045, size=n_records), 4)
    contract_rate = np.clip(contract_rate, 0.0369, 0.0649)

    # Gross annual income correlated with loan size + realistic debt-to-income spread
    target_loan_to_income = rng.normal(loc=3.05, scale=0.65, size=n_records)
    target_loan_to_income = np.clip(target_loan_to_income, 1.6, 5.2)
    verified_annual_income = np.round(base_loan_amount / target_loan_to_income, 2)
    verified_annual_income = np.clip(verified_annual_income, 55_000, 650_000)

    # Declared income: 92% within +/- 1.5% of CRA NOA/T4; 8% have material discrepancy (>2%)
    has_income_mismatch = rng.random(n_records) < 0.08
    small_noise = rng.uniform(-0.015, 0.015, size=n_records)
    large_noise = rng.choice([-1, 1], size=n_records) * rng.uniform(0.03, 0.14, size=n_records)
    declared_annual_income = np.round(
        verified_annual_income * (1 + np.where(has_income_mismatch, large_noise, small_noise)),
        2,
    )

    # Equifax credit score: Prime skewed (mean ~735, std ~55)
    credit_score = np.clip(np.round(rng.normal(loc=748, scale=48, size=n_records)).astype(int), 550, 860)

    # Monthly housing carrying costs (property tax + heating + 50% condo fees if applicable)
    monthly_property_tax = np.round((property_value * rng.uniform(0.007, 0.012, size=n_records)) / 12, 2)
    monthly_heating = np.round(rng.uniform(110, 185, size=n_records), 2)
    is_condo = rng.random(n_records) < 0.28
    monthly_condo_fees = np.where(is_condo, np.round(rng.uniform(280, 680, size=n_records), 2), 0.0)

    # Non-mortgage monthly debt obligations (auto loans, LOCs, credit cards, student loans)
    monthly_other_debts = np.round(
        np.where(
            rng.random(n_records) < 0.25,
            0.0,
            rng.lognormal(mean=6.15, sigma=0.65, size=n_records),
        ),
        2,
    )
    monthly_other_debts = np.clip(monthly_other_debts, 0.0, 2_800.0)

    # Compliance & Documentation Flags
    pipeda_consent_signed = rng.random(n_records) < 0.995  # Portal gate enforces ~99.5%
    fintrac_pep_or_sanctions_hit = rng.random(n_records) < 0.018  # ~1.8% AML/PEP screening hits
    # 90-day bank statement provenance verified for down payments >= $10k (~96.5% clean)
    sof_90day_verified = np.where(
        down_payment >= DEFAULT_POLICY.sof_provenance_threshold,
        rng.random(n_records) < 0.965,
        True,
    )

    df = pd.DataFrame(
        {
            "application_id": app_ids,
            "province": provinces,
            "employment_type": employment_type,
            "property_value": property_value,
            "down_payment": down_payment,
            "ltv": ltv,
            "base_loan_amount": base_loan_amount,
            "contract_rate": contract_rate,
            "declared_annual_income": declared_annual_income,
            "verified_annual_income": verified_annual_income,
            "credit_score": credit_score,
            "monthly_property_tax": monthly_property_tax,
            "monthly_heating": monthly_heating,
            "monthly_condo_fees": monthly_condo_fees,
            "monthly_other_debts": monthly_other_debts,
            "pipeda_consent_signed": pipeda_consent_signed,
            "fintrac_pep_or_sanctions_hit": fintrac_pep_or_sanctions_hit,
            "sof_90day_verified": sof_90day_verified,
        }
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df):,} synthetic applications -> {output_path}")
    print(f"Average Base Loan: ${df['base_loan_amount'].mean():,.2f} CAD | Total Volume: ${df['base_loan_amount'].sum()/1e9:.2f}B")
    return df


if __name__ == "__main__":
    generate_mortgage_applications()