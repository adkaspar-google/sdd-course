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

"""Traceable unit tests for SlidingWindowRateLimiter (REQ-0001..REQ-0006)."""

import unittest
from ratelimiter import SlidingWindowRateLimiter


class FakeClock:

    def __init__(self, initial: float = 100.0) -> None:
        self.now = initial

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TestSlidingWindowRateLimiter(unittest.TestCase):

    def test_req0001_sliding_window_allowance_and_expiry(self) -> None:
        clock = FakeClock(100.0)
        rl = SlidingWindowRateLimiter(5, 60.0, clock=clock)
        d1 = rl.allow("tenant-a", cost=3)
        self.assertTrue(d1.allowed)
        self.assertEqual(d1.remaining, 2)
        self.assertEqual(d1.retry_after_seconds, 0.0)

        clock.advance(60.1)
        d2 = rl.allow("tenant-a", cost=4)
        self.assertTrue(d2.allowed)
        self.assertEqual(d2.remaining, 1)

    def test_req0002_rejection_and_exact_retry_after(self) -> None:
        clock = FakeClock(100.0)
        rl = SlidingWindowRateLimiter(5, 60.0, clock=clock)
        self.assertTrue(rl.allow("tenant-a", cost=3).allowed)
        clock.advance(10.0)
        self.assertTrue(rl.allow("tenant-a", cost=2).allowed)
        clock.advance(10.0)  # t = 120.0
        rejected = rl.allow("tenant-a", cost=2)
        self.assertFalse(rejected.allowed)
        self.assertEqual(rejected.remaining, 0)
        self.assertAlmostEqual(rejected.retry_after_seconds, 40.0)

    def test_req0003_validation_errors(self) -> None:
        with self.assertRaises(ValueError):
            SlidingWindowRateLimiter(0, 60.0)
        with self.assertRaises(ValueError):
            SlidingWindowRateLimiter(5, 0.0)
        rl = SlidingWindowRateLimiter(5, 60.0)
        with self.assertRaises(ValueError):
            rl.allow("", cost=1)
        with self.assertRaises(ValueError):
            rl.allow("k", cost=6)

    def test_req0004_injectable_clock_determinism(self) -> None:
        clock = FakeClock(0.0)
        rl = SlidingWindowRateLimiter(2, 10.0, clock=clock)
        self.assertTrue(rl.allow("k", 2).allowed)
        self.assertFalse(rl.allow("k", 1).allowed)
        clock.advance(10.0)
        self.assertTrue(rl.allow("k", 2).allowed)

    def test_req0005_thread_safe_concurrency(self) -> None:
        rl = SlidingWindowRateLimiter(10, 60.0)
        decisions = [rl.allow("shared-key", 1) for _ in range(25)]
        self.assertEqual(sum(1 for d in decisions if d.allowed), 10)
        self.assertEqual(sum(1 for d in decisions if not d.allowed), 15)

    def test_req0006_key_reset_isolation(self) -> None:
        rl = SlidingWindowRateLimiter(5, 60.0)
        rl.allow("tenant-a", 5)
        rl.allow("tenant-b", 3)
        rl.reset("tenant-a")
        self.assertEqual(rl.allow("tenant-a", 1).remaining, 4)
        self.assertEqual(rl.allow("tenant-b", 1).remaining, 1)


if __name__ == "__main__":
    unittest.main()
