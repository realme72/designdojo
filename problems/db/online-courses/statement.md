# Online Courses (Udemy)

> **Interview questions** (tab next to Problem): start there.

Design courses, enrolments and progress tracking (**PostgreSQL 17**).

## Requirements

1. **Courses** have a title and ordered **lessons** (positions 1, 2, 3 … in the order added).
2. **Students** **enrol** in courses (once each).
3. Students **complete** lessons — only lessons of courses they're enrolled in. Completing the
   same lesson again changes nothing.

## Operations

| Operation | Returns |
|---|---|
| `add_course(:title)`, `add_student(:name)` | one row: `id` |
| `add_lesson(:course_id, :title)` | one row: `id` (appended at the next position) |
| `enroll(:student_id, :course_id)` | nothing |
| `complete(:student_id, :lesson_id, :at)` | nothing |
| `progress(:student_id, :course_id)` | one row: `done`, `total`, `percent` (whole number, rounded down) |
| `next_lesson(:student_id, :course_id)` | one row: `title`: the lowest-position lesson not completed (no row if all done) |
| `completion_board(:course_id)` | rows `student`, `percent`: every enrolled student, by percent desc then name |
