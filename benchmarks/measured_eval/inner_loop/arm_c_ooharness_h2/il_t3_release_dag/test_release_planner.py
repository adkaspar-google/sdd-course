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
"""Unit tests for DependencyReleasePlanner using OO-Harness + Harness^2 boundary probes."""

import unittest
from release_planner import DependencyReleasePlanner


class TestDependencyReleasePlanner(unittest.TestCase):

  def test_register_service_semver_and_self_dep(self) -> None:
    planner = DependencyReleasePlanner()
    planner.register_service(
        "db", "0.0.1", depends_on=["cache", "cache"], critical=True
    )
    self.assertEqual(planner.services["db"]["depends_on"], ["cache"])
    for bad_ver in ["", "1.2", "1.2.3.4", "v1.0.0", "-1.0.0", "1.-2.0"]:
      with self.assertRaises(ValueError):
        planner.register_service("api", bad_ver)
    with self.assertRaises(ValueError):
      planner.register_service("api", "1.0.0", depends_on=["api"])

  def test_waves_and_rollout_precedence(self) -> None:
    planner = DependencyReleasePlanner()
    planner.register_service("db", "1.0.0", critical=False)
    planner.register_service("cache", "1.0.0", critical=False)
    planner.register_service(
        "auth", "1.0.0", depends_on=["db"], critical=True
    )
    planner.register_service(
        "search", "1.0.0", depends_on=["cache"], critical=False
    )
    planner.register_service(
        "gateway", "1.0.0", depends_on=["auth"], critical=False
    )
    planner.register_service(
        "ui", "1.0.0", depends_on=["search"], critical=False
    )

    res = planner.simulate_rollout(failed_services=["db", "auth", "gateway"])
    self.assertEqual(
        res["waves"],
        [["cache", "db"], ["auth", "search"], ["gateway", "ui"]],
    )
    self.assertFalse(res["halt_triggered"])
    self.assertEqual(res["failed"], ["db"])
    self.assertEqual(res["blocked"], ["auth", "gateway"])
    self.assertEqual(res["deployed"], ["cache", "search", "ui"])

  def test_critical_halt_and_impact_radius(self) -> None:
    planner = DependencyReleasePlanner()
    planner.register_service("crit_db", "1.0.0", critical=True)
    planner.register_service("peer_w0", "1.0.0", critical=False)
    planner.register_service(
        "w1_svc", "1.0.0", depends_on=["peer_w0"], critical=False
    )
    res = planner.simulate_rollout(failed_services=["crit_db", "w1_svc"])
    self.assertTrue(res["halt_triggered"])
    self.assertEqual(res["deployed"], ["peer_w0"])
    self.assertEqual(res["failed"], ["crit_db"])
    self.assertEqual(res["blocked"], ["w1_svc"])
    self.assertEqual(planner.impact_radius("peer_w0"), ["w1_svc"])


if __name__ == "__main__":
  unittest.main()
