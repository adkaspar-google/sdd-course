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

"""Adversarial Clean-Room Rebuild Contract Suite for CoursePulse (SPEC.md)."""

import unittest
from coursepulse import (
    CoursePulseService,
    EnrollmentStatus,
)


class TestCoursePulseRebuildContract(unittest.TestCase):

    def test_req0001_course_creation_and_validation(self) -> None:
        svc = CoursePulseService()
        roster = svc.create_course("CS-401", "Spec-Driven Engineering", capacity=2)
        self.assertEqual(roster.course_id, "CS-401")
        self.assertEqual(roster.capacity, 2)
        self.assertEqual(roster.enrolled, ())
        self.assertEqual(roster.waitlist, ())

        with self.assertRaises(ValueError):
            svc.create_course("CS-401", "Duplicate", capacity=2)
        with self.assertRaises(ValueError):
            svc.create_course("CS-000", "Zero Cap", capacity=0)
        with self.assertRaises(ValueError):
            svc.create_course("", "Empty ID", capacity=5)

    def test_req0002_seat_allocation_and_waitlist_overflow(self) -> None:
        svc = CoursePulseService()
        svc.create_course("CS-401", "Spec-Driven Engineering", capacity=2)

        r1 = svc.enroll("CS-401", "stu-1")
        self.assertEqual(r1.status, EnrollmentStatus.ENROLLED)
        self.assertIsNone(r1.waitlist_position)

        r2 = svc.enroll("CS-401", "stu-2")
        self.assertEqual(r2.status, EnrollmentStatus.ENROLLED)
        self.assertIsNone(r2.waitlist_position)

        r3 = svc.enroll("CS-401", "stu-3")
        self.assertEqual(r3.status, EnrollmentStatus.WAITLISTED)
        self.assertEqual(r3.waitlist_position, 1)

        r4 = svc.enroll("CS-401", "stu-4")
        self.assertEqual(r4.status, EnrollmentStatus.WAITLISTED)
        self.assertEqual(r4.waitlist_position, 2)

    def test_req0003_idempotent_duplicate_enrollment(self) -> None:
        svc = CoursePulseService()
        svc.create_course("CS-401", "Spec-Driven Engineering", capacity=1)
        svc.enroll("CS-401", "stu-1")
        svc.enroll("CS-401", "stu-2")
        svc.enroll("CS-401", "stu-3")

        dup_enrolled = svc.enroll("CS-401", "stu-1")
        self.assertEqual(dup_enrolled.status, EnrollmentStatus.ENROLLED)
        self.assertIsNone(dup_enrolled.waitlist_position)

        dup_waitlisted = svc.enroll("CS-401", "stu-3")
        self.assertEqual(dup_waitlisted.status, EnrollmentStatus.WAITLISTED)
        self.assertEqual(dup_waitlisted.waitlist_position, 2)

        roster = svc.get_roster("CS-401")
        self.assertEqual(roster.enrolled, ("stu-1",))
        self.assertEqual(roster.waitlist, ("stu-2", "stu-3"))

    def test_req0004_fifo_waitlist_promotion_on_enrolled_drop(self) -> None:
        svc = CoursePulseService()
        svc.create_course("CS-401", "Spec-Driven Engineering", capacity=1)
        svc.enroll("CS-401", "stu-1")
        svc.enroll("CS-401", "stu-2")
        svc.enroll("CS-401", "stu-3")

        drop_res = svc.drop("CS-401", "stu-1")
        self.assertEqual(drop_res.status, EnrollmentStatus.DROPPED)
        self.assertEqual(drop_res.promoted_student_id, "stu-2")

        roster = svc.get_roster("CS-401")
        self.assertEqual(roster.enrolled, ("stu-2",))
        self.assertEqual(roster.waitlist, ("stu-3",))

    def test_req0005_waitlist_drop_and_non_member_drop(self) -> None:
        svc = CoursePulseService()
        svc.create_course("CS-401", "Spec-Driven Engineering", capacity=1)
        svc.enroll("CS-401", "stu-1")
        svc.enroll("CS-401", "stu-2")

        wl_drop = svc.drop("CS-401", "stu-2")
        self.assertEqual(wl_drop.status, EnrollmentStatus.DROPPED)
        self.assertIsNone(wl_drop.promoted_student_id)

        missing_drop = svc.drop("CS-401", "stu-999")
        self.assertEqual(missing_drop.status, EnrollmentStatus.NOT_FOUND)
        self.assertIsNone(missing_drop.promoted_student_id)

    def test_req0006_immutable_roster_snapshot_and_missing_course_errors(
        self,
    ) -> None:
        svc = CoursePulseService()
        with self.assertRaises(KeyError):
            svc.get_roster("NO-SUCH-COURSE")
        with self.assertRaises(KeyError):
            svc.enroll("NO-SUCH-COURSE", "stu-1")


if __name__ == "__main__":
    unittest.main()
