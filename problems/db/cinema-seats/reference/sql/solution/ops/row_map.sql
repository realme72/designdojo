select st.label as seat, exists (select 1 from booked_seats b where b.show_id = sh.id and b.seat_id = st.id) as taken
from shows sh join seats st on st.screen_id = sh.screen_id and st.row_label = :row
where sh.id = :show_id
order by st.number;
