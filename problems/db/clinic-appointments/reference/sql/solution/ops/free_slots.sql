select slot
from generate_series((:day::date + time '09:00')::timestamp at time zone 'UTC',
                     (:day::date + time '16:30')::timestamp at time zone 'UTC',
                     interval '30 minutes') as slot
where not exists (
  select 1 from appointments a
  where a.doctor_id = :doctor_id and a.status = 'BOOKED'
    and tstzrange(a.starts_at, a.ends_at) && tstzrange(slot, slot + interval '30 minutes')
)
order by slot;
