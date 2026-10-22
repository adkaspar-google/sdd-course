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
"""Unit tests for ConferenceScheduler using OO-Harness + Harness^2 boundary probes."""

import unittest
from conference_scheduler import ConferenceScheduler


class TestConferenceScheduler(unittest.TestCase):

  def setUp(self) -> None:
    self.sched = ConferenceScheduler()
    self.sched.add_room("RoomB", 100)
    self.sched.add_room("RoomA", 100)
    self.sched.add_room("SmallRoom", 30)
    self.sched.add_room("LargeRoom", 250)

  def test_schedule_talk_exact_boundaries(self) -> None:
    talk1 = self.sched.schedule_talk(
        "t1", "Opening", "Alice", "SmallRoom", 0, 15, 1
    )
    self.assertEqual(talk1["talk_id"], "t1")
    talk2 = self.sched.schedule_talk(
        "t2", "Closing", "Bob", "SmallRoom", 1260, 1440, 30
    )
    self.assertEqual(talk2["expected_attendees"], 30)

    for bad_args in [
        ("t3", "Short", "Carol", "RoomA", 100, 114, 10),
        ("t3", "Long", "Carol", "RoomA", 100, 281, 10),
        ("t3", "DayEnd", "Carol", "RoomA", 1400, 1441, 10),
        ("t3", "OverCap", "Carol", "SmallRoom", 100, 130, 31),
    ]:
      with self.assertRaises(ValueError):
        self.sched.schedule_talk(*bad_args)

  def test_speaker_bidirectional_cross_room_cooldown(self) -> None:
    self.sched.schedule_talk("t1", "Alice 1", "Alice", "RoomA", 100, 160, 50)
    with self.assertRaises(ValueError):
      self.sched.schedule_talk(
          "t_after_14", "Alice A14", "Alice", "RoomB", 174, 204, 50
      )
    with self.assertRaises(ValueError):
      self.sched.schedule_talk(
          "t_before_14", "Alice B14", "Alice", "RoomB", 56, 86, 50
      )
    self.sched.schedule_talk(
        "t_after_15", "Alice A15", "Alice", "RoomB", 175, 205, 50
    )
    self.sched.schedule_talk(
        "t_before_15", "Alice B15", "Alice", "RoomB", 55, 85, 50
    )

  def test_utilization_and_available_rooms(self) -> None:
    self.sched.schedule_talk("t1", "T1", "Alice", "RoomA", 60, 120, 50)
    self.sched.schedule_talk("t2", "T2", "Bob", "RoomA", 180, 240, 50)
    self.assertEqual(self.sched.get_room_utilization("RoomA"), 66.67)
    self.assertEqual(
        self.sched.find_available_rooms(120, 150, 10, speaker="Alice"),
        ["RoomA"],
    )


if __name__ == "__main__":
  unittest.main()
