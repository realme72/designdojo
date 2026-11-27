select p.id as post_id, p.title, coalesce(sum(v.value), 0) as score
from posts p
left join votes v on v.post_id = p.id
where p.community_id = :community_id
group by p.id
order by score desc, p.created_at desc, p.id
limit :n;
