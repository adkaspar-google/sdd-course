#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "================================================================================"
echo " [1/5] Running Forensic Provenance & Statistical Audit (252 Upstream Trials)..."
echo "================================================================================"
python3 verification/verify_all_claims.py

echo ""
echo "================================================================================"
echo " [2/5] Running Mathematical Formula & Compiler Rollback Verification..."
echo "================================================================================"
python3 verification/verify_all_formulas.py

echo ""
echo "================================================================================"
echo " [3/5] Running Controlled 36-Workspace Sealed Oracle & Mutation Benchmark..."
echo "================================================================================"
python3 benchmarks/controlled_36_workspaces/run_sdd_benchmark.py

echo ""
echo "================================================================================"
echo " [4/5] Running OO-Harness & Dual-Loop Benchmark Unit Test Suite..."
echo "================================================================================"
python3 -m unittest discover -s benchmarks/controlled_36_workspaces -p "test_*.py" -v

echo ""
echo "================================================================================"
echo " [5/5] Running Open-Source Hygiene & Vendor-Neutral Nomenclature Audit..."
echo "================================================================================"
python3 verification/leak_scan_repo.py

echo ""
echo "================================================================================"
echo " ALL 5 VERIFICATION SUITES PASSED 100%!"
echo "================================================================================"
