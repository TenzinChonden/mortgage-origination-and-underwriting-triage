# Maple Crest Bank: Retail Mortgage Origination & Underwriting Triage
**Business Analysis, Enterprise Architecture & Python Decision Simulation Case Study**

> **Project Status:** Active Build (Phase 1 Enterprise Architecture & Process Discovery in progress; Phase 2 Python B-20/CMHC Rules Engine & Power BI Analytics queued next).

---

## Executive Summary
Maple Crest Bank of Canada (a simulated retail mortgage lender funding ~8,400 residential mortgages annually at $485,000 CAD average loan size / $4.07B volume) faces a **6.0-business-day** turnaround time for conditional commitments due to manual T4/NOA re-keying, separate credit pulls, and offline Excel debt-service calculations. This bottleneck drives a **35% rework rate** and **14.0% applicant abandonment** (~1,367 lost files annually).

This case study demonstrates an end-to-end **Business Analysis and Enterprise Architecture** solution automating Straight-Through Processing (STP) for prime salaried borrowers while maintaining strict compliance with **OSFI Guideline B-20**, **CMHC insured caps**, **FINTRAC AML rules**, and **PIPEDA privacy mandates**[cite: 1, 2]:
* **Target STP Rate:** 75% of prime salaried intake (45% overall STP) with `< 15 minute` automated conditional commitment letters[cite: 1].
* **Projected Business Impact:** `$1.50M/yr` net benefit on a `$1.20M` build (`~9.6-month` payback), recovering `+385` funded loans annually[cite: 1].

---

## Repository Structure
```text
├── architecture/
│   ├── exports/
│   │   ├── 01-capability-value-stream-map.png   # ArchiMate 3.x Capability Heatmap & Value Stream
│   │   └── As-Is-bpmn.png                       # BPMN 2.0 Current-State Bottleneck Process Map
│   └── source/
│       ├── maple-crest-ea.archimate             # Native Archi model file
│       └── As-Is_Process_Map.bpmn               # Native Camunda/BPMN 2.0 source file
├── docs/
│   ├── Maple Crest Bank — Streamlined Mortgage Triage BRD (Weekend Edition).pdf
│   └── 02-rtm-and-decisions.md                  # Requirements Traceability Matrix & ADRs
└── requirements.txt                             # Python environment for Phase 2 simulation
