with links as (select user_a as me, user_b as friend from friendships union all select user_b, user_a from friendships)
select p.name from links x join links y on y.friend = x.friend join people p on p.id = x.friend
where x.me = :a_id and y.me = :b_id order by p.name;
