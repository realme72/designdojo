select t.name as room_type,
       count(distinct b.room_id) as occupied,
       count(distinct r.id)      as rooms
from room_types t
left join rooms r    on r.room_type_id = t.id
left join bookings b on b.room_id = r.id
                    and b.status = 'CONFIRMED'
                    and b.check_in <= :day and :day < b.check_out
group by t.id, t.name
order by t.name;
