with pick as (
  select t.id, t.label from dining_tables t
  where t.seats >= :party_size
    and not exists (select 1 from reservations r where r.table_id = t.id and not r.cancelled
                    and tstzrange(r.starts_at, r.ends_at) && tstzrange(:starts_at, :starts_at::timestamptz + interval '2 hours'))
  order by t.seats, t.label limit 1
),
r as (
  insert into reservations (table_id, guest, party_size, starts_at, ends_at)
  select (select id from pick), :guest, :party_size, :starts_at, :starts_at::timestamptz + interval '2 hours'
  returning id, table_id
)
select r.id as reservation_id, t.label as table_label from r join dining_tables t on t.id = r.table_id;
