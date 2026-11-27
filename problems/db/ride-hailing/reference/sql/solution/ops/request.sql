with pick as (
  select d.id, d.name from drivers d
  where d.online and d.class = :class and d.lat is not null
    and not exists (select 1 from trips t where t.driver_id = d.id and t.status = 'ACCEPTED')
  order by (d.lat - :lat) ^ 2 + (d.lng - :lng) ^ 2, d.id
  limit 1
  for update skip locked
),
t as (
  insert into trips (rider_id, driver_id, class, pickup_lat, pickup_lng, requested_at)
  select :rider_id, (select id from pick), :class, :lat, :lng, :at    -- no driver -> NULL -> refused
  returning id, driver_id
)
select t.id as trip_id, d.name as driver from t join drivers d on d.id = t.driver_id;
