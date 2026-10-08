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

echo "=== Lab 05 Self-Diagnosis: SDD Code Review & Stacked PR Decomposition ==="

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "[FAIL] Target directory does not exist: ${TARGET_DIR}"
  exit 1
fi

SPEC_FILE="${TARGET_DIR}/openspec/specs/kv-cache/spec.md"
TASKS_FILE="${TARGET_DIR}/tasks.md"

for f in "$SPEC_FILE" "$TASKS_FILE"; do
  if [[ ! -s "$f" ]]; then
    echo "[FAIL] Missing required artifact: $f"
    exit 1
  fi
done

if ! compgen -G "${TARGET_DIR}/test_*.py" > /dev/null; then
  echo "[FAIL] Missing required test_*.py files in ${TARGET_DIR}"
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

python3 - "${SPEC_FILE}" "${TASKS_FILE}" << 'PYEOF'
import sys

spec_path, tasks_path = sys.argv[1], sys.argv[2]
with open(spec_path, "r", encoding="utf-8") as f:
    spec_text = f.read()

for req_id in ["REQ-0001", "REQ-0002", "REQ-0003", "REQ-0004", "REQ-0005", "REQ-0006"]:
    if req_id not in spec_text:
        print(f"[FAIL] Synchronized spec missing {req_id}")
        sys.exit(1)

with open(tasks_path, "r", encoding="utf-8") as f:
    tasks_text = f.read()

for marker in ["Batch 1", "Batch 2", "Archive PR N+1"]:
    if marker not in tasks_text:
        print(f"[FAIL] tasks.md missing Stacked PR marker: {marker}")
        sys.exit(1)

print("[PASS] SDD Code Review remediation, REQ-0006 spec sync, and Stacked PR batches verified.")
PYEOF
