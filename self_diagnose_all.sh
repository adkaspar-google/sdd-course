#!/bin/bash
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

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================================================"
echo "  SDD-Crash-Course: Running Master Self-Diagnosis Across All 6 Labs"
echo "========================================================================"

LABS=(
  "lab_01_greenfield_proposals_to_specs"
  "lab_02_brownfield_spec_recovery"
  "lab_03_from_specs_to_tdd_code"
  "lab_04_drift_detection_and_5step_refactoring"
  "lab_05_sdd_code_review_and_stacked_prs"
  "lab_06_capstone_ssot_and_rebuild_test"
)

PASSED=0
for lab in "${LABS[@]}"; do
  echo ""
  "${ROOT_DIR}/labs/${lab}/self_diagnose.sh"
  PASSED=$((PASSED + 1))
done

echo ""
echo "========================================================================"
echo "  [ALL PASSED] ${PASSED}/${#LABS[@]} Hands-On SDD-Crash-Course Labs Verified!"
echo "========================================================================"
