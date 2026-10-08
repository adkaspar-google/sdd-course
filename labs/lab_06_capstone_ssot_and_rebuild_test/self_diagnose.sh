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

echo "=== Lab 06 Self-Diagnosis: 8-Section SPEC.md & Clean-Room Rebuild Test ==="

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "[FAIL] Target directory does not exist: ${TARGET_DIR}"
  exit 1
fi

IMPL_FILE="${TARGET_DIR}/coursepulse.py"
if [[ ! -s "${IMPL_FILE}" ]]; then
  echo "[FAIL] Missing required artifact: ${IMPL_FILE}"
  exit 1
fi

CLEAN_ROOM_DIR="$(mktemp -d)"
cleanup() {
  chmod -R u+w "${CLEAN_ROOM_DIR}" 2>/dev/null || true
  rm -rf "${CLEAN_ROOM_DIR}"
}
trap cleanup EXIT

cp "${LAB_DIR}/SPEC.md" "${CLEAN_ROOM_DIR}/SPEC.md"
cp "${IMPL_FILE}" "${CLEAN_ROOM_DIR}/coursepulse.py"
mkdir -p "${CLEAN_ROOM_DIR}/adversarial_tests"
cp "${LAB_DIR}/adversarial_tests/test_rebuild_contract.py" "${CLEAN_ROOM_DIR}/adversarial_tests/test_rebuild_contract.py"

# Lock adversarial tests read-only to enforce the Adversarial Verification Gate
chmod -R a-w "${CLEAN_ROOM_DIR}/adversarial_tests"

TEST_OUT="$(PYTHONPATH="${CLEAN_ROOM_DIR}" python3 -m unittest discover -s "${CLEAN_ROOM_DIR}/adversarial_tests" -p "test_*.py" -v 2>&1)" || {
  echo "${TEST_OUT}"
  echo "[FAIL] Clean-Room Rebuild Test failed adversarial contract tests"
  exit 1
}
echo "${TEST_OUT}"
if [[ "${TEST_OUT}" == *"Ran 0 tests"* ]]; then
  echo "[FAIL] No adversarial contract tests ran"
  exit 1
fi

echo "[PASS] Clean-Room Rebuild Test passed all read-only adversarial contract tests (REQ-0001..REQ-0006)."
