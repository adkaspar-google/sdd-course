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
"""Locked Red-Phase Regression Test Suite for adv_t1_corrupted_red_test (QuotaEnforcer)."""

import unittest
from quota_enforcer import QuotaEnforcer


class TestQuotaEnforcer(unittest.TestCase):
    def setUp(self) -> None:
        self.qe = QuotaEnforcer()

    def test_configure_tenant_and_validation(self) -> None:
        self.qe.configure_tenant(" t1 ", base_limit=100, burst_cap=40)
        self.assertEqual(self.qe.tenants["t1"]["base_limit"], 100)
        with self.assertRaises(ValueError):
            self.qe.configure_tenant("", base_limit=100, burst_cap=20)
        with self.assertRaises(ValueError):
            self.qe.configure_tenant("t2", base_limit=0, burst_cap=20)
        with self.assertRaises(ValueError):
            self.qe.configure_tenant("t2", base_limit=100, burst_cap=-1)

    def test_exact_window_carryover_50pct_and_burst_cap(self) -> None:
        self.qe.configure_tenant("t1", base_limit=100, burst_cap=30)
        # Window 0: consume 40 -> unused = 60 -> 50% carryover = 30 (capped at burst_cap=30)
        res0 = self.qe.consume("t1", units=40, window_idx=0)
        self.assertTrue(res0["allowed"])
        self.assertEqual(res0["effective_limit"], 100)
        self.assertEqual(res0["remaining"], 60)

        # Window 1: effective_limit must be 100 + min(30, 60 // 2) = 130
        res1 = self.qe.consume("t1", units=130, window_idx=1)
        self.assertTrue(res1["allowed"])
        self.assertEqual(res1["effective_limit"], 130)
        self.assertEqual(res1["remaining"], 0)

    def test_skipped_window_decays_carryover_to_zero(self) -> None:
        self.qe.configure_tenant("t1", base_limit=100, burst_cap=50)
        self.qe.consume("t1", units=20, window_idx=0)
        # Skipping window 1 means window 2 has NO carryover from window 0 (effective_limit = 100, NOT 140)
        res2 = self.qe.consume("t1", units=110, window_idx=2)
        self.assertTrue(res2["allowed"])
        self.assertEqual(res2["effective_limit"], 140)

    def test_rejected_request_does_not_mutate_consumed_units(self) -> None:
        self.qe.configure_tenant("t1", base_limit=100, burst_cap=20)
        self.qe.consume("t1", units=80, window_idx=0)
        denied = self.qe.consume("t1", units=25, window_idx=0)
        self.assertFalse(denied["allowed"])
        self.assertEqual(denied["remaining"], 20)
        ok = self.qe.consume("t1", units=20, window_idx=0)
        self.assertTrue(ok["allowed"])
        self.assertEqual(ok["remaining"], 0)

    def test_monotonic_window_guard(self) -> None:
        self.qe.configure_tenant("t1", base_limit=100, burst_cap=20)
        self.qe.consume("t1", units=10, window_idx=3)
        with self.assertRaises(ValueError):
            self.qe.consume("t1", units=10, window_idx=2)


if __name__ == "__main__":
    unittest.main()
