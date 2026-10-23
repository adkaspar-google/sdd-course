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
"""Unit tests for EscrowDisputeResolver (without boundary/remainder clarification)."""

import unittest
from escrow_dispute_resolver import EscrowDisputeResolver


class TestEscrowDisputeResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.edr = EscrowDisputeResolver()

    def test_even_split_and_interior_freeze(self) -> None:
        self.edr.create_escrow("e1", "m1", 100, freeze_start=10, freeze_end=20)
        with self.assertRaises(ValueError):
            self.edr.resolve_dispute("e1", 5000, 5000, timestamp=15)
        res = self.edr.resolve_dispute("e1", buyer_bps=5000, seller_bps=5000, timestamp=25)
        self.assertEqual(res["buyer_refund_cents"] + res["seller_payout_cents"], 100)


if __name__ == "__main__":
    unittest.main()
