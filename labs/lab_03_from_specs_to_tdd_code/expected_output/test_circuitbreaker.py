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

"""Traceable TDD test suite for CircuitBreaker (REQ-0001..REQ-0007)."""

import unittest
from circuitbreaker import CircuitBreaker, CircuitOpenError, CircuitState


class FakeClock:

    def __init__(self, initial: float = 100.0) -> None:
        self.now = initial

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TestCircuitBreaker(unittest.TestCase):

    def test_req0001_closed_state_forwards_calls(self) -> None:
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=30.0)
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertEqual(cb.call(lambda x: x + 1, 41), 42)
        self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_req0002_failure_threshold_trips_to_open(self) -> None:
        clock = FakeClock(100.0)
        cb = CircuitBreaker(3, 30.0, clock=clock)

        def fail() -> None:
            raise RuntimeError("boom")

        for _ in range(3):
            with self.assertRaises(RuntimeError):
                cb.call(fail)
        self.assertEqual(cb.state, CircuitState.OPEN)
        self.assertEqual(cb.consecutive_failures, 3)

    def test_req0003_open_state_fails_fast_without_invoking_callable(self) -> None:
        clock = FakeClock(100.0)
        cb = CircuitBreaker(2, 30.0, clock=clock)
        for _ in range(2):
            with self.assertRaises(ValueError):
                cb.call(lambda: (_ for _ in ()).throw(ValueError("err")))

        invocations = 0

        def tracked_call() -> str:
            nonlocal invocations
            invocations += 1
            return "ok"

        clock.advance(15.0)
        with self.assertRaises(CircuitOpenError):
            cb.call(tracked_call)
        self.assertEqual(invocations, 0)

    def test_req0004_cooldown_transitions_to_half_open(self) -> None:
        clock = FakeClock(100.0)
        cb = CircuitBreaker(1, 30.0, clock=clock)
        with self.assertRaises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("trip")))
        self.assertEqual(cb.state, CircuitState.OPEN)
        clock.advance(30.0)
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)

    def test_req0005_probe_success_closes_circuit(self) -> None:
        clock = FakeClock(100.0)
        cb = CircuitBreaker(1, 30.0, clock=clock)
        with self.assertRaises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("trip")))
        clock.advance(30.0)
        self.assertEqual(cb.call(lambda: "recovered"), "recovered")
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertEqual(cb.consecutive_failures, 0)

    def test_req0006_probe_failure_reopens_circuit(self) -> None:
        clock = FakeClock(100.0)
        cb = CircuitBreaker(1, 30.0, clock=clock)
        with self.assertRaises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("trip1")))
        clock.advance(30.0)
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)
        with self.assertRaises(ConnectionError):
            cb.call(lambda: (_ for _ in ()).throw(ConnectionError("trip2")))
        self.assertEqual(cb.state, CircuitState.OPEN)
        clock.advance(20.0)
        with self.assertRaises(CircuitOpenError):
            cb.call(lambda: "blocked")

    def test_req0007_success_resets_failure_streak(self) -> None:
        cb = CircuitBreaker(3, 30.0)
        for _ in range(2):
            with self.assertRaises(RuntimeError):
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("flaky")))
        self.assertEqual(cb.consecutive_failures, 2)
        self.assertEqual(cb.call(lambda: "ok"), "ok")
        self.assertEqual(cb.consecutive_failures, 0)
        for _ in range(2):
            with self.assertRaises(RuntimeError):
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("flaky")))
        self.assertEqual(cb.state, CircuitState.CLOSED)


if __name__ == "__main__":
    unittest.main()
