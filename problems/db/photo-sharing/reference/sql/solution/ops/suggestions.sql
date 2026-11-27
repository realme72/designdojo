select u.username, count(*) as mutuals
from follows mine
join follows theirs on theirs.follower_id = mine.followee_id
join users u on u.id = theirs.followee_id
where mine.follower_id = :user_id
  and theirs.followee_id <> :user_id
  and not exists (select 1 from follows f where f.follower_id = :user_id and f.followee_id = theirs.followee_id)
group by u.id, u.username
order by mutuals desc, u.username;
