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

"""Unit tests for the Brownfield Distributed Lease Lock Manager."""

import unittest
from leasemanager import LeaseManager


class FakeClock:

    def __init__(self, initial: float = 100.0) -> None:
        self.now = initial

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TestLeaseManager(unittest.TestCase):

    def test_req0001_exclusive_acquisition_and_expiry_takeover(self) -> None:
        clock = FakeClock(100.0)
        mgr = LeaseManager(clock=clock)
        lease1 = mgr.acquire("shard-1", "worker-a", ttl_seconds=10.0)
        self.assertIsNotNone(lease1)
        assert lease1 is not None
        self.assertEqual(lease1.fencing_token, 1)
        self.assertEqual(lease1.expires_at, 110.0)

        clock.advance(10.0)
        lease2 = mgr.acquire("shard-1", "worker-b", ttl_seconds=15.0)
        self.assertIsNotNone(lease2)
        assert lease2 is not None
        self.assertEqual(lease2.holder_id, "worker-b")
        self.assertEqual(lease2.fencing_token, 2)

    def test_req0002_monotonic_fencing_tokens_never_reset(self) -> None:
        clock = FakeClock(0.0)
        mgr = LeaseManager(clock=clock)
        l1 = mgr.acquire("res-a", "w1", 5.0)
        assert l1 is not None
        self.assertTrue(mgr.release("res-a", "w1", l1.fencing_token))
        l2 = mgr.acquire("res-a", "w2", 5.0)
        assert l2 is not None
        self.assertGreater(l2.fencing_token, l1.fencing_token)

    def test_req0003_contended_acquisition_rejected(self) -> None:
        clock = FakeClock(50.0)
        mgr = LeaseManager(clock=clock)
        self.assertIsNotNone(mgr.acquire("db-lock", "node-1", 30.0))
        self.assertIsNone(mgr.acquire("db-lock", "node-2", 30.0))

    def test_req0004_holder_renewal_advances_token_and_ttl(self) -> None:
        clock = FakeClock(10.0)
        mgr = LeaseManager(clock=clock)
        l1 = mgr.acquire("job-1", "worker-1", 20.0)
        assert l1 is not None
        clock.advance(15.0)
        renewed = mgr.renew("job-1", "worker-1", l1.fencing_token, 20.0)
        self.assertIsNotNone(renewed)
        assert renewed is not None
        self.assertEqual(renewed.expires_at, 45.0)
        self.assertGreater(renewed.fencing_token, l1.fencing_token)

    def test_req0005_release_verifies_holder_and_fencing_token(self) -> None:
        clock = FakeClock(0.0)
        mgr = LeaseManager(clock=clock)
        l1 = mgr.acquire("lock-x", "owner-1", 10.0)
        assert l1 is not None
        self.assertFalse(mgr.release("lock-x", "owner-2", l1.fencing_token))
        self.assertFalse(mgr.release("lock-x", "owner-1", l1.fencing_token + 99))
        self.assertTrue(mgr.release("lock-x", "owner-1", l1.fencing_token))

    def test_req0006_evict_expired_cleans_stale_leases(self) -> None:
        clock = FakeClock(0.0)
        mgr = LeaseManager(clock=clock)
        mgr.acquire("r1", "h1", 5.0)
        mgr.acquire("r2", "h2", 20.0)
        clock.advance(10.0)
        self.assertEqual(mgr.evict_expired(), 1)
        self.assertIsNone(mgr.get_lease("r1"))
        self.assertIsNotNone(mgr.get_lease("r2"))


if __name__ == "__main__":
    unittest.main()
