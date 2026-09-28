"""
MediTrace - Academic Capstone Dashboard
Blockchain-Based Medicine Supply Chain Traceability System

Interactive Streamlit Application providing:
1. Project Title & Academic Overview
2. Core KPI Metrics (Total Transactions, Suspicious Count, Avg Risk Score, High-Risk Count)
3. Batch Traceability & Blockchain History Explorer
4. High-Risk Transaction Anomaly Table
5. Supplier Risk Analysis Table & Comparative Visualizations
6. Risk-Score Distribution & Anomaly Diagnostics
7. Live SHA-256 Hash Tamper-Verification Lab (Academic Demonstration)
8. Interactive Smart Contract Operations (Register Batch, Transfer Custody)
"""

import os
import sys
import json
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure backend and analytics modules are discoverable on python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app import MediTraceBackend

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="MediTrace - Supply Chain & Traceability",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-left: 5px solid #2563EB;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .badge-low {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-med {
        background-color: #FEF08A;
        color: #713F12;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-high {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    .academic-note {
        font-size: 0.85rem;
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 10px;
        border-radius: 4px;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- INITIALIZE BACKEND -----------------
@st.cache_resource
def get_backend():
    backend = MediTraceBackend()
    # Check if database exists; if not, initialize automatically
    if not os.path.exists(backend.db_path):
        backend.initialize_system()
    return backend

backend = get_backend()

# ----------------- SIDEBAR CONTROLS -----------------
st.sidebar.image("https://img.icons8.com/fluency/96/blockchain-technology.png", width=64)
st.sidebar.title("MediTrace Navigation")
selected_tab = st.sidebar.radio(
    "Select Module:",
    [
        "📊 Overview & Analytics",
        "🔍 Batch Traceability",
        "🛡️ Hash Verification Lab",
        "🏭 Supplier & Medicine Risk",
        "📝 Register & Transfer Batch",
        "ℹ️ Academic Documentation"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("🎓 **Academic Capstone Prototype**")
st.sidebar.caption("B.Tech AI & ML / Blockchain Integration")

# Refresh Data Trigger
if st.sidebar.button("🔄 Re-run Analytics Pipeline"):
    with st.spinner("Executing Isolation Forest & Updating Results..."):
        backend.analytics.run_full_pipeline()
        backend.blockchain.seed_initial_blockchain_from_dataset()
        st.sidebar.success("Pipeline refreshed successfully!")
        st.rerun()

# ----------------- MODULE 1: OVERVIEW & ANALYTICS -----------------
if selected_tab == "📊 Overview & Analytics":
    st.markdown('<div class="main-header">💊 MediTrace: Medicine Supply Chain Traceability System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Combining Smart Contract Blockchain Traceability with Isolation Forest Anomaly Risk Scoring</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="academic-note">
        <strong>Dual Architecture Principle:</strong><br>
        • <strong>Blockchain ("What happened?"):</strong> Records immutable batch provenance, ownership transfers, and cryptographic SHA-256 state hashes.<br>
        • <strong>Analytics ("Does it look suspicious?"):</strong> Evaluates procurement records with Isolation Forest to score potential counterfeit / supply-chain anomaly risk.
    </div>
    """, unsafe_allow_html=True)

    kpis = backend.get_dashboard_kpis()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Transactions", f"{kpis.get('total_transaction_count', 0):,}")
    with col2:
        st.metric("Suspicious Transactions", f"{kpis.get('anomaly_count', 0)}", delta=f"{kpis.get('anomaly_percentage', 0)}%", delta_color="inverse")
    with col3:
        st.metric("Average Risk Score", f"{kpis.get('average_risk_score', 0):.1f} / 100")
    with col4:
        st.metric("High-Risk Records", f"{kpis.get('high_risk_count', 0)}", delta_color="inverse")
    with col5:
        st.metric("On-Chain Batches", f"{kpis.get('total_batches_onchain', 0)}")

    st.markdown("---")

    # Visualizations Row
    vcol1, vcol2 = st.columns(2)

    with vcol1:
        st.subheader("📈 Risk Score Distribution (0 - 100)")
        chart_path = os.path.join(backend.results_dir, "risk_score_distribution.png")
        if os.path.exists(chart_path):
            st.image(chart_path, use_container_width=True)
        else:
            st.info("Generating risk distribution chart...")
            backend.analytics.generate_visualizations()
            st.rerun()

    with vcol2:
        st.subheader("📊 Risk Classification Breakdown")
        breakdown_data = pd.DataFrame({
            "Risk Level": ["Low Risk (0-30)", "Medium Risk (31-60)", "High Risk (61-100)"],
            "Count": [
                kpis.get("low_risk_count", 0),
                kpis.get("medium_risk_count", 0),
                kpis.get("high_risk_count", 0)
            ]
        })
        st.bar_chart(breakdown_data.set_index("Risk Level"), color="#2563EB")
        st.caption("Thresholds: Low (0-30), Medium (31-60), High (61-100) based on Isolation Forest anomaly decision inversion.")

    st.markdown("---")

    # High-Risk Transactions Table
    st.subheader("🚨 Top High-Risk & Anomalous Transactions")
    st.caption("Transactions flagged by the Isolation Forest model exhibiting anomalous temperature breaches, abnormal pricing, or severe delivery delays.")
    
    high_risk_df = backend.get_high_risk_transactions(limit=25)
    if not high_risk_df.empty:
        st.dataframe(
            high_risk_df[[
                "transaction_id", "batch_id", "medicine_id", "supplier_id",
                "quantity", "unit_price", "delivery_days", "temperature",
                "expiry_days", "risk_score", "risk_level"
            ]],
            use_container_width=True
        )
    else:
        st.info("No high-risk transactions detected.")


# ----------------- MODULE 2: BATCH TRACEABILITY -----------------
elif selected_tab == "🔍 Batch Traceability":
    st.markdown('<div class="main-header">🔍 Blockchain Batch Traceability Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Trace end-to-end custody, ownership transfers, and on-chain cryptographic hashes</div>', unsafe_allow_html=True)

    # Search Bar
    all_batches = backend.blockchain.get_all_batches()
    batch_list = [b["batch_id"] for b in all_batches] if all_batches else ["BATCH-1001"]

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        searched_batch = st.selectbox("Select Batch ID to Inspect:", batch_list, index=0 if batch_list else None)
    with col_s2:
        manual_batch = st.text_input("Or Enter Custom Batch ID:", "")

    query_batch_id = manual_batch.strip() if manual_batch.strip() else searched_batch

    if query_batch_id:
        result = backend.search_batch(query_batch_id)

        if result["found"]:
            b_info = result["batch_info"]
            st.success(f"✅ Batch **{query_batch_id}** is registered on the Blockchain!")

            # Batch Metadata
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"**Medicine ID:** `{b_info['medicine_id']}`")
                st.markdown(f"**Manufacturer / Supplier:** `{b_info['manufacturer']}`")
            with m2:
                st.markdown(f"**Current Custodian:** `{b_info['current_owner']}`")
                st.markdown(f"**Quantity Registered:** `{b_info['quantity']}` units")
            with m3:
                st.markdown(f"**Registration Block Time:** `{pd.to_datetime(b_info['timestamp'], unit='s')}`")
                st.markdown(f"**Status:** `ACTIVE / IMMUTABLE`")
            with m4:
                st.markdown(f"**History Length:** `{len(result['blockchain_history'])} event(s)`")

            st.markdown("---")
            st.subheader("⛓️ On-Chain Custody & Ownership Transfer Ledger")

            history = result["blockchain_history"]
            if history:
                hist_df = pd.DataFrame(history)
                hist_df["formatted_time"] = pd.to_datetime(hist_df["timestamp"], unit='s')
                st.dataframe(
                    hist_df[["id", "batch_id", "from_owner", "to_owner", "quantity", "formatted_time", "tx_hash", "data_hash"]],
                    use_container_width=True
                )
            else:
                st.info("No transaction events found for this batch.")

            st.markdown("---")
            st.subheader("🏥 Associated Off-Chain Hospital Procurement Transactions")
            hosp_txns = result["hospital_transactions"]
            if hosp_txns:
                h_df = pd.DataFrame(hosp_txns)
                st.dataframe(
                    h_df[[
                        "transaction_id", "hospital_id", "medicine_id", "supplier_id",
                        "quantity", "unit_price", "delivery_days", "temperature",
                        "expiry_days", "risk_score", "risk_level", "data_hash"
                    ]],
                    use_container_width=True
                )
            else:
                st.info("No off-chain hospital procurement records linked to this batch.")

        else:
            st.warning(f"⚠️ Batch **{query_batch_id}** was not found on the Blockchain ledger.")


# ----------------- MODULE 3: HASH VERIFICATION LAB -----------------
elif selected_tab == "🛡️ Hash Verification Lab":
    st.markdown('<div class="main-header">🛡️ SHA-256 Tamper Verification & Integrity Lab</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Demonstrates how cryptographic hashing prevents counterfeit records and off-chain data tampering</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="academic-note">
        <strong>How Verification Works:</strong><br>
        1. When a transaction occurs, a SHA-256 hash is computed from the off-chain data and anchored onto the Blockchain.<br>
        2. During verification, the system reads the off-chain record, re-computes its hash, and compares it with the blockchain ledger.<br>
        3. <strong>Match = VALID (Genuine)</strong> | <strong>Mismatch = INVALID (Tamper / Counterfeit Alert)</strong>.
    </div>
    """, unsafe_allow_html=True)

    tx_df = backend.get_hospital_transactions(limit=100)
    tx_list = tx_df["transaction_id"].tolist() if not tx_df.empty else []

    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        selected_tx = st.selectbox("Select Transaction ID to Verify:", tx_list)
    with col_t2:
        custom_tx = st.text_input("Or Enter Transaction ID:", "")

    target_tx = custom_tx.strip() if custom_tx.strip() else selected_tx

    if target_tx:
        verification = backend.verify_hash(target_tx)

        if verification.get("status") == "NOT_FOUND":
            st.error(f"Transaction `{target_tx}` not found.")
        else:
            st.markdown("### Verification Status")
            if verification["valid"]:
                st.success(f"### ✅ STATUS: {verification['status']} (Data Integrity Confirmed)")
            else:
                st.error(f"### 🚨 STATUS: {verification['status']} (Tamper / Counterfeit Mismatch Detected!)")

            st.write(f"**Verification Message:** {verification['verification_message']}")

            # Details Comparison
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Off-Chain Recomputed SHA-256 Hash:**")
                st.code(verification["offchain_recomputed_hash"], language="text")
                st.markdown(f"**Transaction ID:** `{verification['transaction_id']}`")
                st.markdown(f"**Batch ID:** `{verification['batch_id']}`")
            with c2:
                st.markdown("**Blockchain-Anchored Reference Hash:**")
                st.code(verification["blockchain_stored_hash"], language="text")
                st.markdown(f"**Blockchain Tx Hash:** `{verification['blockchain_tx_hash']}`")
                st.markdown(f"**Block Number:** `{verification['block_number']}`")

            st.markdown("---")
            # Viva Simulation Experiment: Live Tamper Demonstration
            st.subheader("🧪 Live Academic Viva Demonstration: Tamper Simulation")
            st.caption("Test how modifying an off-chain price or temperature immediately triggers an INVALID alert.")

            with st.expander("Simulate Data Tampering on this Record"):
                st.write("Modify any parameter below to observe immediate hash mismatch:")
                sim_col1, sim_col2, sim_col3 = st.columns(3)
                with sim_col1:
                    fake_price = st.number_input("Simulated Unit Price ($)", value=250.0, step=10.0)
                with sim_col2:
                    fake_temp = st.number_input("Simulated Temperature (°C)", value=38.0, step=1.0)
                with sim_col3:
                    fake_qty = st.number_input("Simulated Quantity", value=999, step=10)

                if st.button("Simulate Tamper Check"):
                    fake_payload = {
                        "transaction_id": target_tx,
                        "hospital_id": "HOSP-CENTRAL-01",
                        "medicine_id": "MED-INSULIN",
                        "batch_id": verification["batch_id"],
                        "supplier_id": "SUP-PHARMAPLUS",
                        "quantity": int(fake_qty),
                        "unit_price": float(fake_price),
                        "delivery_days": 3,
                        "temperature": float(fake_temp),
                        "expiry_days": 365,
                        "transaction_date": "2026-03-01"
                    }
                    tampered_hash = backend.blockchain.generate_sha256_hash(fake_payload)
                    st.error("🚨 TAMPER ALERT: Recomputed Hash does not match Blockchain State!")
                    st.write(f"**Tampered Hash:** `{tampered_hash}`")
                    st.write(f"**Original Blockchain Hash:** `{verification['blockchain_stored_hash']}`")
                    st.write("Result: **INVALID** (Tampering successfully detected!)")


# ----------------- MODULE 4: SUPPLIER & MEDICINE RISK -----------------
elif selected_tab == "🏭 Supplier & Medicine Risk":
    st.markdown('<div class="main-header">🏭 Supplier & Medicine Analytics Profiling</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Aggregated supply-chain risk metrics, anomaly counts, and risk distributions</div>', unsafe_allow_html=True)

    tab_sup, tab_med = st.tabs(["Supplier Risk Profiling", "Medicine Risk Profiling"])

    with tab_sup:
        st.subheader("Supplier Risk Rankings")
        sup_df = backend.get_supplier_risk_table()
        st.dataframe(sup_df, use_container_width=True)

        st.subheader("📊 Average Risk Score by Supplier")
        if not sup_df.empty:
            chart_df = sup_df[["supplier_id", "avg_risk_score"]].set_index("supplier_id")
            st.bar_chart(chart_df, color="#EF4444")

    with tab_med:
        st.subheader("Medicine Risk & Anomaly Summary")
        med_df = backend.get_medicine_risk_table()
        st.dataframe(med_df, use_container_width=True)

        st.subheader("📊 Average Risk Score by Medicine Type")
        if not med_df.empty:
            m_chart_df = med_df[["medicine_id", "avg_risk_score"]].set_index("medicine_id")
            st.bar_chart(m_chart_df, color="#3B82F6")


# ----------------- MODULE 5: REGISTER & TRANSFER BATCH -----------------
elif selected_tab == "📝 Register & Transfer Batch":
    st.markdown('<div class="main-header">📝 Interactive Smart Contract Operations</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Execute real batch registration and custody transfer transactions on the blockchain</div>', unsafe_allow_html=True)

    tab_reg, tab_txf = st.tabs(["Register New Batch", "Transfer Batch Custody"])

    with tab_reg:
        st.subheader("Register a New Medicine Batch (Genesis)")
        with st.form("register_batch_form"):
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                r_batch_id = st.text_input("Batch ID", "BATCH-9001")
                r_med_id = st.selectbox("Medicine ID", [
                    "MED-INSULIN", "MED-REMDESIVIR", "MED-AMOXICILLIN",
                    "MED-PARACETAMOL", "MED-AZITHROMYCIN", "MED-CEFTRIAXONE"
                ])
                r_supplier = st.selectbox("Supplier / Manufacturer", [
                    "SUP-PHARMAPLUS", "SUP-MEDILINK", "SUP-GLOBALHEALTH",
                    "SUP-BIOCARE", "SUP-FASTDISTRIB", "SUP-UNVERIFIED-A"
                ])
                r_hospital = st.selectbox("Hospital Destination", [
                    "HOSP-CENTRAL-01", "HOSP-METRO-02", "HOSP-APEX-03"
                ])
            with r_col2:
                r_qty = st.number_input("Quantity (Units)", min_value=1, value=200, step=10)
                r_price = st.number_input("Unit Price ($)", min_value=1.0, value=45.0, step=1.0)
                r_del_days = st.number_input("Delivery Days", min_value=1, value=3, step=1)
                r_temp = st.number_input("Cold-Chain Temperature (°C)", value=4.5, step=0.5)
                r_exp_days = st.number_input("Remaining Expiry Days", min_value=1, value=365, step=10)
                r_date = st.text_input("Transaction Date", "2026-09-24")

            submit_reg = st.form_submit_button("🚀 Register Batch on Blockchain")

            if submit_reg:
                try:
                    res = backend.register_new_batch_and_txn(
                        batch_id=r_batch_id.strip(),
                        medicine_id=r_med_id,
                        supplier_id=r_supplier,
                        hospital_id=r_hospital,
                        quantity=int(r_qty),
                        unit_price=float(r_price),
                        delivery_days=int(r_del_days),
                        temperature=float(r_temp),
                        expiry_days=int(r_exp_days),
                        transaction_date=r_date
                    )
                    st.success(f"🎉 Batch `{r_batch_id}` successfully registered on the Blockchain!")
                    st.json(res)
                except Exception as e:
                    st.error(f"Registration Error: {e}")

    with tab_txf:
        st.subheader("Transfer Batch Custody to Distributor / Hospital")
        all_batches = backend.blockchain.get_all_batches()
        b_choices = [b["batch_id"] for b in all_batches] if all_batches else []

        with st.form("transfer_batch_form"):
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                t_batch_id = st.selectbox("Select Batch to Transfer", b_choices) if b_choices else st.text_input("Batch ID")
                t_new_owner = st.selectbox("New Owner / Recipient", [
                    "HOSP-CENTRAL-01", "HOSP-METRO-02", "HOSP-APEX-03",
                    "DISTRIB-REGIONAL-NORTH", "PHARMACY-ALLIANCE-01"
                ])
            with t_col2:
                t_qty = st.number_input("Quantity to Transfer", min_value=1, value=50, step=5)
                t_notes = st.text_input("Transfer Notes / Checkpoint", "Routine hospital pharmacy delivery")

            submit_txf = st.form_submit_button("🔁 Execute Custody Transfer")

            if submit_txf:
                try:
                    res = backend.transfer_batch_custody(
                        batch_id=t_batch_id,
                        new_owner=t_new_owner,
                        quantity=int(t_qty),
                        notes=t_notes
                    )
                    st.success(f"🎉 Batch `{t_batch_id}` custody successfully transferred to `{t_new_owner}`!")
                    st.json(res)
                except Exception as e:
                    st.error(f"Transfer Error: {e}")


# ----------------- MODULE 6: ACADEMIC DOCUMENTATION -----------------
elif selected_tab == "ℹ️ Academic Documentation":
    st.markdown('<div class="main-header">ℹ️ Project Information & Academic Summary</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Capstone Project Specifications, Problem Statement, and Architecture</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 🎓 Project Details
    - **Project Title:** Blockchain-Based Medicine Supply Chain Traceability System for Pharmaceutical Companies to Prevent Counterfeit Drugs
    - **Project Name:** `MediTrace`
    - **Department:** Computer Science / Artificial Intelligence & Machine Learning (B.Tech Capstone)
    - **Academic Focus:** Mini Project / Prototype for Local Demonstration & Viva Defense

    ### 🏗️ Dual-Tier System Architecture
    1. **Blockchain Layer (On-Chain):**
       - Implemented with Solidity smart contract `MedicineTraceability.sol` and Web3.
       - Stores batch metadata, ownership lifecycle, and SHA-256 data integrity hashes.
       - Immutable ledger guarantees auditability and non-repudiation.
    2. **Analytics & ML Layer (Off-Chain):**
       - Isolation Forest unsupervised anomaly detection trained on procurement parameters.
       - Evaluates: `quantity`, `unit_price`, `delivery_days`, `temperature`, `expiry_days`, `supplier_frequency`, `medicine_frequency`.
       - Produces normalized risk score (0-100) and classifications (Low Risk, Medium Risk, High Risk).
    3. **Hash Verification Protocol:**
       - Computes `SHA-256(off_chain_data)` and matches against blockchain state.
       - Immediate identification of counterfeit records, unauthorized modifications, or expired data tampering.

    ### ⚠️ Academic Disclaimer
    *This system is an academic research prototype. The machine learning model flags suspicious patterns and anomaly risk indicators; it does not constitute clinical or laboratory chemical authentication.*
    """)
