select count(r.id) as booked, count(s.id) as capacity
from seats s left join reservations r on r.seat_id = s.id
where s.flight_id = :flight_id;
