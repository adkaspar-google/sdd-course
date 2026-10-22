"""Starter module for IL-T2: ConferenceScheduler."""

from typing import Any, Dict, List, Optional


class ConferenceScheduler:
    """Manages conference rooms and talk schedules."""

    def __init__(self) -> None:
        self.rooms: Dict[str, int] = {}
        self.talks: Dict[str, Dict[str, Any]] = {}
        # TODO(legacy): add export_markdown_schedule() and auto_assign_catering()

    def add_room(self, room_id: str, capacity: int) -> None:
        if not isinstance(room_id, str) or not room_id.strip():
            raise ValueError("Invalid room")
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("Invalid room capacity")
        self.rooms[room_id.strip()] = capacity

    def _has_room_conflict(
        self, room_id: str, start_min: int, end_min: int
    ) -> bool:
        for existing in self.talks.values():
            if existing["room_id"] == room_id:
                if start_min < existing["end_min"] and end_min > existing["start_min"]:
                    return True
        return False

    def _has_speaker_conflict(
        self, speaker: str, room_id: str, start_min: int, end_min: int
    ) -> bool:
        for existing in self.talks.values():
            if existing["speaker"] != speaker:
                continue
            if existing["room_id"] == room_id:
                if start_min < existing["end_min"] and end_min > existing["start_min"]:
                    return True
            else:
                if (
                    start_min < existing["end_min"] + 15
                    and end_min + 15 > existing["start_min"]
                ):
                    return True
        return False

    def schedule_talk(
        self,
        talk_id: str,
        title: str,
        speaker: str,
        room_id: str,
        start_min: int,
        end_min: int,
        expected_attendees: int,
    ) -> Dict[str, Any]:
        if not isinstance(talk_id, str) or not talk_id.strip():
            raise ValueError("Invalid talk_id")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Invalid title")
        if not isinstance(speaker, str) or not speaker.strip():
            raise ValueError("Invalid speaker")
        if not isinstance(room_id, str) or room_id not in self.rooms:
            raise ValueError("Unknown room")
        if talk_id in self.talks:
            raise ValueError("Duplicate talk_id")
        if (
            isinstance(start_min, bool)
            or isinstance(end_min, bool)
            or not isinstance(start_min, int)
            or not isinstance(end_min, int)
        ):
            raise ValueError("Invalid time bounds")
        if not (0 <= start_min < end_min <= 1440):
            raise ValueError("Invalid start/end time")
        duration = end_min - start_min
        if not (15 <= duration <= 180):
            raise ValueError("Invalid talk duration")
        if (
            isinstance(expected_attendees, bool)
            or not isinstance(expected_attendees, int)
            or not (0 < expected_attendees <= self.rooms[room_id])
        ):
            raise ValueError("Invalid expected_attendees")

        if self._has_room_conflict(room_id, start_min, end_min):
            raise ValueError("Room time conflict")
        if self._has_speaker_conflict(speaker, room_id, start_min, end_min):
            raise ValueError("Speaker conflict or cross-room cooldown violation")

        record = {
            "talk_id": talk_id,
            "title": title,
            "speaker": speaker,
            "room_id": room_id,
            "start_min": start_min,
            "end_min": end_min,
            "expected_attendees": expected_attendees,
        }
        self.talks[talk_id] = record
        return dict(record)

    def cancel_talk(self, talk_id: str) -> bool:
        return self.talks.pop(talk_id, None) is not None

    def get_room_utilization(self, room_id: str) -> float:
        if not isinstance(room_id, str) or room_id not in self.rooms:
            raise ValueError("Unknown room")
        room_talks = [
            t for t in self.talks.values() if t["room_id"] == room_id
        ]
        if not room_talks:
            return 0.0
        min_start = min(t["start_min"] for t in room_talks)
        max_end = max(t["end_min"] for t in room_talks)
        span = max_end - min_start
        if span <= 0:
            return 0.0
        occupied = sum(t["end_min"] - t["start_min"] for t in room_talks)
        return round((occupied / span) * 100.0, 2)

    def find_available_rooms(
        self,
        start_min: int,
        end_min: int,
        min_capacity: int,
        speaker: Optional[str] = None,
    ) -> List[str]:
        check_speaker = (
            speaker if (isinstance(speaker, str) and speaker.strip()) else None
        )
        available: List[str] = []
        for room_id, capacity in self.rooms.items():
            if capacity < min_capacity:
                continue
            if self._has_room_conflict(room_id, start_min, end_min):
                continue
            if check_speaker is not None and self._has_speaker_conflict(
                check_speaker, room_id, start_min, end_min
            ):
                continue
            available.append(room_id)
        available.sort(key=lambda r: (self.rooms[r], r))
        return available
