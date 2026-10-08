#!/usr/bin/env bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail
LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TARGET_ARG="${1:-expected_output}"
if [[ "${TARGET_ARG}" = /* ]]; then
  TARGET_DIR="${TARGET_ARG}"
else
  TARGET_DIR="${LAB_DIR}/${TARGET_ARG}"
fi

echo "=== Lab 03 Self-Diagnosis: From Specs to TDD Code (Circuit Breaker) ==="

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "[FAIL] Target directory does not exist: ${TARGET_DIR}"
  exit 1
fi

TEST_FILE="${TARGET_DIR}/test_circuitbreaker.py"
if [[ ! -s "${TEST_FILE}" ]]; then
  echo "[FAIL] Missing required artifact: ${TEST_FILE}"
  exit 1
fi

TEST_OUT="$(PYTHONPATH="${TARGET_DIR}" python3 -m unittest discover -s "${TARGET_DIR}" -p "test_*.py" -v 2>&1)" || {
  echo "${TEST_OUT}"
  echo "[FAIL] Unit tests failed in ${TARGET_DIR}"
  exit 1
}
echo "${TEST_OUT}"
if [[ "${TEST_OUT}" == *"Ran 0 tests"* ]]; then
  echo "[FAIL] No unit tests ran in ${TARGET_DIR}"
  exit 1
fi

python3 - "${TEST_FILE}" << 'PYEOF'
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    test_src = f.read()

for i in range(1, 8):
    req_fn = f"test_req000{i}_"
    if req_fn not in test_src:
        print(f"[FAIL] Missing traceable unit test prefix: {req_fn}")
        sys.exit(1)

print("[PASS] All 7 CircuitBreaker requirements (REQ-0001..REQ-0007) have passing, traceable unit tests.")
PYEOF
