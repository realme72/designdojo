select t.label, t.seats from dining_tables t
where not exists (select 1 from reservations r where r.table_id = t.id and not r.cancelled
                  and tstzrange(r.starts_at, r.ends_at) @> :at::timestamptz)
order by t.seats, t.label;
