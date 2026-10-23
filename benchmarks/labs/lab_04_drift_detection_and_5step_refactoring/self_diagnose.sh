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

echo "=== Lab 04 Self-Diagnosis: Spec Drift Detection & 5-Step Brownfield Refactoring (TaskFlow DailyPlanner) ==="

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "[FAIL] Target directory does not exist: ${TARGET_DIR}"
  exit 1
fi

SPEC_FILE="${TARGET_DIR}/spec.md"
if [[ ! -s "${SPEC_FILE}" ]]; then
  echo "[FAIL] Missing required artifact: ${SPEC_FILE}"
  exit 1
fi

if ! compgen -G "${TARGET_DIR}/test_*.py" > /dev/null; then
  echo "[FAIL] Missing required test_*.py files in ${TARGET_DIR}"
  exit 1
fi

# 1. Verify fixed implementation passes all REQ-0001..0004 tests
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

# 2. Verify bugged implementation actually fails REQ-0003 (proving drift detection)
python3 - "${LAB_DIR}/service" "${SPEC_FILE}" << 'PYEOF'
import sys

service_dir, track_spec = sys.argv[1], sys.argv[2]
sys.path.insert(0, service_dir)
import daily_planner  # type: ignore

buggy = daily_planner.DailyPlanner(120)
buggy.schedule_task("Block 1", 60)
if buggy.schedule_task("Block 2 (Exact 60 min remaining)", 60):
    print("[FAIL] service/daily_planner.py should exhibit the REQ-0003 exact-budget off-by-one bug")
    sys.exit(1)

with open(track_spec, "r", encoding="utf-8") as f:
    spec_text = f.read()

for deferred in ["F-02", "F-03", "F-04", "Out of Scope"]:
    if deferred not in spec_text:
        print(f"[FAIL] Track spec.md must explicitly list {deferred} in Out of Scope")
        sys.exit(1)

print("[PASS] Drift bug confirmed in service/daily_planner.py, fixed in target directory, and scoped via 5-Step Scorecard Track Spec.")
PYEOF
