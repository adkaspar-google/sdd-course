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
        self.scheduler.add_room("RoomB", 50)
        self.scheduler.add_room("RoomC", 200)

    def test_add_room_and_validation(self) -> None:
        with self.assertRaises(ValueError):
            self.scheduler.add_room("", 50)
        with self.assertRaises(ValueError):
            self.scheduler.add_room("RoomD", 0)
        with self.assertRaises(ValueError):
            self.scheduler.add_room("RoomD", -10)

    def test_schedule_talk_validation_and_overlaps(self) -> None:
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("", "Title", "Alice", "RoomA", 60, 120, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("t1", "Title", "Alice", "Unknown", 60, 120, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("t1", "Title", "Alice", "RoomA", 60, 70, 50)
        with self.assertRaises(ValueError):
            self.scheduler.schedule_talk("t1", "Title", "Alice", "RoomA", 60, 120, 150)

        self.scheduler.schedule_talk("t1", "Title", "Alice", "RoomA", 60, 120, 50)
        with self.assertRaisesRegex(ValueError, "Duplicate talk_id"):
            self.scheduler.schedule_talk("t1", "Other", "Bob", "RoomB", 200, 260, 30)
        with self.assertRaisesRegex(ValueError, "Room overlap"):
            self.scheduler.schedule_talk("t2", "Other", "Bob", "RoomA", 90, 150, 30)
        with self.assertRaisesRegex(ValueError, "Speaker overlap"):
            self.scheduler.schedule_talk("t3", "Other", "Alice", "RoomB", 90, 150, 30)

    def test_schedule_talk_basic_and_same_room_back_to_back(self) -> None:
        t1 = self.scheduler.schedule_talk(
            "t1", "Intro", "Alice", "RoomA", 60, 120, 80
        )
        self.assertEqual(t1["talk_id"], "t1")
        # Back-to-back in the same room (after and before) should succeed
        t2 = self.scheduler.schedule_talk(
            "t2", "Deep Dive", "Alice", "RoomA", 120, 180, 80
        )
        self.assertEqual(t2["talk_id"], "t2")
        t0 = self.scheduler.schedule_talk(
            "t0", "Prequel", "Alice", "RoomA", 30, 60, 50
        )
        self.assertEqual(t0["talk_id"], "t0")

    def test_speaker_cooldown_different_room_forward_order(self) -> None:
        self.scheduler.schedule_talk(
            "t1", "Talk 1", "Alice", "RoomA", 60, 120, 50
        )
        # Starting in RoomB at 120 (0 min gap) or 134 (14 min gap) must fail
        with self.assertRaisesRegex(ValueError, "Speaker cooldown violation"):
            self.scheduler.schedule_talk(
                "t2", "Talk 2", "Alice", "RoomB", 120, 150, 30
            )
        with self.assertRaisesRegex(ValueError, "Speaker cooldown violation"):
            self.scheduler.schedule_talk(
                "t2", "Talk 2", "Alice", "RoomB", 134, 164, 30
            )
        # Exactly 15 min gap (starts at 135) is allowed
        t2 = self.scheduler.schedule_talk(
            "t2", "Talk 2", "Alice", "RoomB", 135, 165, 30
        )
        self.assertEqual(t2["talk_id"], "t2")

    def test_speaker_cooldown_different_room_reverse_order(self) -> None:
        # Later talk scheduled first: [120, 180] in RoomA
        self.scheduler.schedule_talk(
            "t_later", "Later Talk", "Alice", "RoomA", 120, 180, 50
        )
        # Earlier talk in RoomB ending at 120 (0 min gap) must fail
        with self.assertRaisesRegex(ValueError, "Speaker cooldown violation"):
            self.scheduler.schedule_talk(
                "t_earlier_0", "Earlier Talk", "Alice", "RoomB", 60, 120, 30
            )
        # Earlier talk in RoomB ending at 106 (14 min gap before 120) must fail
        with self.assertRaisesRegex(ValueError, "Speaker cooldown violation"):
            self.scheduler.schedule_talk(
                "t_earlier_14", "Earlier Talk", "Alice", "RoomB", 60, 106, 30
            )
        # Earlier talk in RoomB ending at 105 (15 min gap before 120) must succeed
        t_ok = self.scheduler.schedule_talk(
            "t_earlier_15", "Earlier Talk", "Alice", "RoomB", 60, 105, 30
        )
        self.assertEqual(t_ok["talk_id"], "t_earlier_15")

    def test_find_available_rooms_without_speaker(self) -> None:
        self.scheduler.schedule_talk(
            "t1", "Talk 1", "Alice", "RoomA", 60, 120, 50
        )
        # During [60, 120], RoomA is busy; RoomB (50) and RoomC (200) are free
        self.assertEqual(
            self.scheduler.find_available_rooms(60, 120, 50),
            ["RoomB", "RoomC"],
        )
        self.assertEqual(
            self.scheduler.find_available_rooms(60, 120, 100),
            ["RoomC"],
        )

    def test_find_available_rooms_with_speaker_overlap(self) -> None:
        self.scheduler.schedule_talk(
            "t1", "Talk 1", "Alice", "RoomA", 60, 120, 50
        )
        # Alice has a talk during [60, 120], so no rooms are available for Alice at [90, 150]
        self.assertEqual(
            self.scheduler.find_available_rooms(90, 150, 30, speaker="Alice"),
            [],
        )
        # Bob has no conflicts at [90, 150], so RoomB and RoomC are available
        self.assertEqual(
            self.scheduler.find_available_rooms(90, 150, 30, speaker="Bob"),
            ["RoomB", "RoomC"],
        )

    def test_find_available_rooms_with_speaker_cross_room_cooldown(self) -> None:
        self.scheduler.schedule_talk(
            "t1", "Talk 1", "Alice", "RoomA", 60, 120, 50
        )
        # Immediately after [120, 150] (0 min gap) or [130, 160] (10 min gap):
        # Alice can only use RoomA (same room back-to-back is allowed), not RoomB or RoomC!
        self.assertEqual(
            self.scheduler.find_available_rooms(120, 150, 30, speaker="Alice"),
            ["RoomA"],
        )
        self.assertEqual(
            self.scheduler.find_available_rooms(130, 160, 30, speaker="Alice"),
            ["RoomA"],
        )
        # Immediately before [30, 60] (0 min gap) or [20, 50] (10 min gap):
        # Alice can only use RoomA, not RoomB or RoomC!
        self.assertEqual(
            self.scheduler.find_available_rooms(30, 60, 30, speaker="Alice"),
            ["RoomA"],
        )
        self.assertEqual(
            self.scheduler.find_available_rooms(20, 50, 30, speaker="Alice"),
            ["RoomA"],
        )
        # With >= 15 min gap after ([135, 165]) or before ([15, 45]): all rooms available
        self.assertEqual(
            self.scheduler.find_available_rooms(135, 165, 30, speaker="Alice"),
            ["RoomB", "RoomA", "RoomC"],
        )
        self.assertEqual(
            self.scheduler.find_available_rooms(15, 45, 30, speaker="Alice"),
            ["RoomB", "RoomA", "RoomC"],
        )

    def test_cancel_talk_and_utilization(self) -> None:
        self.scheduler.schedule_talk("t1", "Talk 1", "Alice", "RoomA", 60, 120, 50)
        self.scheduler.schedule_talk("t2", "Talk 2", "Bob", "RoomA", 180, 240, 50)
        self.assertEqual(self.scheduler.get_room_utilization("RoomA"), 66.67)
        self.assertTrue(self.scheduler.cancel_talk("t2"))
        self.assertFalse(self.scheduler.cancel_talk("t2"))
        self.assertEqual(self.scheduler.get_room_utilization("RoomA"), 100.0)


if __name__ == "__main__":
    unittest.main()
