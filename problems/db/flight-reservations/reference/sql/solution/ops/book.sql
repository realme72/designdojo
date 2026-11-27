with seat as (
  select s.id, s.seat_no from seats s
  where s.flight_id = :flight_id and s.class = :class
    and not exists (select 1 from reservations r where r.seat_id = s.id)
  order by s.seat_no
  limit 1
  for update skip locked
),
r as (
  insert into reservations (pnr, passenger, seat_id)
  select :pnr, :passenger, (select id from seat)        -- no free seat -> NULL -> refused
  returning seat_id
)
select s.seat_no from r join seats s on s.id = r.seat_id;
