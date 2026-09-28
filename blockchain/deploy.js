const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("Starting deployment of MedicineTraceability contract...");

  const MedicineTraceability = await hre.ethers.getContractFactory("MedicineTraceability");
  const contract = await MedicineTraceability.deploy();

  await contract.waitForDeployment();
  const contractAddress = await contract.getAddress();

  console.log(`MedicineTraceability deployed successfully at address: ${contractAddress}`);

  // Save deployment artifact address and ABI for backend/Web3.py consumption
  const deploymentInfo = {
    address: contractAddress,
    network: hre.network.name,
    deployedAt: new Date().toISOString()
  };

  const deploymentPath = path.join(__dirname, "contract_address.json");
  fs.writeFileSync(deploymentPath, JSON.stringify(deploymentInfo, null, 2));
  console.log(`Deployment metadata saved to ${deploymentPath}`);
}

main().catch((error) => {
  console.error("Deployment failed:", error);
  process.exitCode = 1;
});
