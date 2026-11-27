select l.title from lessons l
where l.course_id = :course_id
  and not exists (select 1 from completions c where c.lesson_id = l.id and c.student_id = :student_id)
order by l.position limit 1;
