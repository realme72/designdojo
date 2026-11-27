select count(c.lesson_id) as done, count(l.id) as total,
       case when count(l.id) = 0 then 0 else (100 * count(c.lesson_id) / count(l.id)) end as percent
from lessons l
left join completions c on c.lesson_id = l.id and c.student_id = :student_id
where l.course_id = :course_id;
