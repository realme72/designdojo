# Instructor override

An instructor can let a specific student skip the prerequisites of one course:
`grant_override(student, course_id)` (`UnknownCourse` for an unknown course). The override
waives **only** the prerequisite check for that student and course; every other rule
(already completed, already registered, course limit, waitlist) still applies.

*Interviewer's question:* how do you switch off one rule for one student without an `if` in every rule?
