"""
As-Is vs. To-Be Operational ROI & OSFI MQR Rate-Shock Sensitivity Simulation
Maple Crest Bank — Retail Mortgage Origination & Underwriting Triage
"""

import os
import pandas as pd
from config import PolicyConfig, DEFAULT_POLICY
from rules_engine import evaluate_application


def run_roi_and_sensitivity(
    triaged_path: str = "data/triaged_applications.csv",
    summary_output_dir: str = "data/dashboard_exports",
    policy: PolicyConfig = DEFAULT_POLICY,
) -> None:
    df = pd.read_csv(triaged_path)
    total_apps = len(df)

    # --- 1. Baseline (As-Is) vs. Target (To-Be) Funnel & Financial Model ---
    # Baseline: 6.0-day SLA drives 14.0% applicant abandonment; 72% pull-through on retained files
    as_is_abandoned = round(total_apps * policy.baseline_abandonment_rate)
    as_is_retained = total_apps - as_is_abandoned
    as_is_funded = round(as_is_retained * 0.72)

    # To-Be: STP files (<15m) abandon at only 1.5%; Workbench/Compliance (<=2d) abandon at 8.5%
    stp_apps = int((df["routing_decision"] == "STP_APPROVED").sum())
    exception_apps = total_apps - stp_apps

    to_be_abandoned = round(stp_apps * 0.015 + exception_apps * 0.085)
    to_be_retained = total_apps - to_be_abandoned
    to_be_funded = round(to_be_retained * 0.73)  # Slight pull-through lift from faster commitment

    recovered_funded_loans = to_be_funded - as_is_funded
    incremental_gross_margin = recovered_funded_loans * policy.avg_net_margin_per_funded_loan

    # Operational rework savings (eliminating 35% manual doc-chasing & offline Excel re-keying)
    ops_efficiency_savings = 420_000.0
    annual_run_rate_cost = 785_000.0  # Cloud, OCR, API gateway & maintenance
    net_annual_benefit = incremental_gross_margin + ops_efficiency_savings - annual_run_rate_cost
    payback_months = round((policy.implementation_cost_cad / net_annual_benefit) * 12, 1)

    weighted_to_be_sla_days = round(
        ((stp_apps * (policy.target_stp_sla_minutes / (60 * 8))) + (exception_apps * policy.target_exception_sla_days))
        / total_apps,
        2,
    )

    print("=" * 72)
    print("MAPLE CREST BANK — AS-IS vs. TO-BE TRIAGE SIMULATION SUMMARY")
    print("=" * 72)
    print(f"Annual Intake Volume:           {total_apps:,} applications (${df['base_loan_amount'].sum()/1e9:.2f}B)")
    print(f"Overall STP Rate (< 15 min):    {stp_apps:,} ({stp_apps/total_apps:.1%})")
    print(f"Avg Turnaround SLA:             {policy.baseline_sla_days:.1f} days -> {weighted_to_be_sla_days:.2f} days")
    print(f"Applicant Abandonment:          {as_is_abandoned:,} ({as_is_abandoned/total_apps:.1%}) -> {to_be_abandoned:,} ({to_be_abandoned/total_apps:.1%})")
    print(f"Net Recovered Funded Loans:     +{recovered_funded_loans:,} loans/yr")
    print(f"Net Annual Financial Benefit:   ${net_annual_benefit:,.0f} CAD/yr")
    print(f"Payback Period ($1.20M Build):  {payback_months} months")
    print("=" * 72)

    # --- 2. OSFI MQR Rate-Shock Sensitivity Analysis ---
    sensitivity_rows = []
    for label, floor in [
        ("Base Case (MQR 5.25% Floor)", 0.0525),
        ("Moderate Shock (+100 bps / 6.25%)", 0.0625),
        ("Severe Rate Shock (+200 bps / 7.25%)", 0.0725),
    ]:
        shock_policy = PolicyConfig(mqr_floor_rate=floor)
        shock_res = df.apply(
            lambda r: evaluate_application(r.to_dict(), shock_policy), axis=1, result_type="expand"
        )
        stp_cnt = int((shock_res["routing_decision"] == "STP_APPROVED").sum())
        uw_cnt = int((shock_res["routing_decision"] == "UNDERWRITER_WORKBENCH").sum())
        comp_cnt = int((shock_res["routing_decision"] == "COMPLIANCE_QUEUE").sum())
        avg_gds = shock_res["gds_ratio"].mean()
        avg_tds = shock_res["tds_ratio"].mean()

        sensitivity_rows.append(
            {
                "scenario": label,
                "mqr_floor": floor,
                "stp_count": stp_cnt,
                "stp_rate": round(stp_cnt / total_apps, 4),
                "workbench_count": uw_cnt,
                "compliance_count": comp_cnt,
                "avg_gds": round(avg_gds, 4),
                "avg_tds": round(avg_tds, 4),
            }
        )

    sens_df = pd.DataFrame(sensitivity_rows)
    print("\nOSFI B-20 MQR RATE-SHOCK SENSITIVITY:")
    print(sens_df.to_string(index=False))

    # --- 3. Export Clean Tables for Step 6 Executive Dashboard ---
    os.makedirs(summary_output_dir, exist_ok=True)

    # Export A: Sensitivity Summary
    sens_df.to_csv(f"{summary_output_dir}/mqr_sensitivity.csv", index=False)

    # Export B: Exploded Reason Code Breakdown (for Pareto chart)
    reasons_exploded = (
        df.assign(reason_code=df["reason_codes"].str.split("|"))
        .explode("reason_code")
        .groupby(["routing_decision", "reason_code"], as_index=False)
        .agg(application_count=("application_id", "count"), total_loan_volume=("base_loan_amount", "sum"))
        .sort_values("application_count", ascending=False)
    )
    reasons_exploded.to_csv(f"{summary_output_dir}/reason_code_pareto.csv", index=False)

    # Export C: Provincial & Track Summary
    prov_summary = df.groupby(["province", "track", "routing_decision"], as_index=False).agg(
        application_count=("application_id", "count"),
        avg_loan_size=("base_loan_amount", "mean"),
        avg_gds=("gds_ratio", "mean"),
        avg_tds=("tds_ratio", "mean"),
        total_cmhc_premiums=("cmhc_premium", "sum"),
    )
    prov_summary.to_csv(f"{summary_output_dir}/provincial_track_summary.csv", index=False)
    print(f"\nExported dashboard tables -> {summary_output_dir}/")


if __name__ == "__main__":
    run_roi_and_sensitivity()