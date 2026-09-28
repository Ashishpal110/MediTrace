"""
MediTrace Academic Capstone Project
Comprehensive Master Test Suite

Executes and verifies all 10 mandatory academic evaluation requirements:
1. Valid batch registration
2. Duplicate batch rejection
3. Valid batch transfer
4. Invalid batch transfer (non-existing batch)
5. Excess quantity transfer rejection
6. Batch history retrieval
7. Hash verification (VALID and TAMPERED INVALID)
8. Dataset loading & integrity
9. Analytics execution & Isolation Forest
10. Risk-score generation & classification
"""

import os
import sys
import unittest

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tests.test_blockchain import TestBlockchainService
from tests.test_analytics import TestAnalyticsPipeline
from tests.test_hash_verification import TestHashVerification

def run_all_tests():
    print("=" * 70)
    print("MEDITRACE CAPSTONE PROJECT: COMPREHENSIVE ACADEMIC TEST SUITE")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestBlockchainService))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalyticsPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestHashVerification))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print("ACADEMIC VERIFICATION SUMMARY:")
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    if result.wasSuccessful():
        print(">> ALL 10 ACADEMIC REQUIREMENTS VERIFIED SUCCESSFULLY! <<\n")
        return 0
    else:
        print(">> TEST SUITE FAILED! Please review errors above. <<\n")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
