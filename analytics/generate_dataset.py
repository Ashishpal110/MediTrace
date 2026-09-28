"""
MediTrace Academic Capstone Project
Synthetic Hospital Medicine Dataset Generator

Generates a realistic synthetic dataset (~1000 records) representing
hospital medicine procurement and supply-chain transactions.

Academic Disclaimer:
This dataset is synthetically generated for academic demonstration and evaluation.
It does not represent real hospital patient records or real clinical data.
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def generate_hospital_medicine_dataset(
    num_records=1000,
    output_csv_path="hospital_medicine_data.csv",
    random_seed=42
):
    np.random.seed(random_seed)
    random.seed(random_seed)

    hospitals = [
        "HOSP-CENTRAL-01", "HOSP-METRO-02", "HOSP-APEX-03",
        "HOSP-CITY-04", "HOSP-MEMORIAL-05", "HOSP-VALLEY-06"
    ]

    medicines = [
        {"id": "MED-INSULIN", "type": "cold_chain", "base_price": 45.0, "temp_range": (2.0, 8.0)},
        {"id": "MED-REMDESIVIR", "type": "critical", "base_price": 120.0, "temp_range": (15.0, 25.0)},
        {"id": "MED-AMOXICILLIN", "type": "antibiotic", "base_price": 12.5, "temp_range": (15.0, 25.0)},
        {"id": "MED-PARACETAMOL", "type": "analgesic", "base_price": 4.0, "temp_range": (15.0, 25.0)},
        {"id": "MED-AZITHROMYCIN", "type": "antibiotic", "base_price": 22.0, "temp_range": (15.0, 25.0)},
        {"id": "MED-CEFTRIAXONE", "type": "critical", "base_price": 65.0, "temp_range": (15.0, 25.0)},
        {"id": "MED-ATORVASTATIN", "type": "cardio", "base_price": 18.0, "temp_range": (15.0, 25.0)},
        {"id": "MED-PANTOPRAZOLE", "type": "gastro", "base_price": 8.5, "temp_range": (15.0, 25.0)},
        {"id": "MED-VACCINE-COV", "type": "cold_chain", "base_price": 85.0, "temp_range": (2.0, 8.0)},
        {"id": "MED-HEPARIN", "type": "critical", "base_price": 55.0, "temp_range": (15.0, 25.0)},
    ]

    suppliers = [
        {"id": "SUP-PHARMAPLUS", "reliable": True, "weight": 0.25},
        {"id": "SUP-MEDILINK", "reliable": True, "weight": 0.22},
        {"id": "SUP-GLOBALHEALTH", "reliable": True, "weight": 0.20},
        {"id": "SUP-BIOCARE", "reliable": True, "weight": 0.15},
        {"id": "SUP-FASTDISTRIB", "reliable": True, "weight": 0.10},
        {"id": "SUP-UNVERIFIED-A", "reliable": False, "weight": 0.05},
        {"id": "SUP-SHADOWTRADE-B", "reliable": False, "weight": 0.03},
    ]

    supplier_ids = [s["id"] for s in suppliers]
    supplier_weights = [s["weight"] for s in suppliers]
    supplier_dict = {s["id"]: s for s in suppliers}

    base_date = datetime(2026, 1, 1)

    records = []
    
    # We will generate ~1000 records
    for i in range(1, num_records + 1):
        txn_id = f"TXN-{10000 + i}"
        batch_id = f"BATCH-{1000 + (i % 250) + 1}"
        hosp_id = random.choice(hospitals)
        med = random.choice(medicines)
        med_id = med["id"]
        sup_id = np.random.choice(supplier_ids, p=supplier_weights)
        sup_info = supplier_dict[sup_id]

        # Normal transaction date distribution
        days_offset = random.randint(0, 260)
        txn_date = (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")

        # Anomaly trigger probability (~8% to 10% realistic synthetic anomaly injection)
        is_anomalous_candidate = (not sup_info["reliable"]) or (random.random() < 0.06)

        if not is_anomalous_candidate:
            # Regular, normal procurement record
            quantity = int(np.random.normal(loc=150, scale=40))
            quantity = max(20, min(quantity, 400))

            price_jitter = np.random.normal(loc=1.0, scale=0.08)
            unit_price = round(med["base_price"] * price_jitter, 2)

            delivery_days = int(np.random.gamma(shape=2.5, scale=1.4)) + 1
            delivery_days = max(1, min(delivery_days, 10))

            t_min, t_max = med["temp_range"]
            temp_center = (t_min + t_max) / 2.0
            temperature = round(float(np.random.normal(loc=temp_center, scale=0.8)), 2)
            temperature = max(t_min - 0.5, min(temperature, t_max + 0.5))

            expiry_days = int(np.random.normal(loc=420, scale=90))
            expiry_days = max(120, min(expiry_days, 730))
        else:
            # Anomalous / Suspicious supply-chain characteristics (e.g., thermal breach, price dumping/gouging, severe delay, expired dump)
            anomaly_type = random.choice(["thermal_breach", "price_anomaly", "delivery_delay", "short_expiry", "bulk_irregularity"])

            if anomaly_type == "thermal_breach":
                # Temperature excursion (severe violation of cold chain)
                quantity = random.randint(50, 300)
                unit_price = round(med["base_price"] * random.uniform(0.9, 1.1), 2)
                delivery_days = random.randint(2, 8)
                if med["type"] == "cold_chain":
                    temperature = round(random.uniform(22.0, 38.5), 2)  # Critical cold chain failure
                else:
                    temperature = round(random.uniform(42.0, 55.0), 2)  # Severe overheating
                expiry_days = random.randint(180, 500)

            elif anomaly_type == "price_anomaly":
                # Severe undercutting (potential counterfeit indication) or extreme gouging
                quantity = random.randint(100, 450)
                multiplier = random.choice([0.15, 0.25, 4.5, 6.0])
                unit_price = round(med["base_price"] * multiplier, 2)
                delivery_days = random.randint(3, 14)
                temperature = round(random.uniform(med["temp_range"][0], med["temp_range"][1]), 2)
                expiry_days = random.randint(150, 450)

            elif anomaly_type == "delivery_delay":
                # Suspicious intermediate diversion / delay
                quantity = random.randint(50, 250)
                unit_price = round(med["base_price"] * random.uniform(0.9, 1.2), 2)
                delivery_days = random.randint(25, 65)  # Huge delay
                temperature = round(random.uniform(med["temp_range"][0] + 3, med["temp_range"][1] + 8), 2)
                expiry_days = random.randint(100, 350)

            elif anomaly_type == "short_expiry":
                # Near-expiry or expired medicine dump
                quantity = random.randint(200, 600)
                unit_price = round(med["base_price"] * random.uniform(0.3, 0.6), 2)
                delivery_days = random.randint(4, 12)
                temperature = round(random.uniform(med["temp_range"][0], med["temp_range"][1]), 2)
                expiry_days = random.randint(-5, 25)  # Near expiry / already expired

            else: # bulk_irregularity
                # Extreme quantity irregularity
                quantity = random.choice([5, 1800, 2500, 3200])
                unit_price = round(med["base_price"] * random.uniform(0.7, 1.4), 2)
                delivery_days = random.randint(8, 20)
                temperature = round(random.uniform(med["temp_range"][0], med["temp_range"][1]), 2)
                expiry_days = random.randint(80, 300)

        records.append({
            "transaction_id": txn_id,
            "hospital_id": hosp_id,
            "medicine_id": med_id,
            "batch_id": batch_id,
            "supplier_id": sup_id,
            "quantity": int(quantity),
            "unit_price": float(unit_price),
            "delivery_days": int(delivery_days),
            "temperature": float(temperature),
            "expiry_days": int(expiry_days),
            "transaction_date": txn_date
        })

    df = pd.DataFrame(records)
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_csv_path) or ".", exist_ok=True)
    df.to_csv(output_csv_path, index=False)
    print(f"[Dataset] Generated {len(df)} records saved to '{output_csv_path}'.")
    return df

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_csv = os.path.join(current_dir, "hospital_medicine_data.csv")
    generate_hospital_medicine_dataset(num_records=1000, output_csv_path=target_csv)
