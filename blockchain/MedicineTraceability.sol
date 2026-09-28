// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MedicineTraceability
 * @dev Academic Capstone Smart Contract for MediTrace
 * Implements tamper-resistant medicine batch registration, custody transfer, and hash-based verification.
 */
contract MedicineTraceability {
    // Structure to represent a medicine batch
    struct Batch {
        string batchId;
        string medicineId;
        string manufacturer;
        string currentOwner;
        uint256 quantity;
        uint256 timestamp;
        bool exists;
    }

    // Structure to represent a supply-chain custody transaction
    struct TransactionRecord {
        string batchId;
        string fromOwner;
        string toOwner;
        uint256 quantity;
        uint256 timestamp;
        string dataHash; // SHA-256 hash of off-chain hospital/supplier transaction details
    }

    // State mappings
    mapping(string => Batch) private batches;
    mapping(string => TransactionRecord[]) private batchHistory;
    string[] private allBatchIds;

    // Events
    event BatchRegistered(
        string indexed batchId,
        string indexed medicineId,
        string manufacturer,
        uint256 quantity,
        uint256 timestamp,
        string dataHash
    );

    event MedicineTransferred(
        string indexed batchId,
        string fromOwner,
        string indexed toOwner,
        uint256 quantity,
        uint256 timestamp,
        string dataHash
    );

    /**
     * @dev Register a new medicine batch onto the blockchain
     * @param _batchId Unique batch identifier (e.g., BATCH-1001)
     * @param _medicineId Medicine catalog identifier (e.g., MED-001)
     * @param _manufacturer Manufacturer or initial supplier name/address
     * @param _quantity Batch item count
     * @param _dataHash SHA-256 integrity hash of off-chain transaction record
     */
    function registerBatch(
        string memory _batchId,
        string memory _medicineId,
        string memory _manufacturer,
        uint256 _quantity,
        string memory _dataHash
    ) public {
        require(bytes(_batchId).length > 0, "Batch ID cannot be empty");
        require(bytes(_medicineId).length > 0, "Medicine ID cannot be empty");
        require(bytes(_manufacturer).length > 0, "Manufacturer cannot be empty");
        require(_quantity > 0, "Batch quantity must be greater than zero");
        require(!batches[_batchId].exists, "Duplicate Error: Batch is already registered");

        uint256 currentTime = block.timestamp;

        batches[_batchId] = Batch({
            batchId: _batchId,
            medicineId: _medicineId,
            manufacturer: _manufacturer,
            currentOwner: _manufacturer,
            quantity: _quantity,
            timestamp: currentTime,
            exists: true
        });

        allBatchIds.push(_batchId);

        TransactionRecord memory initialTx = TransactionRecord({
            batchId: _batchId,
            fromOwner: "GENESIS_MANUFACTURER",
            toOwner: _manufacturer,
            quantity: _quantity,
            timestamp: currentTime,
            dataHash: _dataHash
        });

        batchHistory[_batchId].push(initialTx);

        emit BatchRegistered(_batchId, _medicineId, _manufacturer, _quantity, currentTime, _dataHash);
    }

    /**
     * @dev Transfer batch ownership across the supply chain
     * @param _batchId Unique batch identifier
     * @param _newOwner Recipient organization (e.g., Distributor, Hospital)
     * @param _quantity Quantity transferred
     * @param _dataHash SHA-256 integrity hash of off-chain transfer record
     */
    function transferBatch(
        string memory _batchId,
        string memory _newOwner,
        uint256 _quantity,
        string memory _dataHash
    ) public {
        require(batches[_batchId].exists, "Validation Error: Batch does not exist");
        require(bytes(_newOwner).length > 0, "New owner cannot be empty");
        require(_quantity > 0, "Transfer quantity must be greater than zero");
        require(
            _quantity <= batches[_batchId].quantity,
            "Quantity Error: Transfer quantity exceeds available batch quantity"
        );

        string memory prevOwner = batches[_batchId].currentOwner;
        uint256 currentTime = block.timestamp;

        // Update current owner and maintain quantity trace
        batches[_batchId].currentOwner = _newOwner;

        TransactionRecord memory transferTx = TransactionRecord({
            batchId: _batchId,
            fromOwner: prevOwner,
            toOwner: _newOwner,
            quantity: _quantity,
            timestamp: currentTime,
            dataHash: _dataHash
        });

        batchHistory[_batchId].push(transferTx);

        emit MedicineTransferred(_batchId, prevOwner, _newOwner, _quantity, currentTime, _dataHash);
    }

    /**
     * @dev Get current state and details of a medicine batch
     */
    function getBatch(string memory _batchId)
        public
        view
        returns (
            string memory batchId,
            string memory medicineId,
            string memory manufacturer,
            string memory currentOwner,
            uint256 quantity,
            uint256 timestamp,
            bool exists
        )
    {
        require(batches[_batchId].exists, "Batch not found");
        Batch memory b = batches[_batchId];
        return (
            b.batchId,
            b.medicineId,
            b.manufacturer,
            b.currentOwner,
            b.quantity,
            b.timestamp,
            b.exists
        );
    }

    /**
     * @dev Get number of custody transactions for a batch
     */
    function getHistoryLength(string memory _batchId) public view returns (uint256) {
        require(batches[_batchId].exists, "Batch not found");
        return batchHistory[_batchId].length;
    }

    /**
     * @dev Retrieve a specific transaction record from the history of a batch
     */
    function getTransaction(string memory _batchId, uint256 index)
        public
        view
        returns (
            string memory batchId,
            string memory fromOwner,
            string memory toOwner,
            uint256 quantity,
            uint256 timestamp,
            string memory dataHash
        )
    {
        require(batches[_batchId].exists, "Batch not found");
        require(index < batchHistory[_batchId].length, "Transaction index out of bounds");
        TransactionRecord memory txRec = batchHistory[_batchId][index];
        return (
            txRec.batchId,
            txRec.fromOwner,
            txRec.toOwner,
            txRec.quantity,
            txRec.timestamp,
            txRec.dataHash
        );
    }

    /**
     * @dev Helper to count total registered batches
     */
    function getTotalBatchesCount() public view returns (uint256) {
        return allBatchIds.length;
    }

    /**
     * @dev Get batch ID by index
     */
    function getBatchIdByIndex(uint256 index) public view returns (string memory) {
        require(index < allBatchIds.length, "Index out of bounds");
        return allBatchIds[index];
    }
}
