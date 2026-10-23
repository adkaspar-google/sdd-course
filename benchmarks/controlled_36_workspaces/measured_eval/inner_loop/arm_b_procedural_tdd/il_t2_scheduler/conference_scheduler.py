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
"""Starter module for IL-T2: ConferenceScheduler."""

from typing import Any, Dict, List, Optional


class ConferenceScheduler:
    """Manages conference rooms and talk schedules."""

    def __init__(self) -> None:
        self.rooms: Dict[str, int] = {}
        self.talks: Dict[str, Dict[str, Any]] = {}

    def add_room(self, room_id: str, capacity: int) -> None:
        if not isinstance(room_id, str) or not room_id.strip():
            raise ValueError("Invalid room_id")
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity <= 0:
            raise ValueError("Invalid capacity")
        self.rooms[room_id.strip()] = capacity

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
        if not isinstance(room_id, str) or not room_id.strip():
            raise ValueError("Invalid room_id")

        talk_id = talk_id.strip()
        title = title.strip()
        speaker = speaker.strip()
        room_id = room_id.strip()

        if room_id not in self.rooms:
            raise ValueError("Unknown room")
        if talk_id in self.talks:
            raise ValueError("Duplicate talk_id")
        if start_min < 0 or end_min > 1440 or start_min >= end_min:
            raise ValueError("Invalid time window")
        duration = end_min - start_min
        if duration < 15 or duration > 180:
            raise ValueError("Invalid duration")
        if expected_attendees <= 0 or expected_attendees > self.rooms[room_id]:
            raise ValueError("Exceeds room capacity or non-positive attendees")

        for existing in self.talks.values():
            if existing["room_id"] == room_id:
                if start_min < existing["end_min"] and end_min > existing["start_min"]:
                    raise ValueError("Room time conflict")
            if existing["speaker"] == speaker:
                if existing["room_id"] == room_id:
                    if start_min < existing["end_min"] and end_min > existing["start_min"]:
                        raise ValueError("Speaker time conflict")
                else:
                    if (
                        start_min < existing["end_min"] + 15
                        and existing["start_min"] < end_min + 15
                    ):
                        raise ValueError(
                            "Speaker conflict or cross-room cooldown violation"
                        )

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
        if not isinstance(room_id, str) or room_id.strip() not in self.rooms:
            raise ValueError("Unknown room")
        room_id = room_id.strip()
        room_talks = [t for t in self.talks.values() if t["room_id"] == room_id]
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
        clean_speaker = (
            speaker.strip() if isinstance(speaker, str) and speaker.strip() else None
        )
        available: List[str] = []
        for room_id, capacity in self.rooms.items():
            if capacity < min_capacity:
                continue
            conflict = False
            for existing in self.talks.values():
                if existing["room_id"] == room_id:
                    if (
                        start_min < existing["end_min"]
                        and end_min > existing["start_min"]
                    ):
                        conflict = True
                        break
                if clean_speaker is not None and existing["speaker"] == clean_speaker:
                    if existing["room_id"] == room_id:
                        if (
                            start_min < existing["end_min"]
                            and end_min > existing["start_min"]
                        ):
                            conflict = True
                            break
                    else:
                        if (
                            start_min < existing["end_min"] + 15
                            and existing["start_min"] < end_min + 15
                        ):
                            conflict = True
                            break
            if not conflict:
                available.append(room_id)
        available.sort(key=lambda r: (self.rooms[r], r))
        return available
