# Enrollment & Waitlist Capability Specification

## Purpose
The `enrollment` capability governs student seat allocation, capacity enforcement, deterministic FIFO waitlist promotion, and idempotent enrollment mutations for university courses in the CoursePulse service (`labs/lab_06_capstone_ssot_and_rebuild_test/`).

## Requirements

### Requirement: Course Creation and Capacity Validation (REQ-0001)
The system SHALL allow creation of courses with a unique `course_id`, non-empty `title`, and integer `capacity >= 1`.

#### Scenario: Valid course creation
- **GIVEN** no course with `course_id="CS-401"` exists
- **WHEN** `create_course(course_id="CS-401", title="Spec-Driven Engineering", capacity=2)` is invoked
- **THEN** the course is stored with `enrolled_count=0`, `waitlist_count=0`, and `capacity=2`

#### Scenario: Invalid non-positive capacity rejected
- **GIVEN** an administrator attempts to create a course with `capacity=0`
- **WHEN** `create_course(course_id="CS-000", title="Invalid", capacity=0)` is invoked
- **THEN** the system MUST raise `ValueError`

### Requirement: Seat Allocation and Waitlist Overflow (REQ-0002)
When a student requests enrollment in an existing course, the system SHALL allocate a confirmed seat (`ENROLLED`) if `enrolled_count < capacity`, and SHALL otherwise append the student to a deterministic FIFO waitlist (`WAITLISTED`) with a 1-based position.

#### Scenario: Direct enrollment when capacity is available
- **GIVEN** course `"CS-401"` has `capacity=2` and `0` enrolled students
- **WHEN** student `"stu-1"` calls `enroll("CS-401", "stu-1")`
- **THEN** the response status MUST be `"ENROLLED"` with `waitlist_position=None`

#### Scenario: Waitlist placement when course is at capacity
- **GIVEN** course `"CS-401"` has `capacity=1` and `"stu-1"` is already `"ENROLLED"`
- **WHEN** student `"stu-2"` calls `enroll("CS-401", "stu-2")`
- **THEN** the response status MUST be `"WAITLISTED"` with `waitlist_position=1`

### Requirement: Idempotent Duplicate Enrollment Handling (REQ-0003)
The system SHALL treat repeated `enroll(course_id, student_id)` calls for an already-enrolled or already-waitlisted student as idempotent no-ops returning their current status without duplicating seats or altering waitlist order.

#### Scenario: Duplicate enrollment request by enrolled student
- **GIVEN** student `"stu-1"` is already `"ENROLLED"` in `"CS-401"`
- **WHEN** `"stu-1"` calls `enroll("CS-401", "stu-1")` again
- **THEN** the system MUST return status `"ENROLLED"` and `enrolled_count` MUST remain unchanged

### Requirement: Automatic FIFO Waitlist Promotion on Drop (REQ-0004)
When an `"ENROLLED"` student drops a course and the course waitlist is non-empty, the system SHALL atomically promote the student at the head of the FIFO waitlist (`waitlist_position=1`) to `"ENROLLED"` and decrement all remaining waitlist positions by 1.

#### Scenario: Dropping an enrolled seat promotes the first waitlisted student
- **GIVEN** course `"CS-401"` (`capacity=1`) has `"stu-1"` enrolled and `["stu-2", "stu-3"]` waitlisted in order
- **WHEN** `"stu-1"` calls `drop("CS-401", "stu-1")`
- **THEN** `"stu-2"` MUST transition to `"ENROLLED"`, `"stu-3"` MUST move to `waitlist_position=1`, and the drop result MUST report `promoted_student_id="stu-2"`
