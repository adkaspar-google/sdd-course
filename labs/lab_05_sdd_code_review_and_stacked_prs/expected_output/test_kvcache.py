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

"""Traceable unit tests for KVCache (REQ-0001..REQ-0006)."""

import unittest
from kvcache import KVCache


class FakeClock:

    def __init__(self, initial: float = 100.0) -> None:
        self.now = initial

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TestKVCache(unittest.TestCase):

    def test_req0001_put_and_get_roundtrip(self) -> None:
        cache = KVCache(max_size=3)
        cache.put("k1", "v1")
        self.assertEqual(cache.get("k1"), "v1")
        self.assertIsNone(cache.get("missing"))

    def test_req0002_fifo_eviction_unaffected_by_get_reads(self) -> None:
        cache = KVCache(max_size=2)
        cache.put("k1", "v1")
        cache.put("k2", "v2")
        # Reading k1 MUST NOT turn eviction into LRU
        self.assertEqual(cache.get("k1"), "v1")
        cache.put("k3", "v3")
        self.assertIsNone(cache.get("k1"))
        self.assertEqual(cache.get("k2"), "v2")
        self.assertEqual(cache.get("k3"), "v3")

    def test_req0003_in_place_update_preserves_fifo_order(self) -> None:
        cache = KVCache(max_size=2)
        cache.put("k1", "v1")
        cache.put("k2", "v2")
        cache.put("k1", "v1-updated")
        self.assertEqual(len(cache), 2)
        self.assertEqual(cache.get("k1"), "v1-updated")

    def test_req0004_explicit_key_deletion(self) -> None:
        cache = KVCache(max_size=2)
        cache.put("k1", "v1")
        self.assertTrue(cache.delete("k1"))
        self.assertFalse(cache.delete("k1"))

    def test_req0005_validation_rejects_invalid_size_or_key(self) -> None:
        with self.assertRaises(ValueError):
            KVCache(max_size=0)
        cache = KVCache(max_size=2)
        with self.assertRaises(ValueError):
            cache.put("", "val")

    def test_req0006_per_entry_ttl_expiration_and_capacity_reclamation(
        self,
    ) -> None:
        clock = FakeClock(100.0)
        cache = KVCache(max_size=2, clock=clock)
        with self.assertRaises(ValueError):
            cache.put_with_ttl("bad", "v", ttl_seconds=0)

        cache.put_with_ttl("k1", "v1", ttl_seconds=10.0)
        cache.put("k2", "v2")
        clock.advance(10.0)
        # k1 is now expired at t=110.0, so inserting k3 must purge k1 and keep k2
        cache.put("k3", "v3")
        self.assertIsNone(cache.get("k1"))
        self.assertEqual(cache.get("k2"), "v2")
        self.assertEqual(cache.get("k3"), "v3")


if __name__ == "__main__":
    unittest.main()
