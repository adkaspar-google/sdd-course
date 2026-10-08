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

"""Clean-room implementation of CoursePulse regenerated from SPEC.md."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import threading
from typing import Optional


class EnrollmentStatus(str, Enum):
    ENROLLED = "ENROLLED"
    WAITLISTED = "WAITLISTED"
    DROPPED = "DROPPED"
    NOT_FOUND = "NOT_FOUND"


@dataclass(frozen=True)
class EnrollmentResult:
    course_id: str
    student_id: str
    status: EnrollmentStatus
    waitlist_position: Optional[int] = None


@dataclass(frozen=True)
class DropResult:
    course_id: str
    dropped_student_id: str
    status: EnrollmentStatus
    promoted_student_id: Optional[str] = None


@dataclass(frozen=True)
class CourseRoster:
    course_id: str
    title: str
    capacity: int
    enrolled: tuple[str, ...]
    waitlist: tuple[str, ...]


@dataclass
class _CourseState:
    course_id: str
    title: str
    capacity: int
    enrolled: list[str] = field(default_factory=list)
    waitlist: deque[str] = field(default_factory=deque)


class CoursePulseService:
    """Thread-safe CoursePulse Enrollment & Waitlist Service (REQ-0001..0006)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._courses: dict[str, _CourseState] = {}

    def _get_course(self, course_id: str) -> _CourseState:
        course = self._courses.get(course_id)
        if course is None:
            raise KeyError(f"Course not found: {course_id}")
        return course

    def create_course(
        self, course_id: str, title: str, capacity: int
    ) -> CourseRoster:
        if not course_id or not title:
            raise ValueError("course_id and title must be non-empty")
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        with self._lock:
            if course_id in self._courses:
                raise ValueError(f"Course already exists: {course_id}")
            state = _CourseState(
                course_id=course_id, title=title, capacity=capacity
            )
            self._courses[course_id] = state
            return CourseRoster(
                course_id=course_id,
                title=title,
                capacity=capacity,
                enrolled=(),
                waitlist=(),
            )

    def enroll(self, course_id: str, student_id: str) -> EnrollmentResult:
        if not student_id:
            raise ValueError("student_id must be non-empty")
        with self._lock:
            course = self._get_course(course_id)
            if student_id in course.enrolled:
                return EnrollmentResult(
                    course_id=course_id,
                    student_id=student_id,
                    status=EnrollmentStatus.ENROLLED,
                    waitlist_position=None,
                )
            if student_id in course.waitlist:
                pos = list(course.waitlist).index(student_id) + 1
                return EnrollmentResult(
                    course_id=course_id,
                    student_id=student_id,
                    status=EnrollmentStatus.WAITLISTED,
                    waitlist_position=pos,
                )
            if len(course.enrolled) < course.capacity:
                course.enrolled.append(student_id)
                return EnrollmentResult(
                    course_id=course_id,
                    student_id=student_id,
                    status=EnrollmentStatus.ENROLLED,
                    waitlist_position=None,
                )
            course.waitlist.append(student_id)
            return EnrollmentResult(
                course_id=course_id,
                student_id=student_id,
                status=EnrollmentStatus.WAITLISTED,
                waitlist_position=len(course.waitlist),
            )

    def drop(self, course_id: str, student_id: str) -> DropResult:
        if not student_id:
            raise ValueError("student_id must be non-empty")
        with self._lock:
            course = self._get_course(course_id)
            if student_id in course.enrolled:
                course.enrolled.remove(student_id)
                promoted: Optional[str] = None
                if course.waitlist:
                    promoted = course.waitlist.popleft()
                    course.enrolled.append(promoted)
                return DropResult(
                    course_id=course_id,
                    dropped_student_id=student_id,
                    status=EnrollmentStatus.DROPPED,
                    promoted_student_id=promoted,
                )
            if student_id in course.waitlist:
                course.waitlist.remove(student_id)
                return DropResult(
                    course_id=course_id,
                    dropped_student_id=student_id,
                    status=EnrollmentStatus.DROPPED,
                    promoted_student_id=None,
                )
            return DropResult(
                course_id=course_id,
                dropped_student_id=student_id,
                status=EnrollmentStatus.NOT_FOUND,
                promoted_student_id=None,
            )

    def get_roster(self, course_id: str) -> CourseRoster:
        with self._lock:
            course = self._get_course(course_id)
            return CourseRoster(
                course_id=course.course_id,
                title=course.title,
                capacity=course.capacity,
                enrolled=tuple(course.enrolled),
                waitlist=tuple(course.waitlist),
            )
