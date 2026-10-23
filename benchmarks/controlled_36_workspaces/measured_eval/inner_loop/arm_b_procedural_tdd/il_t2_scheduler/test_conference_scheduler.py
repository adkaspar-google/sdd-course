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
        self.scheduler = ConferenceScheduler()

    def test_add_room_valid_and_invalid(self) -> None:
        self.scheduler.add_room("R1", 100)
        self.scheduler.add_room("  R2  ", 50)
        self.assertEqual(self.scheduler.rooms["R1"], 100)
        self.assertEqual(self.scheduler.rooms["R2"], 50)

        with self.assertRaises(ValueError):
            self.scheduler.add_room("", 50)
        with self.assertRaises(ValueError):
            self.scheduler.add_room("   ", 50)
        with self.assertRaises(ValueError):
            self.scheduler.add_room("R3", 0)
        with self.assertRaises(ValueError):
            self.scheduler.add_room("R3", -10)

    def test_schedule_talk_validation(self) -> None:
        self.scheduler.add_room("R1", 100)

        # Valid talk
        talk = self.scheduler.schedule_talk(
            "T1", "Keynote", "Alice", "R1", 540, 600, 80
        )
        self.assertEqual(talk["talk_id"], "T1")
        self.assertEqual(talk["room_id"], "R1")
        self.assertEqual(talk["expected_attendees"], 80)

        # Duplicate talk_id
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk(
                "T1", "Another", "Bob", "R1", 600, 660, 50
            )

        # Empty fields
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("", "Title", "Bob", "R1", 600, 660, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("  ", "Title", "Bob", "R1", 600, 660, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "", "Bob", "R1", 600, 660, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "   ", "Bob", "R1", 600, 660, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Title", "", "R1", 600, 660, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Title", "  ", "R1", 600, 660, 50)

        # Unknown room
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk(
                "T2", "Title", "Bob", "UNKNOWN", 600, 660, 50
            )

        # Time bounds: 0 <= start_min < end_min <= 1440
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Title", "Bob", "R1", -1, 30, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Title", "Bob", "R1", 1400, 1441, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Title", "Bob", "R1", 600, 600, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Title", "Bob", "R1", 660, 600, 50)

        # Duration bounds: 15 <= (end_min - start_min) <= 180
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Title", "Bob", "R1", 600, 614, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Title", "Bob", "R1", 600, 781, 50)

        # Boundary durations: 15 and 180 allowed
        self.scheduler.schedule_talk("T_15", "Short", "Bob", "R1", 0, 15, 1)
        self.scheduler.schedule_talk("T_180", "Long", "Charlie", "R1", 1260, 1440, 100)

        # Attendee bounds: 0 < expected_attendees <= capacity
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Title", "Bob", "R1", 600, 630, 0)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Title", "Bob", "R1", 600, 630, -5)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Title", "Bob", "R1", 600, 630, 101)

    def test_room_conflict_and_back_to_back(self) -> None:
        self.scheduler.add_room("R1", 100)
        self.scheduler.schedule_talk("T1", "Talk 1", "Alice", "R1", 100, 160, 50)

        # Overlapping in same room rejected
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Talk 2", "Bob", "R1", 150, 200, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Talk 2", "Bob", "R1", 80, 110, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Talk 2", "Bob", "R1", 110, 150, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Talk 2", "Bob", "R1", 90, 170, 50)

        # Back-to-back in same room allowed (both before and after)
        self.scheduler.schedule_talk("T_before", "Before", "Bob", "R1", 40, 100, 50)
        self.scheduler.schedule_talk("T_after", "After", "Charlie", "R1", 160, 220, 50)

    def test_speaker_conflict_and_cross_room_cooldown(self) -> None:
        self.scheduler.add_room("R1", 100)
        self.scheduler.add_room("R2", 100)

        self.scheduler.schedule_talk("T1", "Talk 1", "Alice", "R1", 100, 160, 50)

        # Overlapping talk by same speaker in different room rejected
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Talk 2", "Alice", "R2", 120, 180, 50)

        # Cross-room cooldown < 15 min after T1 rejected
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Talk 2", "Alice", "R2", 160, 200, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Talk 2", "Alice", "R2", 174, 200, 50)

        # Cross-room cooldown < 15 min before T1 rejected
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Talk 2", "Alice", "R2", 60, 100, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("T2", "Talk 2", "Alice", "R2", 60, 86, 50)

        # Cross-room cooldown == 15 min allowed in both directions
        self.scheduler.schedule_talk("T_before_15", "Before 15", "Alice", "R2", 55, 85, 50)
        # Same-room back-to-back (0 min gap) for same speaker IS allowed
        self.scheduler.schedule_talk("T_same_room", "Same Room", "Alice", "R1", 160, 175, 50)
        # And 15 min after T_same_room in R2 IS allowed
        self.scheduler.schedule_talk("T_after_15", "After 15", "Alice", "R2", 190, 220, 50)

    def test_cancel_talk(self) -> None:
        self.scheduler.add_room("R1", 100)
        self.scheduler.schedule_talk("T1", "Talk 1", "Alice", "R1", 100, 160, 50)

        self.assertFalse(self.scheduler.cancel_talk("NON_EXISTENT"))
        self.assertTrue(self.scheduler.cancel_talk("T1"))
        self.assertFalse(self.scheduler.cancel_talk("T1"))

        # Slot is now free again
        self.scheduler.schedule_talk("T2", "Talk 2", "Bob", "R1", 100, 160, 50)

    def test_get_room_utilization(self) -> None:
        self.scheduler.add_room("R1", 100)
        self.scheduler.add_room("R2", 100)

        with self.assertRaises(ValueError):
            self.scheduler.get_room_utilization("UNKNOWN")

        # Empty room -> 0.0
        self.assertEqual(self.scheduler.get_room_utilization("R1"), 0.0)

        # Single talk -> 100.0% of its span
        self.scheduler.schedule_talk("T1", "Talk 1", "Alice", "R1", 60, 120, 50)
        self.assertEqual(self.scheduler.get_room_utilization("R1"), 100.0)

        # Two talks: [60, 120] (60m) and [180, 240] (60m) -> span [60, 240] = 180m -> 120/180 = 66.67%
        self.scheduler.schedule_talk("T2", "Talk 2", "Bob", "R1", 180, 240, 50)
        self.assertEqual(self.scheduler.get_room_utilization("R1"), 66.67)

    def test_find_available_rooms(self) -> None:
        self.scheduler.add_room("R_big", 200)
        self.scheduler.add_room("R_med_b", 100)
        self.scheduler.add_room("R_med_a", 100)
        self.scheduler.add_room("R_small", 30)

        # Sorted by capacity ascending, then room_id alphabetically
        avail = self.scheduler.find_available_rooms(100, 160, 50)
        self.assertEqual(avail, ["R_med_a", "R_med_b", "R_big"])

        # Schedule Alice in R_med_a from 100 to 160
        self.scheduler.schedule_talk("T1", "Talk 1", "Alice", "R_med_a", 100, 160, 50)

        # During [120, 150], R_med_a is busy; for Bob, R_med_b and R_big are free
        self.assertEqual(
            self.scheduler.find_available_rooms(120, 150, 50, speaker="Bob"),
            ["R_med_b", "R_big"],
        )
        # During [120, 150], Alice overlaps with T1 so no rooms are free for Alice
        self.assertEqual(
            self.scheduler.find_available_rooms(120, 150, 50, speaker="Alice"),
            [],
        )

        # Back-to-back [160, 190] for Alice:
        # R_med_a IS available (same room, 0-min gap allowed!)
        # R_med_b and R_big are NOT available (different room, needs 15-min cooldown!)
        self.assertEqual(
            self.scheduler.find_available_rooms(160, 190, 50, speaker="Alice"),
            ["R_med_a"],
        )

        # After 15-min cooldown [175, 205] for Alice: all rooms >= 50 cap available
        self.assertEqual(
            self.scheduler.find_available_rooms(175, 205, 50, speaker="Alice"),
            ["R_med_a", "R_med_b", "R_big"],
        )


if __name__ == "__main__":
    unittest.main()
