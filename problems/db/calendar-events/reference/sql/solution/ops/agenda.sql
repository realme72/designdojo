select e.title, e.starts_at, a.response
from attendees a join events e on e.id = a.event_id
where a.user_id = :user_id and a.response <> 'DECLINED'
  and e.starts_at < :to and e.ends_at > :from
order by e.starts_at, e.title;
