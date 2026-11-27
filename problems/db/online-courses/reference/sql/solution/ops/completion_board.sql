select s.name as student,
       case when t.total = 0 then 0 else 100 * (select count(*) from completions c
                                                  where c.student_id = e.student_id and c.course_id = e.course_id) / t.total end as percent
from enrollments e
join students s on s.id = e.student_id
cross join (select count(*) as total from lessons where course_id = :course_id) t
where e.course_id = :course_id
order by percent desc, s.name;
