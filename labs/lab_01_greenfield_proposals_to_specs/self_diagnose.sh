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

echo "=== Lab 01 Self-Diagnosis: Greenfield Proposals to Dual-Engine Specs ==="

python3 -m unittest discover -s "${LAB_DIR}/expected_output" -p "test_*.py" -v

SPEC_FILE="${LAB_DIR}/expected_output/openspec/specs/rate-limiter/spec.md"
TRACK_SPEC="${LAB_DIR}/expected_output/conductor/tracks/rate_limiter_mvp/spec.md"
ADR1="${LAB_DIR}/expected_output/ADR-0001-storage-engine.md"
ADR2="${LAB_DIR}/expected_output/ADR-0002-sync-protocol.md"

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

for section in ["Overview", "Architecture", "Functional Requirements", "Non-Functional Requirements", "Acceptance Criteria", "Out of Scope", "Verification Commands"]:
    if section not in track_text:
        print(f"[FAIL] Conductor track spec.md missing required section: {section}")
        sys.exit(1)

print("[PASS] OpenSpec REQ-0001..0006, 4-hashtag Scenarios, ADRs, 7-Section Conductor Track Spec, and TDD tests verified.")
PYEOF
