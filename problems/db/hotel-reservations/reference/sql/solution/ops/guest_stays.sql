select r.number, b.check_in, b.check_out - b.check_in as nights, b.total, b.status
from bookings b
join rooms r on r.id = b.room_id
where b.guest_id = :guest_id
order by b.check_in, b.id;
