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
"""Comprehensive boundary and equivalence-class unit tests for ConferenceScheduler."""

import unittest
from conference_scheduler import ConferenceScheduler


class TestConferenceScheduler(unittest.TestCase):
    def setUp(self) -> None:
        self.sched = ConferenceScheduler()
        self.sched.add_room("RoomB", 100)
        self.sched.add_room("RoomA", 100)
        self.sched.add_room("SmallRoom", 30)
        self.sched.add_room("LargeRoom", 250)

    def test_out_of_scope_methods_not_implemented(self) -> None:
        self.assertFalse(hasattr(self.sched, "export_markdown_schedule"))
        self.assertFalse(hasattr(self.sched, "auto_assign_catering"))

    def test_add_room_validation(self) -> None:
        with self.assertRaises(ValueError):
            self.sched.add_room("", 50)
        with self.assertRaises(ValueError):
            self.sched.add_room("   ", 50)
        with self.assertRaises(ValueError):
            self.sched.add_room("RoomZ", 0)
        with self.assertRaises(ValueError):
            self.sched.add_room("RoomZ", -10)

    def test_schedule_talk_basic_and_validation_boundaries(self) -> None:
        # Valid boundary: start_min=0, duration=15, attendees=1
        talk1 = self.sched.schedule_talk(
            "t1", "Opening", "Alice", "SmallRoom", 0, 15, 1
        )
        self.assertEqual(talk1["talk_id"], "t1")
        self.assertEqual(talk1["start_min"], 0)
        self.assertEqual(talk1["end_min"], 15)
        self.assertEqual(talk1["expected_attendees"], 1)

        # Valid boundary: end_min=1440, duration=180, attendees=capacity (30)
        talk2 = self.sched.schedule_talk(
            "t2", "Closing Marathon", "Bob", "SmallRoom", 1260, 1440, 30
        )
        self.assertEqual(talk2["talk_id"], "t2")

        # Duplicate talk_id rejected
        with self.assertRaises(ValueError):
            self.sched.schedule_talk(
                "t1", "Another Title", "Charlie", "RoomA", 200, 230, 10
            )

        # Empty strings rejected
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("", "Title", "Charlie", "RoomA", 200, 230, 10)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("  ", "Title", "Charlie", "RoomA", 200, 230, 10)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t3", "", "Charlie", "RoomA", 200, 230, 10)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t3", "   ", "Charlie", "RoomA", 200, 230, 10)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t3", "Title", "", "RoomA", 200, 230, 10)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t3", "Title", "   ", "RoomA", 200, 230, 10)

        # Unregistered room
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t3", "Title", "Charlie", "Unknown", 200, 230, 10)

        # Time range boundaries: start_min < 0 or end_min > 1440 or start >= end
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t3", "Title", "Charlie", "RoomA", -1, 20, 10)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t3", "Title", "Charlie", "RoomA", 1420, 1441, 10)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t3", "Title", "Charlie", "RoomA", 100, 100, 10)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t3", "Title", "Charlie", "RoomA", 120, 100, 10)

        # Duration boundaries: 14 min (< 15) and 181 min (> 180)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t3", "Too Short", "Charlie", "RoomA", 100, 114, 10)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t3", "Too Long", "Charlie", "RoomA", 100, 281, 10)

        # Attendees boundaries: 0, negative, capacity + 1
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t3", "Zero Att", "Charlie", "SmallRoom", 100, 130, 0)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t3", "Neg Att", "Charlie", "SmallRoom", 100, 130, -5)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t3", "Over Cap", "Charlie", "SmallRoom", 100, 130, 31)

    def test_room_conflict_and_back_to_back(self) -> None:
        self.sched.schedule_talk("t1", "Talk 1", "Alice", "RoomA", 60, 120, 50)

        # Overlapping in RoomA -> rejected
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t2", "Overlap 1", "Bob", "RoomA", 60, 120, 50)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t2", "Overlap 2", "Bob", "RoomA", 90, 150, 50)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t2", "Overlap 3", "Bob", "RoomA", 30, 90, 50)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t2", "Overlap 4", "Bob", "RoomA", 70, 110, 50)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t2", "Overlap 5", "Bob", "RoomA", 30, 150, 50)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t2", "Overlap 1min", "Bob", "RoomA", 119, 150, 50)

        # Back-to-back after (120 to 150) and before (30 to 60) -> allowed!
        self.sched.schedule_talk("t_after", "After", "Bob", "RoomA", 120, 150, 50)
        self.sched.schedule_talk("t_before", "Before", "Charlie", "RoomA", 30, 60, 50)

    def test_speaker_conflict_and_bidirectional_cross_room_cooldown(self) -> None:
        # Alice speaks in RoomA [100, 160]
        self.sched.schedule_talk("t1", "Alice 1", "Alice", "RoomA", 100, 160, 50)

        # Same speaker overlapping in another room -> rejected
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t_ov", "Alice Ov", "Alice", "RoomB", 150, 180, 50)

        # Different room AFTER: gap 0 (160) and gap 14 (174) -> rejected
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t_after_0", "Alice A0", "Alice", "RoomB", 160, 190, 50)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t_after_14", "Alice A14", "Alice", "RoomB", 174, 204, 50)

        # Different room BEFORE: gap 0 (end=100) and gap 14 (end=86) -> rejected
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t_before_0", "Alice B0", "Alice", "RoomB", 70, 100, 50)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("t_before_14", "Alice B14", "Alice", "RoomB", 56, 86, 50)

        # Different room AFTER with exact 15-min gap (start=175) -> allowed!
        self.sched.schedule_talk("t_after_15", "Alice A15", "Alice", "RoomB", 175, 205, 50)

        # Different room BEFORE with exact 15-min gap (end=85) -> allowed!
        self.sched.schedule_talk("t_before_15", "Alice B15", "Alice", "RoomB", 55, 85, 50)

        # Same room back-to-back (0-min gap) for same speaker -> allowed!
        # Bob speaks in RoomA [300, 330], then [330, 360], and [270, 300] in RoomA
        self.sched.schedule_talk("b1", "Bob 1", "Bob", "RoomA", 300, 330, 40)
        self.sched.schedule_talk("b2", "Bob 2", "Bob", "RoomA", 330, 360, 40)
        self.sched.schedule_talk("b0", "Bob 0", "Bob", "RoomA", 270, 300, 40)

    def test_cancel_talk(self) -> None:
        self.assertFalse(self.sched.cancel_talk("nonexistent"))
        self.sched.schedule_talk("t1", "Talk 1", "Alice", "RoomA", 60, 120, 50)
        self.assertTrue(self.sched.cancel_talk("t1"))
        self.assertFalse(self.sched.cancel_talk("t1"))

        # Now t1 and slot [60, 120] in RoomA are free again
        self.sched.schedule_talk("t1", "Talk 1 Reborn", "Alice", "RoomB", 60, 120, 50)

    def test_get_room_utilization(self) -> None:
        with self.assertRaises(ValueError):
            self.sched.get_room_utilization("UnknownRoom")

        # Empty room -> 0.0
        self.assertEqual(self.sched.get_room_utilization("RoomA"), 0.0)

        # Single talk [60, 120] -> 100.0
        self.sched.schedule_talk("t1", "T1", "Alice", "RoomA", 60, 120, 50)
        self.assertEqual(self.sched.get_room_utilization("RoomA"), 100.0)

        # Second talk [150, 180]: occupied = 60 + 30 = 90, span = 180 - 60 = 120 -> 75.0
        self.sched.schedule_talk("t2", "T2", "Bob", "RoomA", 150, 180, 50)
        self.assertEqual(self.sched.get_room_utilization("RoomA"), 75.0)

        # Third talk [210, 240]: occupied = 60 + 30 + 30 = 120, span = 240 - 60 = 180 -> 66.67
        self.sched.schedule_talk("t3", "T3", "Charlie", "RoomA", 210, 240, 50)
        self.assertEqual(self.sched.get_room_utilization("RoomA"), 66.67)

    def test_find_available_rooms(self) -> None:
        # Initial order: SmallRoom (30), RoomA (100), RoomB (100), LargeRoom (250)
        self.assertEqual(
            self.sched.find_available_rooms(60, 120, 30),
            ["SmallRoom", "RoomA", "RoomB", "LargeRoom"],
        )
        self.assertEqual(
            self.sched.find_available_rooms(60, 120, 31),
            ["RoomA", "RoomB", "LargeRoom"],
        )
        self.assertEqual(
            self.sched.find_available_rooms(60, 120, 100),
            ["RoomA", "RoomB", "LargeRoom"],
        )

        # Schedule Alice in RoomA [100, 160]
        self.sched.schedule_talk("t1", "T1", "Alice", "RoomA", 100, 160, 50)

        # During [120, 150] without speaker: RoomA is busy
        self.assertEqual(
            self.sched.find_available_rooms(120, 150, 10),
            ["SmallRoom", "RoomB", "LargeRoom"],
        )

        # During [160, 190] without speaker: RoomA is free (back-to-back)
        self.assertEqual(
            self.sched.find_available_rooms(160, 190, 10),
            ["SmallRoom", "RoomA", "RoomB", "LargeRoom"],
        )

        # During [160, 190] WITH speaker="Alice":
        # Only RoomA is available! Cross-room requires 15-min gap (175).
        self.assertEqual(
            self.sched.find_available_rooms(160, 190, 10, speaker="Alice"),
            ["RoomA"],
        )
        # At [174, 204] WITH speaker="Alice": still only RoomA (gap 14 < 15)
        self.assertEqual(
            self.sched.find_available_rooms(174, 204, 10, speaker="Alice"),
            ["RoomA"],
        )
        # At [175, 205] WITH speaker="Alice": all rooms with cap >= 10 available!
        self.assertEqual(
            self.sched.find_available_rooms(175, 205, 10, speaker="Alice"),
            ["SmallRoom", "RoomA", "RoomB", "LargeRoom"],
        )
        # Before [100, 160]: at [56, 86] (gap 14) -> only RoomA
        self.assertEqual(
            self.sched.find_available_rooms(56, 86, 10, speaker="Alice"),
            ["RoomA"],
        )
        # Before [100, 160]: at [55, 85] (gap 15) -> all rooms
        self.assertEqual(
            self.sched.find_available_rooms(55, 85, 10, speaker="Alice"),
            ["SmallRoom", "RoomA", "RoomB", "LargeRoom"],
        )
        # Overlapping [150, 180] WITH speaker="Alice": no rooms available
        self.assertEqual(
            self.sched.find_available_rooms(150, 180, 10, speaker="Alice"),
            [],
        )


if __name__ == "__main__":
    unittest.main()
