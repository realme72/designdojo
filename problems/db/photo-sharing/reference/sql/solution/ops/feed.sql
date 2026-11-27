select p.id as post_id, u.username as author, p.caption,
       (select count(*) from likes l where l.post_id = p.id)    as likes,
       (select count(*) from comments c where c.post_id = p.id) as comments
from follows f
join posts p on p.user_id = f.followee_id
join users u on u.id = p.user_id
where f.follower_id = :user_id
order by p.posted_at desc, p.id desc
limit :n;
