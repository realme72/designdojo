with links as (select user_a as me, user_b as friend from friendships union all select user_b, user_a from friendships)
select p.name from links l join people p on p.id = l.friend where l.me = :person_id order by p.name;
