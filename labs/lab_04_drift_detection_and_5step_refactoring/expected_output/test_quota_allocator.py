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

"""Unit tests for TokenBucketQuotaAllocator (REQ-0001..REQ-0006)."""

import unittest
from quota_allocator_fixed import TokenBucketQuotaAllocator


class FakeClock:

    def __init__(self, initial: float = 0.0) -> None:
        self.now = initial

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TestTokenBucketQuotaAllocator(unittest.TestCase):

    def test_req0001_initial_bucket_starts_at_full_capacity(self) -> None:
        clock = FakeClock(0.0)
        alloc = TokenBucketQuotaAllocator(10, 1.0, clock=clock)
        self.assertTrue(alloc.consume("tenant-1", 4))
        self.assertEqual(alloc.available_tokens("tenant-1"), 6)

    def test_req0002_insufficient_tokens_leaves_balance_unchanged(self) -> None:
        clock = FakeClock(0.0)
        alloc = TokenBucketQuotaAllocator(5, 1.0, clock=clock)
        self.assertTrue(alloc.consume("tenant-1", 3))
        self.assertFalse(alloc.consume("tenant-1", 4))
        self.assertEqual(alloc.available_tokens("tenant-1"), 2)

    def test_req0003_refill_caps_at_capacity(self) -> None:
        clock = FakeClock(0.0)
        alloc = TokenBucketQuotaAllocator(10, 2.0, clock=clock)
        self.assertTrue(alloc.consume("tenant-1", 10))
        clock.advance(50.0)
        self.assertEqual(alloc.available_tokens("tenant-1"), 10)

    def test_req0004_validation_rejects_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            TokenBucketQuotaAllocator(0, 1.0)
        alloc = TokenBucketQuotaAllocator(5, 1.0)
        with self.assertRaises(ValueError):
            alloc.consume("", 1)
        with self.assertRaises(ValueError):
            alloc.consume("k", 0)

    def test_req0005_sub_quantum_polling_preserves_fractional_elapsed_time(
        self,
    ) -> None:
        clock = FakeClock(0.0)
        alloc = TokenBucketQuotaAllocator(5, 1.0, clock=clock)
        self.assertTrue(alloc.consume("tenant-1", 5))
        self.assertEqual(alloc.available_tokens("tenant-1"), 0)

        # Poll at t=0.4s and t=0.8s (each < 1.0s quantum)
        clock.advance(0.4)
        self.assertFalse(alloc.consume("tenant-1", 1))
        clock.advance(0.4)
        self.assertFalse(alloc.consume("tenant-1", 1))

        # At t=1.2s total elapsed >= 1.0s -> 1 token MUST be replenished!
        clock.advance(0.4)
        self.assertTrue(alloc.consume("tenant-1", 1))

    def test_req0006_concurrent_consumption_safety(self) -> None:
        alloc = TokenBucketQuotaAllocator(10, 0.001)
        results = [alloc.consume("shared", 1) for _ in range(15)]
        self.assertEqual(sum(1 for r in results if r), 10)
        self.assertEqual(alloc.available_tokens("shared"), 0)


if __name__ == "__main__":
    unittest.main()
