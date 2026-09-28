"""
MediTrace Academic Capstone Project
Test Suite: Dataset & Analytics Pipeline

Tests:
8. Dataset loading & integrity
9. Analytics execution & feature engineering
10. Risk-score generation & classification
"""

import os
import sys
import unittest
import pandas as pd

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from analytics.generate_dataset import generate_hospital_medicine_dataset
from analytics.analytics import MediTraceAnalytics


class TestAnalyticsPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_csv = os.path.join(project_root, "analytics", "test_hospital_medicine_data.csv")
        cls.test_db = os.path.join(project_root, "database", "test_analytics.db")
        cls.test_results = os.path.join(project_root, "results", "test_results")

        # Generate a small 100-record test dataset
        generate_hospital_medicine_dataset(
            num_records=100,
            output_csv_path=cls.test_csv,
            random_seed=42
        )
        cls.analytics = MediTraceAnalytics(
            data_path=cls.test_csv,
            db_path=cls.test_db,
            results_dir=cls.test_results
        )

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_csv):
            try:
                os.remove(cls.test_csv)
            except Exception:
                pass
        if os.path.exists(cls.test_db):
            try:
                os.remove(cls.test_db)
            except Exception:
                pass

    def test_08_dataset_loading(self):
        """Test 8: Dataset loading, structure and column validation."""
        df = self.analytics.load_and_clean_data()
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 100)
        
        required_cols = [
            "transaction_id", "hospital_id", "medicine_id", "batch_id",
            "supplier_id", "quantity", "unit_price", "delivery_days",
            "temperature", "expiry_days", "transaction_date"
        ]
        for col in required_cols:
            self.assertIn(col, df.columns)

    def test_09_analytics_execution(self):
        """Test 9: Feature engineering and Isolation Forest anomaly detection execution."""
        df, feature_cols = self.analytics.engineer_features()
        self.assertIn("supplier_frequency", df.columns)
        self.assertIn("medicine_frequency", df.columns)
        self.assertEqual(len(feature_cols), 7)

        processed_df = self.analytics.train_anomaly_detection()
        self.assertIn("is_anomaly", processed_df.columns)
        self.assertIn("raw_decision_score", processed_df.columns)
        self.assertIn("risk_score", processed_df.columns)
        self.assertIn("risk_level", processed_df.columns)

    def test_10_risk_score_generation(self):
        """Test 10: Risk score range (0-100) and risk level categories (Low, Medium, High)."""
        df = self.analytics.processed_df
        min_risk = df["risk_score"].min()
        max_risk = df["risk_score"].max()
        
        self.assertGreaterEqual(min_risk, 0.0)
        self.assertLessEqual(max_risk, 100.0)

        # Check categories
        valid_levels = {"Low Risk", "Medium Risk", "High Risk"}
        actual_levels = set(df["risk_level"].unique())
        self.assertTrue(actual_levels.issubset(valid_levels))

        # Check summary metrics
        _, _, summary = self.analytics.compute_aggregates_and_summaries()
        self.assertEqual(summary["total_transaction_count"], 100)
        self.assertGreaterEqual(summary["anomaly_count"], 0)
        self.assertGreaterEqual(summary["average_risk_score"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
