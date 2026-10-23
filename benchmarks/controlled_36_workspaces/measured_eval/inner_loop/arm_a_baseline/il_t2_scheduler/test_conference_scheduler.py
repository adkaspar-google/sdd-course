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
"""Unit tests for ConferenceScheduler."""

import unittest
from conference_scheduler import ConferenceScheduler


class TestConferenceScheduler(unittest.TestCase):

    def setUp(self) -> None:
        self.s = ConferenceScheduler()
        self.s.add_room("R1", 50)
        self.s.add_room("R2", 100)
        self.s.add_room("A1", 50)

    def test_add_room_validation(self) -> None:
        with self.assertRaises(ValueError):
            self.s.add_room("", 50)
        with self.assertRaises(ValueError):
            self.s.add_room("   ", 50)
        with self.assertRaises(ValueError):
            self.s.add_room("R3", 0)
        with self.assertRaises(ValueError):
            self.s.add_room("R3", -10)

    def test_schedule_talk_validation(self) -> None:
        # Empty fields
        with self.assertRaises(ValueError):
            self.s.schedule_talk("", "Title", "Alice", "R1", 60, 120, 10)
        with self.assertRaises(ValueError):
            self.s.schedule_talk("  ", "Title", "Alice", "R1", 60, 120, 10)
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T1", "", "Alice", "R1", 60, 120, 10)
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T1", "Title", "", "R1", 60, 120, 10)
        # Unknown room
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T1", "Title", "Alice", "UNKNOWN", 60, 120, 10)
        # Time bounds
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T1", "Title", "Alice", "R1", -1, 60, 10)
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T1", "Title", "Alice", "R1", 1400, 1441, 10)
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T1", "Title", "Alice", "R1", 60, 60, 10)
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T1", "Title", "Alice", "R1", 70, 60, 10)
        # Duration bounds (15 <= duration <= 180)
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T1", "Title", "Alice", "R1", 60, 74, 10)
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T1", "Title", "Alice", "R1", 60, 241, 10)
        # Attendees bounds (0 < expected_attendees <= capacity)
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T1", "Title", "Alice", "R1", 60, 120, 0)
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T1", "Title", "Alice", "R1", 60, 120, -5)
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T1", "Title", "Alice", "R1", 60, 120, 51)

        # Valid boundary cases
        rec = self.s.schedule_talk("T1", "Title", "Alice", "R1", 0, 15, 50)
        self.assertEqual(rec["talk_id"], "T1")
        # Duplicate talk_id
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T1", "Other", "Bob", "R2", 200, 260, 10)

    def test_room_conflicts_and_back_to_back(self) -> None:
        self.s.schedule_talk("T1", "Talk 1", "Alice", "R1", 60, 120, 30)
        # Overlapping in R1 fails
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T2", "Talk 2", "Bob", "R1", 90, 150, 30)
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T2", "Talk 2", "Bob", "R1", 30, 90, 30)
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T2", "Talk 2", "Bob", "R1", 60, 120, 30)
        # Back-to-back in R1 succeeds
        self.s.schedule_talk("T2", "Talk 2", "Bob", "R1", 120, 180, 30)
        self.s.schedule_talk("T3", "Talk 3", "Charlie", "R1", 0, 60, 30)

    def test_speaker_conflict_and_cooldown(self) -> None:
        self.s.schedule_talk("T1", "Talk 1", "Alice", "R1", 100, 160, 30)
        # Same speaker in same room back-to-back (0 min gap) is allowed
        self.s.schedule_talk("T2", "Talk 2", "Alice", "R1", 160, 200, 30)
        # Same speaker in different room with < 15 min gap after T2 fails
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T3", "Talk 3", "Alice", "R2", 200, 230, 30)
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T3", "Talk 3", "Alice", "R2", 214, 244, 30)
        # Exactly 15 min gap after T2 in R2 succeeds
        self.s.schedule_talk("T3", "Talk 3", "Alice", "R2", 215, 245, 30)
        # Before T1 in R2: < 15 min gap fails
        with self.assertRaises(ValueError):
            self.s.schedule_talk("T4", "Talk 4", "Alice", "R2", 56, 86, 30)
        # Before T1 in R2: 15 min gap (ends at 85) succeeds
        self.s.schedule_talk("T4", "Talk 4", "Alice", "R2", 55, 85, 30)

    def test_cancel_talk_and_utilization(self) -> None:
        with self.assertRaises(ValueError):
            self.s.get_room_utilization("NO_ROOM")
        self.assertEqual(self.s.get_room_utilization("R1"), 0.0)
        self.s.schedule_talk("T1", "Talk 1", "Alice", "R1", 60, 120, 20)
        self.assertEqual(self.s.get_room_utilization("R1"), 100.0)
        self.s.schedule_talk("T2", "Talk 2", "Bob", "R1", 180, 240, 20)
        # span = 240 - 60 = 180, occupied = 120 -> 66.67%
        self.assertEqual(self.s.get_room_utilization("R1"), 66.67)
        self.assertFalse(self.s.cancel_talk("NON_EXISTENT"))
        self.assertTrue(self.s.cancel_talk("T2"))
        self.assertEqual(self.s.get_room_utilization("R1"), 100.0)

    def test_find_available_rooms(self) -> None:
        # Sorted by capacity ascending, then room_id ascending: A1 (50), R1 (50), R2 (100)
        self.assertEqual(
            self.s.find_available_rooms(60, 120, 40),
            ["A1", "R1", "R2"],
        )
        self.assertEqual(
            self.s.find_available_rooms(60, 120, 60),
            ["R2"],
        )
        self.s.schedule_talk("T1", "Talk 1", "Alice", "R1", 60, 120, 30)
        # During [120, 150], for Alice: R1 is same room (0-min gap ok), A1 and R2 violate 15-min cross-room cooldown!
        self.assertEqual(
            self.s.find_available_rooms(120, 150, 20, speaker="Alice"),
            ["R1"],
        )
        # Without speaker or for Bob, all 3 rooms are free during [120, 150]
        self.assertEqual(
            self.s.find_available_rooms(120, 150, 20, speaker="Bob"),
            ["A1", "R1", "R2"],
        )
        # At [135, 165], Alice has 15-min cooldown satisfied for A1 and R2 too
        self.assertEqual(
            self.s.find_available_rooms(135, 165, 20, speaker="Alice"),
            ["A1", "R1", "R2"],
        )


if __name__ == "__main__":
    unittest.main()
