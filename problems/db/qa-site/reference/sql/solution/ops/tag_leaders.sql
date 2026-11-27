select u.name, coalesce(sum(v.value), 0) as score
from answers a
join question_tags qt on qt.question_id = a.question_id
join tags g on g.id = qt.tag_id and g.name = :tag
join users u on u.id = a.user_id
left join answer_votes v on v.answer_id = a.id
group by u.id, u.name
order by score desc, u.name
limit :n;
