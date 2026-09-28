"""
MediTrace Academic Capstone Project
Test Suite: Blockchain Smart Contract & Service Operations

Tests:
1. Valid batch registration
2. Duplicate batch rejection
3. Valid batch transfer
4. Invalid batch transfer (non-existent batch)
5. Excess quantity transfer rejection
6. Batch history retrieval
"""

import os
import sys
import unittest
import hashlib

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.blockchain_service import MediTraceBlockchainService


class TestBlockchainService(unittest.TestCase):
    def setUp(self):
        # Use a temporary test database to isolate tests
        self.test_db = os.path.join(project_root, "database", "test_meditrace.db")
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.service = MediTraceBlockchainService(db_path=self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except Exception:
                pass

    def test_01_valid_batch_registration(self):
        """Test 1: Valid batch registration onto the blockchain."""
        sample_hash = hashlib.sha256(b"genesis_payload_01").hexdigest()
        res = self.service.register_batch(
            batch_id="BATCH-TEST-001",
            medicine_id="MED-INSULIN",
            manufacturer="SUP-PHARMAPLUS",
            quantity=500,
            data_hash=sample_hash
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["action"], "BatchRegistered")
        self.assertEqual(res["batch_id"], "BATCH-TEST-001")

        # Verify state
        batch = self.service.get_batch("BATCH-TEST-001")
        self.assertIsNotNone(batch)
        self.assertEqual(batch["quantity"], 500)
        self.assertEqual(batch["current_owner"], "SUP-PHARMAPLUS")
        self.assertTrue(batch["exists"])

    def test_02_duplicate_batch_rejection(self):
        """Test 2: Rejection of duplicate batch registration."""
        sample_hash = hashlib.sha256(b"genesis_payload_02").hexdigest()
        self.service.register_batch("BATCH-TEST-002", "MED-PARACETAMOL", "SUP-MEDILINK", 300, sample_hash)

        # Attempt duplicate registration
        with self.assertRaises(ValueError) as ctx:
            self.service.register_batch("BATCH-TEST-002", "MED-PARACETAMOL", "SUP-MEDILINK", 300, sample_hash)
        self.assertIn("Duplicate Error", str(ctx.exception))

    def test_03_valid_batch_transfer(self):
        """Test 3: Valid custody transfer to downstream distributor/hospital."""
        sample_hash = hashlib.sha256(b"genesis_payload_03").hexdigest()
        self.service.register_batch("BATCH-TEST-003", "MED-REMDESIVIR", "SUP-GLOBALHEALTH", 400, sample_hash)

        transfer_hash = hashlib.sha256(b"transfer_payload_03").hexdigest()
        txf_res = self.service.transfer_batch(
            batch_id="BATCH-TEST-003",
            new_owner="HOSP-CENTRAL-01",
            quantity=200,
            data_hash=transfer_hash
        )
        self.assertTrue(txf_res["success"])
        self.assertEqual(txf_res["action"], "MedicineTransferred")
        self.assertEqual(txf_res["from_owner"], "SUP-GLOBALHEALTH")
        self.assertEqual(txf_res["to_owner"], "HOSP-CENTRAL-01")

        # Check updated current owner
        batch = self.service.get_batch("BATCH-TEST-003")
        self.assertEqual(batch["current_owner"], "HOSP-CENTRAL-01")

    def test_04_invalid_batch_transfer(self):
        """Test 4: Rejection of transfer for a non-existing batch."""
        sample_hash = hashlib.sha256(b"fake_payload").hexdigest()
        with self.assertRaises(ValueError) as ctx:
            self.service.transfer_batch("BATCH-NON-EXISTENT", "HOSP-APEX-03", 50, sample_hash)
        self.assertIn("does not exist", str(ctx.exception))

    def test_05_excess_quantity_transfer_rejection(self):
        """Test 5: Rejection of transfer when quantity exceeds available batch quantity."""
        sample_hash = hashlib.sha256(b"genesis_payload_05").hexdigest()
        self.service.register_batch("BATCH-TEST-005", "MED-AMOXICILLIN", "SUP-BIOCARE", 100, sample_hash)

        # Attempt to transfer 150 units when only 100 exist
        with self.assertRaises(ValueError) as ctx:
            self.service.transfer_batch("BATCH-TEST-005", "HOSP-CITY-04", 150, sample_hash)
        self.assertIn("exceeds available batch quantity", str(ctx.exception))

    def test_06_batch_history_retrieval(self):
        """Test 6: Retrieval of complete chronological custody history."""
        sample_hash = hashlib.sha256(b"genesis_payload_06").hexdigest()
        self.service.register_batch("BATCH-TEST-006", "MED-AZITHROMYCIN", "SUP-FASTDISTRIB", 500, sample_hash)

        # Execute 2 transfers
        h1 = hashlib.sha256(b"txf_1").hexdigest()
        self.service.transfer_batch("BATCH-TEST-006", "DISTRIB-NORTH", 200, h1)
        h2 = hashlib.sha256(b"txf_2").hexdigest()
        self.service.transfer_batch("BATCH-TEST-006", "HOSP-METRO-02", 100, h2)

        history = self.service.get_batch_history("BATCH-TEST-006")
        self.assertEqual(len(history), 3) # Genesis + 2 transfers
        self.assertEqual(history[0]["from_owner"], "GENESIS_MANUFACTURER")
        self.assertEqual(history[1]["to_owner"], "DISTRIB-NORTH")
        self.assertEqual(history[2]["to_owner"], "HOSP-METRO-02")


if __name__ == "__main__":
    unittest.main(verbosity=2)
