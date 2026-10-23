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
        self.scheduler.add_room("RoomA", 100)
        self.scheduler.add_room("RoomB", 150)
        self.scheduler.add_room("RoomC", 50)

    def test_add_room_validation(self) -> None:
        with self.assertRaises(ValueError):
            self.scheduler.add_room("", 50)
        with self.assertRaises(ValueError):
            self.scheduler.add_room("   ", 50)
        with self.assertRaises(ValueError):
            self.scheduler.add_room("RoomD", 0)
        with self.assertRaises(ValueError):
            self.scheduler.add_room("RoomD", -10)

    def test_schedule_talk_basic_and_validation(self) -> None:
        rec = self.scheduler.schedule_talk(
            "T1", "Intro to AI", "Alice", "RoomA", 60, 120, 80
        )
        self.assertEqual(rec["talk_id"], "T1")
        self.assertEqual(rec["room_id"], "RoomA")

        # Duplicate talk_id
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk(
                "T1", "Other", "Bob", "RoomB", 200, 260, 50
            )

        # Invalid parameters
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk(
                "", "Title", "Bob", "RoomB", 200, 260, 50
            )
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk(
                "T2", "Title", "Bob", "UnknownRoom", 200, 260, 50
            )

        # Invalid time window and duration
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk(
                "T2", "Title", "Bob", "RoomB", -1, 60, 50
            )
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk(
                "T2", "Title", "Bob", "RoomB", 1400, 1441, 50
            )
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk(
                "T2", "Title", "Bob", "RoomB", 100, 110, 50
            )
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk(
                "T2", "Title", "Bob", "RoomB", 100, 300, 50
            )

        # Invalid attendees
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk(
                "T2", "Title", "Bob", "RoomC", 200, 260, 60
            )
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk(
                "T2", "Title", "Bob", "RoomC", 200, 260, 0
            )

    def test_room_overlap_and_same_room_back_to_back(self) -> None:
        self.scheduler.schedule_talk(
            "T1", "Part 1", "Alice", "RoomA", 100, 160, 50
        )
        # Room overlap with another speaker
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk(
                "T2", "Conflict", "Bob", "RoomA", 150, 210, 50
            )
        # Same speaker, same room, back-to-back (both after and before) is allowed
        self.scheduler.schedule_talk(
            "T3", "Part 2", "Alice", "RoomA", 160, 220, 50
        )
        self.scheduler.schedule_talk(
            "T0", "Part 0", "Alice", "RoomA", 40, 100, 50
        )
        self.assertEqual(len(self.scheduler.talks), 3)

    def test_speaker_overlap_across_rooms(self) -> None:
        self.scheduler.schedule_talk(
            "T1", "Talk 1", "Alice", "RoomA", 100, 160, 50
        )
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk(
                "T2", "Talk 2", "Alice", "RoomB", 120, 180, 50
            )
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk(
                "T3", "Talk 3", "Alice", "RoomB", 80, 120, 50
            )

    def test_speaker_cross_room_cooldown_both_orders(self) -> None:
        # First talk at [100, 160] in RoomA
        self.scheduler.schedule_talk(
            "T1", "Talk 1", "Alice", "RoomA", 100, 160, 50
        )

        # Subsequent talk in RoomB starting < 15 mins after T1 ends -> rejected
        for start in (160, 165, 174):
            with self.assertRaises(ValueError):
                self.scheduler.schedule_talk(
                    "T_after_bad", "After Bad", "Alice", "RoomB", start, start + 30, 50
                )

        # Earlier talk in RoomB ending < 15 mins before T1 starts (scheduled second) -> rejected
        for end in (100, 95, 86):
            with self.assertRaises(ValueError):
                self.scheduler.schedule_talk(
                    "T_before_bad", "Before Bad", "Alice", "RoomB", end - 30, end, 50
                )

        # Exact 15-minute gap after T1 in RoomB -> allowed
        self.scheduler.schedule_talk(
            "T_after_ok", "After OK", "Alice", "RoomB", 175, 205, 50
        )
        # Exact 15-minute gap before T1 in RoomC -> allowed
        self.scheduler.schedule_talk(
            "T_before_ok", "Before OK", "Alice", "RoomC", 55, 85, 40
        )
        self.assertEqual(len(self.scheduler.talks), 3)

    def test_find_available_rooms_without_speaker(self) -> None:
        self.scheduler.schedule_talk(
            "T1", "Talk 1", "Alice", "RoomA", 100, 160, 50
        )
        # During [120, 150], RoomA is busy; RoomC (50) and RoomB (150) are free
        self.assertEqual(
            self.scheduler.find_available_rooms(120, 150, 50),
            ["RoomC", "RoomB"],
        )
        # With min_capacity 100, only RoomB is free
        self.assertEqual(
            self.scheduler.find_available_rooms(120, 150, 100),
            ["RoomB"],
        )

    def test_find_available_rooms_with_speaker(self) -> None:
        # Alice is in RoomA from 100 to 160
        self.scheduler.schedule_talk(
            "T1", "Talk 1", "Alice", "RoomA", 100, 160, 50
        )

        # 1. Overlapping window [120, 180]: Alice cannot use ANY room
        self.assertEqual(
            self.scheduler.find_available_rooms(120, 180, 50, speaker="Alice"),
            [],
        )
        # Another speaker (Bob) can still use RoomC and RoomB
        self.assertEqual(
            self.scheduler.find_available_rooms(120, 180, 50, speaker="Bob"),
            ["RoomC", "RoomB"],
        )

        # 2. Immediately after T1 [160, 190] or within 15 min [170, 200]:
        # Alice can only use RoomA (same room, no travel gap needed), not RoomB or RoomC
        self.assertEqual(
            self.scheduler.find_available_rooms(160, 190, 50, speaker="Alice"),
            ["RoomA"],
        )
        self.assertEqual(
            self.scheduler.find_available_rooms(174, 204, 50, speaker="Alice"),
            ["RoomA"],
        )

        # 3. Immediately before T1 [70, 100] or ending within 15 min before T1 [56, 86]:
        # Alice can only use RoomA, not RoomB or RoomC
        self.assertEqual(
            self.scheduler.find_available_rooms(70, 100, 50, speaker="Alice"),
            ["RoomA"],
        )
        self.assertEqual(
            self.scheduler.find_available_rooms(56, 86, 50, speaker="Alice"),
            ["RoomA"],
        )

        # 4. At least 15 minutes after T1 [175, 205] or 15 minutes before T1 [55, 85]:
        # All rooms meeting capacity are available for Alice
        self.assertEqual(
            self.scheduler.find_available_rooms(175, 205, 50, speaker="Alice"),
            ["RoomC", "RoomA", "RoomB"],
        )
        self.assertEqual(
            self.scheduler.find_available_rooms(55, 85, 50, speaker="Alice"),
            ["RoomC", "RoomA", "RoomB"],
        )

    def test_cancel_and_utilization(self) -> None:
        self.assertEqual(self.scheduler.get_room_utilization("RoomA"), 0.0)
        self.scheduler.schedule_talk(
            "T1", "Talk 1", "Alice", "RoomA", 100, 150, 50
        )
        self.scheduler.schedule_talk(
            "T2", "Talk 2", "Bob", "RoomA", 200, 300, 50
        )
        # occupied = 50 + 100 = 150, span = 300 - 100 = 200 -> 75.0%
        self.assertEqual(self.scheduler.get_room_utilization("RoomA"), 75.0)
        self.assertTrue(self.scheduler.cancel_talk("T2"))
        self.assertFalse(self.scheduler.cancel_talk("T2"))
        self.assertEqual(self.scheduler.get_room_utilization("RoomA"), 100.0)


if __name__ == "__main__":
    unittest.main()
