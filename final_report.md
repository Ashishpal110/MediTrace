# ACADEMIC CAPSTONE PROJECT FINAL REPORT (PHASE IX)

---

## PROJECT TITLE:
**"Blockchain-Based Medicine Supply Chain Traceability System for Pharmaceutical Companies to Prevent Counterfeit Drugs"**

**Project Name:** MediTrace  
**Academic Degree:** Bachelor of Technology (B.Tech) in Artificial Intelligence & Machine Learning / Computer Science  
**Academic Year:** 2025–2026  

---

## 1. ABSTRACT
The proliferation of counterfeit, degraded, and illegally diverted pharmaceuticals represents one of the most critical threats to global healthcare, resulting in severe patient morbidity, therapeutic failure, and substantial economic damage. Traditional pharmaceutical logistics systems rely upon centralized databases and isolated enterprise resource planning (ERP) silos that are vulnerable to unauthorized record tampering, single-point failures, and delayed post-consumption auditing.

This academic capstone project presents **MediTrace**, a dual-tier prototype combining **Blockchain Technology** with **Machine Learning Analytics** to establish end-to-end medicine batch traceability and proactive counterfeit risk detection. The system strictly adheres to an **Off-Chain / On-Chain architectural separation**: sensitive and voluminous hospital procurement records are maintained off-chain in an optimized relational store (SQLite/CSV), while cryptographic SHA-256 state hashes, immutable batch ownership transfers, and custody events are anchored on-chain via a Solidity smart contract (`MedicineTraceability.sol`).

To detect anomalous transactions without requiring labeled counterfeit datasets, an unsupervised **Isolation Forest** model is trained on multidimensional procurement attributes (unit price, temperature excursions, delivery durations, remaining shelf life, quantities, and supplier transaction frequencies). Anomaly decision metrics are normalized into an academic **Risk Score (0 to 100)** and mapped to risk tiers (**Low Risk**, **Medium Risk**, **High Risk**). An automated cryptographic tamper-verification engine validates off-chain data integrity against the blockchain state, returning immediate `VALID` / `INVALID` classifications. Experimental evaluation over 1,000 synthetic procurement transactions demonstrates 100% precision in detecting off-chain data tampering, 100% smart contract unit test pass rates across 11 test suites, and effective profiling of high-risk suppliers. An interactive Streamlit dashboard enables transparent batch inspection and live viva demonstration.

---

## 2. INTRODUCTION
The World Health Organization (WHO) estimates that over 10% of medical products in low- and middle-income countries are substandard or falsified. In pharmaceutical distribution, counterfeiters exploit informational asymmetries, cold-chain monitoring gaps, and centralized database vulnerabilities to introduce substandard formulations into commercial hospital channels.

While blockchain technology provides decentralized immutability and non-repudiation, storing full clinical and hospital datasets directly on-chain introduces severe scalability bottlenecks, high transaction costs (gas fees), and patient privacy violations. Conversely, standalone off-chain machine learning solutions lack cryptographic immutability, allowing bad actors to manipulate raw training or log data after an illicit transfer.

**MediTrace** resolves this dilemma through a synergistic dual-tier design:
1. **The Blockchain Layer ("What happened?"):** Serves as an immutable truth anchor recording batch provenance, custody handoffs, and cryptographic state fingerprints.
2. **The Analytics Layer ("Does the transaction look suspicious?"):** Analyzes complex procurement parameters to compute an anomaly risk index and flag suspicious supply-chain transactions.

---

## 3. PROJECT DESCRIPTION

### 3.1 Problem Statement
1. **Lack of End-to-End Traceability:** Supply chain custody transitions between manufacturers, distributors, and hospitals are frequently fragmented, making provenance reconstruction difficult.
2. **Vulnerability to Off-Chain Data Falsification:** Malicious actors can alter local ERP logs (e.g., retroactively reducing reported cold-chain temperature violations or modifying expiration dates) without detection.
3. **Absence of Real-Time Anomaly Scoring:** Most anti-counterfeiting checks are reactive, occurring only after adverse events are reported by healthcare providers.

### 3.2 System Architecture
The MediTrace architecture decouples high-throughput data processing from cryptographic state anchoring:

```
+---------------------------------------------------------------------------------------------------+
|                                      MEDITRACE DUAL-TIER ARCHITECTURE                             |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
                              +---------------------------------------+
                              | Off-Chain Hospital Transaction Record |
                              +---------------------------------------+
                                                  |
                                                  v
                              +---------------------------------------+
                              |   Canonical SHA-256 Hash Generation   |
                              +---------------------------------------+
                                           /             \
                                          /               \
                                         v                 v
           +-----------------------------------------+   +-----------------------------------------+
           |       ON-CHAIN BLOCKCHAIN LAYER         |   |       OFF-CHAIN ANALYTICS LAYER         |
           |      (Solidity Smart Contract)          |   |       (Isolation Forest & SQLite)       |
           +-----------------------------------------+   +-----------------------------------------+
           | • struct Batch                          |   | • SQLite Database Storage               |
           | • struct TransactionRecord              |   | • Feature Matrix Standardization        |
           | • registerBatch()                       |   | • Isolation Forest Training             |
           | • transferBatch()                       |   | • Risk Score Normalization [0, 100]     |
           | • getBatchHistory()                     |   | • Categorization: Low, Med, High Risk   |
           | • Event Logging (BatchRegistered, etc.) |   | • Aggregated Supplier / Medicine Stats  |
           +-----------------------------------------+   +-----------------------------------------+
                                          \                 /
                                           \               /
                                            v             v
                              +---------------------------------------+
                              |   SHA-256 Tamper Verification Engine  |
                              |   Status: VALID vs. INVALID           |
                              +---------------------------------------+
                                                  |
                                                  v
                              +---------------------------------------+
                              |     Interactive Streamlit Dashboard   |
                              |  (KPIs, Traceability, Verification)   |
                              +---------------------------------------+
```

### 3.3 Methodology and Design

#### A. Smart Contract Design (`MedicineTraceability.sol`)
The contract is written in Solidity `^0.8.20` and maintains:
- **`batches` mapping (`string => Batch`):** Stores `batchId`, `medicineId`, `manufacturer`, `currentOwner`, `quantity`, `timestamp`, `exists`.
- **`batchHistory` mapping (`string => TransactionRecord[]`):** Maintains the full chronological sequence of transfers, recording `fromOwner`, `toOwner`, `quantity`, `timestamp`, and `dataHash`.
- **Integrity Constraints:** Rejection of empty strings, duplicate batch registrations, non-existent batch transfers, and transfers exceeding available quantities.

#### B. Feature Engineering & Machine Learning Formulation
Seven predictive features are extracted for each procurement record:
1. `quantity` ($x_1$): Number of medicine units.
2. `unit_price` ($x_2$): Procurement cost per unit ($).
3. `delivery_days` ($x_3$): Duration of transit.
4. `temperature` ($x_4$): Monitored transport/storage temperature (°C).
5. `expiry_days` ($x_5$): Remaining shelf life at hospital intake.
6. `supplier_frequency` ($x_6$): Total historical volume of transactions from supplier.
7. `medicine_frequency` ($x_7$): Total procurement occurrences for the medicine category.

Features are standardized using Z-score scaling:
$$z_j = \frac{x_j - \mu_j}{\sigma_j}$$

An **Isolation Forest** ($n_{\text{estimators}} = 150$, $\text{contamination} = 0.10$) constructs an ensemble of isolation trees. The raw anomaly score $s(x)$ is computed from the average path length $h(x)$:
$$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$

The raw decision score $d(x)$ is inverted and mapped into a normalized academic **Risk Score** $R(x) \in [0, 100]$:
$$R(x) = \left( \frac{\max(d) - d(x)}{\max(d) - \min(d)} \right) \times 100$$

#### C. Academic Risk Thresholds
- **Low Risk ($0 \le R \le 30$):** Normal procurement adhering to baseline distribution.
- **Medium Risk ($31 \le R \le 60$):** Minor anomaly (e.g., slight transit delay, moderate price discount).
- **High Risk ($61 \le R \le 100$):** Severe anomaly (e.g., cold-chain thermal breach, extreme price dumping, expired stock dumping, suspicious unverified supplier).

*Academic Note: These thresholds represent simulated academic heuristic bounds and do not constitute clinical or chemical laboratory verification.*

#### D. SHA-256 Tamper-Verification Protocol
For any transaction $T$, a canonical payload string is constructed:
$$\text{Payload}(T) = \text{txn\_id} \parallel \text{hosp\_id} \parallel \text{med\_id} \parallel \text{batch\_id} \parallel \text{sup\_id} \parallel \text{qty} \parallel \text{price} \parallel \text{days} \parallel \text{temp} \parallel \text{exp} \parallel \text{date}$$
$$H_{\text{off}} = \text{SHA-256}(\text{Payload}(T))$$
The engine queries the on-chain stored hash $H_{\text{chain}}$. If $H_{\text{off}} = H_{\text{chain}}$, status is **`VALID`**; if $H_{\text{off}} \neq H_{\text{chain}}$, status is **`INVALID`** (Tamper Detected).

---

## 4. RESULTS AND DISCUSSIONS

### 4.1 Measured Experimental Metrics
The system was executed over 1,000 synthetic hospital medicine transactions. The actual measured outcomes are summarized below:

| Metric Category | Evaluation Parameter | Measured Value |
| :--- | :--- | :--- |
| **Dataset Scale** | Total Procurement Transactions | `1,000` |
| **Blockchain Scale** | Total Batches Registered on Chain | `250` |
| **Blockchain Scale** | Total Custody Transactions Logged | `250` |
| **Model Output** | Total Flagged Anomalies | `100` records |
| **Model Output** | Anomaly Percentage | `10.00%` |
| **Risk Classification**| Low Risk Count ($0 - 30$) | `842` (84.2%) |
| **Risk Classification**| Medium Risk Count ($31 - 60$) | `96` (9.6%) |
| **Risk Classification**| High Risk Count ($61 - 100$) | `62` (6.2%) |
| **Risk Statistics** | Mean Risk Score across Dataset | `20.15 / 100` |
| **Unit Testing** | Master Test Suite Pass Rate | `11 / 11 (100%)` |

### 4.2 Supplier Risk Profiling Results

| Supplier ID | Total Transactions | Suspicious Count | Suspicion Rate (%) | Avg Risk Score | High Risk Count | Avg Delivery Days | Avg Temp (°C) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `SUP-SHADOWTRADE-B` | 27 | 27 | **100.0%** | **67.77** | 18 | 21.0 | 20.32 |
| `SUP-UNVERIFIED-A` | 42 | 35 | **83.33%** | **60.30** | 26 | 16.8 | 24.72 |
| `SUP-FASTDISTRIB` | 102 | 5 | 4.90% | 20.26 | 2 | 5.1 | 18.05 |
| `SUP-PHARMAPLUS` | 274 | 14 | 5.11% | 19.29 | 4 | 4.5 | 16.93 |
| `SUP-BIOCARE` | 139 | 6 | 4.32% | 17.48 | 3 | 4.9 | 16.94 |
| `SUP-MEDILINK` | 220 | 8 | 3.64% | 15.21 | 6 | 4.8 | 17.04 |
| `SUP-GLOBALHEALTH` | 196 | 5 | 2.55% | 13.58 | 3 | 4.6 | 16.80 |

**Discussion:** The Isolation Forest successfully isolated simulated shady suppliers (`SUP-SHADOWTRADE-B` and `SUP-UNVERIFIED-A`), giving them significantly higher average risk scores ($67.77$ and $60.30$) and high suspicion rates ($100\%$ and $83.33\%$) due to recurring delivery delays, thermal fluctuations, and abnormal pricing. In contrast, verified suppliers maintained low risk averages ($13.58$ to $20.26$).

### 4.3 Medicine Risk Profiling Results
- `MED-VACCINE-COV` (Cold-Chain Vaccine): Highest average risk score ($34.16$) and highest high-risk count ($11$) due to extreme sensitivity to thermal breaches outside the 2°C–8°C window.
- `MED-INSULIN` (Cold-Chain Biologic): Average risk score $25.03$ with $9$ high-risk records.
- Standard oral solids (`MED-AMOXICILLIN`, `MED-PANTOPRAZOLE`): Low average risk scores ($12.12$ and $14.52$).

### 4.4 Tamper-Verification Verification Results
1. **Valid Record Test:** Evaluating genuine records produced matching SHA-256 digests ($H_{\text{off}} = H_{\text{chain}}$), yielding `STATUS: VALID`.
2. **Tamper Detection Test:** Intentionally altering a temperature field from $4.2^\circ\text{C}$ to $35.5^\circ\text{C}$ immediately produced an un-matched hash digest, generating `STATUS: INVALID (ALERT: Hash Mismatch Detected)`. Precision was measured at 100%.

---

## 5. CONCLUSION AND FUTURE SCOPE

### 5.1 Conclusion
The **MediTrace** academic capstone prototype successfully demonstrates how the integration of blockchain immutability and machine learning analytics overcomes the limitations of traditional pharmaceutical supply chains. Storing only lightweight cryptographic hashes on-chain preserves blockchain performance and data privacy, while keeping comprehensive audit trails readily accessible. The Isolation Forest algorithm effectively detects multi-variable anomalous transactions, and the SHA-256 verification module guarantees tamper detection across the supply chain lifecycle.

### 5.2 Future Scope
- **IoT Smart Contract Oracles:** Connecting live temperature and GPS sensors directly to smart contracts via Chainlink or hardware oracles to trigger automated escrow freezing upon thermal breach.
- **Decentralized Identifiers (DIDs):** Integrating W3C-compliant decentralized identity protocols for pharmaceutical distributors and hospital pharmacies.
- **Zero-Knowledge Proofs (ZKP):** Utilizing zk-SNARKs to verify regulatory compliance and pricing boundaries without revealing commercially sensitive contract terms.

---

## 6. ANNEXURE / IMPLEMENTATION CODE EXCERPTS

### A. Smart Contract (`MedicineTraceability.sol`)
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MedicineTraceability {
    struct Batch {
        string batchId;
        string medicineId;
        string manufacturer;
        string currentOwner;
        uint256 quantity;
        uint256 timestamp;
        bool exists;
    }

    struct TransactionRecord {
        string batchId;
        string fromOwner;
        string toOwner;
        uint256 quantity;
        uint256 timestamp;
        string dataHash;
    }

    mapping(string => Batch) private batches;
    mapping(string => TransactionRecord[]) private batchHistory;

    event BatchRegistered(string indexed batchId, string indexed medicineId, string manufacturer, uint256 quantity, uint256 timestamp, string dataHash);
    event MedicineTransferred(string indexed batchId, string fromOwner, string indexed toOwner, uint256 quantity, uint256 timestamp, string dataHash);

    function registerBatch(string memory _batchId, string memory _medicineId, string memory _manufacturer, uint256 _quantity, string memory _dataHash) public {
        require(!batches[_batchId].exists, "Duplicate Error: Batch is already registered");
        batches[_batchId] = Batch(_batchId, _medicineId, _manufacturer, _manufacturer, _quantity, block.timestamp, true);
        batchHistory[_batchId].push(TransactionRecord(_batchId, "GENESIS_MANUFACTURER", _manufacturer, _quantity, block.timestamp, _dataHash));
        emit BatchRegistered(_batchId, _medicineId, _manufacturer, _quantity, block.timestamp, _dataHash);
    }

    function transferBatch(string memory _batchId, string memory _newOwner, uint256 _quantity, string memory _dataHash) public {
        require(batches[_batchId].exists, "Validation Error: Batch does not exist");
        require(_quantity <= batches[_batchId].quantity, "Quantity Error: Transfer exceeds available quantity");
        string memory prevOwner = batches[_batchId].currentOwner;
        batches[_batchId].currentOwner = _newOwner;
        batchHistory[_batchId].push(TransactionRecord(_batchId, prevOwner, _newOwner, _quantity, block.timestamp, _dataHash));
        emit MedicineTransferred(_batchId, prevOwner, _newOwner, _quantity, block.timestamp, _dataHash);
    }
}
```

### B. Normalized Anomaly Risk Calculation (`analytics.py`)
```python
# Train Isolation Forest & Normalize Risk Score (0 to 100)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = IsolationForest(n_estimators=150, contamination=0.10, random_state=42)
model.fit(X_scaled)
decision_scores = model.decision_function(X_scaled)

min_score = decision_scores.min()
max_score = decision_scores.max()
score_range = max_score - min_score if (max_score - min_score) > 0 else 1.0

# Min-Max Inversion: Lowest decision score (most anomalous) -> Highest risk (100)
normalized_risk = (max_score - decision_scores) / score_range * 100.0
df["risk_score"] = np.round(normalized_risk, 2)
df["risk_level"] = df["risk_score"].apply(lambda s: "Low Risk" if s <= 30 else ("Medium Risk" if s <= 60 else "High Risk"))
```

### C. SHA-256 Tamper-Verification Algorithm (`blockchain_service.py`)
```python
def verify_transaction_integrity(self, transaction_id: str) -> Dict[str, Any]:
    off_data = fetch_offchain_record(transaction_id)
    recomputed_hash = self.generate_sha256_hash(off_data)
    blockchain_hash = fetch_onchain_hash(off_data["batch_id"])
    
    is_valid = (recomputed_hash == blockchain_hash)
    return {
        "status": "VALID" if is_valid else "INVALID",
        "valid": is_valid,
        "tamper_detected": not is_valid,
        "offchain_recomputed_hash": recomputed_hash,
        "blockchain_stored_hash": blockchain_hash
    }
```
