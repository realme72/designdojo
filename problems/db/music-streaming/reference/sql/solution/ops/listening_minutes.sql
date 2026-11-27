select coalesce(sum(seconds), 0) / 60 as minutes
from plays
where user_id = :user_id
  and played_at >= (:day::date)::timestamp at time zone 'UTC'
  and played_at <  (:day::date + 1)::timestamp at time zone 'UTC';
