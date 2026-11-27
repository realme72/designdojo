with mine as (
  select e.id, e.title, e.starts_at, e.ends_at from attendees a join events e on e.id = a.event_id
  where a.user_id = :user_id and a.response = 'ACCEPTED'
)
select x.title as first, y.title as second
from mine x join mine y
  on x.starts_at < y.ends_at and y.starts_at < x.ends_at
 and (x.starts_at, x.id) < (y.starts_at, y.id)
order by x.starts_at, x.id, y.starts_at;
