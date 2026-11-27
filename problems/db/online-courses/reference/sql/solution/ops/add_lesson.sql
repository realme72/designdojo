insert into lessons (course_id, title, position)
select :course_id, :title, coalesce(max(position), 0) + 1 from lessons where course_id = :course_id
returning id;
