with links as (select user_a as me, user_b as friend from friendships union all select user_b, user_a from friendships)
select p.name, count(l.friend) as friends from people p left join links l on l.me = p.id
group by p.id, p.name order by friends desc, p.name limit :n;
