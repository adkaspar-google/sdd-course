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

echo "=== Lab 02 Self-Diagnosis: Brownfield Spec Recovery (Lease Manager) ==="

python3 -m unittest discover -s "${LAB_DIR}/service" -p "test_*.py" -v

SPEC_FILE="${LAB_DIR}/expected_output/openspec/specs/lease-manager/spec.md"
ADR_FILE="${LAB_DIR}/expected_output/ADR-0001-fencing-tokens.md"

python3 - "$SPEC_FILE" "$ADR_FILE" << 'PYEOF'
import sys

spec_file, adr_file = sys.argv[1], sys.argv[2]
with open(spec_file, "r", encoding="utf-8") as f:
    spec_text = f.read()

for req_id in ["REQ-0001", "REQ-0002", "REQ-0003", "REQ-0004", "REQ-0005", "REQ-0006"]:
    if req_id not in spec_text:
        print(f"[FAIL] Recovered spec missing {req_id}")
        sys.exit(1)

with open(adr_file, "r", encoding="utf-8") as f:
    adr_text = f.read()

if "fencing_token" not in adr_text:
    print("[FAIL] ADR-0001 must document monotonic fencing_token safety")
    sys.exit(1)

print("[PASS] Brownfield unit tests and recovered OpenSpec REQ-0001..0006 + ADR-0001 verified.")
PYEOF
