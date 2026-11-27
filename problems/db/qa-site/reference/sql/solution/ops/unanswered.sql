select q.id, q.title
from questions q
join question_tags qt on qt.question_id = q.id
join tags g on g.id = qt.tag_id and g.name = :tag
where not exists (select 1 from answers a where a.question_id = q.id)
order by q.asked_at, q.id;
