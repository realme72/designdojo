select coalesce(sum(x.fee), 0)
from sessions x join spots s on s.id = x.spot_id
where s.lot_id = :lot_id
  and x.exited_at >= (:day::date)::timestamp at time zone 'UTC'
  and x.exited_at <  (:day::date + 1)::timestamp at time zone 'UTC';
