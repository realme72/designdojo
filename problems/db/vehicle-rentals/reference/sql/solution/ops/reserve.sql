with pick as (
  select v.id, v.plate from vehicles v
  where v.category = :category
    and not exists (select 1 from rentals r where r.vehicle_id = v.id and r.status <> 'CANCELLED'
                    and daterange(r.from_day, r.to_day) && daterange(:from_day, :to_day))
  order by v.plate limit 1
),
r as (
  insert into rentals (vehicle_id, customer_id, from_day, to_day)
  select (select id from pick), :customer_id, :from_day, :to_day
  returning id, vehicle_id
)
select r.id as rental_id, v.plate from r join vehicles v on v.id = r.vehicle_id;
