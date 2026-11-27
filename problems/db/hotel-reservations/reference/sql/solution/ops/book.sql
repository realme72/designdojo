insert into bookings (room_id, guest_id, check_in, check_out, total)
select r.id, :guest_id, :check_in, :check_out, (:check_out::date - :check_in::date) * t.nightly_rate
from rooms r
join room_types t on t.id = r.room_type_id
where r.id = :room_id
union all
select :room_id, :guest_id, :check_in, :check_out, null   -- unknown room: NULL total -> rejected
where not exists (select 1 from rooms where id = :room_id)
returning id as booking_id, total;
