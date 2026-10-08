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

echo "=== Lab 01 Self-Diagnosis: Greenfield Proposals to Dual-Engine Specs ==="

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "[FAIL] Target directory does not exist: ${TARGET_DIR}"
  exit 1
fi

if compgen -G "${TARGET_DIR}/test_*.py" > /dev/null; then
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
else
  echo "[SKIP] No test_*.py found in ${TARGET_DIR}; skipping optional unit-test step."
fi

SPEC_FILE="${TARGET_DIR}/openspec/specs/rate-limiter/spec.md"
TRACK_SPEC="${TARGET_DIR}/conductor/tracks/rate_limiter_mvp/spec.md"
ADR1="${TARGET_DIR}/ADR-0001-storage-engine.md"
ADR2="${TARGET_DIR}/ADR-0002-sync-protocol.md"

for f in "$SPEC_FILE" "$TRACK_SPEC" "$ADR1" "$ADR2"; do
  if [[ ! -s "$f" ]]; then
    echo "[FAIL] Missing required artifact: $f"
    exit 1
  fi
done

python3 - "$SPEC_FILE" "$TRACK_SPEC" << 'PYEOF'
import sys

spec_path, track_spec_path = sys.argv[1], sys.argv[2]
with open(spec_path, "r", encoding="utf-8") as f:
    spec_text = f.read()

for req_id in ["REQ-0001", "REQ-0002", "REQ-0003", "REQ-0004", "REQ-0005", "REQ-0006"]:
    if req_id not in spec_text:
        print(f"[FAIL] OpenSpec spec.md missing {req_id}")
        sys.exit(1)

if "#### Scenario:" not in spec_text or "SHALL" not in spec_text:
    print("[FAIL] OpenSpec spec.md must use 4-hashtag '#### Scenario:' and RFC 2119 'SHALL'/'MUST'")
    sys.exit(1)

with open(track_spec_path, "r", encoding="utf-8") as f:
    track_text = f.read()

for section in [
    "Overview",
    "Architecture & Component Topology",
    "Functional Requirements",
    "Non-Functional Requirements",
    "Acceptance Criteria",
    "Out of Scope",
    "Verification Commands",
]:
    if section not in track_text:
        print(f"[FAIL] Conductor track spec.md missing required section: {section}")
        sys.exit(1)

print("[PASS] OpenSpec REQ-0001..0006, 4-hashtag Scenarios, ADRs, and 7-Section Conductor Track Spec verified.")
PYEOF
