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
"""Conference Room & Speaker Cooldown Scheduler."""

from __future__ import annotations
from typing import Any


class ConferenceScheduler:
    def __init__(self) -> None:
        self.rooms: dict[str, int] = {}
        self.talks: dict[str, dict[str, Any]] = {}

    def add_room(self, room_id: str, capacity: int) -> None:
        if not isinstance(room_id, str) or not room_id.strip() or capacity <= 0:
            raise ValueError("Invalid room")
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
    ) -> dict[str, Any]:
        if not talk_id or not title or not speaker or room_id not in self.rooms:
            raise ValueError("Invalid parameters")
        if talk_id in self.talks:
            raise ValueError("Duplicate talk_id")
        if start_min < 0 or end_min > 1440 or start_min >= end_min:
            raise ValueError("Invalid time window")
        if (end_min - start_min) < 15 or (end_min - start_min) > 180:
            raise ValueError("Invalid talk duration")
        if expected_attendees <= 0 or expected_attendees > self.rooms[room_id]:
            raise ValueError("Invalid attendees")

        for existing in self.talks.values():
            if existing["room_id"] == room_id:
                if start_min < existing["end_min"] and end_min > existing["start_min"]:
                    raise ValueError("Room overlap")
            if existing["speaker"] == speaker:
                if start_min < existing["end_min"] and end_min > existing["start_min"]:
                    raise ValueError("Speaker overlap")
                if existing["room_id"] != room_id and (
                    0 <= start_min - existing["end_min"] < 15
                    or 0 <= existing["start_min"] - end_min < 15
                ):
                    raise ValueError("Speaker cooldown violation")

        rec = {
            "talk_id": talk_id,
            "title": title,
            "speaker": speaker,
            "room_id": room_id,
            "start_min": start_min,
            "end_min": end_min,
            "expected_attendees": expected_attendees,
        }
        self.talks[talk_id] = rec
        return dict(rec)

    def cancel_talk(self, talk_id: str) -> bool:
        return self.talks.pop(talk_id, None) is not None

    def get_room_utilization(self, room_id: str) -> float:
        if room_id not in self.rooms:
            raise ValueError("Unknown room")
        room_talks = [t for t in self.talks.values() if t["room_id"] == room_id]
        if not room_talks:
            return 0.0
        span = max(t["end_min"] for t in room_talks) - min(t["start_min"] for t in room_talks)
        occupied = sum(t["end_min"] - t["start_min"] for t in room_talks)
        return round((occupied / span) * 100.0, 2)

    def find_available_rooms(
        self,
        start_min: int,
        end_min: int,
        min_capacity: int,
        speaker: str | None = None,
    ) -> list[str]:
        avail = []
        for r_id, cap in self.rooms.items():
            if cap < min_capacity:
                continue
            conflict = False
            for t in self.talks.values():
                if t["room_id"] == r_id and start_min < t["end_min"] and end_min > t["start_min"]:
                    conflict = True
                    break
                if speaker is not None and t["speaker"] == speaker:
                    if start_min < t["end_min"] and end_min > t["start_min"]:
                        conflict = True
                        break
                    if t["room_id"] != r_id and (
                        0 <= start_min - t["end_min"] < 15
                        or 0 <= t["start_min"] - end_min < 15
                    ):
                        conflict = True
                        break
            if not conflict:
                avail.append(r_id)
        avail.sort(key=lambda r: (self.rooms[r], r))
        return avail

    # TODO: implement auto_assign_catering(self, room_id: str) -> dict helper
    # TODO: implement export_ical_feed(self) -> str helper
