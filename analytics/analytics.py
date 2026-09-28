"""
MediTrace Academic Capstone Project
Analytics Engine: Anomaly Detection & Counterfeit Risk Scoring

Implements:
1. Data loading & validation
2. Missing value & cleaning checks
3. Descriptive statistics
4. Feature engineering (supplier_frequency, medicine_frequency)
5. Standardization (StandardScaler)
6. Isolation Forest unsupervised anomaly detection
7. Risk score calculation (0 - 100 scale)
8. Academic Risk Level Classification:
   - Low Risk: 0 - 30
   - Medium Risk: 31 - 60
   - High Risk: 61 - 100
9. Summary metrics & CSV / visualization chart exports

Academic Disclaimer:
The anomaly detection model flags anomalous supply-chain patterns and produces an
academic risk index. It does not provide definitive biochemical or clinical proof of counterfeit drugs.
"""

import os
import json
import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use('Agg') # Headless rendering
import matplotlib.pyplot as plt
import seaborn as sns

class MediTraceAnalytics:
    def __init__(self, data_path=None, db_path=None, results_dir=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = data_path or os.path.join(base_dir, "analytics", "hospital_medicine_data.csv")
        self.db_path = db_path or os.path.join(base_dir, "database", "meditrace.db")
        self.results_dir = results_dir or os.path.join(base_dir, "results")
        
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self.df = None
        self.processed_df = None
        self.model = None
        self.scaler = None
        self.metrics_summary = {}

    def load_and_clean_data(self):
        """Loads dataset, inspects missing values, cleans and prepares dataframe."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Dataset file not found at: {self.data_path}. Please run generate_dataset.py first.")
        
        self.df = pd.read_csv(self.data_path)
        print(f"[Analytics] Loaded {len(self.df)} records from {self.data_path}")

        # Check missing values
        missing_counts = self.df.isnull().sum()
        if missing_counts.sum() > 0:
            print("[Analytics] Handling missing values via imputation/drop...")
            self.df = self.df.dropna()

        # Type validations
        self.df["quantity"] = pd.to_numeric(self.df["quantity"], errors="coerce").fillna(0).astype(int)
        self.df["unit_price"] = pd.to_numeric(self.df["unit_price"], errors="coerce").fillna(0.0).astype(float)
        self.df["delivery_days"] = pd.to_numeric(self.df["delivery_days"], errors="coerce").fillna(0).astype(int)
        self.df["temperature"] = pd.to_numeric(self.df["temperature"], errors="coerce").fillna(0.0).astype(float)
        self.df["expiry_days"] = pd.to_numeric(self.df["expiry_days"], errors="coerce").fillna(0).astype(int)

        return self.df

    def engineer_features(self):
        """Calculates frequency features and prepares feature matrix."""
        df = self.df.copy()

        # Frequency encoding
        supplier_counts = df["supplier_id"].value_counts()
        medicine_counts = df["medicine_id"].value_counts()

        df["supplier_frequency"] = df["supplier_id"].map(supplier_counts)
        df["medicine_frequency"] = df["medicine_id"].map(medicine_counts)

        feature_cols = [
            "quantity",
            "unit_price",
            "delivery_days",
            "temperature",
            "expiry_days",
            "supplier_frequency",
            "medicine_frequency"
        ]

        self.feature_cols = feature_cols
        self.processed_df = df
        return df, feature_cols

    def train_anomaly_detection(self, contamination=0.10, random_state=42):
        """
        Standardizes features and trains Isolation Forest model for unsupervised anomaly detection.
        Computes normalized risk scores (0 to 100) and classifies risk levels.
        """
        if self.processed_df is None:
            self.engineer_features()

        X = self.processed_df[self.feature_cols].values

        # Feature Standardization
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Isolation Forest
        self.model = IsolationForest(
            n_estimators=150,
            contamination=contamination,
            max_samples='auto',
            random_state=random_state,
            n_jobs=-1
        )
        self.model.fit(X_scaled)

        # Predict: -1 for anomaly, 1 for normal
        raw_preds = self.model.predict(X_scaled)
        decision_scores = self.model.decision_function(X_scaled)

        # Anomaly Flag: 1 for Suspicious / Anomaly, 0 for Normal
        self.processed_df["is_anomaly"] = np.where(raw_preds == -1, 1, 0)
        self.processed_df["raw_decision_score"] = decision_scores

        # Normalize Risk Score to 0 - 100
        # Decision function is lower (more negative) for anomalies, higher for normal points.
        # We invert it: min decision score -> max risk (100), max decision score -> min risk (0)
        min_score = decision_scores.min()
        max_score = decision_scores.max()
        score_range = max_score - min_score if (max_score - min_score) > 0 else 1.0

        normalized_risk = (max_score - decision_scores) / score_range * 100.0
        self.processed_df["risk_score"] = np.round(normalized_risk, 2)

        # Assign Risk Category (Academic Thresholds)
        # 0 - 30: Low Risk
        # 31 - 60: Medium Risk
        # 61 - 100: High Risk
        def categorize_risk(score):
            if score <= 30.0:
                return "Low Risk"
            elif score <= 60.0:
                return "Medium Risk"
            else:
                return "High Risk"

        self.processed_df["risk_level"] = self.processed_df["risk_score"].apply(categorize_risk)
        return self.processed_df

    def compute_aggregates_and_summaries(self):
        """Generates supplier risk stats, medicine risk stats, and overall project metrics."""
        df = self.processed_df

        # Overall counts
        total_txns = int(len(df))
        anomaly_count = int(df["is_anomaly"].sum())
        anomaly_pct = round((anomaly_count / total_txns) * 100.0, 2)

        risk_counts = df["risk_level"].value_counts().to_dict()
        low_risk_count = int(risk_counts.get("Low Risk", 0))
        med_risk_count = int(risk_counts.get("Medium Risk", 0))
        high_risk_count = int(risk_counts.get("High Risk", 0))
        avg_risk_score = round(float(df["risk_score"].mean()), 2)

        # Supplier Risk Table
        supplier_summary = df.groupby("supplier_id").agg(
            total_transactions=("transaction_id", "count"),
            suspicious_transactions=("is_anomaly", "sum"),
            avg_risk_score=("risk_score", "mean"),
            high_risk_count=("risk_level", lambda x: (x == "High Risk").sum()),
            avg_delivery_days=("delivery_days", "mean"),
            avg_temperature=("temperature", "mean")
        ).reset_index()

        supplier_summary["avg_risk_score"] = supplier_summary["avg_risk_score"].round(2)
        supplier_summary["avg_delivery_days"] = supplier_summary["avg_delivery_days"].round(1)
        supplier_summary["avg_temperature"] = supplier_summary["avg_temperature"].round(2)
        supplier_summary["suspicion_rate_pct"] = (
            (supplier_summary["suspicious_transactions"] / supplier_summary["total_transactions"]) * 100
        ).round(2)
        supplier_summary = supplier_summary.sort_values(by="avg_risk_score", ascending=False)

        # Medicine Risk Table
        medicine_summary = df.groupby("medicine_id").agg(
            total_transactions=("transaction_id", "count"),
            suspicious_transactions=("is_anomaly", "sum"),
            avg_unit_price=("unit_price", "mean"),
            avg_risk_score=("risk_score", "mean"),
            high_risk_count=("risk_level", lambda x: (x == "High Risk").sum()),
            avg_temperature=("temperature", "mean")
        ).reset_index()

        medicine_summary["avg_unit_price"] = medicine_summary["avg_unit_price"].round(2)
        medicine_summary["avg_risk_score"] = medicine_summary["avg_risk_score"].round(2)
        medicine_summary["avg_temperature"] = medicine_summary["avg_temperature"].round(2)
        medicine_summary["suspicion_rate_pct"] = (
            (medicine_summary["suspicious_transactions"] / medicine_summary["total_transactions"]) * 100
        ).round(2)
        medicine_summary = medicine_summary.sort_values(by="avg_risk_score", ascending=False)

        # Store summaries
        self.metrics_summary = {
            "total_transaction_count": total_txns,
            "anomaly_count": anomaly_count,
            "anomaly_percentage": anomaly_pct,
            "low_risk_count": low_risk_count,
            "medium_risk_count": med_risk_count,
            "high_risk_count": high_risk_count,
            "average_risk_score": avg_risk_score,
            "evaluation_timestamp": pd.Timestamp.now().isoformat()
        }

        # Save CSV results
        sup_csv_path = os.path.join(self.results_dir, "supplier_risk_analysis.csv")
        med_csv_path = os.path.join(self.results_dir, "medicine_risk_results.csv")
        summary_json_path = os.path.join(self.results_dir, "analytics_summary.json")

        supplier_summary.to_csv(sup_csv_path, index=False)
        medicine_summary.to_csv(med_csv_path, index=False)

        with open(summary_json_path, "w") as f:
            json.dump(self.metrics_summary, f, indent=4)

        print(f"[Analytics] Exported supplier risk analysis -> {sup_csv_path}")
        print(f"[Analytics] Exported medicine risk results -> {med_csv_path}")
        print(f"[Analytics] Exported summary JSON -> {summary_json_path}")

        return supplier_summary, medicine_summary, self.metrics_summary

    def generate_visualizations(self):
        """Generates risk score distribution and supplier risk charts."""
        df = self.processed_df
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Subplot 1: Risk Score Distribution Histogram & KDE
        sns.histplot(
            df["risk_score"],
            bins=30,
            kde=True,
            ax=axes[0],
            color="#2563EB",
            edgecolor="white"
        )
        axes[0].axvline(30, color="#10B981", linestyle="--", linewidth=1.5, label="Low / Med Threshold (30)")
        axes[0].axvline(60, color="#EF4444", linestyle="--", linewidth=1.5, label="Med / High Threshold (60)")
        axes[0].set_title("MediTrace Risk Score Distribution (0-100)", fontsize=12, fontweight="bold")
        axes[0].set_xlabel("Computed Anomaly Risk Score")
        axes[0].set_ylabel("Transaction Count")
        axes[0].legend(loc="upper right")
        axes[0].grid(axis="y", alpha=0.3)

        # Subplot 2: Risk Level Category Count Bar Chart
        level_order = ["Low Risk", "Medium Risk", "High Risk"]
        palette = {"Low Risk": "#10B981", "Medium Risk": "#F59E0B", "High Risk": "#EF4444"}
        sns.countplot(
            data=df,
            x="risk_level",
            hue="risk_level",
            legend=False,
            order=level_order,
            palette=palette,
            ax=axes[1],
            edgecolor="black",
            linewidth=0.5
        )
        axes[1].set_title("Transaction Count by Risk Level", fontsize=12, fontweight="bold")
        axes[1].set_xlabel("Academic Risk Category")
        axes[1].set_ylabel("Number of Transactions")
        axes[1].grid(axis="y", alpha=0.3)

        for p in axes[1].patches:
            height = p.get_height()
            if not np.isnan(height) and height > 0:
                axes[1].annotate(f"{int(height)}",
                                 (p.get_x() + p.get_width() / 2., height / 2),
                                 ha='center', va='center', fontsize=11, color='white', fontweight='bold')

        plt.tight_layout()
        chart_path = os.path.join(self.results_dir, "risk_score_distribution.png")
        plt.savefig(chart_path, dpi=300)
        plt.close()
        print(f"[Analytics] Saved visualization chart -> {chart_path}")
        return chart_path

    def sync_to_sqlite(self):
        """Synchronizes hospital medicine transactions and computed analytics results to SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create table for hospital transactions + analytics
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

        # Compute SHA-256 hash for each off-chain transaction record to ensure tamper verification
        import hashlib
        def compute_row_hash(row):
            payload = f"{row['transaction_id']}|{row['hospital_id']}|{row['medicine_id']}|{row['batch_id']}|{row['supplier_id']}|{row['quantity']}|{row['unit_price']:.2f}|{row['delivery_days']}|{row['temperature']:.2f}|{row['expiry_days']}|{row['transaction_date']}"
            return hashlib.sha256(payload.encode('utf-8')).hexdigest()

        df_to_save = self.processed_df.copy()
        df_to_save["data_hash"] = df_to_save.apply(compute_row_hash, axis=1)

        # Write to SQLite
        df_to_save.to_sql("hospital_transactions", conn, if_exists="replace", index=False)
        conn.commit()
        conn.close()
        print(f"[Database] Synchronized {len(df_to_save)} records into SQLite: {self.db_path}")
        return df_to_save

    def run_full_pipeline(self):
        """Executes the complete end-to-end data analytics and risk scoring workflow."""
        print("=== Running MediTrace Analytics Pipeline ===")
        self.load_and_clean_data()
        self.engineer_features()
        self.train_anomaly_detection()
        self.compute_aggregates_and_summaries()
        self.generate_visualizations()
        synced_df = self.sync_to_sqlite()
        print("=== Analytics Pipeline Completed Successfully ===")
        return synced_df, self.metrics_summary

if __name__ == "__main__":
    analytics = MediTraceAnalytics()
    analytics.run_full_pipeline()
