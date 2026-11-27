insert into completions (student_id, course_id, lesson_id, completed_at)
select :student_id, (select course_id from lessons where id = :lesson_id), :lesson_id, :at
on conflict (student_id, lesson_id) do nothing;
