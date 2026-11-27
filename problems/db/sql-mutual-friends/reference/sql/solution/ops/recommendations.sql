with links as (select user_a as me, user_b as friend from friendships union all select user_b, user_a from friendships)
select p.name, count(*) as mutuals
from links mine join links theirs on theirs.me = mine.friend
join people p on p.id = theirs.friend
where mine.me = :person_id and theirs.friend <> :person_id
  and not exists (select 1 from links f where f.me = :person_id and f.friend = theirs.friend)
group by p.id, p.name order by mutuals desc, p.name limit :n;
