select r.number
from rooms r
where r.room_type_id = :room_type_id
  and not exists (
    select 1 from bookings b
    where b.room_id = r.id
      and b.status = 'CONFIRMED'
      and daterange(b.check_in, b.check_out) && daterange(:check_in, :check_out)
  )
order by r.number;
