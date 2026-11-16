"""
Executive Triage & Regulatory Stress Dashboard Generator
Exports a 4-panel KPI & analytics summary to architecture/exports/04-executive-triage-dashboard.png
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#CCCCCC"
plt.rcParams["axes.linewidth"] = 0.8


def generate_executive_dashboard(
    triaged_path: str = "data/triaged_applications.csv",
    export_dir: str = "data/dashboard_exports",
    output_img: str = "architecture/exports/04-executive-triage-dashboard.png",
) -> None:
    df = pd.read_csv(triaged_path)
    sens_df = pd.read_csv(f"{export_dir}/mqr_sensitivity.csv")
    pareto_df = pd.read_csv(f"{export_dir}/reason_code_pareto.csv")

    fig, axes = plt.subplots(2, 2, figsize=(16, 10), dpi=200)
    fig.patch.set_facecolor("#F8FAFC")
    fig.suptitle(
        "Maple Crest Bank — Target State Mortgage Triage & OSFI B-20 Analytics (N = 8,400 | $4.04B)",
        fontsize=15,
        fontweight="bold",
        color="#0F172A",
        y=0.97,
    )

    # --- Panel 1: Triage Routing Outcome Split ---
    ax1 = axes[0, 0]
    counts = df["routing_decision"].value_counts()
    labels = [
        f"STP Approved (<15m)\n{counts.get('STP_APPROVED', 0):,} ({counts.get('STP_APPROVED', 0)/len(df):.1%})",
        f"Underwriter Workbench (<=2d)\n{counts.get('UNDERWRITER_WORKBENCH', 0):,} ({counts.get('UNDERWRITER_WORKBENCH', 0)/len(df):.1%})",
        f"Compliance Queue (<=2d)\n{counts.get('COMPLIANCE_QUEUE', 0):,} ({counts.get('COMPLIANCE_QUEUE', 0)/len(df):.1%})",
    ]
    values = [
        counts.get("STP_APPROVED", 0),
        counts.get("UNDERWRITER_WORKBENCH", 0),
        counts.get("COMPLIANCE_QUEUE", 0),
    ]
    colors = ["#10B981", "#3B82F6", "#F59E0B"]
    bars = ax1.barh(labels[::-1], values[::-1], color=colors[::-1], height=0.55)
    ax1.set_title("1. Automated Triage Routing Distribution (Zero Auto-Declines)", fontweight="bold", loc="left", pad=10)
    ax1.set_xlabel("Application Count")
    ax1.set_xlim(0, max(values) * 1.18)
    ax1.grid(axis="x", linestyle="--", alpha=0.4)
    for bar in bars:
        w = bar.get_width()
        ax1.text(w + 80, bar.get_y() + bar.get_height() / 2, f"{int(w):,}", va="center", fontweight="bold", fontsize=10)

    # --- Panel 2: Exception & Hold Reason Code Pareto ---
    ax2 = axes[0, 1]
    exc_pareto = pareto_df[pareto_df["reason_code"] != "OK-STP-PRIME"].head(7).iloc[::-1]
    bars2 = ax2.barh(exc_pareto["reason_code"], exc_pareto["application_count"], color="#6366F1", height=0.6)
    ax2.set_title("2. Top Deterministic Exception & Hold Reason Codes", fontweight="bold", loc="left", pad=10)
    ax2.set_xlabel("Triggered Applications (Multi-Flag Inclusive)")
    ax2.set_xlim(0, exc_pareto["application_count"].max() * 1.18)
    ax2.grid(axis="x", linestyle="--", alpha=0.4)
    for bar in bars2:
        w = bar.get_width()
        ax2.text(w + 35, bar.get_y() + bar.get_height() / 2, f"{int(w):,}", va="center", fontsize=9.5)

    # --- Panel 3: GDS vs. TDS Distribution Across Track A & Track B ---
    ax3 = axes[1, 0]
    for track, col in [("Track B (Conventional)", "#0EA5E9"), ("Track A (Insured)", "#8B5CF6")]:
        sub = df[df["track"] == track]
        ax3.scatter(sub["gds_ratio"] * 100, sub["tds_ratio"] * 100, alpha=0.22, s=14, label=track, color=col)
    ax3.axvline(39.0, color="#EF4444", linestyle="--", linewidth=1.4, label="OSFI/CMHC Max GDS (39%)")
    ax3.axhline(44.0, color="#DC2626", linestyle=":", linewidth=1.4, label="OSFI/CMHC Max TDS (44%)")
    ax3.set_title("3. OSFI B-20 Stressed GDS vs. TDS Qualification Frontier", fontweight="bold", loc="left", pad=10)
    ax3.set_xlabel("Gross Debt Service — GDS (%)")
    ax3.set_ylabel("Total Debt Service — TDS (%)")
    ax3.set_xlim(10, 62)
    ax3.set_ylim(12, 72)
    ax3.grid(True, linestyle="--", alpha=0.35)
    ax3.legend(loc="upper left", fontsize=8.5, framealpha=0.9)

    # --- Panel 4: MQR Rate-Shock Sensitivity ---
    ax4 = axes[1, 1]
    short_labels = ["Base Case\n(5.25% Floor)", "+100 bps Shock\n(6.25% Floor)", "+200 bps Shock\n(7.25% Floor)"]
    x = range(len(short_labels))
    w = 0.36
    b1 = ax4.bar([i - w / 2 for i in x], sens_df["stp_count"], width=w, label="STP Approved (<15m)", color="#10B981")
    b2 = ax4.bar([i + w / 2 for i in x], sens_df["workbench_count"], width=w, label="Underwriter Workbench (<=2d)", color="#3B82F6")
    ax4.set_title("4. OSFI MQR Rate-Shock Stress Sensitivity", fontweight="bold", loc="left", pad=10)
    ax4.set_xticks(list(x))
    ax4.set_xticklabels(short_labels)
    ax4.set_ylabel("Application Count")
    ax4.set_ylim(0, 5000)
    ax4.grid(axis="y", linestyle="--", alpha=0.4)
    ax4.legend(loc="upper right", fontsize=9)
    for bar in list(b1) + list(b2):
        h = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width() / 2, h + 70, f"{int(h):,}", ha="center", fontsize=8.5, fontweight="bold")

    plt.tight_layout(rect=[0, 0.02, 1, 0.94])
    os.makedirs(os.path.dirname(output_img), exist_ok=True)
    plt.savefig(output_img, dpi=200)
    print(f"Saved executive dashboard visual -> {output_img}")


if __name__ == "__main__":
    generate_executive_dashboard()