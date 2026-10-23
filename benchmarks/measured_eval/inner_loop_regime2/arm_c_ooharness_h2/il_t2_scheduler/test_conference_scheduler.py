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
        self.scheduler = ConferenceScheduler()
        self.scheduler.add_room("R1", 50)
        self.scheduler.add_room("R2", 100)
        self.scheduler.add_room("R3", 50)

    def test_same_room_back_to_back_allowed_both_directions(self) -> None:
        self.scheduler.schedule_talk("T1", "Intro", "Alice", "R1", 60, 90, 40)
        # Immediately after in same room (gap = 0)
        t2 = self.scheduler.schedule_talk("T2", "Part 2", "Alice", "R1", 90, 120, 40)
        self.assertEqual(t2["talk_id"], "T2")
        # Immediately before in same room (gap = 0)
        t0 = self.scheduler.schedule_talk("T0", "Part 0", "Alice", "R1", 30, 60, 40)
        self.assertEqual(t0["talk_id"], "T0")

    def test_cross_room_speaker_cooldown_forward_and_backward(self) -> None:
        self.scheduler.schedule_talk("T1", "Main Talk", "Alice", "R1", 100, 130, 50)

        # Forward: second talk in R2 starts at 130 (gap 0) or 144 (gap 14) -> blocked
        with self.assertRaisesRegex(ValueError, "Speaker cooldown violation"):
            self.scheduler.schedule_talk("T2", "Followup", "Alice", "R2", 130, 160, 50)
        with self.assertRaisesRegex(ValueError, "Speaker cooldown violation"):
            self.scheduler.schedule_talk("T2", "Followup", "Alice", "R2", 144, 174, 50)

        # Backward: earlier talk in R2 ends at 100 (gap 0) or 86 (gap 14) -> blocked
        with self.assertRaisesRegex(ValueError, "Speaker cooldown violation"):
            self.scheduler.schedule_talk("T0", "Prequel", "Alice", "R2", 70, 100, 50)
        with self.assertRaisesRegex(ValueError, "Speaker cooldown violation"):
            self.scheduler.schedule_talk("T0", "Prequel", "Alice", "R2", 56, 86, 50)

        # Exact 15-minute boundary in both directions -> allowed
        t_after = self.scheduler.schedule_talk("T_after", "After", "Alice", "R2", 145, 175, 50)
        self.assertEqual(t_after["start_min"], 145)
        t_before = self.scheduler.schedule_talk("T_before", "Before", "Alice", "R2", 55, 85, 50)
        self.assertEqual(t_before["end_min"], 85)

    def test_speaker_direct_overlap_rejected(self) -> None:
        self.scheduler.schedule_talk("T1", "Talk 1", "Alice", "R1", 100, 130, 40)
        with self.assertRaisesRegex(ValueError, "Speaker overlap"):
            self.scheduler.schedule_talk("T2", "Talk 2", "Alice", "R2", 120, 150, 40)
        with self.assertRaisesRegex(ValueError, "Speaker overlap"):
            self.scheduler.schedule_talk("T3", "Talk 3", "Alice", "R2", 80, 110, 40)

    def test_find_available_rooms_without_and_with_speaker(self) -> None:
        # Alice is in R1 from 100 to 130
        self.scheduler.schedule_talk("T1", "Talk 1", "Alice", "R1", 100, 130, 50)

        # Without speaker: R2 and R3 are available during [100, 130]
        self.assertEqual(self.scheduler.find_available_rooms(100, 130, 50), ["R3", "R2"])

        # With speaker="Alice" during [100, 130]: overlapping, so no rooms available
        self.assertEqual(
            self.scheduler.find_available_rooms(100, 130, 50, speaker="Alice"),
            [],
        )

        # Immediately after [130, 160] for Alice:
        # R1 (same room, 0 gap) is available; R2 and R3 (different rooms, 0 < 15 gap) are NOT!
        self.assertEqual(
            self.scheduler.find_available_rooms(130, 160, 50, speaker="Alice"),
            ["R1"],
        )

        # 14 minutes after [144, 174] for Alice: only R1 is available
        self.assertEqual(
            self.scheduler.find_available_rooms(144, 174, 50, speaker="Alice"),
            ["R1"],
        )

        # 15 minutes after [145, 175] for Alice: all rooms >= 50 capacity are available
        self.assertEqual(
            self.scheduler.find_available_rooms(145, 175, 50, speaker="Alice"),
            ["R1", "R3", "R2"],
        )

        # Immediately before [70, 100] for Alice: only R1 is available
        self.assertEqual(
            self.scheduler.find_available_rooms(70, 100, 50, speaker="Alice"),
            ["R1"],
        )

        # 14 minutes before [56, 86] for Alice: only R1 is available
        self.assertEqual(
            self.scheduler.find_available_rooms(56, 86, 50, speaker="Alice"),
            ["R1"],
        )

        # 15 minutes before [55, 85] for Alice: all rooms are available
        self.assertEqual(
            self.scheduler.find_available_rooms(55, 85, 50, speaker="Alice"),
            ["R1", "R3", "R2"],
        )

    def test_capacity_and_duration_boundaries(self) -> None:
        # Exact 15-min and 180-min duration and exact 50-seat capacity bounds
        t_min = self.scheduler.schedule_talk("T_min", "Short", "Bob", "R1", 0, 15, 50)
        self.assertEqual(t_min["expected_attendees"], 50)
        t_max = self.scheduler.schedule_talk("T_max", "Long", "Bob", "R1", 1260, 1440, 1)
        self.assertEqual(t_max["end_min"] - t_max["start_min"], 180)

        with self.assertRaisesRegex(ValueError, "Invalid talk duration"):
            self.scheduler.schedule_talk("T_too_short", "Too Short", "Bob", "R2", 200, 214, 10)
        with self.assertRaisesRegex(ValueError, "Invalid talk duration"):
            self.scheduler.schedule_talk("T_too_long", "Too Long", "Bob", "R2", 200, 381, 10)
        with self.assertRaisesRegex(ValueError, "Invalid attendees"):
            self.scheduler.schedule_talk("T_over_cap", "Over Cap", "Bob", "R1", 200, 230, 51)


if __name__ == "__main__":
    unittest.main()
