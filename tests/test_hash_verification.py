"""
MediTrace Academic Capstone Project
Test Suite: SHA-256 Hash Verification & Tamper Detection

Tests:
7. Hash verification (Valid off-chain vs Blockchain comparison, and Invalid tamper-detection)
"""

import os
import sys
import unittest
import hashlib
import sqlite3

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.blockchain_service import MediTraceBlockchainService


class TestHashVerification(unittest.TestCase):
    def setUp(self):
        self.test_db = os.path.join(project_root, "database", "test_hash_verify.db")
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.service = MediTraceBlockchainService(db_path=self.test_db)

        # Set up a mock off-chain record
        self.sample_record = {
            "transaction_id": "TXN-TEST-777",
            "hospital_id": "HOSP-CENTRAL-01",
            "medicine_id": "MED-INSULIN",
            "batch_id": "BATCH-TEST-777",
            "supplier_id": "SUP-PHARMAPLUS",
            "quantity": 250,
            "unit_price": 45.00,
            "delivery_days": 3,
            "temperature": 4.20,
            "expiry_days": 365,
            "transaction_date": "2026-09-24"
        }

        # Compute SHA-256 hash
        self.correct_hash = self.service.generate_sha256_hash(self.sample_record)

        # Store in on-chain ledger
        self.service.register_batch(
            batch_id="BATCH-TEST-777",
            medicine_id="MED-INSULIN",
            manufacturer="SUP-PHARMAPLUS",
            quantity=250,
            data_hash=self.correct_hash
        )

        # Store in off-chain SQLite table
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hospital_transactions (
                transaction_id TEXT PRIMARY KEY,
                hospital_id TEXT,
                medicine_id TEXT,
                batch_id TEXT,
                supplier_id TEXT,
                quantity INTEGER,
                unit_price REAL,
                delivery_days INTEGER,
                temperature REAL,
                expiry_days INTEGER,
                transaction_date TEXT,
                is_anomaly INTEGER,
                risk_score REAL,
                risk_level TEXT,
                data_hash TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO hospital_transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 12.5, 'Low Risk', ?)
        """, (
            self.sample_record["transaction_id"],
            self.sample_record["hospital_id"],
            self.sample_record["medicine_id"],
            self.sample_record["batch_id"],
            self.sample_record["supplier_id"],
            self.sample_record["quantity"],
            self.sample_record["unit_price"],
            self.sample_record["delivery_days"],
            self.sample_record["temperature"],
            self.sample_record["expiry_days"],
            self.sample_record["transaction_date"],
            self.correct_hash
        ))
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except Exception:
                pass

    def test_07_hash_verification_valid(self):
        """Test 7A: Verifies untampered off-chain transaction returns status VALID."""
        res = self.service.verify_transaction_integrity("TXN-TEST-777")
        self.assertEqual(res["status"], "VALID")
        self.assertTrue(res["valid"])
        self.assertFalse(res["tamper_detected"])
        self.assertEqual(res["offchain_recomputed_hash"], res["blockchain_stored_hash"])

    def test_07_hash_verification_tampered_invalid(self):
        """Test 7B: Simulates off-chain database tampering (altering temperature) and verifies status INVALID."""
        # Tamper with temperature in SQLite
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("UPDATE hospital_transactions SET temperature = 35.50 WHERE transaction_id = 'TXN-TEST-777'")
        conn.commit()
        conn.close()

        res = self.service.verify_transaction_integrity("TXN-TEST-777")
        self.assertEqual(res["status"], "INVALID")
        self.assertFalse(res["valid"])
        self.assertTrue(res["tamper_detected"])
        self.assertNotEqual(res["offchain_recomputed_hash"], res["blockchain_stored_hash"])
        self.assertIn("ALERT: Hash Mismatch Detected", res["verification_message"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
