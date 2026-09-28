"""
MediTrace Academic Capstone Project
Backend Application Engine & API Service

Orchestrates:
1. Analytics execution & SQLite database sync
2. Blockchain service integration (Registration, Custody Transfers, Traceability)
3. SHA-256 Hash Verification & Counterfeit Tamper-Detection
4. Unified API and programmatic interface for the Streamlit dashboard
"""

import os
import sys
import json
import sqlite3
from typing import Dict, Any, List, Optional
import pandas as pd

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from analytics.analytics import MediTraceAnalytics
from backend.blockchain_service import MediTraceBlockchainService


class MediTraceBackend:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = base_dir
        self.db_path = os.path.join(base_dir, "database", "meditrace.db")
        self.results_dir = os.path.join(base_dir, "results")
        
        self.analytics = MediTraceAnalytics(db_path=self.db_path, results_dir=self.results_dir)
        self.blockchain = MediTraceBlockchainService(db_path=self.db_path)

    def initialize_system(self):
        """Initializes dataset, analytics pipeline, and seeds blockchain state."""
        print("[MediTrace Backend] Initializing MediTrace System...")
        # 1. Run analytics pipeline
        self.analytics.run_full_pipeline()
        # 2. Seed initial blockchain batches from dataset
        self.blockchain.seed_initial_blockchain_from_dataset()
        print("[MediTrace Backend] Initialization completed successfully.")

    def get_dashboard_kpis(self) -> Dict[str, Any]:
        """Calculates key performance metrics for the main dashboard display."""
        summary_file = os.path.join(self.results_dir, "analytics_summary.json")
        if os.path.exists(summary_file):
            with open(summary_file, "r") as f:
                metrics = json.load(f)
        else:
            metrics = {
                "total_transaction_count": 0,
                "anomaly_count": 0,
                "anomaly_percentage": 0.0,
                "low_risk_count": 0,
                "medium_risk_count": 0,
                "high_risk_count": 0,
                "average_risk_score": 0.0
            }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM blockchain_batches WHERE exists_flag = 1")
        total_batches = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM blockchain_transactions")
        total_chain_txns = cursor.fetchone()[0]
        conn.close()

        metrics["total_batches_onchain"] = total_batches
        metrics["total_blockchain_transactions"] = total_chain_txns
        return metrics

    def get_hospital_transactions(self, limit: int = 1000, filter_risk: Optional[str] = None) -> pd.DataFrame:
        """Retrieves hospital medicine transactions from SQLite database."""
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM hospital_transactions"
        params = []
        if filter_risk:
            query += " WHERE risk_level = ?"
            params.append(filter_risk)
        query += " ORDER BY transaction_date DESC, transaction_id DESC LIMIT ?"
        params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    def get_high_risk_transactions(self, limit: int = 50) -> pd.DataFrame:
        """Retrieves top high-risk / suspicious transactions."""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT transaction_id, hospital_id, medicine_id, batch_id, supplier_id,
                   quantity, unit_price, delivery_days, temperature, expiry_days,
                   transaction_date, risk_score, risk_level
            FROM hospital_transactions
            WHERE risk_level = 'High Risk' OR is_anomaly = 1
            ORDER BY risk_score DESC, transaction_date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=[limit])
        conn.close()
        return df

    def get_supplier_risk_table(self) -> pd.DataFrame:
        """Loads supplier risk statistics from result CSV or database."""
        sup_path = os.path.join(self.results_dir, "supplier_risk_analysis.csv")
        if os.path.exists(sup_path):
            return pd.read_csv(sup_path)
        
        # Fallback to database query
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("""
            SELECT supplier_id,
                   COUNT(*) as total_transactions,
                   SUM(is_anomaly) as suspicious_transactions,
                   ROUND(AVG(risk_score), 2) as avg_risk_score,
                   SUM(CASE WHEN risk_level = 'High Risk' THEN 1 ELSE 0 END) as high_risk_count
            FROM hospital_transactions
            GROUP BY supplier_id
            ORDER BY avg_risk_score DESC
        """, conn)
        conn.close()
        return df

    def get_medicine_risk_table(self) -> pd.DataFrame:
        """Loads medicine risk statistics from result CSV or database."""
        med_path = os.path.join(self.results_dir, "medicine_risk_results.csv")
        if os.path.exists(med_path):
            return pd.read_csv(med_path)
        
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("""
            SELECT medicine_id,
                   COUNT(*) as total_transactions,
                   SUM(is_anomaly) as suspicious_transactions,
                   ROUND(AVG(unit_price), 2) as avg_unit_price,
                   ROUND(AVG(risk_score), 2) as avg_risk_score,
                   SUM(CASE WHEN risk_level = 'High Risk' THEN 1 ELSE 0 END) as high_risk_count
            FROM hospital_transactions
            GROUP BY medicine_id
            ORDER BY avg_risk_score DESC
        """, conn)
        conn.close()
        return df

    def search_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Queries blockchain and database for end-to-end traceability of a batch.
        """
        batch_info = self.blockchain.get_batch(batch_id)
        history = self.blockchain.get_batch_history(batch_id)

        # Retrieve related hospital transactions
        conn = sqlite3.connect(self.db_path)
        tx_df = pd.read_sql_query(
            "SELECT * FROM hospital_transactions WHERE batch_id = ? ORDER BY transaction_date ASC",
            conn,
            params=[batch_id]
        )
        conn.close()

        return {
            "found": batch_info is not None,
            "batch_info": batch_info,
            "blockchain_history": history,
            "hospital_transactions": tx_df.to_dict(orient="records")
        }

    def register_new_batch_and_txn(
        self,
        batch_id: str,
        medicine_id: str,
        supplier_id: str,
        hospital_id: str,
        quantity: int,
        unit_price: float,
        delivery_days: int,
        temperature: float,
        expiry_days: int,
        transaction_date: str
    ) -> Dict[str, Any]:
        """
        End-to-End Workflow:
        1. Build transaction record
        2. Generate SHA-256 data hash
        3. Register batch and genesis transaction on blockchain
        4. Save off-chain transaction record in SQLite
        5. Return status and hashes
        """
        import uuid
        txn_id = f"TXN-{uuid.uuid4().hex[:6].upper()}"

        record = {
            "transaction_id": txn_id,
            "hospital_id": hospital_id,
            "medicine_id": medicine_id,
            "batch_id": batch_id,
            "supplier_id": supplier_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "delivery_days": delivery_days,
            "temperature": temperature,
            "expiry_days": expiry_days,
            "transaction_date": transaction_date
        }

        # 1. Generate SHA-256 hash
        data_hash = self.blockchain.generate_sha256_hash(record)

        # 2. Register on Blockchain
        chain_res = self.blockchain.register_batch(
            batch_id=batch_id,
            medicine_id=medicine_id,
            manufacturer=supplier_id,
            quantity=quantity,
            data_hash=data_hash
        )

        # 3. Store off-chain in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hospital_transactions (
                transaction_id, hospital_id, medicine_id, batch_id, supplier_id,
                quantity, unit_price, delivery_days, temperature, expiry_days,
                transaction_date, is_anomaly, risk_score, risk_level, data_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 15.0, 'Low Risk', ?)
        """, (
            txn_id, hospital_id, medicine_id, batch_id, supplier_id,
            quantity, unit_price, delivery_days, temperature, expiry_days,
            transaction_date, data_hash
        ))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "transaction_id": txn_id,
            "batch_id": batch_id,
            "data_hash": data_hash,
            "blockchain_result": chain_res
        }

    def transfer_batch_custody(
        self,
        batch_id: str,
        new_owner: str,
        quantity: int,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Executes ownership transfer on blockchain with off-chain hash generation."""
        # Create transfer record hash
        current_time = pd.Timestamp.now().isoformat()
        tx_payload = f"TRANSFER|{batch_id}|{new_owner}|{quantity}|{current_time}|{notes}"
        import hashlib
        data_hash = hashlib.sha256(tx_payload.encode()).hexdigest()

        chain_res = self.blockchain.transfer_batch(
            batch_id=batch_id,
            new_owner=new_owner,
            quantity=quantity,
            data_hash=data_hash
        )
        return chain_res

    def verify_hash(self, transaction_id: str) -> Dict[str, Any]:
        """Verifies off-chain record hash vs blockchain hash for tamper detection."""
        return self.blockchain.verify_transaction_integrity(transaction_id)


if __name__ == "__main__":
    app = MediTraceBackend()
    app.initialize_system()
    kpis = app.get_dashboard_kpis()
    print("Dashboard KPIs:", kpis)
