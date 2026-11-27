with v as (
  insert into vehicles (plate) values (:plate) on conflict (plate) do update set plate = excluded.plate returning id
),
spot as (
  select s.id, s.number from spots s
  where s.lot_id = :lot_id and s.type = :type
    and not exists (select 1 from sessions x where x.spot_id = s.id and x.exited_at is null)
  order by s.number limit 1
  for update skip locked
),
ins as (
  insert into sessions (spot_id, vehicle_id, entered_at)
  select (select id from spot), v.id, :at from v     -- no free spot -> NULL -> refused
  returning spot_id
)
select s.number as spot_no from ins join spots s on s.id = ins.spot_id;
