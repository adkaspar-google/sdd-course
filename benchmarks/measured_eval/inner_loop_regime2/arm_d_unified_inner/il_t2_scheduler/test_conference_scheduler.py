"""Unit tests for ConferenceScheduler."""

import unittest
from conference_scheduler import ConferenceScheduler


class TestConferenceScheduler(unittest.TestCase):
    def setUp(self) -> None:
        self.sched = ConferenceScheduler()
        self.sched.add_room("R1", 100)
        self.sched.add_room("R2", 150)
        self.sched.add_room("R3", 100)

    def test_add_room_and_validation(self) -> None:
        with self.assertRaises(ValueError):
            self.sched.add_room("", 50)
        with self.assertRaises(ValueError):
            self.sched.add_room("   ", 50)
        with self.assertRaises(ValueError):
            self.sched.add_room("R4", 0)
        with self.assertRaises(ValueError):
            self.sched.add_room("R4", -10)

    def test_schedule_talk_boundaries(self) -> None:
        # Exact 15 min duration at start of day (0 to 15) and exact capacity
        rec1 = self.sched.schedule_talk("T1", "Intro", "Alice", "R1", 0, 15, 100)
        self.assertEqual(rec1["talk_id"], "T1")

        # Exact 180 min duration at end of day (1260 to 1440) and min attendees (1)
        rec2 = self.sched.schedule_talk("T2", "Closing", "Bob", "R2", 1260, 1440, 1)
        self.assertEqual(rec2["talk_id"], "T2")

        # Invalid durations (14 and 181)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("T_short", "Short", "Charlie", "R3", 100, 114, 10)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("T_long", "Long", "Charlie", "R3", 100, 281, 10)

        # Invalid attendees (0 and capacity + 1)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("T_zero", "Zero", "Charlie", "R1", 200, 230, 0)
        with self.assertRaises(ValueError):
            self.sched.schedule_talk("T_over", "Over", "Charlie", "R1", 200, 230, 101)

    def test_bidirectional_speaker_cooldown_different_rooms(self) -> None:
        # Schedule middle talk in R1: [100, 160]
        self.sched.schedule_talk("T_mid", "Mid Talk", "Alice", "R1", 100, 160, 50)

        # 1. Forward cooldown (after T_mid in R2):
        # Gap = 0 ([160, 190]) -> violation
        with self.assertRaisesRegex(ValueError, "Speaker cooldown violation"):
            self.sched.schedule_talk("T_after_0", "After 0", "Alice", "R2", 160, 190, 50)
        # Gap = 14 ([174, 204]) -> violation
        with self.assertRaisesRegex(ValueError, "Speaker cooldown violation"):
            self.sched.schedule_talk("T_after_14", "After 14", "Alice", "R2", 174, 204, 50)
        # Gap = 15 ([175, 205]) -> allowed
        rec_after = self.sched.schedule_talk("T_after_15", "After 15", "Alice", "R2", 175, 205, 50)
        self.assertEqual(rec_after["start_min"], 175)

        # 2. Backward cooldown (before T_mid in R2):
        # Gap = 0 ([70, 100]) -> violation
        with self.assertRaisesRegex(ValueError, "Speaker cooldown violation"):
            self.sched.schedule_talk("T_before_0", "Before 0", "Alice", "R2", 70, 100, 50)
        # Gap = 14 ([56, 86]) -> violation
        with self.assertRaisesRegex(ValueError, "Speaker cooldown violation"):
            self.sched.schedule_talk("T_before_14", "Before 14", "Alice", "R2", 56, 86, 50)
        # Gap = 15 ([55, 85]) -> allowed
        rec_before = self.sched.schedule_talk("T_before_15", "Before 15", "Alice", "R2", 55, 85, 50)
        self.assertEqual(rec_before["end_min"], 85)

    def test_same_room_back_to_back_allowed_both_orders(self) -> None:
        self.sched.schedule_talk("T_mid", "Mid Talk", "Alice", "R1", 200, 260, 50)
        # Immediately before in same room R1: [170, 200]
        rec_prev = self.sched.schedule_talk("T_prev", "Prev Talk", "Alice", "R1", 170, 200, 50)
        self.assertEqual(rec_prev["end_min"], 200)
        # Immediately after in same room R1: [260, 290]
        rec_next = self.sched.schedule_talk("T_next", "Next Talk", "Alice", "R1", 260, 290, 50)
        self.assertEqual(rec_next["start_min"], 260)
        # 5-minute gap in same room R1: [295, 325]
        rec_gap5 = self.sched.schedule_talk("T_gap5", "Gap 5", "Alice", "R1", 295, 325, 50)
        self.assertEqual(rec_gap5["start_min"], 295)

    def test_find_available_rooms_with_and_without_speaker(self) -> None:
        # Alice has a talk in R1 from 100 to 160
        self.sched.schedule_talk("T1", "Talk 1", "Alice", "R1", 100, 160, 80)

        # Without speaker: during [100, 160], R1 is occupied, R3 (100) and R2 (150) are available
        self.assertEqual(self.sched.find_available_rooms(100, 160, 100), ["R3", "R2"])

        # With speaker="Alice" during overlapping window [120, 150]: no rooms available
        self.assertEqual(self.sched.find_available_rooms(120, 150, 50, speaker="Alice"), [])

        # With speaker="Alice" in forward cooldown window [160, 190] (gap=0) and [174, 204] (gap=14):
        # Same room R1 IS available (0-gap allowed in same room), different rooms R2 and R3 are NOT!
        self.assertEqual(self.sched.find_available_rooms(160, 190, 50, speaker="Alice"), ["R1"])
        self.assertEqual(self.sched.find_available_rooms(174, 204, 50, speaker="Alice"), ["R1"])

        # At exact 15-min gap after ([175, 205]): R1, R3, R2 all available
        self.assertEqual(
            self.sched.find_available_rooms(175, 205, 50, speaker="Alice"),
            ["R1", "R3", "R2"],
        )

        # With speaker="Alice" in backward cooldown window [70, 100] (gap=0) and [56, 86] (gap=14):
        # Same room R1 IS available, different rooms R2 and R3 are NOT!
        self.assertEqual(self.sched.find_available_rooms(70, 100, 50, speaker="Alice"), ["R1"])
        self.assertEqual(self.sched.find_available_rooms(56, 86, 50, speaker="Alice"), ["R1"])

        # At exact 15-min gap before ([55, 85]): R1, R3, R2 all available
        self.assertEqual(
            self.sched.find_available_rooms(55, 85, 50, speaker="Alice"),
            ["R1", "R3", "R2"],
        )

    def test_out_of_scope_todos_not_implemented(self) -> None:
        self.assertFalse(hasattr(self.sched, "auto_assign_catering"))
        self.assertFalse(hasattr(self.sched, "export_ical_feed"))


if __name__ == "__main__":
    unittest.main()
