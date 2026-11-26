# Course Registration System

Design course enrolment for a university: prerequisites, capacity, waitlists and limits.

## Requirements

1. `add_course(course_id, capacity, prerequisites)`: prerequisites must be existing courses
   (`UnknownCourse`); `capacity < 1` → `InvalidCapacity`; repeated id → `DuplicateCourse`.
2. `complete(student, course_id)` records a finished course on the student's transcript.
3. `enroll(student, course_id)` → `ENROLLED` if a seat is free, else `WAITLISTED` (FIFO).
   Checks, in order: `UnknownCourse`; already completed → `AlreadyCompleted`; already enrolled
   or waitlisted → `AlreadyRegistered`; a prerequisite not completed → `MissingPrerequisite`;
   for a seat (not the waitlist), the student already holds `max_courses` (config)
   enrolments → `TooManyCourses`.
4. `drop(student, course_id)` removes an enrolment or waitlist entry (`NotRegistered`
   otherwise). When an enrolled student drops, the **first waitlisted student who is still
   eligible** (under their course limit) is promoted; ineligible ones keep their place.
5. `roster(course_id)` → enrolled students sorted; `waitlist(course_id)` → waitlisted in order.
6. Registration opens and thousands enrol at once: capacity is never exceeded.

## Things an interviewer will push on

- How would you add rules (year restrictions, time clashes) without touching enroll()?
- How are waitlisted students notified on promotion?
- What lock guards a course, and what about the per-student limit across courses?
