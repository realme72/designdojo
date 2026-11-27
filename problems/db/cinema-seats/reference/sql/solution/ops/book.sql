with b as (   -- no seats requested: NULL customer -> NOT NULL refuses the booking
  insert into bookings (show_id, customer)
  values (:show_id, case when coalesce(cardinality(:seats::text[]), 0) > 0 then :customer end)
  returning id, show_id
),
wanted as (select distinct unnest(:seats::text[]) as label),
found as (
  select w.label, st.id as seat_id, sh.screen_id
  from wanted w
  join shows sh on sh.id = :show_id
  left join seats st on st.screen_id = sh.screen_id and st.label = w.label
),
ins as (
  insert into booked_seats (booking_id, show_id, screen_id, seat_id)
  select b.id, b.show_id, f.screen_id, f.seat_id from b, found f    -- unknown label -> NULL seat -> refused
)
select id as booking_id from b;
